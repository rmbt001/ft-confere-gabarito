"""Parser do .pjc (arquivo nativo do PJe-Calc) — alternativa ao parse_pjc (PDF).

O .pjc é o grafo de objetos do próprio motor do PJe-Calc, serializado com XStream
(ZIP → XML ISO-8859-1). Traz os MESMOS números que o PDF renderiza, mas como
campos nomeados e em precisão cheia — sem adivinhação de coluna/layout.

Devolve EXATAMENTE o mesmo dict que `parse_pjc.parse_pjc`, para ser plugável no
gerar_telas/comparar sem mudar mais nada:

    {cabecalho, resumo, verbas, historico_salarial, ferias_gozo, dias_ferias_mes}

Mapeamento (verificado em arquivos reais v2.15.1):
  verba            <- <Reflexo> (nome, ativo, ocorrencias)
  competência      <- OcorrenciaDeVerba.dataFinal (epoch-ms) -> AAAA-MM
  devido (líquido) <- devidoIntegral - pagoIntegral  (== "Diferença" do PDF)
  base/mult/qtd    <- baseIntegral / multiplicador / quantidade
  histórico        <- <HistoricoSalarial> (nome) + OcorrenciaDoHistoricoSalarial
  partes/CNJ       <- <processo><Processo>
  férias de gozo   <- listaDeFerias.<Ferias> (períodos de Gozo 1..3)

Escolhas conscientes (a validar contra um par PDF×.pjc real):
  - só verbas/ocorrências com <ativo>true</ativo> (aproxima "o que o PDF mostra");
  - `reflexo` mantém a MESMA regra do parser de PDF ('SOBRE' no nome), p/ o
    comparador a jusante se comportar igual;
  - `resumo` (Valor Corrigido/Juros) é a atualização monetária, que vive noutro
    bloco (dadosEstruturados/atualização) — preenchido best-effort; ver TODO.
"""
from __future__ import annotations

import datetime
import html
import io
import re
import zipfile
from pathlib import Path

GMT3 = datetime.timezone(datetime.timedelta(hours=-3))


