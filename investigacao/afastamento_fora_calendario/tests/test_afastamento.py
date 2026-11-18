"""Testes da checagem "afastamento fora do calendário" com casos sintéticos (sem Jev, sem Nekt).

Rodar da raiz do repositório:  uv run --with pytest pytest investigacao/afastamento_fora_calendario/tests -q
"""
import json
import subprocess
import sys
from pathlib import Path

PASTA = Path(__file__).parents[1]
sys.path.insert(0, str(PASTA))
import afastamento_fora_calendario as A  # noqa: E402

CRIT_EXCLUI = "Adicional de 20% sobre o salário mínimo. Excluir da apuração os períodos de afastamento e suspensão contratual."
CRIT_NADA = "Adicional de 20% sobre o salário mínimo, por todo o contrato."


def mes(m, valor=100.0, afast=0, pjc=100.0):
    return {"competencia": m, "cal_p8": {"dias": 30, "afast": afast}, "ia": {"valor": valor},
            "pjc": [{"rotulo": "x", "valor": pjc}]}


def verba(nome="Adicional de Insalubridade", crit=CRIT_EXCLUI, meses=None, total_ia=1000.0, total_pjc=1000.0):
    return {"nome_ia": nome, "status": "coincide", "total_ia": total_ia, "total_pjc": total_pjc,
            "p4": {"criterio": crit}, "competencias": meses or [mes("2020-01"), mes("2020-02")]}


def caso(verbas, a=90.0, ia=60_000, pjc=60_000, faixa="alta", p7=None):
    return {"apto": True, "processo": {"reclamante": "FULANO DE TAL"}, "verbas": verbas,
            "quadro": {"total_ia": ia, "total_pjc": pjc, "assertividade": a},
            "confianca": {"faixa": faixa}, "historico_p7": p7 or {}}


def p7(linhas):
    return {"rubricas": ["Salário Base (BT090)", "Salário Contribuição - INSS"],
            "linhas": [{"competencia": m, "valores": [b, sc]} for m, b, sc in linhas]}


# --- partes da regra ----------------------------------------------------------------------------------------
def test_so_adicional_principal():
    c = caso([verba(), verba("Horas Extras 50%"), verba("13º Salário sobre Adicional de Insalubridade"),
              verba("Adicional de Periculosidade", total_ia=0)])
    assert [v["nome_ia"] for v in A.verbas_adicional(c)] == ["Adicional de Insalubridade"]


def test_texto_da_decisao():
    assert A.EXCL.search(CRIT_EXCLUI)
    assert A.EXCL.search("Observar os afastamentos previdenciários do período.")
    assert A.EXCL.search("descontados os meses de auxílio-doença")
    assert not A.EXCL.search(CRIT_NADA)
    assert not A.EXCL.search("Indenização pelo afastamento indevido do cargo.")


def test_calendario_sem_afastamento_em_nenhum_mes():
    assert A.p8_sem_afast(verba(meses=[mes("2020-01"), mes("2020-02")]))
    assert not A.p8_sem_afast(verba(meses=[mes("2020-01"), mes("2020-02", afast=10)]))
    assert not A.p8_sem_afast(verba(meses=[mes("2020-01"), mes("2020-02", valor=0, afast=30)]))   # a ficha chegou: sem descasamento


def test_queda_da_contribuicao_exige_dois_meses_seguidos():
    v = verba(meses=[mes(m) for m in ("2021-05", "2021-06", "2021-07", "2021-08", "2021-09")])
    dois = p7([("2021-05", 1800, 1800), ("2021-06", 1800, None), ("2021-07", 1800, 0), ("2021-08", 1800, 1800), ("2021-09", 1800, 1800)])
    assert A.queda_contribuicao(caso([v], p7=dois), v) == ["2021-06", "2021-07"]
    um = p7([("2021-05", 1800, 1800), ("2021-06", 1800, 100), ("2021-07", 1800, 1800), ("2021-08", 1800, 1800), ("2021-09", 1800, 1800)])
    assert A.queda_contribuicao(caso([v], p7=um), v) == []
    pouco_lido = p7([(m, 1800, None) for m in ("2021-05", "2021-06", "2021-07", "2021-08", "2021-09")])
    assert A.queda_contribuicao(caso([v], p7=pouco_lido), v) == []    # contribuição não lida no holerite: sem sinal


def test_faixas_aceita_formatos(tmp_path):
    casos = {"A": caso([]), "B": caso([], faixa="media")}
    for conteudo in ({"A": "baixa"}, {"A": {"faixa": "baixa"}}, {"casos": {"A": {"confianca": {"faixa": "baixa"}}}}, [{"cnj": "A", "faixa": "baixa"}]):
        f = tmp_path / "f.json"
        f.write_text(json.dumps(conteudo), encoding="utf-8")
        F = A.faixas_de(f, casos)
        assert F["A"] == "baixa" and F["B"] == "media"
    assert A.faixas_de(None, casos)["A"] == "alta"


# --- ponta a ponta, sem Jev ---------------------------------------------------------------------------------
def test_ponta_a_ponta_sem_jev(tmp_path):
    casos = {
        # acende: critério manda excluir, P8 sem afastamento, IA paga a mais
        "0000001-00.2020.5.01.0001": caso([verba(total_ia=2000, total_pjc=1000)], a=60, faixa="alta"),
        # não acende: o calendário já tem o afastamento
        "0000002-00.2020.5.01.0001": caso([verba(meses=[mes("2020-01"), mes("2020-02", afast=30, valor=0)])], faixa="alta"),
        # não acende: o critério não fala de afastamento
        "0000003-00.2020.5.01.0001": caso([verba(crit=CRIT_NADA)], faixa="alta"),
        # acende, mas é restrita: a faixa não muda
        "0000004-00.2020.5.01.0001": caso([verba()], faixa="restrita"),
    }
    comp = tmp_path / "rodada" / "comparacao.json"
    comp.parent.mkdir()
    comp.write_text(json.dumps({"casos": casos}), encoding="utf-8")
    saida = tmp_path / "saida"
    r = subprocess.run([sys.executable, str(PASTA / "afastamento_fora_calendario.py"), "--comparacao", str(comp),
                        "--sem-jev", "--saida", str(saida)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    res = json.loads((saida / "resultado.json").read_text(encoding="utf-8"))["marcados"]
    assert set(res) == {"0000001-00.2020.5.01.0001", "0000004-00.2020.5.01.0001"}
    assert res["0000001-00.2020.5.01.0001"]["nova"] == "baixa" and res["0000001-00.2020.5.01.0001"]["vmais"]
    assert res["0000004-00.2020.5.01.0001"]["nova"] == "restrita"
    assert "1 acertos × 1 falsos positivos" in r.stdout
    assert (saida / "verbas_adicional.csv").exists()
