"""Busca, na íntegra recortada do S3 de produção, o cálculo do PJe-Calc de cada CNJ de uma lista.

Só LÊ do S3 (list-objects-v2 e cp do bucket para a máquina, perfil prod-s3). Nada é apagado nem enviado ao bucket.

Passos, por CNJ:
  1. Nekt: só segue quem tem a última execução com P10 (travado antes do P10 não tem cálculo da IA para comparar);
  2. lista as peças do processo em lift-fast-track-integras-recortes-prod/<CNJ só dígitos>/;
  3. escolhe as candidatas pelo nome: categorias 38 (atualização), 39 (apresentação) e 42 (planilha) inteiras, e
     qualquer peça com cálculo/calc/planilha/liquidação no nome; tira impugnação, contestação, recurso, manifestação,
     sentença, acórdão e decisão;
  4. baixa da mais recente para a mais antiga (a posição na íntegra é o 2º número do nome) e lê o PDF: é PJe-Calc
     quando as primeiras páginas têm "PLANILHA DE CÁLCULO" e "Resumo do Cálculo". Do PJe-Calc tira assinante, data
     de juntada, "liquidado por" (nome = PJe-Calc do tribunal; "offline" = PJe-Calc Cidadão, de parte ou perito),
     data de liquidação, reclamado e o total corrigido do Resumo;
  5. escolhida (regra B, 07/11): a do tribunal mais recente; sem conta do tribunal, a mais recente que é PJe-Calc.
     Conta offline anterior à 1ª sentença (cálculo da inicial) fica de fora; a do tribunal, não (sentença líquida). A escolhida é copiada para
     _escolhidas e a pasta de baixados do CNJ é apagada logo em seguida (com --todas, fica tudo, para estudo).

Retomável: cada CNJ terminado vira saidas/<rótulo>/por_cnj/<CNJ>.json e é pulado na próxima rodada. Se o login do
SSO expirar, o script para e diz o comando; depois é só rodar de novo.

Uso:
    uv run python busca_calculos_s3.py <lista.csv> [--n 50] [--rotulo piloto50] [--todas] [--workers 8]
Saída em saidas/<rótulo>/: candidatas.csv, escolhida_por_cnj.csv; PDFs em pecas_s3/<CNJ>/ e as escolhidas em
pecas_s3/_escolhidas/<rótulo>/<CNJ>/ (pronto para: uv run python compara.py pecas_s3/_escolhidas/<rótulo>).
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
BUCKET = "lift-fast-track-integras-recortes-prod"
PERFIL = "prod-s3"
PECAS = AQUI / "pecas_s3"

RX_NOME = re.compile(r"^(\d+)-(\d+)-(.+)\.pdf$", re.I)
RX_CALC = re.compile(r"calc|planilha|liquidac")
RX_FORA = re.compile(r"impugna|contesta|recurso|manifesta|senten|acord|decis")
CATS_CALC = {38, 39, 42}

RX_ASSINA = re.compile(r"Assinado eletronicamente por:\s*(.+?)\s*-\s*(?:Juntado em:\s*)?(\d{2}/\d{2}/\d{4})")
RX_LIQ = re.compile(r"C.lculo liquidado por\s+(.+?)\s+na vers.o\s+([\d.]+)\s+em\s+(\d{2}/\d{2}/\d{4})")
RX_DLIQ = re.compile(r"Data Liquida..o:\s*(\d{2}/\d{2}/\d{4})")
RX_RECLAMADO = re.compile(r"Reclamad[oa]:?\s*(.+)")
RX_TOTAL = re.compile(r"^Total\s+([\d.,()]+)\s+([\d.,()]+)\s+([\d.,()]+)\s*$", re.M)

PARAR = threading.Event()
MSG_PARADA = []


def _sem_acento(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)).lower()


def _opcao(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


def _aws(args):
    env = dict(os.environ, PYTHONUTF8="1", AWS_PROFILE=PERFIL)
    r = subprocess.run(["aws", *args], capture_output=True, env=env)
    if r.returncode:
        err = r.stderr.decode("utf-8", "replace").strip()
        if re.search(r"token|sso|expired|credentials", err, re.I):
            PARAR.set()
            MSG_PARADA.append(f"login do SSO expirou ou falhou: rode  aws sso login --profile {PERFIL}  e rode este script de novo\n  ({err[:200]})")
        raise RuntimeError(err[:300])
    return r.stdout.decode("utf-8")


_S3 = None
_S3_LOCK = threading.Lock()


def _s3():
    """Cliente boto3 único (só leitura: list_objects_v2 e download_file). Abrir um aws.exe por peça custava 1–2 s de
    CPU cada e travava a máquina de 4 núcleos (10/11)."""
    global _S3
    with _S3_LOCK:
        if _S3 is None:
            import boto3
            from botocore.config import Config
            _S3 = boto3.Session(profile_name=PERFIL).client("s3", config=Config(max_pool_connections=32))
        return _S3


def _boto(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as e:  # noqa: BLE001
        err = str(e)
        if re.search(r"token|sso|expired|credentials", err, re.I):
            PARAR.set()
            MSG_PARADA.append(f"login do SSO expirou ou falhou: rode  aws sso login --profile {PERFIL}  e rode este script de novo\n  ({err[:200]})")
        raise RuntimeError(err[:300]) from e


def _lista(prefixo):
    objs = []
    for pg in _s3().get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=prefixo):
        objs += [{"Key": o["Key"], "Size": o["Size"]} for o in pg.get("Contents", [])]
    return objs


def _num(s):
    s = s.strip()
    neg = s.startswith("(")
    v = float(s.strip("()").replace(".", "").replace(",", "."))
    return -v if neg else v


def le_pdf(caminho):
    import pdfplumber
    with pdfplumber.open(caminho) as d:
        n = len(d.pages)
        ini = "\n".join((pg.extract_text() or "") for pg in d.pages[:4])
        fim = d.pages[-1].extract_text() or ""
    sa = _sem_acento(ini)
    info = {"paginas": n, "pjecalc": "planilha de calculo" in sa and "resumo do calculo" in sa}
    if not info["pjecalc"]:
        return info
    m = RX_ASSINA.search(fim)
    info["assinante"], info["data_juntada"] = (m.group(1), m.group(2)) if m else ("", "")
    m = RX_LIQ.search(fim)
    info["liquidado_por"], info["versao_pjecalc"], info["data_calculo"] = (m.group(1), m.group(2), m.group(3)) if m else ("", "", "")
    info["pjecalc_tribunal"] = bool(info["liquidado_por"]) and info["liquidado_por"].lower() != "offline"
    m = RX_DLIQ.search(ini)
    info["data_liquidacao"] = m.group(1) if m else ""
    m = RX_RECLAMADO.search(ini)
    info["reclamado"] = m.group(1).strip()[:80] if m else ""
    m = RX_TOTAL.search(ini)
    try:
        info["total_corrigido"], info["total_com_juros"] = (_num(m.group(1)), _num(m.group(3))) if m else (None, None)
    except ValueError:
        info["total_corrigido"], info["total_com_juros"] = None, None
    return info


def pos_primeira_sentenca(objs):
    """Posição da 1ª sentença de conhecimento na íntegra (0 se não houver). Cálculo antes dela é o da inicial."""
    pos = []
    for o in objs:
        m = RX_NOME.match(o["Key"].split("/", 1)[1])
        if m and int(m.group(1)) == 1:
            t = _sem_acento(m.group(3))
            if "senten" in t and not re.search(r"liquidac|impugna|contesta|anexo|homologa", t):
                pos.append(int(m.group(2)))
    return min(pos) if pos else 0


def candidatas(objs):
    corte = pos_primeira_sentenca(objs)
    out = []
    for o in objs:
        nome = o["Key"].split("/", 1)[1]
        m = RX_NOME.match(nome)
        if not m:
            continue
        cat, pos, tipo = int(m.group(1)), int(m.group(2)), m.group(3)
        t = _sem_acento(tipo)
        if RX_FORA.search(t) or not (cat in CATS_CALC or RX_CALC.search(t)):
            continue
        # antes da sentença: pode ser o cálculo da inicial (fica fora) ou a conta da vara na sentença líquida
        # (fica, se for do tribunal) — por isso só se decide depois de ler o PDF
        out.append({"categoria": cat, "posicao": pos, "peca": tipo, "arquivo": nome, "kb": round(o["Size"] / 1024),
                    "antes_sentenca": pos < corte,
                    "chave_s3": f"s3://{BUCKET}/{o['Key']}"})
    return sorted(out, key=lambda x: -x["posicao"])


def processa(cnj, todas, dir_json, dir_esc):
    if PARAR.is_set():
        return None
    d = re.sub(r"\D", "", cnj)
    objs = _boto(_lista, f"{d}/")
    cands = candidatas(objs)
    pasta = PECAS / cnj
    # regra B (Raíra, 07/11): lê todas as candidatas; fica a do tribunal mais recente ("liquidado por" um nome);
    # sem nenhuma do tribunal, a mais recente que é PJe-Calc
    for c in cands:
        if PARAR.is_set():
            return None
        local = pasta / c["arquivo"]
        if not local.exists():
            pasta.mkdir(parents=True, exist_ok=True)
            _boto(_s3().download_file, BUCKET, c["chave_s3"].split(f"s3://{BUCKET}/", 1)[1], str(local))
        try:
            c.update(le_pdf(local))
        except Exception as e:  # noqa: BLE001
            c.update({"pjecalc": False, "erro_pdf": type(e).__name__})
    trib = [c for c in cands if c.get("pjecalc") and c.get("pjecalc_tribunal")]  # já em ordem: mais recente primeiro
    pjc = [c for c in cands if c.get("pjecalc") and not c["antes_sentenca"]]
    escolhida = (trib or pjc or [None])[0]
    if escolhida:
        escolhida["escolhida"] = True
        escolhida["regra"] = "tribunal" if trib else "mais recente (sem conta do tribunal)"
        dest = dir_esc / cnj
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pasta / escolhida["arquivo"], dest / escolhida["arquivo"])
    if not todas and pasta.exists():  # apaga logo o que foi baixado; a escolhida já está em _escolhidas
        shutil.rmtree(pasta)
    r = {"cnj": cnj, "rodou_esteira": True, "pecas_no_s3": len(objs), "candidatas": cands,
         "escolhida": escolhida["arquivo"] if escolhida else None}
    (dir_json / f"{cnj}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    return r


def rodaram_na_esteira(cnjs, arq):
    """CNJs cuja ÚLTIMA execução chegou ao P10 (tem linha no P10a ou no P10b). Travado antes do P10 não tem cálculo
    da IA, então não vale buscar gabarito. (O .pjc do ged não serve de filtro: há caso com P10 e sem .pjc.)"""
    if arq.exists():
        return set(json.loads(arq.read_text(encoding="utf-8"))["chegou_p10"])
    import pyarrow.compute as pc
    from baixa_cnj import RAW, _dataset, _digitos, _formata, _le
    ds = sorted({_digitos(c) for c in cnjs})
    proc = _le("raw", "ft_lift_tb_cnj_processado", pc.field("cnj").isin(ds))
    if not len(proc):
        sys.exit("nenhum desses CNJs rodou na esteira (ou a Nekt falhou)")
    ult = proc.sort_values("criado_em").groupby(proc["cnj"].astype(str)).tail(1)
    idps = list(ult["id_processado"])
    com_p10 = set()
    for a in ("P10A", "P10B"):
        t = _dataset("raw", RAW[a]).to_table(columns=["id_processado"], filter=pc.field("id_processado").isin(idps))
        com_p10 |= set(t.column("id_processado").to_pylist())
    rodou = sorted({_formata(str(c)) for c in ult["cnj"]})
    p10 = sorted({_formata(str(r.cnj)) for r in ult.itertuples() if r.id_processado in com_p10})
    arq.write_text(json.dumps({"rodou": rodou, "chegou_p10": p10}), encoding="utf-8")
    return set(p10)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pos = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in ("--n", "--rotulo", "--workers")]
    if not pos:
        sys.exit(__doc__)
    with open(pos[0], encoding="utf-8-sig") as f:
        cnjs = [r["cnj"].strip() for r in csv.DictReader(f) if r.get("cnj", "").strip()]
    if _opcao("--n"):
        cnjs = cnjs[: int(_opcao("--n"))]
    todas = "--todas" in sys.argv
    rot = _opcao("--rotulo") or f"busca_{len(cnjs)}"
    saida = AQUI / "saidas" / rot
    dir_json = saida / "por_cnj"
    dir_json.mkdir(parents=True, exist_ok=True)
    dir_esc = PECAS / "_escolhidas" / rot

    rodou = rodaram_na_esteira(cnjs, saida / "esteira.json")
    nao_rodou = [c for c in cnjs if c not in rodou]
    feitos = {p.stem for p in dir_json.glob("*.json")}
    fila = [c for c in cnjs if c in rodou and c not in feitos]
    print(f"{len(cnjs)} CNJs · {len(rodou & set(cnjs))} chegaram ao P10 · {len(nao_rodou)} não (sem cálculo da IA) · "
          f"{len(feitos)} já feitos · {len(fila)} na fila" + (" · modo --todas" if todas else ""))

    with ThreadPoolExecutor(max_workers=int(_opcao("--workers", 8))) as ex:
        futs = {ex.submit(processa, c, todas, dir_json, dir_esc): c for c in fila}
        for i, fu in enumerate(as_completed(futs), 1):
            c = futs[fu]
            try:
                r = fu.result()
            except RuntimeError as e:
                if not PARAR.is_set():
                    print(f"  {c}: erro ({e}); fica para a próxima rodada")
                continue
            if r:
                esc = next((x for x in r["candidatas"] if x.get("escolhida")), None)
                print(f"  [{i}/{len(fila)}] {c}: {len(r['candidatas'])} candidata(s)"
                      + (f" → {esc['posicao']} {esc['peca'][:50]}" if esc else " · nenhum PJe-Calc"))
    if PARAR.is_set():
        sys.exit("\nPAROU: " + MSG_PARADA[0])

    # agrega tudo o que já foi feito (inclusive de rodadas anteriores)
    linhas_c, linhas_e = [], []
    for c in cnjs:
        fp = dir_json / f"{c}.json"
        if c in nao_rodou:
            linhas_e.append({"cnj": c, "situacao": "IA não chegou ao P10"})
            continue
        if not fp.exists():
            linhas_e.append({"cnj": c, "situacao": "pendente (erro ou interrompido)"})
            continue
        r = json.loads(fp.read_text(encoding="utf-8"))
        n_pjc = sum(1 for x in r["candidatas"] if x.get("pjecalc"))
        esc = next((x for x in r["candidatas"] if x.get("escolhida")), None)
        for x in r["candidatas"]:
            linhas_c.append({"cnj": c, **{k: x.get(k) for k in CAMPOS_C}})
        linha = {"cnj": c, "situacao": "com PJe-Calc" if esc else ("sem PJe-Calc" if r["candidatas"] else "sem peça de cálculo"),
                 "pecas_no_s3": r["pecas_no_s3"], "candidatas": len(r["candidatas"]), "pjecalc_achados": n_pjc}
        if esc:
            linha.update({k: esc.get(k) for k in CAMPOS_C})
            linha["tribunal_mais_recente"] = next((x["arquivo"] for x in r["candidatas"] if x.get("pjecalc_tribunal")), "")
        linhas_e.append(linha)
    _csv(saida / "candidatas.csv", linhas_c, ["cnj", *CAMPOS_C])
    _csv(saida / "escolhida_por_cnj.csv", linhas_e,
         ["cnj", "situacao", "pecas_no_s3", "candidatas", "pjecalc_achados", *CAMPOS_C, "tribunal_mais_recente"])
    from collections import Counter
    cont = Counter(x["situacao"] for x in linhas_e)
    print("\n" + " · ".join(f"{v} {k}" for k, v in cont.most_common()))
    print(f"{saida / 'escolhida_por_cnj.csv'}\n{saida / 'candidatas.csv'}\nescolhidas: {dir_esc}")


CAMPOS_C = ["categoria", "posicao", "antes_sentenca", "peca", "kb", "paginas", "pjecalc", "escolhida", "regra", "pjecalc_tribunal", "liquidado_por",
            "assinante", "data_juntada", "data_calculo", "data_liquidacao", "versao_pjecalc", "reclamado",
            "total_corrigido", "total_com_juros", "erro_pdf", "chave_s3"]


def _csv(arq, linhas, campos):
    with open(arq, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    main()
