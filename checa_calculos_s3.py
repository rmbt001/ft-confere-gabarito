"""Procura, na íntegra recortada de cada CNJ (S3 de produção), as peças que mencionam cálculo no nome.

Só lê do S3 (aws s3api list-objects-v2, perfil prod-s3). Nada é baixado nem enviado.

O nome de cada peça é `<categoria>-<posição>-<Tipo>.pdf`. A posição (3 dígitos) é a ordem da peça na íntegra:
quanto maior, mais recente. Quando um processo tem mais de uma peça de cálculo, fica marcada a de maior posição.

Uso:
    uv run python checa_calculos_s3.py <lista.csv> [--n 10] [--rotulo nome]
Saída em saidas/<rótulo>/: pecas_calculo.csv (todas as peças que casaram) e escolhida_por_cnj.csv (uma por CNJ).
"""
import csv
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BUCKET = "lift-fast-track-integras-recortes-prod"
PERFIL = "prod-s3"

# "cálculo", "calc", "planilha", "liquidação" no nome da peça (sem acento, minúsculo)
RX_CALC = re.compile(r"calc|planilha|liquidac")
RX_NOME = re.compile(r"^(\d+)-(\d+)-(.+)\.pdf$", re.I)


def _sem_acento(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)).lower()


def _opcao(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


def lista_pecas(cnj_digitos):
    env = dict(os.environ, PYTHONUTF8="1", AWS_PROFILE=PERFIL)
    r = subprocess.run(["aws", "s3api", "list-objects-v2", "--bucket", BUCKET, "--prefix", f"{cnj_digitos}/",
                        "--output", "json"], capture_output=True, env=env)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip())
    txt = r.stdout.decode("utf-8")
    return json.loads(txt).get("Contents", []) if txt.strip() else []


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in ("--n", "--rotulo")]
    if not args:
        sys.exit(__doc__)
    with open(args[0], encoding="utf-8-sig") as f:
        cnjs = [row["cnj"].strip() for row in csv.DictReader(f) if row.get("cnj", "").strip()]
    n = _opcao("--n")
    if n:
        cnjs = cnjs[: int(n)]
    rot = _opcao("--rotulo") or f"calculos_s3_{len(cnjs)}"
    saida = AQUI / "saidas" / rot
    saida.mkdir(parents=True, exist_ok=True)

    todas, escolhidas = [], []
    for c in cnjs:
        d = re.sub(r"\D", "", c)
        try:
            objs = lista_pecas(d)
        except RuntimeError as e:
            sys.exit(f"{c}: erro no S3 ({e}). Se for token, rode: aws sso login --profile {PERFIL}")
        achadas = []
        for o in objs:
            nome = o["Key"].split("/", 1)[1]
            m = RX_NOME.match(nome)
            if not m or not RX_CALC.search(_sem_acento(m.group(3))):
                continue
            achadas.append({"cnj": c, "categoria": int(m.group(1)), "posicao": int(m.group(2)), "peca": m.group(3),
                            "tamanho_kb": round(o["Size"] / 1024), "chave_s3": f"s3://{BUCKET}/{o['Key']}"})
        achadas.sort(key=lambda x: x["posicao"])
        for i, a in enumerate(achadas):
            a["mais_recente"] = i == len(achadas) - 1
        todas += achadas
        ult = achadas[-1] if achadas else None
        escolhidas.append({"cnj": c, "pecas_no_s3": len(objs), "pecas_calculo": len(achadas),
                           "escolhida": ult["peca"] if ult else "", "posicao": ult["posicao"] if ult else "",
                           "chave_s3": ult["chave_s3"] if ult else ""})
        print(f"{c}: {len(objs)} peças, {len(achadas)} de cálculo" + (f" → {ult['posicao']} {ult['peca']}" if ult else ""))

    campos = ["cnj", "categoria", "posicao", "peca", "tamanho_kb", "mais_recente", "chave_s3"]
    with open(saida / "pecas_calculo.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(todas)
    with open(saida / "escolhida_por_cnj.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(escolhidas[0]), delimiter=";")
        w.writeheader()
        w.writerows(escolhidas)
    com = sum(1 for e in escolhidas if e["pecas_calculo"])
    print(f"\n{com} de {len(escolhidas)} CNJs têm peça de cálculo na íntegra recortada")
    print(f"{saida / 'pecas_calculo.csv'}\n{saida / 'escolhida_por_cnj.csv'}")


if __name__ == "__main__":
    main()
