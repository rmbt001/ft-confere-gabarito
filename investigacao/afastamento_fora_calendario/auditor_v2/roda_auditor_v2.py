"""Auditor de sobrecálculo v2 (18/11/2026): a instrução de hoje + um parágrafo sobre afastamento fora do calendário.
Roda num lote da alta e compara com o auditor anterior e com o PJC. Só leitura nos dados; chama o OpenRouter.

O parágrafo novo: "alto" quando (1) a decisão manda excluir afastamento do adicional, (2) o P7 mostra 2+ meses
seguidos de salário de contribuição zerado ou abaixo de metade e (3) a IA pagou o adicional nesses meses sem
afastamento no calendário. Teste em 9 casos da alta de 09/11: mudou só 0000789-64.2021.5.13.0005 (médio → alto, duas
vezes), sem falso positivo.

Como rodar: ver o README.md desta pasta.
"""
import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[2]
sys.path.insert(0, str(AQUI.parent))
import afastamento_fora_calendario as AF  # noqa: E402

V2 = AQUI / "auditor_sobrecalculo_v2.md"
CUSTO_CASO = 0.17


def carrega_auditor(pacote):
    """O código do auditor é o do pacote do score (bt-prod-apps/ft/score_confianca): a chamada, a limpeza do arquivo
    do caso e o manual saem de lá; daqui só muda a instrução."""
    p = Path(pacote)
    if not (p / "score_confianca" / "auditor.py").exists():
        raise SystemExit(f"não achei o pacote do score em {p} (use --pacote ou SCORE_CONFIANCA_DIR)")
    sys.path.insert(0, str(p))
    from score_confianca import auditor
    return auditor, p / "instrucoes" / "auditor_sobrecalculo.md"


def chave():
    if not os.getenv("OPENROUTER_API_KEY"):
        try:
            from dotenv import load_dotenv
            load_dotenv(REPO / ".env")
        except ImportError:
            pass
    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("falta OPENROUTER_API_KEY (variável de ambiente ou .env da raiz do repositório, fora do Git)")


def risco_base(pasta, k):
    f = Path(pasta) / f"{k}.json" if pasta else None
    if not f or not f.exists():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))
    return (d.get("auditor") or d).get("risco_sobrecalculo")