# --------------------------------------------------------------------------- #
# leitura física
# --------------------------------------------------------------------------- #
def _ler_xml(caminho: Path) -> str:
    """Devolve o XML interno (ISO-8859-1). Aceita o .pjc (ZIP) ou o .PJC já
    extraído (XML cru), detectando pela assinatura 'PK' do zip."""
    dados = caminho.read_bytes()
    if dados[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            dados = z.read(z.namelist()[0])
    return dados.decode("iso-8859-1")


# --------------------------------------------------------------------------- #
# helpers de baixo nível
# --------------------------------------------------------------------------- #
def _txt(s: str) -> str:
    """Decodifica entidades (&#186; etc.) e normaliza espaços."""
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _num(v: str | None) -> float | None:
    """Campo numérico do XStream ('366.84', '0E-25', 'null') -> float | None."""
    if v is None:
        return None
    v = v.strip()
    if not v or v == "null":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _epoch_data(ms: str | None) -> datetime.date | None:
    if ms is None or ms.strip() in ("", "null"):
        return None
    try:
        return datetime.datetime.fromtimestamp(int(ms) / 1000, GMT3).date()
    except (ValueError, OverflowError, OSError):
        return None


def _comp(ms: str | None) -> str | None:
    d = _epoch_data(ms)
    return f"{d.year}-{d.month:02d}" if d else None


def _ddmmaaaa(ms: str | None) -> str | None:
    d = _epoch_data(ms)
    return f"{d.day:02d}/{d.month:02d}/{d.year}" if d else None


def _extract_balanced(s: str, tag: str, i: int) -> tuple[str | None, int]:
    """Bloco <tag>..</tag> balanceado a partir de i (XStream aninha o mesmo tag)."""
    o, c = f"<{tag}>", f"</{tag}>"
    depth, j = 0, i
    while j < len(s):
        no, nc = s.find(o, j), s.find(c, j)
        if nc < 0:
            break
        if no != -1 and no < nc:
            depth += 1
            j = no + len(o)
        else:
            depth -= 1
            j = nc + len(c)
            if depth == 0:
                return s[i:j], j
    return None, -1


def _leaf(blk: str, tag: str) -> str | None:
    """Valor do 1º <tag>..</tag> (folha) no bloco."""
    m = re.search(rf"<{tag}>([^<]*)</{tag}>", blk)
    return m.group(1) if m else None


def _blocos(s: str, tag: str, so_objetos: bool = True, aninhados: bool = False):
    """Itera os blocos <tag>..</tag> balanceados. so_objetos=True pula os stubs
    de referência (`<tag><internalRef>N</internalRef></tag>`), devolvendo só os
    objetos de verdade (que têm <id> próprio). aninhados=True também devolve os
    blocos de mesmo tag que estão DENTRO de outro (o XStream serializa o objeto
    inteiro onde ele aparece pela 1ª vez, que pode ser dentro de outra verba)."""
    i = 0
    while True:
        i = s.find(f"<{tag}>", i)
        if i < 0:
            return
        blk, fim = _extract_balanced(s, tag, i)
        if blk is None:
            return
        i = i + len(tag) + 2 if aninhados else fim
        if so_objetos and "<internalRef>" in blk[: len(f"<{tag}>") + 30]:
            continue  # stub de back-ref, não é o objeto
        yield blk


# --------------------------------------------------------------------------- #
# seções
# --------------------------------------------------------------------------- #
def _cabecalho(s: str) -> dict:
    raiz = s[: s.find("<gprec>")] if "<gprec>" in s else s[:6000]

    cnj = None
    mid = re.search(r"<IdentificadorDoProcesso>(.*?)</IdentificadorDoProcesso>", s, re.S)
    if mid:
        g = {t: _leaf(mid.group(1), t) for t in
             ("numero", "digito", "ano", "justica", "regiao", "vara")}
        try:
            cnj = (f"{int(g['numero']):07d}-{int(g['digito']):02d}.{int(g['ano'])}."
                   f"{int(g['justica'])}.{int(g['regiao']):02d}.{int(g['vara']):04d}")
        except (TypeError, ValueError):
            cnj = None

    def _parte(tag):
        m = re.search(rf"<{tag}>.*?<nome>([^<]*)</nome>", s, re.S)
        return _txt(m.group(1)) if m else None

    ini = _epoch_data(_leaf(raiz, "dataInicioCalculo"))
    fim = _epoch_data(_leaf(raiz, "dataTerminoCalculo"))
    periodo = (f"{ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"
               if ini and fim else None)

    # id do cálculo no PJe-Calc (raiz <Calculo><id>): o mesmo processo pode ter
    # mais de um cálculo (ex.: 514 × 551), e só o id diz qual deles subiu como
    # gabarito. O painel confere contra a curadoria de gabarito a corrigir.
    # Nos .pjc mais novos a raiz abre com <gprec> e/ou <dadosEstruturados> antes do
    # <id>; sem pular esses blocos o id saía vazio em ~55% dos casos (28/10/2026).
    mid_calc = re.match(r"\s*(?:<\?xml[^>]*\?>)?\s*<Calculo>\s*"
                        r"(?:<(gprec|dadosEstruturados)>.*?</\1>\s*)*"
                        r"<id>(\d+)</id>", s, re.S)

    return {
        "processo": cnj,
        "id_calculo": mid_calc.group(2) if mid_calc else None,
        "reclamante": _parte("reclamante"),
        "reclamado": _parte("reclamad[oa]"),
        "periodo_calculo": periodo,
        "data_ajuizamento": _ddmmaaaa(_leaf(raiz, "dataAjuizamento")),
        "admissao": _ddmmaaaa(_leaf(raiz, "dataAdmissao")),
        "demissao": _ddmmaaaa(_leaf(raiz, "dataDemissao")),
        "_periodo_ini": ini,  # usado p/ completar o período se dataTerminoCalculo for null
    }


_VERBA_CLASSES = ("Calculada", "Reflexo", "Informada")
# início dos subobjetos de uma verba — o cabeçalho escalar (id/nome/ativo) vem
# antes deles; cortar aqui evita ler o nome de uma verba ANINHADA (grafo XStream).
_CORTE_HEAD = re.compile(r"<(?:calculo|ocorrencias|verbaDeCalculo|formula|assuntoCnj|"
                         r"historicosDaVerba|cartoesDePonto|valesTransportes)\b")


def _indice_verbas(s: str) -> dict[str, dict]:
    """id -> {nome, reflexo, ativo} de toda verba (Calculada/Reflexo/Informada).
    Lê nome/ativo só do CABEÇALHO do objeto (antes dos subobjetos), para não
    capturar dados de uma verba aninhada por referência do XStream.
    Percorre também as verbas aninhadas: quando a verba X é base de outra (ex.: HE 100%
    na base do DSR da OJ 394), o XStream pode escrever X inteira DENTRO da outra, e só
    um stub no nível de cima; sem isso a principal X sumia e só os reflexos dela ficavam
    (1001511-64.2025.5.02.0711, 0101430-28.2019.5.01.0017)."""
    idx: dict[str, dict] = {}
    for cls in _VERBA_CLASSES:
        for blk in _blocos(s, cls, aninhados=True):
            vid = _leaf(blk, "id")
            if vid is None or vid in idx:
                continue
            m = _CORTE_HEAD.search(blk)
            head = blk[: m.start()] if m else blk
            nome = _txt(_leaf(head, "nome") or "")
            if not nome:
                continue
            idx[vid] = {"nome": nome, "ativo": (_leaf(head, "ativo") or "").strip() == "true",
                        # palavra inteira: "HORAS SOBREAVISO" não é reflexo (07/11/2026, 0000728-23)
                        "reflexo": cls == "Reflexo" or bool(re.search(r"\bSOBRE\b", nome.upper())),
                        # bloco "Verbas que não compõem o Principal" do PDF: linha
                        # informativa (pedidos improcedentes, base de reflexo, versão
                        # sem teto) — não é crédito e não entra no total
                        "compor_principal": (_leaf(head, "comporPrincipal") or "").strip() != "NAO",
                        # Opção "zerar valor negativo" do PJe-Calc, marcada pelo calculista verba
                        # a verba: a ocorrência com devido − pago < 0 vale zero. Lê-se como o PJC
                        # entrega: o PDF do mesmo cálculo soma só os meses positivos dessas verbas
                        # (conferido ao centavo em 8 aptos em 16/10/2026, BT081 e HE comum; a regra
                        # tinha saído em 15/10 e voltou com essa prova, decisão da Raíra). A regra da
                        # ESTEIRA para o lado da IA é outra (card BT-1559) e não mora aqui.
                        "zera_negativo": (_leaf(head, "zeraValorNegativo") or "").strip() == "true"}
    return idx


def _verbas(s: str) -> list[dict]:
    """Uma verba por objeto (Calculada/Reflexo/Informada). Cada OcorrenciaDeVerba
    é ligada à sua verba pelo <verbaDeCalculo><internalRef>, e agrupada por nome
    (como o parser de PDF). `_blocos` avança pelo bloco balanceado, então a
    `ocorrenciaOriginal` aninhada em cada ocorrência não é recontada."""
    idx = _indice_verbas(s)
    porg: dict[str, dict] = {}
    ordem: list[str] = []
    vistos: set[str] = set()
    for oc in _blocos(s, "OcorrenciaDeVerba"):
        oid = _leaf(oc, "id")
        if oid is None or oid in vistos:
            continue
        vistos.add(oid)
        if (_leaf(oc, "ativo") or "").strip() != "true":
            continue
        # a verba desta ocorrência: 1º <verbaDeCalculo>..<internalRef>N</..> do bloco
        mref = re.search(r"<verbaDeCalculo><\w+><internalRef>(\d+)</internalRef>", oc)
        verba = idx.get(mref.group(1)) if mref else None
        if not verba or not verba["ativo"]:
            continue  # sem verba ativa correspondente -> fora (aproxima o PDF)
        comp = _comp(_leaf(oc, "dataFinal")) or _comp(_leaf(oc, "dataInicial"))
        if comp is None:
            continue
        # Usa `devido`/`pago`/`base` (alta precisão), NÃO os `*Integral`: para
        # reflexos MÉDIA o `devidoIntegral` vem ×30 (integral por dia) e infla a
        # soma; `devido` é o valor monetário consistente entre os tipos de verba
        # (na CALCULADA principal, devido == devidoIntegral).
        devido = _num(_leaf(oc, "devido")) or 0.0
        pago = _num(_leaf(oc, "pago")) or 0.0
        # `indiceAcumulado` = fator de correção monetária acumulado DESTA ocorrência
        # (competência -> data-base do cálculo). Corrigido = (devido − pago) × fator,
        # que é o "Valor Corrigido" do Resumo do PDF. Validado no 0011753: soma
        # 67.940 × 67.808 do resumo (fora FGTS, que o .pjc não traz como verba).
        # Sem juros: juros vive noutro bloco (ApuracaoDeJuros), ainda não mapeado.
        indice = _num(_leaf(oc, "indiceAcumulado"))
        nome = verba["nome"]
        v = porg.get(nome)
        if v is None:
            v = porg[nome] = {"nome": nome, "soma_devido": 0.0,
                              "reflexo": verba["reflexo"], "competencias": [],
                              "compor_principal": verba["compor_principal"],
                              "zera_negativo": verba["zera_negativo"]}
            ordem.append(nome)
        dif = devido - pago
        if verba["zera_negativo"] and dif < 0:
            dif = 0.0   # o PJC zera a ocorrência negativa quando a verba manda (opção do calculista)
        v["competencias"].append({
            "competencia": comp,
            "base": _num(_leaf(oc, "base")),
            "multiplicador": _num(_leaf(oc, "multiplicador")),
            "quantidade": _num(_leaf(oc, "quantidade")),
            "devido": round(dif, 2),  # "Diferença" do PDF (Devido − Pago, zerada se a verba manda)
            # as duas parcelas da diferença, expostas para comparar a DEDUÇÃO com
            # a da IA (`valores_compensados`): o que o PJC abate por já ter sido
            # pago na folha não aparece no líquido.
            "devido_bruto": round(devido, 2),
            "pago": round(pago, 2),
            "indice": float(indice) if indice is not None else None,
            "corrigido": round(dif * float(indice if indice is not None else 1), 2),
        })

    out = [porg[n] for n in ordem]
    for v in out:
        v["competencias"].sort(key=lambda c: c["competencia"])
        v["soma_devido"] = round(sum(c["devido"] for c in v["competencias"]), 2)
        v["soma_pago"] = round(sum(c["pago"] for c in v["competencias"]), 2)
        v["soma_corrigido"] = round(sum(c["corrigido"] for c in v["competencias"]), 2)
        # fator médio da verba (corrigido ÷ nominal): é o que dá para comparar com
        # o fator que a IA aplicou, competência a competência ou no total da verba
        v["fator_correcao"] = (round(v["soma_corrigido"] / v["soma_devido"], 6)
                               if v["soma_devido"] else None)
        v["n_competencias"] = len(v["competencias"])
    return out


def _rubricas_por_id(s: str) -> dict:
    """id -> nome de cada HistoricoSalarial completo (rubrica da folha)."""
    idx = {}
    for hs in _blocos(s, "HistoricoSalarial"):
        vid, nome = _leaf(hs, "id"), _txt(_leaf(hs, "nome") or "")
        if vid and nome:
            idx.setdefault(vid, nome)
    return idx


def _rubricas_base(s: str, id2nome: dict) -> list:
    """Rubricas que compõem o SALÁRIO BASE, pela estrutura do cálculo: os
    HistoricoSalarialDaVerba com <tipoVinculoHistorico>BASE apontam (por
    internalRef) para a rubrica que serve de base. União dessas rubricas.
    Isso é o que o motor usa — o PDF não expõe, só renderiza a tabela crua."""
    base = set()
    for blk in _blocos(s, "HistoricoSalarialDaVerba"):
        if (_leaf(blk, "tipoVinculoHistorico") or "").strip() != "BASE":
            continue
        m = re.search(r"<historicoSalarial><HistoricoSalarial><internalRef>(\d+)", blk)
        if m and m.group(1) in id2nome:
            base.add(id2nome[m.group(1)])
    return sorted(base)


def _historico_salarial(s: str) -> tuple:
    """({AAAA-MM: {salario_base, premio_metas, todas:{rubrica: valor}}},
        rubricas_base:[str]).

    salario_base = SOMA das rubricas com vínculo BASE naquele mês (estrutural).
    Fallback pro heurístico de nome quando não há vínculo BASE no arquivo."""
    hist: dict[str, dict] = {}
    rubricas: list[str] = []
    for hs in _blocos(s, "HistoricoSalarial"):
        nome = _txt(_leaf(hs, "nome") or "")
        if not nome:
            continue
        rubricas.append(nome)
        oi = hs.find("<ocorrencias>")
        occ_blk = _extract_balanced(hs, "ocorrencias", oi)[0] if oi >= 0 else ""
        for oc in _blocos(occ_blk or "", "OcorrenciaDoHistoricoSalarial"):
            comp = _comp(_leaf(oc, "dataOcorrencia"))
            val = _num(_leaf(oc, "valor"))
            if comp is None or val is None:
                continue
            hist.setdefault(comp, {"salario_base": None, "premio_metas": None, "todas": {}})
            hist[comp]["todas"][nome] = val

    def _acha(*termos, exclui=()):
        for r in rubricas:
            R = r.upper().replace("Á", "A").replace("Ê", "E")
            if all(t in R for t in termos) and not any(e in R for e in exclui):
                return r
        return None

    base_rub = _rubricas_base(s, _rubricas_por_id(s))
    r_base_nome = _acha("SALARIO", "BASE", exclui=("REAJUST",))  # fallback heurístico
    r_prem = _acha("PR", "MIO")
    for comp, linha in hist.items():
        if base_rub:
            vals = [linha["todas"][r] for r in base_rub if r in linha["todas"]]
            linha["salario_base"] = round(sum(vals), 2) if vals else None
        elif r_base_nome:
            linha["salario_base"] = linha["todas"].get(r_base_nome)
        if r_prem:
            linha["premio_metas"] = linha["todas"].get(r_prem)
    return hist, base_rub


def _ferias_gozo(s: str) -> list[tuple[str, str]]:
    """Períodos de GOZO (Gozo 1..3 de cada <Ferias>), em dd/mm/aaaa."""
    per: list[tuple[str, str]] = []
    li = s.find("<listaDeFerias>")
    blk = _extract_balanced(s, "listaDeFerias", li)[0] if li >= 0 else ""
    for fer in _blocos(blk or "", "Ferias"):
        for n in (1, 2, 3):
            ini = _ddmmaaaa(_leaf(fer, f"dataInicialDoPeriodoDeGozo{n}"))
            fim = _ddmmaaaa(_leaf(fer, f"dataFinalDoPeriodoDeGozo{n}"))
            if ini and fim:
                per.append((ini, fim))
    return list(dict.fromkeys(per))


def _dias_ferias_por_mes(periodos: list[tuple[str, str]]) -> dict:
    dias: dict[str, int] = {}
    for ini, fim in periodos:
        try:
            di = datetime.date(*map(int, reversed(ini.split("/"))))
            df = datetime.date(*map(int, reversed(fim.split("/"))))
        except ValueError:
            continue
        d = di
        while d <= df:
            k = f"{d.year}-{d.month:02d}"
            dias[k] = dias.get(k, 0) + 1
            d += datetime.timedelta(days=1)
    return dias


def _multas(s: str) -> list[dict]:
    """Bloco "Multas e Indenizações" do PJe-Calc (<multas><Set><Multa>..).

    Não é verba (não tem ocorrência mensal): é um valor lançado à parte —
    multa por embargos protelatórios, litigância de má-fé, astreinte e, às
    vezes, a própria indenização por dano moral. O PJC soma isso ao crédito,
    mas o parser lia só as verbas, então a BT073 da IA aparecia "a mais".

    Devolve TODAS as multas, com `credor_reclamante` dizendo quem recebe:
    `tipoCredorDevedor` = CREDOR_DEVEDOR (RECLAMANTE_RECLAMADO = o reclamante
    recebe da reclamada). RECLAMADO_RECLAMANTE (o reclamante paga) e
    TERCEIRO_RECLAMANTE (IRRF etc.) não são crédito do reclamante — quem
    consome decide; aqui só se lê. Nominal = `valorMulta`; corrigido = nominal ×
    `indiceCorrecaoMulta` (mesma camada do `soma_corrigido` das verbas)."""
    # O arquivo pode ter mais de um <multas> (um vazio antes do que tem as multas): lê todos,
    # sem repetir a mesma multa. Lendo só o 1º, o dano moral de R$ 35 mil lançado como multa
    # sumia (0000558-61.2024.5.05.0132, 16/10/2026).
    out, vistos, i = [], set(), 0
    blocos = []
    while True:
        i = s.find("<multas>", i)
        if i < 0:
            break
        blk, fim = _extract_balanced(s, "multas", i)
        if blk:
            blocos.extend(_blocos(blk, "Multa"))
        i = fim if fim > i else i + 8
    for m in blocos:
        mid = _leaf(m, "id")
        if mid in vistos:
            continue
        vistos.add(mid)
        valor = _num(_leaf(m, "valorMulta"))
        nome = _txt(_leaf(m, "descricao") or "")
        if valor is None or not nome:
            continue
        indice = _num(_leaf(m, "indiceCorrecaoMulta"))
        tipo = (_leaf(m, "tipoCredorDevedor") or "").strip()
        out.append({"nome": nome, "valor": round(valor, 2),
                    "corrigido": round(valor * (indice if indice is not None else 1.0), 2),
                    "tipo_credor_devedor": tipo,
                    "credor_reclamante": tipo.startswith("RECLAMANTE_")})
    return out


def _resumo(s: str, verbas: list[dict]) -> list[dict]:
    """Best-effort: linha 'Total'. O Valor Corrigido total vem de
    dadosEstruturados.valorPrincipal quando presente; caso contrário None.
    TODO: mapear correção monetária por verba (bloco de atualização)."""
    corrigido = _num(_leaf(s, "valorPrincipal"))
    total_devido = round(sum(v["soma_devido"] for v in verbas), 2)
    return [{"descricao": "Total", "valor_corrigido": corrigido,
             "juros": None, "total": corrigido if corrigido is not None else total_devido}]


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
def parse_pjc_xml(caminho: str | Path) -> dict:
    caminho = Path(caminho)
    s = _ler_xml(caminho)
    todas = _verbas(s)
    verbas = [v for v in todas if v.get("compor_principal", True)]
    # fora do principal: não entram em total nem comparação; ficam para o aviso do caso
    fora_principal = [{"nome": v["nome"], "soma_devido": v["soma_devido"], "reflexo": v["reflexo"]}
                      for v in todas if not v.get("compor_principal", True)]
    cab = _cabecalho(s)
    # completa o fim do período com a última competência vista, se faltar
    if not cab.get("periodo_calculo") and cab.get("_periodo_ini") and verbas:
        comps = [c["competencia"] for v in verbas for c in v["competencias"]]
        if comps:
            y, m = map(int, max(comps).split("-"))
            ult = datetime.date(y + (m == 12), (m % 12) + 1, 1) - datetime.timedelta(days=1)
            cab["periodo_calculo"] = (f"{cab['_periodo_ini'].strftime('%d/%m/%Y')} a "
                                      f"{ult.strftime('%d/%m/%Y')}")
    cab.pop("_periodo_ini", None)
    gozo = _ferias_gozo(s)
    hist, rubricas_base = _historico_salarial(s)
    return {
        "cabecalho": cab,
        "resumo": _resumo(s, verbas),
        "verbas": verbas,
        "verbas_fora_principal": fora_principal,
        "multas": _multas(s),   # bloco "Multas e Indenizações" (fora de `verbas`)
        "historico_salarial": hist,
        "rubricas_base": rubricas_base,  # rubricas que compõem o salário base (só .pjc)
        "ferias_gozo": gozo,
        "dias_ferias_mes": _dias_ferias_por_mes(gozo),
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("uso: python parse_pjc_xml.py <arquivo.pjc | .PJC>")
        raise SystemExit(1)
    r = parse_pjc_xml(sys.argv[1])
    print(json.dumps(r["cabecalho"], ensure_ascii=False, indent=2))
    print(f"\nverbas: {len(r['verbas'])}")
    for v in r["verbas"]:
        tag = "reflexo" if v["reflexo"] else "princip"
        print(f"  [{tag}] {v['nome'][:52]:<52} {v['soma_devido']:>14,.2f}  "
              f"({v['n_competencias']} comp)")
    print(f"\nhistórico: {len(r['historico_salarial'])} competências; "
          f"férias de gozo: {len(r['ferias_gozo'])} período(s)")
