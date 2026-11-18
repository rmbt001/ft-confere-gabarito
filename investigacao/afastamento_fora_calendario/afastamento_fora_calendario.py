"""Simula a checagem "afastamento fora do calendário" numa rodada (18/11/2026). Só leitura: não muda o Jev, o pacote
do score nem o back.

A regra simulada (risco do lado a mais, por verba):
  1. a IA calculou adicional de periculosidade ou de insalubridade;
  2. o critério do P4 dessa verba manda excluir ou descontar afastamento, licença, auxílio-doença ou suspensão
     (pergunta nova ao Jev, lendo só o critério, como o bloco criterio_p4 do pacote; com --sem-jev, busca por texto);
  3. o calendário (P8) da verba não tem nenhum dia de afastamento, em nenhum mês (se tem, a ficha chegou).
Caso marcado em alta, média ou a calcular vai para a baixa (sinal de valor a mais); restrita e baixa não mudam.

Reforço só informativo (não entra na regra): meses em que o salário de contribuição do P7 some ou cai abaixo de
metade do salário-base, 2 ou mais meses seguidos, com a IA pagando o adicional e o P8 sem afastamento.

Como rodar: ver o README.md desta pasta. As respostas do Jev ficam em <saida>/jev_afastamento.json e não são
pedidas de novo.
"""
import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).parent
REPO = RAIZ.parents[1]
ADIC = re.compile(r"periculosidade|insalubridade", re.I)
EXCL = re.compile(r"(exclu|descont|dedu|abat|observ|proporcional|exceto|salvo|ressalvad)\w*[^.]{0,80}"
                  r"(afastament|suspens|licen[çc]a|aux[ií]lio[- ]doen|benef[ií]cio previd)", re.I)
CONTEXTO = ("O texto abaixo traz o critério de cálculo de cada verba de um processo trabalhista, como a leitura da "
            "decisão registrou. Responda só com base no critério da verba perguntada; se ele não trata do ponto, responda não.")
PERGUNTA = ("O critério da verba {n} (\"{verba}\") manda excluir ou descontar do cálculo os períodos de afastamento, "
            "licença, auxílio-doença ou suspensão do contrato de trabalho?")
QUATRO = ["0012290-30.2016.5.15.0071", "0001055-93.2015.5.05.0131", "0010211-93.2015.5.15.0045", "0000789-64.2021.5.13.0005"]


