"""Tabela do PJC por processo e conferência da leitura contra o PDF (16/10/2026).

Primeira etapa da montagem fora do painel: uma linha por verba EXATAMENTE como está no
PJC (o que o PJC separa fica separado, inclusive fatias de período), com o código pelo
de-para. A conferência compara cada linha com o "Resumo do Cálculo" do PDF do mesmo
cálculo, que traz o valor corrigido de cada verba: é o teste de que estamos lendo o
PJC direito, sem depender do painel.

Uso:
    from tabela_pjc import tabela_pjc, resumo_pdf, confere_leitura
    tab = tabela_pjc(parse_pjc_xml("casos/<CNJ>/pjc.pjc"))
    conf, totais = confere_leitura(tab, resumo_pdf("casos/<CNJ>/pjc.pdf"))
"""
import re

import pandas as pd

from depara import norm, pjc_info
from parse_pjc import parse_resumo_only

# linha do Resumo que não é verba: FGTS, contribuições, IR, honorários e totais ficam
# fora da conferência verba a verba (o .pjc não as traz como verba)
_NAO_VERBA = re.compile(r"^(TOTAL|FGTS|MULTA SOBRE FGTS|MULTA DE 40|CONTRIBUI|INSS|IMPOSTO|IRPF|IR |"
                        r"HONOR|CUSTAS|PREVID|DEP[OÓ]SITO)", re.I)


def _base_reflexo(nome):
    m = re.search(r"\bSOBRE\b\s+(.+)$", nome or "", re.I)
    return m.group(1).strip() if m else None


def tabela_pjc(pjc):
    """Uma linha por verba do PJC (principais, reflexos e as que não compõem o principal).

    `pjc` é o dicionário de parse_pjc_xml. Colunas: ordem, verba, tipo (principal | reflexo),
    base (verba de que o reflexo deriva), compoe_principal, codigo (de-para; só principal),
    devido, pago, corrigido, competencias, de, ate."""
    linhas = []
    todas = [(v, True) for v in pjc.get("verbas") or []] + [(v, False) for v in pjc.get("verbas_fora_principal") or []]
    for i, (v, compoe) in enumerate(todas, 1):
        comps = sorted(c.get("competencia") for c in v.get("competencias") or [] if c.get("competencia"))
        refl = bool(v.get("reflexo"))
        info = None if refl else pjc_info(v["nome"])
        linhas.append({
            "ordem": i, "verba": v["nome"], "tipo": "reflexo" if refl else "principal",
            "base": _base_reflexo(v["nome"]) if refl else None,
            "compoe_principal": compoe and v.get("compor_principal", True),
            "codigo": (info or {}).get("codigo"),
            "devido": round(v.get("soma_devido") or 0, 2),
            "pago": round(v.get("soma_pago") or 0, 2) if v.get("soma_pago") is not None else None,
            "corrigido": round(v["soma_corrigido"], 2) if v.get("soma_corrigido") is not None else None,
            "competencias": v.get("n_competencias") or len(comps),
            "de": comps[0] if comps else None, "ate": comps[-1] if comps else None,
        })
    # bloco "Multas e Indenizações": valor lançado à parte (multa de embargos, litigância e,
    # às vezes, o próprio dano moral). Só é crédito quando o reclamante recebe.
    for m in pjc.get("multas") or []:
        info = pjc_info(m["nome"])
        linhas.append({
            "ordem": len(linhas) + 1, "verba": m["nome"], "tipo": "multa", "base": None,
            "compoe_principal": bool(m.get("credor_reclamante")), "codigo": (info or {}).get("codigo"),
            "devido": m["valor"], "pago": None, "corrigido": m.get("corrigido"),
            "competencias": 0, "de": None, "ate": None, "credor_devedor": m.get("tipo_credor_devedor"),
        })
    return pd.DataFrame(linhas)


def resumo_pdf(caminho_pdf):
    """O 'Resumo do Cálculo' do PDF: uma linha por descrição (verba, FGTS, total…)."""
    r = pd.DataFrame(parse_resumo_only(caminho_pdf))
    if r.empty:
        return pd.DataFrame(columns=["descricao", "valor_corrigido", "juros", "total"])
    return r


def confere_leitura(tab, resumo, tolerancia=1.0):
    """Cruza a tabela do .pjc com o Resumo do PDF, verba a verba, pelo nome.

    Devolve (conferencia, totais). Em `conferencia`, status por linha:
      bate          — mesmo nome dos dois lados e corrigido a até `tolerancia` reais;
      diverge       — mesmo nome, valor diferente;
      so_no_pjc     — verba lida do .pjc que o Resumo do PDF não tem;
      so_no_pdf     — verba do Resumo que a leitura do .pjc não trouxe (o furo que importa).
    Linhas do Resumo que não são verba (FGTS, total, contribuições) ficam de fora."""
    _cols_tab = ["ordem", "verba", "tipo", "codigo", "compoe_principal", "corrigido"]
    t = tab.assign(chave=tab["verba"].map(norm)) if not tab.empty else pd.DataFrame(columns=["chave"] + _cols_tab)
    r = resumo[~resumo["descricao"].fillna("").str.strip().str.match(_NAO_VERBA)].copy() if not resumo.empty else resumo
    r["chave"] = r["descricao"].map(norm) if not r.empty else []
    # o Resumo soma linhas de mesmo nome (raro); agrupa para não duplicar o par
    r = r.groupby("chave", as_index=False).agg(descricao=("descricao", "first"), pdf=("valor_corrigido", "sum")) if not r.empty \
        else pd.DataFrame(columns=["chave", "descricao", "pdf"])
    m = t.merge(r, on="chave", how="outer")
    def _st(x):
        if pd.isna(x.get("verba")):
            return "so_no_pdf"
        if pd.isna(x.get("descricao")):
            return "so_no_pjc"
        if x.get("corrigido") is None or pd.isna(x.get("corrigido")):
            return "diverge"
        return "bate" if abs((x["corrigido"] or 0) - (x["pdf"] or 0)) <= tolerancia else "diverge"
    m["status"] = m.apply(_st, axis=1) if not m.empty else []
    m["diferenca"] = (m["corrigido"].fillna(0) - m["pdf"].fillna(0)).round(2) if not m.empty else []
    cols = ["ordem", "verba", "descricao", "tipo", "codigo", "compoe_principal", "corrigido", "pdf", "diferenca", "status"]
    conf = m[[c for c in cols if c in m.columns]].sort_values(["status", "ordem"], na_position="last")
    tot_pdf = next((x["valor_corrigido"] for _, x in resumo.iterrows() if norm(x["descricao"]) == "TOTAL"), None) if not resumo.empty else None
    totais = {
        "verbas_pjc": int((tab["tipo"] == "principal").sum()) if not tab.empty else 0,
        "reflexos_pjc": int((tab["tipo"] == "reflexo").sum()) if not tab.empty else 0,
        "linhas_resumo": int(len(r)),
        "bate": int((conf["status"] == "bate").sum()), "diverge": int((conf["status"] == "diverge").sum()),
        "so_no_pjc": int((conf["status"] == "so_no_pjc").sum()), "so_no_pdf": int((conf["status"] == "so_no_pdf").sum()),
        "corrigido_pjc": round(float(tab.loc[tab["compoe_principal"], "corrigido"].fillna(0).sum()), 2) if not tab.empty else 0.0,
        "corrigido_pdf_verbas": round(float(r["pdf"].fillna(0).sum()), 2) if not r.empty else 0.0,
        "total_resumo_pdf": tot_pdf,
    }
    return conf, totais
