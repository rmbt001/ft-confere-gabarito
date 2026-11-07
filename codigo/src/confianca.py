"""Score de confiança do cálculo: o quanto dá para acreditar no total do LIFT
ANTES de existir o cálculo de referência.

Regra de ouro: só lê o lado LIFT do caso (verbas, competências, P9a, P7). Nada
aqui pode tocar `total_pjc`, `status` de pareamento ou qualquer campo do PJC,
porque em produção o gabarito não existe e o score é para lá. O PJC entra só
depois, na tela, para conferir se a faixa acerta.

Duas classes de componente:
- TRAVA: erro de método que, quando aparece, o cálculo quase nunca bate. Derruba
  o caso para "baixa" sozinha.
- RISCO: complexidade que pesa no acerto sem ser erro em si (gratificação,
  comissões, Súmula 340, meses sem base, ficha sem férias). Soma pontos.

Faixa: alguma trava ou 2+ pontos = baixa; 1 ponto = média; 0 = alta.

Medido em 14/10/2026 sobre os aptos com referência (109 casos; 53 da rodada
07–08/10): sem fator nenhum, mediana da acurácia global 76,9% e 36% ≥ 80;
com 2+ fatores ou trava, 0% ≥ 80. Pesos provisórios: N pequeno.
"""
from collections import Counter

from arvore import COD_JORNADA

# Regra da casa (Raíra, 15/10): o score só lê o que as TABELAS da esteira trazem
# como dado — código de glossário, marcas do P9a, base do P10a, calendário do P8,
# férias do P1. Nada de interpretação da decisão (limitação da inicial, premissa,
# tema do agente) nem de adivinhar pelo nome da verba.
HONORARIOS = {"BT062", "BT063", "BT079"}               # advogado reclamada/reclamante, periciais
COD_HE = {"BT089", "BT001", "BT081", "BT011", "BT087"}  # hora extra por tipo, no glossário
COD_GRATIFICACAO = {"BT025"}
COD_COMISSAO = {"BT024"}
IDS_COMISSAO = {"comissoes", "comissao_fixa", "complemento_comissao"}  # componentes do P9a

SEM_BASE_RISCO = 0.10      # fração de competências sem base que já pesa
SEM_BASE_FORTE = 0.50      # a partir daqui conta 2 pontos (subcálculo em 71% dos casos)
AFAST_MESES = 6            # meses inteiros de afastamento a partir dos quais pesa

FAIXAS = ("alta", "media", "baixa")


def _cod(v):
    """Código de glossário da verba, como a tabela entrega (P10a em `codigo`, P10b em `codigo_glossario`)."""
    return v.get("codigo") or v.get("codigo_glossario")


def _calculadas(c):
    """Verbas que o LIFT de fato calculou (lado IA, com valor), sem honorários (não são crédito do reclamante)."""
    return [v for v in c.get("verbas") or []
            if v.get("status") != "so_pjc" and isinstance(v.get("total_ia"), (int, float))
            and not v.get("fora_comparacao") and _cod(v) not in HONORARIOS]


def _principais(vs):
    return [v for v in vs if v["total_ia"] > 0 and not v.get("is_reflexo")]


def _sem_codigo(vs):
    hits = [v for v in _principais(vs) if v.get("codigo_glossario") == "Não encontrado"]
    if hits:
        tot = sum(v["total_ia"] for v in hits)
        brl = f"{tot:,.2f}".translate(str.maketrans(",.", ".,"))
        return f"{len(hits)} verba(s) sem código no glossário somando R$ {brl}"
    return None


def _he_duplicada(vs):
    """O mesmo código de hora extra em duas verbas principais calculadas."""
    cods = Counter(_cod(v) for v in _principais(vs) if _cod(v) in COD_HE)
    dup = sorted(c for c, n in cods.items() if n > 1)
    return f"mais de uma verba de hora extra com o código {', '.join(dup)}" if dup else None


def _base_e_salario(v):
    """A base da verba vem do salário do mês? Valor fixo da decisão (0017053:
    verba de representação de R$ 2.025,69/mês) e salário mínimo não dependem do
    holerite, então mês zerado ali não é "falta de salário"."""
    e = (v.get("p9a_raw") or {}).get("estrategia_base_calculo") or {}
    tipo = str(e.get("tipo") or "")
    if tipo.startswith("valor_fixo") or tipo == "salario_minimo_nacional":
        return False
    if tipo == "componentes_fixos":
        return bool(e.get("componentes_explicitos") or e.get("componentes"))
    return True