def faixas_de(arquivo, casos):
    """Faixa por CNJ: aceita {cnj: "alta"}, {cnj: {"faixa": ...}}, {"casos": {...}} ou [{"cnj", "faixa"}].
    Sem arquivo, usa o campo confianca de cada caso da comparação."""
    out = {}
    if arquivo:
        d = json.loads(Path(arquivo).read_text(encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("casos"), dict):
            d = d["casos"]
        itens = d.items() if isinstance(d, dict) else ((x.get("cnj"), x) for x in d)
        for k, v in itens:
            f = v if isinstance(v, str) else (v or {}).get("faixa") or ((v or {}).get("confianca") or {}).get("faixa")
            if k and f:
                out[k] = f
    for k, c in casos.items():
        out.setdefault(k, (c.get("confianca") or {}).get("faixa"))
    return out


def verbas_adicional(c):
    return [v for v in c.get("verbas") or [] if v.get("status") != "so_pjc" and " sobre " not in (v.get("nome_ia") or "")
            and ADIC.search(v.get("nome_ia") or "") and (v.get("total_ia") or 0) > 0]


def meses_pagos(v):
    return [x for x in v.get("competencias") or [] if ((x.get("ia") or {}).get("valor") or 0) > 0]


def p8_sem_afast(v):
    """O calendário da verba não tem nenhum dia de afastamento, em nenhum mês. Se tem em algum, o afastamento chegou
    (pela ficha) e não há descasamento."""
    return all(((x.get("cal_p8") or {}).get("afast") or 0) == 0 for x in v.get("competencias") or [])


def queda_contribuicao(c, v):
    """Meses (2+ seguidos) com salário de contribuição ausente ou < 50% do salário-base, IA pagando e P8 sem afastamento."""
    h = c.get("historico_p7") or {}
    rub = h.get("rubricas") or []
    i90 = next((i for i, r in enumerate(rub) if "BT090" in r), None)
    isc = next((i for i, r in enumerate(rub) if re.search(r"contribui", r, re.I)), None)
    if i90 is None or isc is None:
        return []
    L = {str(l.get("competencia"))[:7]: l.get("valores") or [] for l in h.get("linhas") or []}
    if sum(1 for x in L.values() if (x[isc] or 0) > 0) < 0.6 * max(len(L), 1):
        return []
    ms = []
    for x in meses_pagos(v):
        m = str(x.get("competencia"))[:7]
        if ((x.get("cal_p8") or {}).get("afast") or 0) == 0 and m in L and (L[m][i90] or 0):
            sc = L[m][isc]
            if sc is None or sc < 0.5 * L[m][i90]:
                ms.append(m)
    def ant(m):
        y, mm = int(m[:4]), int(m[5:7])
        return f"{y - (mm == 1):04d}-{12 if mm == 1 else mm - 1:02d}"
    s = set(ms)
    run = [m for m in ms if ant(m) in s or any(ant(o) == m for o in s)]
    return sorted(run) if len(run) >= 2 else []


def pergunta_jev(casos, alvos, saida, corte):
    """Uma chamada por caso, uma pergunta por verba de adicional. Cache em <saida>/jev_afastamento.json."""
    cache_f = saida / "jev_afastamento.json"
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}
    falta = [k for k in alvos if k not in cache]
    if falta:
        from dotenv import load_dotenv
        from typesafe_sdk import Noul, RetryPolicy, TypeSafeClient
        load_dotenv(REPO / ".env")   # TYPESAFE_API_KEY no .env da raiz do repositório (fora do Git)
        load_dotenv(RAIZ / ".env")
        cli = TypeSafeClient(retry=RetryPolicy(max_retries=3), timeout=120)
        for i, k in enumerate(falta, 1):
            c = casos[k]
            vs = verbas_adicional(c)
            texto = "\n\n".join(f"=== VERBA {n}: {v.get('nome_ia')} ===\n{str((v.get('p4') or {}).get('criterio') or '(sem critério registrado)')[:1800]}"
                                for n, v in enumerate(vs, 1))
            nome = ((c.get("processo") or {}).get("reclamante") or "").strip()
            if nome:
                texto = re.sub(re.escape(nome), "[RECLAMANTE]", texto, flags=re.I)
            qs = {f"q{n}": PERGUNTA.format(n=n, verba=v.get("nome_ia")) for n, v in enumerate(vs, 1)}
            try:
                r = cli.system_one(state=f"{CONTEXTO}\n\n{texto}", questions={q: Noul(instructions=t) for q, t in qs.items()})
                cache[k] = {v.get("nome_ia"): r.nouls[f"q{n}"].noul for n, v in enumerate(vs, 1)}
            except Exception as e:  # um caso com erro não derruba o lote; fica sem resposta e é pedido de novo depois
                print(f"  {k}: erro no Jev ({str(e)[:120]})")
            if i % 25 == 0 or i == len(falta):
                cache_f.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"  Jev: {i}/{len(falta)}")
    return cache


