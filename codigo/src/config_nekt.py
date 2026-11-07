"""Onde mora o token da Nekt. Fonte única para todos os scripts que falam com o lake.

Existia uma cópia da mesma função em `ingerir.py` e em `varre_truncamento_p9b.py`,
as duas lendo **só** o notebook. Isso quebra em qualquer máquina que não seja a de
quem gerou o token, porque o notebook não pode ser distribuído: ele carrega o
token em texto puro. Aqui a busca é em cascata e o notebook virou o último degrau.

Ordem:
  1. variável de ambiente NEKT_TOKEN  (o que a tarefa agendada usaria)
  2. arquivo .env na raiz do projeto  (o caminho normal; ver .env.exemplo)
  3. codigo/notebooks/01_extrai_saidas_nekt.ipynb  (legado, para não quebrar quem já tinha)
"""
import json
import os
from pathlib import Path

_PLACEHOLDER = "cole_seu_token_aqui"


def token_nekt(raiz=None):
    """Devolve o token, ou levanta SystemExit com instrução do que fazer."""
    base = Path(raiz) if raiz else Path(".")

    tok = (os.environ.get("NEKT_TOKEN") or "").strip()
    if tok:
        return tok

    env = base / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            if chave.strip() == "NEKT_TOKEN":
                valor = valor.strip().strip('"').strip("'")
                if valor and _PLACEHOLDER not in valor:
                    return valor

    nb = base / "codigo" / "notebooks" / "01_extrai_saidas_nekt.ipynb"
    if nb.exists():
        for c in json.loads(nb.read_text(encoding="utf-8"))["cells"]:
            for l in "".join(c.get("source", [])).splitlines():
                if "data_access_token" in l and "=" in l and "INSERT" not in l:
                    return l.split("=", 1)[1].strip().strip('"').strip("'")

    raise SystemExit(
        "Token da Nekt não encontrado.\n"
        "  Crie um arquivo `.env` na raiz do projeto com a linha:\n"
        "      NEKT_TOKEN=seu_token_aqui\n"
        "  (copie o `.env.exemplo`). O token sai da Nekt, em Data Access Tokens."
    )