def _frac_sem_base(vs):
    """Fração das competências das verbas mensais em que o LIFT ficou sem salário.

    Só conta mês que o LIFT calculou (`ia.valor` preenchido). A tabela da verba
    junta os meses dos dois lados, e mês que só a referência apura vem com `ia`
    vazio: contá-lo como "sem salário" fazia o caso 0001460 (2010–2012 só no PJC)
    parecer 41% sem base.

    Meses zerados nas pontas do período (depois do último holerite) CONTAM,
    mesmo parecendo a premissa 15.0: medido em 14/10, contar só o buraco do meio
    derrubou a alta de 54% para 45% na meta, porque na maioria dos casos a
    referência apura esses meses e a IA não (subcálculo). O 0017053, em que a
    referência também para, é a exceção e fica em "média".
    """
    n = zero = 0
    for v in vs:
        if v.get("is_reflexo") or v.get("is_rescisoria") or not _base_e_salario(v):
            continue
        for x in v.get("competencias") or []:
            ia = x.get("ia")
            if not ia or ia.get("valor") is None:
                continue
            # mês sem dia trabalhado (férias ou afastamento integral) zera por
            # direito, não por falta de salário (0000081: 03/2018 e 01/2020)
            if (x.get("cal_p8") or {}).get("dias") == 0:
                continue
            n += 1
            # comissionista (Súmula 340) guarda a base em fixa + variável e deixa
            # `base` vazio: 35 meses calculados do 0000081 pareciam "sem salário"
            zero += not (ia.get("base") or ia.get("base_fixa") or ia.get("base_variavel"))
    return (zero / n) if n else None


def _meses_afastado(vs):
    """Meses calculados sem nenhum dia trabalhado por causa de afastamento."""
    meses = set()
    for v in vs:
        if v.get("is_reflexo"):
            continue
        for x in v.get("competencias") or []:
            p8 = x.get("cal_p8") or {}
            if (x.get("ia") or {}).get("valor") is not None and p8.get("dias") == 0 and (p8.get("afast") or 0) > 0:
                meses.add(x["competencia"])
    return len(meses)


def _meses_calculados(vs):
    return len({x["competencia"] for v in vs if not v.get("is_reflexo")
                for x in v.get("competencias") or [] if (x.get("ia") or {}).get("valor") is not None})


def _componentes_base(vs):
    """Componentes da base que o P9a declarou para as verbas (códigos e identificadores).

    O histórico do P7 fica de fora de propósito: gratificação ou comissão que o
    reclamante recebia mas que nenhuma verba usa (0001460: base do intervalo = só
    salário-base) não torna o cálculo mais arriscado.
    """
    ids = set()
    for v in vs:
        e = (v.get("p9a_raw") or {}).get("estrategia_base_calculo") or {}
        ids |= {str(x) for x in (e.get("componentes_explicitos") or []) + (e.get("componentes") or [])}
    return ids