def medir(casos, faixa, nome):
    L = list(casos)
    if not L:
        return f"{nome}: 0 casos"
    b = sum(1 for k in L if casos[k]["a"] >= 80)
    m = sum(1 for k in L if casos[k]["mais"])
    return f"{nome}: {len(L)} casos · {100 * b / len(L):.0f}% com 80%+ · {m} calculam a mais ({100 * m / len(L):.0f}%)"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparacao", required=True)
    ap.add_argument("--faixas")
    ap.add_argument("--sem-jev", action="store_true")
    ap.add_argument("--corte", type=float, default=0.5)
    ap.add_argument("--cnjs")
    ap.add_argument("--saida")
    a = ap.parse_args()
    comp = Path(a.comparacao)
    saida = Path(a.saida) if a.saida else RAIZ / "saidas" / f"afastamento_{comp.parent.name}"
    saida.mkdir(parents=True, exist_ok=True)
    C = json.loads(comp.read_text(encoding="utf-8"))["casos"]
    F = faixas_de(a.faixas, C)
    so = {l.strip() for l in Path(a.cnjs).read_text(encoding="utf-8").splitlines() if l.strip()} if a.cnjs else None

    base = {}
    for k, c in C.items():
        q = c.get("quadro") or {}
        if not c.get("apto") or not q.get("total_pjc") or q.get("assertividade") is None or c.get("fora_regua"):
            continue
        if so is not None and k not in so:
            continue
        ia = q.get("total_ia") or 0
        base[k] = dict(a=q["assertividade"], mais=ia > 1.1 * q["total_pjc"], av=50_000 <= ia <= 200_000, faixa=F.get(k))
    com_adic = [k for k in base if verbas_adicional(C[k])]
    print(f"aptos com PJC: {len(base)} · com adicional calculado: {len(com_adic)} · faixa conhecida: {sum(1 for k in base if base[k]['faixa'])}")

    jev = {} if a.sem_jev else pergunta_jev(C, com_adic, saida, a.corte)
    linhas, marc = [], {}
    for k in com_adic:
        c = C[k]
        for v in verbas_adicional(c):
            crit = str((v.get("p4") or {}).get("criterio") or "")
            p = (jev.get(k) or {}).get(v.get("nome_ia"))
            manda_txt = bool(EXCL.search(crit))
            manda = (p >= a.corte) if p is not None else (manda_txt if a.sem_jev else False)
            sem = p8_sem_afast(v)
            sc = queda_contribuicao(c, v)
            vmais = (v.get("total_ia") or 0) > 1.1 * (v.get("total_pjc") or 0)
            acende = manda and sem
            linhas.append(dict(cnj=k, verba=v.get("nome_ia"), jev=p, texto=manda_txt, p8_sem_afast=sem, meses_contribuicao=";".join(sc),
                               acende=acende, total_ia=v.get("total_ia"), total_pjc=v.get("total_pjc"), verba_a_mais=vmais,
                               faixa=base[k]["faixa"], assertividade=base[k]["a"], apto_valor=base[k]["av"]))
            if acende:
                marc.setdefault(k, {"vmais": False})["vmais"] |= vmais
    with open(saida / "verbas_adicional.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]) if linhas else ["cnj"], delimiter=";")
        w.writeheader(); w.writerows(linhas)

    nova = {k: ("baixa" if k in marc and base[k]["faixa"] in ("alta", "media", "a_calcular") else base[k]["faixa"]) for k in base}
    acertos = [k for k in marc if marc[k]["vmais"]]
    print(f"\nfonte da decisão: {'busca por texto (--sem-jev)' if a.sem_jev else f'Jev, corte {a.corte}'}")
    print(f"marcados: {len(marc)} · na alta: {sum(1 for k in marc if base[k]['faixa'] == 'alta')} · apto valor: {sum(1 for k in marc if base[k]['av'])}")
    print(f"adicional calculado a mais (IA > PJC + 10% na verba): {len(acertos)} acertos × {len(marc) - len(acertos)} falsos positivos")
    tot_mais = sum(1 for k in com_adic if any((v.get("total_ia") or 0) > 1.1 * (v.get("total_pjc") or 0) for v in verbas_adicional(C[k])))
    print(f"base de comparação: adicional a mais em {tot_mais} de {len(com_adic)} aptos com adicional ({100 * tot_mais / max(len(com_adic), 1):.0f}%)")
    print("\nmarcados:")
    for k in sorted(marc, key=lambda k: base[k]["a"]):
        print(f"  {k} {base[k]['a']:7.1f}% · {base[k]['faixa']} → {nova[k]} · {'apto valor' if base[k]['av'] else '':10s} · "
              f"{'adicional a mais' if marc[k]['vmais'] else 'adicional ok'}")

    print("\nos quatro processos de 16/11:")
    for k in QUATRO:
        if k not in C:
            print(f"  {k}: não está nesta comparação"); continue
        ls = [l for l in linhas if l["cnj"] == k]
        if not ls:
            print(f"  {k}: {'não apto ou sem PJC' if k not in base else 'sem adicional calculado'}"); continue
        for l in ls:
            print(f"  {k} · {l['verba'][:40]} · Jev {l['jev'] if l['jev'] is None else round(l['jev'], 2)} · texto {l['texto']} · "
                  f"P8 sem afastamento {l['p8_sem_afast']} · contribuição cai {l['meses_contribuicao'] or '-'} · marcado {l['acende']}")

    print("\nfaixas antes × depois:")
    for nome, filtro in (("alta", lambda k: True), ("alta do apto valor", lambda k: base[k]["av"])):
        antes = {k: base[k] for k in base if base[k]["faixa"] == "alta" and filtro(k)}
        depois = {k: base[k] for k in base if nova[k] == "alta" and filtro(k)}
        print(f"  {medir(antes, None, nome + ' antes')}\n  {medir(depois, None, nome + ' depois')}")
    json.dump({"marcados": {k: dict(base[k], nova=nova[k], **marc[k]) for k in marc}}, open(saida / "resultado.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nsaída: {saida}")


if __name__ == "__main__":
    main()
