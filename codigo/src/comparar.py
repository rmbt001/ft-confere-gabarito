"""Diff de verbas: LIFT (Devido/total_verba) x PJC (Devido nominal).

- Casa por similaridade de nome (fuzzy) — para revisão humana.
- Quando o PJC fragmenta uma verba do LIFT em várias linhas, soma os Devido
  (cada verba principal do PJC é atribuída ao melhor match do LIFT e agrupada).
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


def normaliza(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    txt = re.sub(r"[^a-z0-9 ]", " ", txt.lower())
    return re.sub(r"\s+", " ", txt).strip()


def score(a: str, b: str) -> float:
    na, nb = normaliza(a), normaliza(b)
    seq = SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jac = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return round(max(seq, jac), 3)


def montar_diff(
    lift_verbas: list[dict],
    pjc_principais: list[dict],
    limiar: float = 0.3,
) -> dict:
    """lift_verbas: [{id_verba, nome, total_verba}]
    pjc_principais: [{nome, soma_devido}]
    Retorna {linhas, pjc_sem_match}.
    """
    # cada verba principal do PJC -> melhor verba do LIFT
    atribuicao: dict[int, list[dict]] = {i: [] for i in range(len(lift_verbas))}
    pjc_sem_match: list[dict] = []
    for p in pjc_principais:
        melhores = [(score(p["nome"], lv["nome"]), i) for i, lv in enumerate(lift_verbas)]
        s, i = max(melhores) if melhores else (0.0, -1)
        if s >= limiar:
            atribuicao[i].append({**p, "score": s})
        else:
            pjc_sem_match.append(p)

    linhas = []
    for i, lv in enumerate(lift_verbas):
        casados = atribuicao[i]
        soma_pjc = round(sum(c["soma_devido"] for c in casados), 2)
        total_lift = lv.get("total_verba")
        linhas.append({
            "id_verba": lv.get("id_verba"),
            "nome_lift": lv["nome"],
            "total_lift": total_lift,
            "verbas_pjc": " + ".join(c["nome"] for c in casados) or None,
            "devido_pjc": soma_pjc if casados else None,
            "score": max((c["score"] for c in casados), default=None),
            "diferenca": round((total_lift or 0) - soma_pjc, 2) if casados else None,
        })
    return {"linhas": linhas, "pjc_sem_match": pjc_sem_match}