def score_confianca(c):
    vs = _calculadas(c)
    if not vs:
        return None
    comp = []

    def add(tipo, chave, rotulo, detalhe, pontos=0):
        comp.append({"tipo": tipo, "chave": chave, "rotulo": rotulo, "detalhe": detalhe, "pontos": pontos})

    if (d := _sem_codigo(vs)):
        add("trava", "sem_codigo", "Verba sem código no glossário", d)
    # "Reflexo acima do teto" (13º > 1/12, férias > 1/9 da base) saiu em 14/10: o
    # próprio PJC passa disso (aviso projetado soma avos sem verba-base; mês de
    # férias reduz o adicional mas conta avo cheio). Com o código de reflexos de
    # 09/10 (homol) ela barrava 16 aptos, inclusive 0100195 (97%) e 1000835 (100%).
    if (d := _he_duplicada(vs)):
        add("trava", "he_duplicada", "Hora extra duplicada", d)

    fsb = _frac_sem_base(vs)
    if fsb is not None and fsb >= SEM_BASE_RISCO:
        forte = fsb >= SEM_BASE_FORTE
        add("risco", "sem_base", "Competências sem salário",
            f"{fsb:.0%} das competências das verbas mensais calculadas com base zero".replace(".", ","),
            2 if forte else 1)

    # Ficha de registro sem férias: o calendário (P8) conta todo dia como
    # trabalhado e a quantidade de HE/intervalo infla. Só pesa com contrato de
    # 12+ meses calculados (antes disso pode não haver férias a gozar). Só pesa
    # com verba que conta DIAS (hora extra, intervalo): verba de valor fixo mensal
    # não muda com férias (0017053, 96,5%, caía para baixa). Peso 1 e não 2:
    # medido em 14/10, +2 jogava casos bons para "baixa" (1000884, 98,8%).
    meses = _meses_calculados(vs)
    jor = any(_cod(v) in COD_JORNADA for v in _principais(vs))
    if c.get("ferias_p1") == [] and meses >= 12 and jor:
        add("risco", "sem_ferias", "Ficha de registro sem férias",
            f"nenhuma férias cadastrada em {meses} meses calculados — os dias de férias viram dias trabalhados na hora extra/intervalo", 1)

    # Afastamento longo: meses inteiros parados (auxílio-doença/acidente) mexem
    # nos avos de 13º/férias, na estabilidade e nos reflexos, e é onde o código
    # cria base em mês sem trabalho. Medido em 14/10: 8 aptos com 6+ meses de
    # afastamento integral, nenhum na meta, 6 com sobrecálculo — 6 dos 8 estavam
    # na faixa alta. Peso 1 basta para tirá-los do automático.
    n_afast = _meses_afastado(vs)
    if n_afast >= AFAST_MESES:
        add("risco", "afastamento_longo", "Afastamento longo",
            f"{n_afast} meses calculados inteiramente em afastamento", 1)

    # Alavancas tiradas da árvore e dos dossiês da homol de 13→14/10 (prompts de
    # homol, código de 09/10), medidas em 230 casos com referência:
    cods = {_cod(v) for v in _principais(vs)}
    # Insalubridade + periculosidade juntas (CLT 193 §2º; 0010185, 0012390, 0020005)
    # separava bem (71% com sobrecálculo contra 35%), mas a correção vai entrar no
    # prompt: é erro a corrigir, não risco a medir (decisão da Raíra, 14/10).
    # verba de representação: o código de reflexos pela média ainda conta meses
    # demais (0001152, 0017053, 0000302). 60% com sobrecálculo contra 36%.
    if "BT082" in cods:
        add("risco", "representacao", "Verba de representação",
            "reflexos pela média da verba costumam contar meses em que ela não existia", 1)

    # "Limitação aos valores da inicial" (T45) entrou e saiu em 15/10: é leitura do
    # texto da decisão, não dado que as tabelas da esteira entreguem.

    flags = [((v.get("p9a_raw") or {}).get("flags_sumulas") or {}) for v in vs]
    comps = _componentes_base(vs)
    s109 = any(f.get("aplica_s109") for f in flags)
    if s109 or comps & COD_GRATIFICACAO or cods & COD_GRATIFICACAO:
        add("risco", "gratificacao", "Gratificação de função",
            "Súmula 109 marcada no P9a" if s109 else "gratificação (BT025) na base ou como verba do cálculo", 1)
    if comps & (COD_COMISSAO | IDS_COMISSAO) or cods & COD_COMISSAO:
        add("risco", "comissoes", "Comissões", "comissão (BT024) na base ou como verba do cálculo", 1)
    if any(f.get("aplica_s340") for f in flags) or any(v.get("usa_s340") for v in vs):
        add("risco", "sumula_340", "Súmula 340", "hora extra de comissionista (só o adicional)", 1)

    travas = [x for x in comp if x["tipo"] == "trava"]
    pontos = sum(x["pontos"] for x in comp)
    faixa = "baixa" if travas or pontos >= 2 else ("media" if pontos == 1 else "alta")
    return {"faixa": faixa, "pontos": pontos, "n_travas": len(travas),
            "frac_sem_base": round(fsb, 3) if fsb is not None else None, "componentes": comp}