def medir(nome, ks, base):
    if not ks:
        return f"{nome}: 0 casos"
    b = sum(1 for k in ks if base[k]["a"] >= 80)
    m = sum(1 for k in ks if base[k]["mais"])
    return f"{nome}: {len(ks)} casos · {100 * b / len(ks):.0f}% com 80%+ · {m} calculam a mais ({100 * m / len(ks):.0f}%)"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--comparacao", required=True, help="comparacao.json da rodada")
    ap.add_argument("--faixas", required=True, help="faixas SEM o auditor (ex.: confianca_jev_sem_auditor.json); o lote é a alta")
    ap.add_argument("--base-auditor", help="pasta com o auditor anterior, um <cnj>.json por caso (ex.: auditor_alta)")
    ap.add_argument("--cnjs", help="só estes CNJs (um por linha), dentro da alta")
    ap.add_argument("--so-sinal", action="store_true", help="só casos com adicional e 2+ meses de contribuição zerada no P7")
    ap.add_argument("--controle", action="store_true", help="roda também a instrução original (mede a oscilação)")
    ap.add_argument("--limite", type=int, help="no máximo N casos")
    ap.add_argument("--seco", action="store_true", help="não chama o OpenRouter: lista o lote e estima o custo")
    ap.add_argument("--pacote", default=os.getenv("SCORE_CONFIANCA_DIR", r"C:\ft\bt-prod-apps\ft\score_confianca"))
    ap.add_argument("--saida")
    a = ap.parse_args()

    comp = Path(a.comparacao)
    saida = Path(a.saida) if a.saida else AQUI.parent / "saidas" / f"auditor_v2_{comp.parent.name}"
    C = json.loads(comp.read_text(encoding="utf-8"))["casos"]
    F = AF.faixas_de(a.faixas, {})
    so = {l.strip() for l in Path(a.cnjs).read_text(encoding="utf-8-sig").splitlines() if l.strip()} if a.cnjs else None

    base = {}
    for k, c in C.items():
        q = c.get("quadro") or {}
        if F.get(k) != "alta" or not c.get("apto") or c.get("fora_regua"):
            continue
        if so is not None and k not in so:
            continue
        sinal = any(AF.queda_contribuicao(c, v) for v in AF.verbas_adicional(c))
        if a.so_sinal and not sinal:
            continue
        tem_pjc = bool(q.get("total_pjc")) and q.get("assertividade") is not None
        base[k] = dict(a=q.get("assertividade") if tem_pjc else None, mais=tem_pjc and (q.get("total_ia") or 0) > 1.1 * q["total_pjc"],
                       av=50_000 <= (q.get("total_ia") or 0) <= 200_000, sinal=sinal, v1=risco_base(a.base_auditor, k),
                       adic_mais=any((v.get("total_ia") or 0) > 1.1 * (v.get("total_pjc") or 0) for v in AF.verbas_adicional(c)))
    lote = sorted(base)[: a.limite] if a.limite else sorted(base)
    n_ver = 2 if a.controle else 1
    print(f"alta no arquivo de faixas: {sum(1 for f in F.values() if f == 'alta')} · no lote: {len(lote)} "
          f"(com sinal no holerite: {sum(1 for k in lote if base[k]['sinal'])}) · chamadas: {len(lote) * n_ver} · "
          f"custo estimado US$ {len(lote) * n_ver * CUSTO_CASO:.2f}")
    if a.seco:
        return

    chave()
    auditor, original = carrega_auditor(a.pacote)
    versoes = [("v2", V2)] + ([("original", original)] if a.controle else [])
    gasto, t0 = 0.0, time.time()
    for nome, instr in versoes:
        pasta = saida / nome
        pasta.mkdir(parents=True, exist_ok=True)
        auditor.INSTRUCAO = instr
        for i, k in enumerate(lote, 1):
            f = pasta / f"{k}.json"
            if f.exists():
                continue
            try:
                r = auditor.auditar(C[k])
            except Exception as e:  # um caso com erro não derruba o lote; fica sem arquivo e é pedido de novo depois
                print(f"  {nome} {k}: erro ({str(e)[:150]})")
                continue
            f.write_text(json.dumps({"cnj": k, "auditor": r}, ensure_ascii=False, indent=1), encoding="utf-8")
            gasto += r.get("custo_usd") or 0
            if i % 10 == 0 or i == len(lote):
                print(f"  {nome}: {i}/{len(lote)} · US$ {gasto:.2f} · {(time.time() - t0) / 60:.0f} min")

    res = {nome: {k: risco_base(saida / nome, k) for k in lote} for nome, _ in versoes}
    print(f"\ngasto nesta execução: US$ {gasto:.2f}")
    for nome in res:
        print(f"{nome}: {dict(Counter(res[nome].values()))}")
    if a.base_auditor:
        print(f"anterior: {dict(Counter(base[k]['v1'] for k in lote))}")

    medidos = [k for k in lote if base[k]["a"] is not None]
    print(f"\ncom PJC para medir: {len(medidos)} de {len(lote)}")
    print("  " + medir("alta sem auditor", medidos, base))
    if a.base_auditor:
        print("  " + medir("alta com o auditor anterior", [k for k in medidos if base[k]["v1"] != "alto"], base))
    for nome in res:
        print("  " + medir(f"alta com o auditor {nome}", [k for k in medidos if res[nome].get(k) != "alto"], base))
    for nome in res:
        al = [k for k in medidos if res[nome].get(k) == "alto"]
        print(f"  {nome} marca alto {len(al)}: {sum(base[k]['mais'] for k in al)} calculam a mais no total")

    ref = "original" if a.controle else ("anterior" if a.base_auditor else None)
    if ref:
        print(f"\nmudaram de {ref} para v2:")
        mud = []
        for k in lote:
            r0 = res["original"].get(k) if ref == "original" else base[k]["v1"]
            r2 = res["v2"].get(k)
            if r0 and r2 and r0 != r2:
                mud.append(k)
                b = base[k]
                a_txt = f"{b['a']:.1f}%" if b["a"] is not None else "sem PJC"
                print(f"  {k} · {r0} → {r2} · total {a_txt} · {'calcula a mais' if b['mais'] else 'total ok'} · "
                      f"adicional {'a mais' if b['adic_mais'] else 'ok'} · sinal no holerite {b['sinal']}"
                      + (f" · anterior {b['v1']}" if ref == "original" and a.base_auditor else ""))
        if not mud:
            print("  nenhum")
    json.dump({"lote": lote, "resultado": res, "base": base}, open(saida / "resumo.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nsaída: {saida}")


if __name__ == "__main__":
    main()
