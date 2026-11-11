"""Árvore de divergências PJC × IA: o diagnóstico de cada caso e o resumo de padrões.

Quem usa: `codigo/analises/arvore_divergencias.py`, que grava um JSON por caso
fora do repo. O painel do app NÃO usa a árvore; o relatório da rodada é um
artefato à parte, montado a partir desses JSONs.

A árvore (página "Árvore de Divergências PJC × IA") decompõe a diferença entre o
total do PJC e o da IA em nós, na ordem em que um erro contamina o outro:

  0.1/0.2 gabarito       — extração do PJC e pareamento das verbas
  1.1  período           — meses que só um dos lados calculou
  1.2  verbas            — verba que só um lado tem, ou deferida e não calculada
  2.1  quantidade        — horas (ou fração do mês); 2.1.2 separa os meses de férias
  2.2.1 salário          — salário mês a mês diferente
  2.2.2 composição       — o que se soma ao salário para formar a base
  2.3  multiplicador     — adicional, fração e divisor
  2.4  pago              — o que cada lado abateu
  2.5  hora extra por tipo — 7ª e 8ª × além da 8ª (limite, teto, gratificação, sobreposição)
  3    reflexos          — herdado da principal × regra própria
  4    totalização       — saldo negativo, honorários e custas

O valor de cada nó sai por substituição sequencial mês a mês: troca-se o fator
da IA pelo do PJC, na ordem acima, e o quanto o valor mudou é o R$ do nó. As
parcelas somam o gap da verba, então nenhum erro é contado duas vezes. A ordem
é fixa de propósito — com outra ordem os números mudam e os casos deixam de ser
comparáveis.

Cada achado leva um código `padrao` fixo. É ele que a varredura agrupa.

Os JSONs ficam FORA do repositório (padrão: Repos/ft_arvore_divergencias), para
não subirem para o Git junto com o código.

Uso avulso, a partir da raiz do app:

    .venv\\Scripts\\python.exe codigo\\analises\\arvore_divergencias.py 2026-10-02 [--saida PASTA]
"""
import argparse
import json
import re
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

_PAIS = Path(__file__).resolve().parents
# no Repos fica 5 níveis acima; no confere gabarito (pasta mais rasa) fica em saidas/
SAIDA_PADRAO = (_PAIS[5] if len(_PAIS) > 5 else _PAIS[2] / "saidas") / "ft_arvore_divergencias"
JSON_PAINEL = Path("saidas/validacao_calculos.json")
MIN_RS = 50.0  # achado abaixo disso é ruído de arredondamento

# códigos que são hora extra / intervalo (quantidade em horas vinda da jornada)
COD_JORNADA = {"BT089", "BT001", "BT081", "BT087", "BT011", "BT004", "BT007", "BT002", "BT037"}
COD_HE = {"BT089", "BT001", "BT081", "BT087"}

# ----------------------------------------------------------------- catálogo de padrões
# rótulo, leitura, o que significa, onde mexer e — quando já confirmada lendo o
# prompt (tabela ft_lift_tb_agente) ou o código do bt-lift-fast-track-back — a
# CAUSA NA RAIZ com versão. Leitura: prompt | medicao | metodo | politica |
# herdado | investigar. O painel e o relatório leem daqui; um padrão novo sem
# entrada aparece com o código cru, de propósito, para ninguém esquecer de catalogar.
PADROES = {
    "pjc_extracao_nao_confiavel": dict(rotulo="Gabarito lido só como subtotal", leitura="medicao",
        o_que="O extrator leu o PJC só pelas linhas de resumo; não há verba para comparar.", onde="Extrator do PJC."),
    "pjc_linha_de_subtotal": dict(rotulo="Linha de subtotal lida como verba", leitura="medicao",
        o_que="'VERBAS TRIBUTÁVEIS', 'CONTRIBUIÇÃO SOCIAL' e afins entraram como verba do PJC.", onde="Extrator do PJC."),
    "pareamento_suspeito": dict(rotulo="Mesma verba com nomes diferentes", leitura="medicao",
        o_que="Verba 'só IA' e verba 'só PJC' da mesma família no mesmo caso — quase sempre a mesma verba sem par no de-para (PPE × PDE, sobreaviso).",
        onde="glossario_bt.json / depara_final_verbas_codigo."),
    "ia_competencias_sem_apuracao": dict(rotulo="Meses sem apuração na IA", leitura="prompt",
        o_que="O mês existe na IA, mas sem quantidade, base nem memória; o P9b gerou menos competências que o período.",
        onde="P9b (CALC_QUANTIFICADOR_MENSAIS) e código do P9b.",
        raiz="Diagnóstico da rodada 02/10 (saídas brutas do P9b e do P10a): (1) P9a define periodo_aplicacao da verba mais curto que o do calculista — 10 verbas/8 casos, ~R$ 100 mil; (2) verba com cartão: passthrough_cartao_utils.py:323-333 mantém só as competências do cartão — 40 verbas/19 casos, ~R$ 80 mil; (3) mês com 0 dias trabalhados (férias/afastamento integral) zerado pelo P9b — 10 verbas, ~R$ 29 mil; (4) P9b devolve menos competências que o período, em geral nas pontas — 14 verbas, ~R$ 28 mil; (5) P9b tem horas mas P10a zera por base vazia (alerta P9b_componente_ausente) — 8 verbas/6 casos, ~R$ 17 mil, único caso de perda entre etapas. Anomalia isolada: 1000943-31.2021.5.02.0471 tem verba_01 duplicada no P10a com 0 competências (alerta P10a_apuracao_incompleta)."),
    "periodo_sem_holerite_nos_autos": dict(rotulo="Meses calculados sem holerite nos autos", leitura="prompt",
        o_que="A IA calcula meses para os quais não há holerite no processo; a regra é restringir o cálculo ao período com holerite.",
        onde="P9b (CALC_QUANTIFICADOR_MENSAIS): hierarquia de fontes de remuneração.",
        raiz="CALC_QUANTIFICADOR_MENSAIS (P9b) v5: 'Holerite é a fonte primária. Dados Iniciais (lista_salarios) é a fonte secundária' — sem holerite no mês, o P9b busca o salário nos Dados Iniciais e calcula assim mesmo."),
    "he_7a8a_compensacao_gratificacao_diverge": dict(rotulo="7ª e 8ª: desconto da gratificação (regra: sempre descontar)", leitura="politica",
        o_que="A orientação é sempre descontar a gratificação de função nas horas de 7ª e 8ª. A IA faz isso; a diferença vem dos casos em que o calculista não descontou.",
        onde="Nenhum ajuste na IA."),
    "periodo_ia_a_mais": dict(rotulo="IA calcula meses que o PJC não calcula", leitura="politica",
        o_que="Prescrição, data de deferimento ou recorte do calculista por falta de holerite.", onde="P4/P9a ou política para meses sem documento."),
    "verba_so_ia": dict(rotulo="Verba trabalhista só na IA", leitura="investigar",
        o_que="A IA deferiu e calculou uma verba que o PJC não tem, sem verba parecida do outro lado.", onde="P4 (INFOS_DECISOES); conferir sentença × acórdão."),
    "verba_so_pjc": dict(rotulo="Verba trabalhista só no PJC", leitura="investigar",
        o_que="O PJC calcula uma verba que a IA não deferiu.", onde="P4 ou de-para."),
    "verba_so_ia_indenizatoria": dict(rotulo="Indenizatória só na IA", leitura="investigar",
        o_que="Dano moral/material, pensão, multas e estabilidade calculados só pela IA.", onde="P4 e escopo do Fast Track."),
    "verba_so_pjc_indenizatoria": dict(rotulo="Indenizatória só no PJC", leitura="investigar",
        o_que="Pensão vincenda, indenizações e estabilidade calculados só pelo PJC.", onde="P4 e escopo."),
    "deferida_nao_calculada": dict(rotulo="Deferida e declarada não calculável", leitura="prompt",
        o_que="O P4 deferiu, o P9a declarou não calculável, o PJC calculou.", onde="P9a: motivos de não-cálculo."),
    "pedaco_de_verba_deferida_so_pjc": dict(rotulo="Parte de verba deferida só no PJC", leitura="prompt",
        o_que="O PJC tem uma linha (ex.: HE 100%) de uma verba que a IA deferiu, mas não alcançou.", onde="P9a (jornada) na maioria."),
    "verba_so_ia_familia_ja_pareada": dict(rotulo="Verba desdobrada na IA", leitura="investigar",
        o_que="Duas verbas da mesma família na IA; só uma tem par.", onde="P4."),
    "conta_sem_detalhe_mensal": dict(rotulo="Verba sem competências para decompor", leitura="investigar",
        o_que="Verba de valor único com valores diferentes, sem detalhe mensal.", onde="Caso a caso."),
    "residuo_conciliacao": dict(rotulo="Resíduo de conciliação", leitura="metodo",
        o_que="Total do painel ≠ soma das competências da verba.", onde="Painel."),
    "horas_ia_a_menos": dict(rotulo="Horas a menos, sem causa identificada", leitura="investigar",
        o_que="Fora das férias, a IA tem menos horas que o PJC e nenhuma regra conhecida explica.", onde="P9a (regimes) / P9b (apuração)."),
    "horas_ia_a_mais": dict(rotulo="Horas a mais, sem causa identificada", leitura="investigar",
        o_que="Fora das férias, a IA tem mais horas que o PJC sem regra conhecida.", onde="P9a / P9b."),
    "jornada_descricao_nao_estruturada": dict(rotulo="Jornada com partes só no texto", leitura="prompt",
        o_que="A descrição cita sábado, domingo ou acionamentos que os regimes não têm; o cálculo só enxerga regimes.",
        onde="P9a: definicoes_contextuais.jornadas[].regimes."),
    "ferias_em_meses_diferentes": dict(rotulo="Férias em meses diferentes", leitura="prompt",
        o_que="Um lado tem férias (≥ 5 dias) num mês em que o outro não tem nenhuma.", onde="P8 (CALC_CALENDARIO): leitura do período de gozo."),
    "ferias_nao_proporcionalizada_pela_ia": dict(rotulo="IA não proporcionaliza nas férias", leitura="prompt",
        o_que="No mês de férias o PJC reduz a verba e a IA cobra o mês cheio (e o reflexo em férias de novo).",
        onde="P10a regra 2.1.",
        raiz="CALC_PRINCIPAL_MENSAIS (P10a) v3, regra 2.1 (BT035/BT036): proporcional por dias trabalhados SÓ no primeiro e no último mês do contrato; 'Cálculo Integral (Meses Intermediários)' mesmo com férias ou afastamento."),
    "ferias_proporcionalizada_so_pela_ia": dict(rotulo="Só a IA proporcionaliza nas férias", leitura="investigar",
        o_que="A IA reduz a verba no mês de férias e o PJC não.", onde="Conferir critério do calculista."),
    "ferias_quantidade_diverge": dict(rotulo="Quantidade diverge em mês de férias", leitura="investigar",
        o_que="Diferença nos meses de férias sem mês trocado nem diferença de proporcionalização. Lembrete: o P8 conta férias em dia útil e o PJC em dia corrido; isso sozinho não é erro.", onde=""),
    "intrajornada_paga_integral": dict(rotulo="Intrajornada paga integral", leitura="prompt",
        o_que="Com gozo parcial, o P9a marcou o intervalo inteiro como suprimido; o PJC paga só o tempo suprimido (art. 71 §4º pós-Reforma).",
        onde="P9a: tratamento_intervalo.tempo_suprimido_minutos.",
        raiz="Sem cartão não há corte da Reforma: P9a v9 CASOS A/B/C e P9b Q2 pagam horas_suprimidas × dias sem separar pré/pós 11/11/2017; o P4 manda 'mínimo legal − gozado; integral só no pré-Reforma', mas nenhum dos dois aplica. Só o motor de cartão (cartao_ponto/.../intrajornada_strategy.py:30-33) faz o corte."),
    "verba_mensal_fracao_ia_menor": dict(rotulo="Fração do mês menor na IA", leitura="investigar", o_que="Fora das férias.", onde="P9b/P10a."),
    "verba_mensal_fracao_ia_maior": dict(rotulo="Fração do mês maior na IA", leitura="investigar",
        o_que="A IA usa o mês cheio onde o PJC proporcionaliza, fora das férias (afastamentos).", onde="P10a regra 2.1.",
        raiz="Provável mesma raiz da proporcionalização: P10a v3 regra 2.1 só proporcionaliza admissão/demissão."),
    "cartao_deferido_nao_usado": dict(rotulo="Cartão deferido e não usado", leitura="prompt",
        o_que="A decisão manda apurar por cartão e a memória do P9b não tem batidas.", onde="P9b."),
    "p7_salario_diverge": dict(rotulo="Salário do P7 diferente do PJC", leitura="prompt",
        o_que="Salário-base extraído diverge do histórico do PJC em 3 meses ou mais.", onde="P7 (HIST_SALARIAL_*)."),
    "p7_salario_constante": dict(rotulo="P7 repete um salário só", leitura="prompt",
        o_que="Mesmo salário em todos os meses enquanto o PJC tem reajustes.", onde="P7."),
    "salario_diverge": dict(rotulo="Salário diverge (pequeno)", leitura="investigar", o_que="", onde=""),
    "base_expandida_com_rubricas_do_holerite": dict(rotulo="Base inflada por rubricas do holerite", leitura="prompt",
        o_que="Com 'dinâmica + expandir com integra_salario', a IA soma à base rubricas do holerite que o PJC não soma.",
        onde="P9a (estrategia_base_calculo) e P9b.",
        raiz="P9a v9 PASSO 3: BT001/BT081/BT089 → dinamica_por_competencia com expandir_com_integra_salario=true; P9b 2.2 manda somar TODAS as rubricas do holerite com integra_salario=true na competência. Código ainda mexe em BT025/BT026/BT049 (composicao_base_horas_extras_strategy.py:38-61)."),
    "base_ia_menor": dict(rotulo="Base menor que a do PJC", leitura="prompt",
        o_que="A IA deixa fora da base algo que o PJC inclui (adicional deferido, gratificação, comissões).", onde="P9a/P9b."),
    "base_ia_maior": dict(rotulo="Base maior que a do PJC", leitura="investigar", o_que="Outros motivos que não a expansão.", onde="P9a/P9b."),
    "base_salario_minimo_diverge": dict(rotulo="Base de salário mínimo diverge", leitura="prompt",
        o_que="Insalubridade sobre salário mínimo com valor do mínimo diferente.", onde="P9a/P9b."),
    "p9b_ignora_componente_deferido_na_base": dict(rotulo="P9b ignora componente pedido pelo P9a", leitura="prompt",
        o_que="O P9a manda somar um adicional deferido à base e o P9b usa só o salário.", onde="P9b: componentes_explicitos."),
    "multiplicador_diverge": dict(rotulo="Multiplicador diverge (sem classificação)", leitura="investigar", o_que="Verbas fixas/comissão sem percentual exposto.", onde=""),
    "multiplicador_residual": dict(rotulo="Resíduo de multiplicador", leitura="metodo",
        o_que="Multiplicador mediano igual; o valor vem de o PJC misturar linhas com percentuais diferentes.", onde="Nenhum."),
    "adicional_ia_maior": dict(rotulo="Adicional maior na IA", leitura="prompt", o_que="Percentual de HE maior que o do PJC.", onde="P9a."),
    "adicional_ia_menor": dict(rotulo="Adicional menor na IA", leitura="prompt",
        o_que="O PJC aplica adicional convencional maior (75%, 100%); a IA ficou no legal.", onde="P9a: adicionais_resolvidos / CCT."),
    "percentual_diverge": dict(rotulo="Percentual da verba diverge", leitura="prompt", o_que="Ex.: insalubridade 40% × 20%.", onde="P4/P9a."),
    "adicional_noturno_hora_cheia": dict(rotulo="Adicional noturno pago como hora cheia", leitura="prompt",
        o_que="A IA multiplica por (1 + adicional), 1,2 ou 1,4, onde o PJC multiplica só pelo adicional: a hora noturna já está no salário.",
        onde="P10a regras 2.3/2.4.",
        raiz="CALC_PRINCIPAL_MENSAIS (P10a) v3, regras 2.3 e 2.4: valor = (base ÷ divisor) × (1 + adicional_percentual/100) × horas para TODA verba por hora — não há exceção para BT037, que paga só o adicional."),
    "pjc_paga_so_adicional": dict(rotulo="PJC paga só o adicional da hora extra", leitura="prompt",
        o_que="O PJC calcula só o adicional (S.340, hora já paga); a IA paga hora + adicional.", onde="P9a/P10a.",
        raiz="Mesma fórmula única do P10a v3 (regras 2.3/2.4): só a regra 2.2 (S.340 com base variável) separa o 'só adicional'."),
    "sobreaviso_sem_fracao_1_3": dict(rotulo="Sobreaviso sem o 1/3", leitura="prompt",
        o_que="A IA paga a hora cheia de sobreaviso; o PJC paga 1/3 (art. 244 §2º).", onde="P9a→P10a.",
        raiz="P10a v3 regras 2.3/2.4 não têm fração; o 1/3 só existe no texto do motivo do P9a, não em campo."),
    "divisor_diverge": dict(rotulo="Divisor diverge", leitura="prompt", o_que="220 × 200 × 180.", onde="P9a."),
    "pago_pjc_nao_abatido_pela_ia": dict(rotulo="IA não abate o que o PJC abate", leitura="prompt",
        o_que="O PJC abate valores pagos e a IA não abate nada.", onde="P7 (rubricas pagas) e P9b (valores_a_compensar)."),
    "ia_abate_o_que_pjc_nao_abate": dict(rotulo="IA abate o que o PJC não abate", leitura="prompt",
        o_que="A IA abate rubricas que o PJC não considera.", onde="P9b: valores_a_compensar."),
    "abatimento_diverge": dict(rotulo="Abatimento diverge nos dois lados", leitura="investigar",
        o_que="Os dois abatem, valores diferentes: rubricas agrupadas ou na verba errada.", onde="P7/P9b."),
    "tipo_he_diverge": dict(rotulo="Tipo de hora extra diverge", leitura="prompt",
        o_que="IA 'além da 8ª' onde o PJC tem '7ª e 8ª', ou o contrário.", onde="P4: codigo_glossario / nome da verba."),
    "he_7a8a_divisor_diverge": dict(rotulo="7ª e 8ª: divisor", leitura="prompt", o_que="180 × 220.", onde="P9a."),
    "he_7a8a_limite_diferente_de_6h": dict(rotulo="7ª e 8ª: limite diferente de 6 h", leitura="prompt", o_que="", onde="P9a."),
    "he_7a8a_sem_teto_2h": dict(rotulo="7ª e 8ª: sem teto de 2 h", leitura="prompt",
        o_que="Mais de 2 h/dia na verba de 7ª e 8ª: invade o 'além da 8ª'.", onde="P9a: teto_excedente_diario_horas."),
    "limite_diario_derivado_7h20": dict(rotulo="Além da 8ª com limite de 7h20", leitura="prompt",
        o_que="O P9a rebaixa o limite diário para 44 ÷ 6 = 7,33 h quando a decisão manda 'excedentes da 8ª diária e 44ª semanal'.",
        onde="P9a Fase 2, Prioridade 1 Caso B.",
        raiz="CALC_QUANTIFICADOR_ROTEAMENTO (P9a) v9, Fase 2 — Prioridade 1, Caso B: com limite diário E semanal, limite_diario_resolvido = min(diário, semanal ÷ dias_trabalho_semana) ('6x1 + diário 8 + semanal 44 → 7,3333'). Contradiz o P4 (EDITOR_DECISOES), que para 8h + 44h na 6x1 manda 8h de seg a sex e o sábado extra depois da 4ª hora. Nenhum código recalcula: o valor do P9a vai direto ao P9b."),
    "he_alem8a_limite_abaixo_de_8h": dict(rotulo="Além da 8ª com limite abaixo de 8 h", leitura="prompt", o_que="Limite 6 h ou outro < 8 numa verba além da 8ª.", onde="P9a."),
    "he_sobreposta": dict(rotulo="Horas extras sobrepostas", leitura="prompt",
        o_que="Duas verbas de HE na IA (ex.: 7ª e 8ª + além da 8ª) e só uma tem par no PJC: as mesmas horas entram duas vezes.",
        onde="P4 (desdobramento) e P9a (faixas)."),
    "reflexo_herda_erro_principal": dict(rotulo="Reflexo herda o erro da principal", leitura="herdado", o_que="Some ao corrigir a principal.", onde="Principal."),
    "reflexo_regra_diverge": dict(rotulo="Regra do reflexo diverge", leitura="metodo",
        o_que="No agregado as razões reflexo/principal são quase iguais (HE 0,40 × 0,43): ruído do método.", onde="Não priorizar."),
    "reflexo_sem_principal_na_ia": dict(rotulo="Reflexo sem principal mapeada", leitura="medicao", o_que="Família do reflexo não reconhecida pelo nome.", onde="Mapeamento reflexo → principal."),
    "saldo_negativo_abate_total": dict(rotulo="Saldo negativo abatendo o total", leitura="prompt",
        o_que="Verba com total negativo entra na soma; o PJC deixa fora do principal.", onde="P10a/P10.",
        raiz="P10a v3, regra de sinal (item 4): 'PARA TODAS AS DEMAIS VERBAS valor_final_competencia pode ser negativo' — e não há trava no total da verba."),
    "nao_verba_no_total": dict(rotulo="Honorários e custas como verba", leitura="prompt",
        o_que="Honorários (inclusive do advogado da reclamada) e custas entram na soma das verbas.", onde="P10b e painel.",
        raiz="Honorários periciais são 'valor fixo único' de rescisória no P9a e entram em total_rescisorias, a menos que o código esteja na variável VERBAS_EXCLUIDAS_CALC_PRINCIPAL_RESULTADO (template.yaml:102-106, vazia por padrão; valor real em GitHub Variables)."),
}
LEITURAS = {"prompt": "Ajuste de prompt", "medicao": "Medição", "metodo": "Efeito do método",
            "politica": "Decisão de política", "herdado": "Herdado", "investigar": "A investigar"}
NOS_ARVORE = {
    "0.1": "PJC extraído inteiro?", "0.2": "Rubricas pareadas certo?", "1.1": "Período igual?",
    "1.1.1": "Meses sem holerite nos autos", "1.1.2": "Meses sem cálculo na IA", "1.1.3": "Meses além do período, outro motivo", "1.2": "Verbas iguais?",
    "2": "Conta sem detalhe mensal", "2.1": "Quantidade (sem causa identificada)", "2.1.1": "Jornada estruturada = decisão?",
    "2.1.2": "Férias e afastamentos", "2.1.3": "Regra de apuração", "2.2.1": "Salário mês a mês", "2.2.2": "Composição da base",
    "2.3": "Multiplicador (outros)", "2.3.1": "Adicional por tipo de dia", "2.3.2": "Fração aplicada", "2.3.3": "Divisor",
    "2.4": "Pago e abatimento", "2.5.1": "Tipo de hora extra", "2.5.2": "7ª e 8ª horas", "2.5.3": "Além da 8ª",
    "2.5.4": "Horas extras sobrepostas", "3.1": "Erro herdado da principal", "3.2": "Regra própria do reflexo",
    "4.1": "Saldo negativo no total", "4.2": "Só verba no total",
}


def meta():
    """O que o painel precisa para rotular a árvore: catálogo, leituras e nós."""
    return {"padroes": PADROES, "leituras": LEITURAS, "nos": NOS_ARVORE, "min_rs": MIN_RS}

FAMILIAS = [  # ordem importa: a mais específica primeiro
    ("DF", ("DOMINGO", "FERIADO", "DSR TRABALHADO", "REPOUSO TRABALHADO")),
    ("IJ", ("INTERJORNADA", "ENTREJORNADA", "INTERSEMANAL")),
    ("IT", ("INTRAJORNADA", "INTERVALO INTRA", "INTERVALO PARA REFEI", "INTERVALO")),
    ("SA", ("SOBREAVISO", "PRONTIDAO")),
    ("AN", ("NOTURN",)),
    ("PE", ("PERICULOSIDADE",)),
    ("IN", ("INSALUBRIDADE",)),
    ("HE", ("HORAS EXTRAS", "HORA EXTRA", "EXTRAS", "HE")),
    ("PR", ("PPE", "PDE", "PREMIA", "PREMIO", "PLR", "PARTICIPACAO NOS LUCROS")),
    ("CO", ("COMISS", "SRV")),
    ("GR", ("GRATIFICA",)),
    ("DS", ("DIFEREN", "EQUIPARA", "REAJUSTE", "PISO")),
    ("AF", ("ACUMULO", "DESVIO")),
    ("FGTS", ("FGTS",)),
]
PREFIXOS_REFLEXO = ("13", "DECIMO", "FERIAS", "AVISO", "DSR", "REPOUSO", "RSR", "FGTS", "MULTA SOBRE FGTS", "MULTA DE 40", "MULTA 40")
NAO_VERBA = ("HONORAR", "CUSTAS", "PERIT")
# linhas de resumo do demonstrativo que o extrator às vezes lê como verba (furo conhecido)
SUBTOTAIS = ("VERBAS TRIBUTAVEIS", "VERBAS NAO TRIBUTAVEIS", "CONTRIBUICAO SOCIAL", "IRPF", "IMPOSTO DE RENDA", "TOTAL")
INDENIZATORIAS = ("INDENIZ", "DANO", "PENSAO", "ESTABILIDADE", "MULTA", "LITIGANCIA", "VINCENDA", "VENCIDA")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.upper()).strip()


def familia(nome):
    n = norm(nome)
    if " SOBRE " in n:
        n = n.split(" SOBRE ", 1)[1]
    elif " S/ " in n:
        n = n.split(" S/ ", 1)[1]
    for f, kws in FAMILIAS:
        # siglas curtas (HE, PPE, PDE, PLR) só como palavra inteira
        if any((re.search(rf"\b{k}\b", n) if len(k) <= 3 else k in n) for k in kws):
            return f
    return "?"


def eh_subtotal(nome):
    n = norm(nome)
    return any(n.startswith(k) for k in SUBTOTAIS)


def eh_indenizatoria(nome):
    n = norm(nome)
    return any(k in n for k in INDENIZATORIAS) and " SOBRE " not in n


def eh_reflexo(nome):
    n = norm(nome)
    return n.startswith(PREFIXOS_REFLEXO) or " SOBRE " in n or " S/ " in n


def eh_nao_verba(nome):
    n = norm(nome)
    return any(k in n for k in NAO_VERBA)


def nome_de(v):
    return v.get("nome_ia") or v.get("nome_pjc") or ""


def num(x):
    return float(x) if isinstance(x, (int, float)) else 0.0


def mediana(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


RE_MEM = re.compile(r"\(\s*R\$\s*([\d.]+)\s*/\s*([\d.]+)\s*\)\s*[×x]\s*([\d.]+)")


def parse_memoria(mem):
    """(base, divisor, multiplicador) do primeiro trecho '(R$ B / D) × M' da memória do P9b."""
    m = RE_MEM.search(mem or "")
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2)), float(m.group(3))
    except ValueError:
        return None


# ----------------------------------------------------------------- séries de salário
def series_salario(c):
    p7 = c.get("historico_p7") or {}
    rub = p7.get("rubricas") or []
    idx = next((i for i, r in enumerate(rub) if "BT090" in r), None)
    s_ia = {}
    if idx is not None:
        for l in p7.get("linhas") or []:
            v = (l.get("valores") or [None] * (idx + 1))[idx]
            if isinstance(v, (int, float)) and v > 0:
                s_ia[l["competencia"]] = float(v)
    pj = c.get("historico_pjc") or {}
    col = next((k for k in pj.get("colunas") or [] if norm(k) in ("SALARIO BASE", "SALARIO")), None)
    s_pj = {}
    if col:
        for l in pj.get("linhas") or []:
            v = (l.get("valores") or {}).get(col)
            if isinstance(v, (int, float)) and v > 0:
                s_pj[l["competencia"]] = float(v)
    return s_ia, s_pj


# ----------------------------------------------------------------- férias (2.1.2)
FERIAS_MIN_DIAS = 5     # mês "de férias" para fins de proporcionalização
FERIAS_CORTE = 0.85     # quantidade no mês de férias ≤ 85% da típica = proporcionalizou


def resumo_ferias(regs):
    """2.1.2: os meses de férias batem, e cada lado proporcionaliza a verba neles?

    "Quantidade" é a hora do mês (verba por hora) ou a fração do mês (verba mensal).
    Compara a quantidade do mês de férias com a típica dos meses sem férias, de
    cada lado. Abaixo de 85% da típica, aquele lado proporcionalizou.
    """
    def lado(chave_fer, chave_drv):
        normais = [r[chave_drv] for r in regs if r["fer_ia"] < 1 and r["fer_pj"] < 1 and r[chave_drv] > 0]
        tip = mediana(normais)
        mf = [r for r in regs if r[chave_fer] >= FERIAS_MIN_DIAS]
        if not tip or not mf:
            return None, len(mf)
        razao = mediana([r[chave_drv] / tip for r in mf])
        return (razao <= FERIAS_CORTE, len(mf)) if razao is not None else (None, len(mf))
    prop_ia, n_ia = lado("fer_ia", "drv_ia")
    prop_pj, n_pj = lado("fer_pj", "drv_pj")
    # mês trocado: um lado tem férias (≥ 5 dias) e o outro não tem nenhuma
    trocados = [r["comp"] for r in regs if (r["fer_ia"] >= FERIAS_MIN_DIAS and r["fer_pj"] < 1) or (r["fer_pj"] >= FERIAS_MIN_DIAS and r["fer_ia"] < 1)]
    # mesmo mês, contagem diferente (ex.: IA 18 × PJC 20 — dias úteis × corridos)
    contagem = [(r["comp"], r["fer_ia"], r["fer_pj"]) for r in regs if r["fer_ia"] >= 1 and r["fer_pj"] >= 1 and abs(r["fer_ia"] - r["fer_pj"]) >= 2]
    diverge = trocados + [c for c, _, _ in contagem]
    em_ferias = [r for r in regs if r["fer_ia"] >= 1 or r["fer_pj"] >= 1]
    return {
        "meses_ferias_ia": n_ia, "meses_ferias_pjc": n_pj,
        "meses_trocados": trocados[:8], "meses_contagem_diferente": len(contagem),
        "ia_conta_menos_dias": bool(contagem) and sum(1 for _, a, b in contagem if a < b) >= 0.8 * len(contagem),
        "exemplos_contagem": contagem[:4],
        "meses_calendario_divergente": len(diverge), "exemplos_divergentes": diverge[:6],
        "proporcionaliza_ia": prop_ia, "proporcionaliza_pjc": prop_pj,
        "rs_quantidade_em_meses_de_ferias": round(sum(r["dq"] for r in em_ferias), 2),
    }


# ----------------------------------------------------------------- tipo de hora extra (2.5)
def tipo_he(nome, cod=None):
    """7ª e 8ª × além da 8ª × após a 6ª × domingos/feriados, pelo NOME (o código do P4 não é confiável)."""
    n = norm(nome)
    if re.search(r"\b7\S{0,2}\s*(E|A)\s*8", n):
        return "7a_8a"
    if re.search(r"ALEM DA 8|ALEM 8|EXCEDENTES? (A|DA) 8|8\S{0,2}\s*(E|/)\s*4[04]|ALEM (DA )?4[04]|EXCEDENTES? (A|DA) 4[04]", n):
        return "alem_8a"
    if re.search(r"ALEM DA 6|EXCEDENTES? (A|DA) 6|APOS A 6|ATE A 6|6\S{0,2} DIARIA", n):
        return "alem_6a"
    if re.search(r"DOMINGO|FERIADO|100", n):
        return "domingos_feriados"
    return {"BT081": "7a_8a", "BT089": "alem_8a", "BT001": "alem_6a", "BT011": "domingos_feriados"}.get(cod, "nao_especificado")


# ----------------------------------------------------------------- ponte de uma verba
PASSOS =("periodo", "quantidade", "salario", "composicao", "divisor", "multiplicador", "pago")


def ponte_verba(v, s_ia, s_pj):
    comps = v.get("competencias") or []
    eh_hora = any(num((m.get("ia") or {}).get("horas")) > 0 for m in comps) or \
        (mediana([num(l.get("horas")) for m in comps for l in (m.get("pjc") or [])]) or 0) > 1
    acc = dict.fromkeys(PASSOS, 0.0)
    meses = {"ia_a_mais": [], "pjc_a_mais": []}
    sinais = defaultdict(list)  # m_ia, m_pj, d_ia, d_pj, k_ia, k_pj
    ia_tot = pj_tot = bruto_ia_tot = bruto_pj_tot = pago_ia = pago_pj = 0.0
    regs = []  # um registro por mês comparável: férias de cada lado, quantidade de cada lado, Δ da quantidade

    # taxa da IA por real de base, para meses sem hora na IA (ex.: interjornada zerada)
    taxas = []
    for m in comps:
        ia = m.get("ia") or {}
        h, b, br = num(ia.get("horas")), num(ia.get("base")), num(ia.get("valor_bruto"))
        if h > 0 and b > 0 and br > 0:
            taxas.append(br / h / b)
    taxa_mediana = mediana(taxas)

    for m in comps:
        comp, ia = m["competencia"], m.get("ia")
        lines = m.get("pjc") or []
        ia = ia or {}
        ia_liq = num(ia.get("valor"))
        br_ia = ia.get("valor_bruto")
        br_ia = num(br_ia) if br_ia is not None else ia_liq + num(ia.get("compensado"))
        p_ia = num(ia.get("compensado"))
        pj_liq = sum(num(l.get("valor")) for l in lines)
        br_pj = sum(num(l.get("valor_bruto")) if l.get("valor_bruto") is not None else num(l.get("valor")) + num(l.get("pago")) for l in lines)
        p_pj = sum(num(l.get("pago")) for l in lines)
        ia_tot += ia_liq; pj_tot += pj_liq
        sem_ia = not m.get("ia") or (br_ia == 0 and p_ia == 0 and num(ia.get("base")) == 0 and ia_liq == 0)
        if not lines or sem_ia:
            if not lines and (ia_liq or p_ia):
                meses["ia_a_mais"].append(comp)
            if sem_ia and lines and (pj_liq or p_pj):
                meses["pjc_a_mais"].append(comp)
            acc["periodo"] += pj_liq - ia_liq
            continue
        bruto_ia_tot += br_ia; bruto_pj_tot += br_pj; pago_ia += p_ia; pago_pj += p_pj
        b_ia = num(ia.get("base"))
        cal = m.get("cal_p8") or {}
        fer_ia = num(cal.get("ferias")) + num(cal.get("afast"))  # dias de férias/afastamento no calendário da IA
        fer_pj = num(m.get("ferias_pjc"))
        si, sp = s_ia.get(comp), s_pj.get(comp)
        f_s = sp / si if si and sp else 1.0
        if si and b_ia:
            sinais["k_ia"].append(b_ia / si)

        if eh_hora:
            h_ia = num(ia.get("horas"))
            h_pj = sum(num(l.get("horas")) for l in lines)
            if h_pj <= 0:
                h_pj = h_ia  # PJC sem horas na linha: não dá para separar quantidade
            b_pj = sum(num(l.get("horas")) * num(l.get("base")) for l in lines) / h_pj if h_pj and any(num(l.get("horas")) for l in lines) else (num(lines[0].get("base")) or b_ia)
            mem = parse_memoria(ia.get("memoria"))
            d_ia = mem[1] if mem else None
            m_ia = mem[2] if mem else None
            # divisor e multiplicador do PJC, ponderados pelas horas
            ds, ms, ws = [], [], []
            for l in lines:
                h, b, pc, br = num(l.get("horas")), num(l.get("base")), l.get("perc"), num(l.get("valor_bruto"))
                if h > 0 and b > 0 and isinstance(pc, (int, float)) and br > 0:
                    ds.append(b * pc / 100 * h / br); ms.append(pc / 100); ws.append(h * b)
            d_pj = sum(d * w for d, w in zip(ds, ws)) / sum(ws) if ws else None
            m_pj = sum(x * w for x, w in zip(ms, ws)) / sum(ws) if ws else None
            if m_ia: sinais["m_ia"].append(m_ia)
            if m_pj: sinais["m_pj"].append(m_pj)
            if d_ia: sinais["d_ia"].append(d_ia)
            if d_pj: sinais["d_pj"].append(d_pj)
            if sp and b_pj:
                sinais["k_pj"].append(b_pj / sp)
            if h_ia > 0 and br_ia > 0:
                r_ia = br_ia / h_ia
            elif taxa_mediana and b_ia:
                r_ia = taxa_mediana * b_ia
            elif d_pj and m_pj and b_ia:
                r_ia = b_ia / d_pj * m_pj  # IA sem taxa conhecida: assume o mesmo multiplicador
            else:
                r_ia = br_pj / h_pj if h_pj else 0
            v0 = br_ia
            v1 = h_pj * r_ia
            v2 = v1 * f_s
            v3 = v1 * (b_pj / b_ia) if b_ia else v2
            v3d = v3 * (d_ia / d_pj) if d_ia and d_pj and abs(d_ia / d_pj - 1) > 0.005 else v3
            v4 = br_pj
            acc["quantidade"] += v1 - v0
            acc["salario"] += v2 - v1
            acc["composicao"] += v3 - v2
            acc["divisor"] += v3d - v3
            acc["multiplicador"] += v4 - v3d
            regs.append(dict(comp=comp, fer_ia=fer_ia, fer_pj=fer_pj, drv_ia=h_ia, drv_pj=h_pj, dq=v1 - v0))
        else:
            # verba mensal percentual ou fixa: bruto = fração do mês × base × percentual
            b_pj = sum(num(l.get("base")) for l in lines) if len(lines) > 1 else num(lines[0].get("base"))
            pcs = [l.get("perc") for l in lines if isinstance(l.get("perc"), (int, float))]
            m_pj = (pcs[0] / 100) if pcs else (br_pj / b_pj if b_pj else None)
            pc_ia = ia.get("perc")
            m_ia = pc_ia / 100 if isinstance(pc_ia, (int, float)) and pc_ia else (br_ia / b_ia if b_ia else None)
            if m_ia: sinais["m_ia"].append(m_ia)
            if m_pj: sinais["m_pj"].append(m_pj)
            if sp and b_pj:
                sinais["k_pj"].append(b_pj / sp)
            q_ia = br_ia / (b_ia * m_ia) if b_ia and m_ia else 1.0
            sinais["_lin"].append((comp, b_pj, sp, q_ia))
            v0 = br_ia
            # a fração do PJC é resolvida depois de conhecer a base "cheia" típica
            sinais["_mes"].append(dict(v0=v0, b_ia=b_ia, m_ia=m_ia or 0, f_s=f_s, b_pj=b_pj, sp=sp, v4=br_pj,
                                       comp=comp, fer_ia=fer_ia, fer_pj=fer_pj, q_ia=q_ia))
        acc["pago"] += (pj_liq - br_pj) - (ia_liq - br_ia)

    if not eh_hora and sinais.get("_mes"):
        # base cheia do PJC = salário × k típico; meses abaixo disso são proporcionais
        ks = [x["b_pj"] / x["sp"] for x in sinais["_mes"] if x["sp"] and x["b_pj"]]
        k = mediana(ks)
        estavel = k and sum(1 for x in ks if abs(x / k - 1) < 0.01) >= 0.6 * len(ks)
        for x in sinais["_mes"]:
            if estavel and x["sp"]:
                full = x["sp"] * k
                q_pj = min(x["b_pj"] / full, 1.0) if full else 1.0
            else:
                full, q_pj = x["b_pj"], 1.0
            v1 = q_pj * x["b_ia"] * x["m_ia"] if x["m_ia"] else x["v0"] * q_pj
            v2 = v1 * x["f_s"]
            v3 = q_pj * full * x["m_ia"] if x["m_ia"] else v2 * (full / x["b_ia"] if x["b_ia"] else 1)
            acc["quantidade"] += v1 - x["v0"]
            acc["salario"] += v2 - v1
            acc["composicao"] += v3 - v2
            acc["multiplicador"] += x["v4"] - v3
            regs.append(dict(comp=x["comp"], fer_ia=x["fer_ia"], fer_pj=x["fer_pj"], drv_ia=x["q_ia"], drv_pj=q_pj, dq=v1 - x["v0"]))
    sinais.pop("_mes", None); sinais.pop("_lin", None)

    total_ia, total_pj = num(v.get("total_ia")), num(v.get("total_pjc"))
    residuo = (total_pj - total_ia) - sum(acc.values())
    resumo = {k: (round(mediana(x), 4) if x else None) for k, x in sinais.items()}
    return {
        "eh_hora": eh_hora, "passos": acc, "residuo": residuo, "meses": meses, "sinais": resumo,
        "ferias": resumo_ferias(regs),
        "ia_comp": ia_tot, "pjc_comp": pj_tot, "bruto_ia": bruto_ia_tot, "bruto_pjc": bruto_pj_tot,
        "pago_ia": pago_ia, "pago_pjc": pago_pj,
    }


# ----------------------------------------------------------------- checagens de texto
def checa_jornada(c):
    """2.1.1: a descrição da jornada fala de algo que os regimes estruturados não têm?"""
    j = c.get("jornada") or {}
    faltas = set()
    textos, dias = [], set()
    for jo in j.get("jornadas") or []:
        textos += [jo.get("descricao") or "", jo.get("observacoes") or ""]
        for r in jo.get("regimes") or []:
            pad = r.get("padrao") or {}
            dias |= {norm(d) for d in pad.get("dias_semana") or []}
            if r.get("tipo") and "fixo" not in norm(r.get("tipo")).lower() and "FIXO" not in norm(r.get("tipo")):
                dias.add("_ESCALA")
    for g in j.get("p4_global") or []:
        textos.append(g.get("descricao") or "")
    t = norm(" ".join(textos))
    if not t:
        return []
    if "_ESCALA" in dias:
        return []
    if "SABADO" in t and "SABADO" not in dias:
        faltas.add("sabado")
    if "DOMINGO" in t and "DOMINGO" not in dias:
        faltas.add("domingo")
    if re.search(r"ACIONAMENT|PLANTA|CHAMAD|CONVOCA", t):
        faltas.add("acionamentos")
    return sorted(faltas)


def checa_salario(s_ia, s_pj):
    comuns = sorted(set(s_ia) & set(s_pj))
    if len(comuns) < 3:
        return None
    ia_vals = {round(s_ia[k], 2) for k in comuns}
    pj_vals = {round(s_pj[k], 2) for k in comuns}
    difs = sum(1 for k in comuns if abs(s_ia[k] / s_pj[k] - 1) > 0.02)
    if len(ia_vals) == 1 and len(pj_vals) >= 2 and len(comuns) >= 6:
        return "p7_salario_constante"
    if difs >= 3:
        return "p7_salario_diverge"
    return None


def componentes_p9a(v):
    est = ((v.get("p9a_raw") or {}).get("estrategia_base_calculo") or {})
    comps = [norm(x) for x in est.get("componentes_explicitos") or []]
    return [x for x in comps if x not in ("SALARIO_BASE", "SALARIO BASE")], est.get("tipo")


# ----------------------------------------------------------------- um caso
def analisa_caso(cnj, c):
    s_ia, s_pj = series_salario(c)
    verbas = c["verbas"]
    achados, refl = [], defaultdict(lambda: {"R_ia": 0.0, "R_pj": 0.0, "B_ia": 0.0, "B_pj": 0.0, "nomes": []})
    pontes = {}
    jornada_faltas = checa_jornada(c)
    pat_sal = checa_salario(s_ia, s_pj)
    # meses com holerite nos autos = meses em que o P7 leu alguma rubrica
    meses_holerite = {l["competencia"] for l in (c.get("historico_p7") or {}).get("linhas") or []
                      if any(isinstance(x, (int, float)) and x for x in (l.get("valores") or []))}

    def add(no, padrao, etapa, rs, verba=None, evidencia="", **extra):
        achados.append({"no": no, "padrao": padrao, "etapa": etapa, "rs": round(rs, 2) if rs is not None else None,
                        "verba": verba, "evidencia": evidencia, **extra})

    principais_coinc = [v for v in verbas if v["status"] == "coincide" and not eh_reflexo(nome_de(v)) and not eh_nao_verba(nome_de(v))]
    fam_coinc = {familia(nome_de(v)) for v in principais_coinc}

    # verbas sem par: classifica antes, para achar pares suspeitos
    so_ia = [v for v in verbas if v["status"] == "so_ia"]
    so_pj = [v for v in verbas if v["status"] == "so_pjc"]
    fam_so_pj = defaultdict(list)
    for v in so_pj:
        if not eh_reflexo(nome_de(v)) and not eh_nao_verba(nome_de(v)):
            fam_so_pj[familia(nome_de(v))].append(v)

    # 0.1: gabarito sem verba legível — nada abaixo disso é comparável
    if c.get("extracao_confiavel") is False:
        ia_t = sum(num(v.get("total_ia")) for v in verbas); pj_t = sum(num(v.get("total_pjc")) for v in verbas)
        add("0.1", "pjc_extracao_nao_confiavel", "extrator", pj_t - ia_t, None,
            "; ".join((c.get("diag_extracao") or {}).get("motivos_extracao") or []) or "extracao_confiavel = false")
        verbas = []

    for v in verbas:
        nm, st = nome_de(v), v["status"]
        ia, pj = num(v.get("total_ia")), num(v.get("total_pjc"))
        cod = v.get("codigo")
        rot = cod or nm
        if st == "so_pjc" and eh_subtotal(nm):
            add("0.1", "pjc_linha_de_subtotal", "extrator", pj, rot, f"'{nm}' é linha de resumo do demonstrativo, não verba")
            continue
        if eh_nao_verba(nm):
            if ia or pj:
                add("4.2", "nao_verba_no_total", "painel/P10", pj - ia, rot, f"{nm}: IA {ia:,.2f} × PJC {pj:,.2f}")
            continue
        if eh_reflexo(nm):
            f = familia(nm)
            refl[f]["R_ia"] += ia; refl[f]["R_pj"] += pj; refl[f]["nomes"].append(nm)
            continue
        f = familia(nm)
        if st == "so_ia":
            par = fam_so_pj.get(f)
            if par and f != "?":
                add("0.2", "pareamento_suspeito", "painel", pj - ia, rot,
                    f"'{nm}' só na IA e '{nome_de(par[0])}' só no PJC: mesma família ({f})")
            elif ia and f == "HE" and "HE" in fam_coinc:
                add("2.5.4", "he_sobreposta", "P4", -ia, rot,
                    f"{nm} ({tipo_he(nm, cod)}): só na IA, e a IA já tem outra hora extra pareada — as mesmas horas em duas verbas",
                    tipo_he=tipo_he(nm, cod))
            elif ia and f in fam_coinc and f != "?":
                add("1.2", "verba_so_ia_familia_ja_pareada", "P4", -ia, rot,
                    f"{nm}: só na IA, mas outra verba da família {f} já está pareada — a IA desdobrou ou duplicou")
            elif ia:
                padrao = "verba_so_ia_indenizatoria" if eh_indenizatoria(nm) else "verba_so_ia"
                add("1.2", padrao, "P4", -ia, rot, f"{nm}: IA {ia:,.2f}, PJC não tem")
            refl[f]["B_ia"] += ia
            continue
        if st == "so_pjc":
            if any(nome_de(x) and familia(nome_de(x)) == f for x in so_ia) and f != "?":
                add("0.2", "pareamento_suspeito", "painel", pj, rot, f"'{nm}' só no PJC; há verba só IA da mesma família ({f})")
            elif f in fam_coinc and f != "?":
                add("1.2", "pedaco_de_verba_deferida_so_pjc", "P9a", pj, rot,
                    f"'{nm}' só no PJC, mas a IA tem verba da mesma família ({f}) — costuma ser parte da jornada (ex.: domingos) ou outro adicional")
            elif pj:
                padrao = "verba_so_pjc_indenizatoria" if eh_indenizatoria(nm) else "verba_so_pjc"
                add("1.2", padrao, "P4", pj, rot, f"{nm}: PJC {pj:,.2f}, IA não deferiu")
            refl[f]["B_pj"] += pj
            continue
        if st == "nao_calc":
            if pj or ia:
                add("1.2", "deferida_nao_calculada", "P9a", pj - ia, rot, f"{nm}: deferida e declarada não calculável; PJC {pj:,.2f}")
            refl[f]["B_pj"] += pj
            continue

        # coincide: ponte mês a mês
        if not v.get("competencias"):
            if abs(pj - ia) >= MIN_RS:
                add("2", "conta_sem_detalhe_mensal", "P9b/P10b", pj - ia, rot, f"{nm}: IA {ia:,.2f} × PJC {pj:,.2f}, sem competências para decompor")
            refl[f]["B_ia"] += ia; refl[f]["B_pj"] += pj
            continue
        p = ponte_verba(v, s_ia, s_pj)
        pontes[rot] = {"nome": nm, "familia": f, "ia": round(ia, 2), "pjc": round(pj, 2), "por_hora": p["eh_hora"],
                       **{k: round(x, 2) for k, x in p["passos"].items()}, "residuo": round(p["residuo"], 2), "sinais": p["sinais"],
                       "ferias": p["ferias"]}
        refl[f]["B_ia"] += p["bruto_ia"]; refl[f]["B_pj"] += p["bruto_pjc"]
        a, sg = p["passos"], p["sinais"]

        p9a = v.get("p9a_raw") or {}
        pjor = p9a.get("parametros_jornada") or {}
        tint = p9a.get("tratamento_intervalo") or {}
        est = p9a.get("estrategia_base_calculo") or {}
        # 1.1 período
        if abs(a["periodo"]) >= MIN_RS:
            ma, mp = p["meses"]["ia_a_mais"], p["meses"]["pjc_a_mais"]
            sem_doc = [k for k in ma if k not in s_pj]
            p9b_total = (v.get("p9b_raw") or {}).get("_total_competencias")
            sem_holerite = [k for k in ma if k not in meses_holerite]
            if mp and len(mp) > len(ma):
                # a competência existe na IA, mas sem apuração: o P9b não chegou nela
                padrao, etapa, no_p = "ia_competencias_sem_apuracao", "P9b", "1.1.2"
            elif ma and len(sem_holerite) == len(ma):
                # regra: o cálculo se restringe ao período com holerite nos autos
                padrao, etapa, no_p = "periodo_sem_holerite_nos_autos", "P9b", "1.1.1"
            else:
                padrao, etapa, no_p = "periodo_ia_a_mais", "P4/P9a/política", "1.1.3"
            ev = (f"IA calculou {len(ma)} meses que o PJC não tem ({ma[0] if ma else ''}–{ma[-1] if ma else ''}); "
                  f"PJC tem {len(mp)} que a IA não apurou ({mp[0] if mp else ''}–{mp[-1] if mp else ''}); P9b gerou {p9b_total} competências")
            add(no_p, padrao, etapa, a["periodo"], rot, ev,
                pjc_sem_holerite_nos_meses=bool(ma) and len(sem_doc) == len(ma))
        # 2.5.1 tipo de hora extra (sem R$ próprio: o R$ da verba já está nos outros nós)
        th = None
        if f == "HE" or cod in COD_HE:
            th = tipo_he(v.get("nome_ia"), cod)
            tp = tipo_he(v.get("nome_pjc"))
            pontes[rot]["tipo_he"] = {"ia": th, "pjc": tp}
            if th != tp and "nao_especificado" not in (th, tp):
                add("2.5.1", "tipo_he_diverge", "P4", None, rot,
                    f"IA '{v.get('nome_ia')}' ({th}) × PJC '{v.get('nome_pjc')}' ({tp})", rs_verba=round(pj - ia, 2), tipo_he=th)
        # 2.1.2 férias: a parte da quantidade que está nos meses de férias/afastamento
        fer = p["ferias"]
        q_fer = fer["rs_quantidade_em_meses_de_ferias"] if (fer["meses_ferias_ia"] or fer["meses_ferias_pjc"] or fer["meses_calendario_divergente"]) else 0.0
        q_rest = a["quantidade"] - q_fer
        if abs(q_fer) >= MIN_RS:
            if fer["proporcionaliza_pjc"] and fer["proporcionaliza_ia"] is False:
                padrao, etapa = "ferias_nao_proporcionalizada_pela_ia", "P9b"
            elif fer["meses_trocados"]:
                padrao, etapa = "ferias_em_meses_diferentes", "P8"
            # contagem de dias diferente NÃO é padrão: o P8 conta férias em dia útil
            # (dias_ferias_em_dia_util) de propósito, o PJC em dia corrido
            elif fer["proporcionaliza_pjc"] and fer["proporcionaliza_ia"] is False:
                padrao, etapa = "ferias_nao_proporcionalizada_pela_ia", "P9b"
            elif fer["proporcionaliza_ia"] and fer["proporcionaliza_pjc"] is False:
                padrao, etapa = "ferias_proporcionalizada_so_pela_ia", "P9b"
            else:
                padrao, etapa = "ferias_quantidade_diverge", "P8/P9b"
            add("2.1.2", padrao, etapa, q_fer, rot,
                f"{nm}: meses de férias IA {fer['meses_ferias_ia']} × PJC {fer['meses_ferias_pjc']}; proporcionaliza IA {fer['proporcionaliza_ia']} × PJC {fer['proporcionaliza_pjc']}; "
                f"meses trocados {fer['meses_trocados']}; dias (mês, IA, PJC) {fer['exemplos_contagem']}",
                tipo_he=th)
        # 2.1 quantidade (fora dos meses de férias)
        if abs(q_rest) >= MIN_RS:
            lim = pjor.get("limite_diario_resolvido")
            teto = pjor.get("teto_excedente_diario_horas")
            s_, c_, g_ = tint.get("tempo_suprimido_minutos"), tint.get("intervalo_contratual_minutos"), tint.get("intervalo_gozado_fixado_decisao_minutos")
            hdia = mediana([num((m.get("ia") or {}).get("horas")) / num((m.get("cal_p8") or {}).get("dias"))
                            for m in v["competencias"] if num((m.get("cal_p8") or {}).get("dias")) > 0 and num((m.get("ia") or {}).get("horas")) > 0])
            if not p["eh_hora"]:
                padrao, no, etapa = ("verba_mensal_fracao_ia_maior" if q_rest < 0 else "verba_mensal_fracao_ia_menor"), "2.1.3", "P9b"
            elif th == "7a_8a" and lim and abs(lim - 6) > 0.01:
                padrao, no, etapa = "he_7a8a_limite_diferente_de_6h", "2.5.2", "P9a"
            elif th == "7a_8a" and hdia and hdia > 2.05 and q_rest < 0:
                padrao, no, etapa = "he_7a8a_sem_teto_2h", "2.5.2", "P9a/P9b"
            elif th == "alem_8a" and lim and abs(lim - 44 / 6) < 0.01 and q_rest < 0:
                padrao, no, etapa = "limite_diario_derivado_7h20", "2.5.3", "P9a"
            elif th == "alem_8a" and lim and lim < 7.9 and q_rest < 0:
                padrao, no, etapa = "he_alem8a_limite_abaixo_de_8h", "2.5.3", "P9a"
            elif cod == "BT007" and s_ and c_ and g_ and s_ == c_ and q_rest < 0:
                padrao, no, etapa = "intrajornada_paga_integral", "2.1.3", "P9a"
            elif cod in COD_JORNADA and jornada_faltas:
                padrao, no, etapa = "jornada_descricao_nao_estruturada", "2.1.1", "P9a"
            else:
                padrao, no, etapa = ("horas_ia_a_menos" if q_rest > 0 else "horas_ia_a_mais"), "2.1", "P9a/P9b"
            add(no, padrao, etapa, q_rest, rot,
                f"{nm}: quantidade IA × PJC fora das férias; limite diário {lim}; teto {teto}; h/dia IA {round(hdia, 2) if hdia else None}; intervalo suprimido {s_} de {c_} (gozado {g_})",
                faltam_na_jornada=jornada_faltas or None, tipo_he=th)
        # 2.2.1 salário
        if abs(a["salario"]) >= MIN_RS:
            add("2.2.1", pat_sal or "salario_diverge", "P7", a["salario"], rot, f"{nm}: salário P7 × histórico PJC")
        # 2.2.2 composição
        if abs(a["composicao"]) >= MIN_RS:
            extras, tipo = componentes_p9a(v)
            k_ia, k_pj = sg.get("k_ia"), sg.get("k_pj")
            if extras and k_ia and abs(k_ia - 1) < 0.02 and a["composicao"] > 0:
                padrao, etapa = "p9b_ignora_componente_deferido_na_base", "P9b"
            elif tipo == "salario_minimo_nacional":
                padrao, etapa = "base_salario_minimo_diverge", "P9a/P9b"
            elif a["composicao"] < 0 and est.get("expandir_com_integra_salario"):
                padrao, etapa = "base_expandida_com_rubricas_do_holerite", "P9a/P9b"
            elif a["composicao"] > 0:
                padrao, etapa = "base_ia_menor", "P9a/P9b"
            else:
                padrao, etapa = "base_ia_maior", "P9a/P9b"
            add("2.2.2", padrao, etapa, a["composicao"], rot,
                f"{nm}: base/salário IA {k_ia} × PJC {k_pj}; P9a pediu {extras or 'só salário'} ({tipo})")
        # 2.3.3 divisor
        if abs(a["divisor"]) >= MIN_RS:
            no, padrao = ("2.5.2", "he_7a8a_divisor_diverge") if th == "7a_8a" else ("2.3.3", "divisor_diverge")
            add(no, padrao, "P9a", a["divisor"], rot, f"{nm}: divisor IA {sg.get('d_ia')} × PJC {sg.get('d_pj')}", tipo_he=th)
        # 2.3.1 / 2.3.2 multiplicador
        if abs(a["multiplicador"]) >= MIN_RS:
            m_ia, m_pj = sg.get("m_ia"), sg.get("m_pj")
            if cod == "BT037" and m_ia and m_pj and m_ia >= 1 and m_pj < 1:
                padrao, no, etapa = "adicional_noturno_hora_cheia", "2.3.2", "P9b"
            elif cod == "BT002" and m_ia and m_pj and abs(m_pj - 1 / 3) < 0.02 and abs(m_ia - 1) < 0.02:
                padrao, no, etapa = "sobreaviso_sem_fracao_1_3", "2.3.2", "P9a→P9b"
            elif cod in COD_HE and m_ia and m_pj and m_ia >= 1 and m_pj < 1:
                padrao, no, etapa = "pjc_paga_so_adicional", "2.3.2", "P9a"
            elif m_ia and m_pj and abs(m_ia - m_pj) < 0.01:
                # mesmo multiplicador mediano: o valor vem de mistura de linhas do PJC ou aproximação da ponte
                padrao, no, etapa = "multiplicador_residual", "2.3", "método"
            elif p["eh_hora"] and m_ia and m_pj:
                padrao, no, etapa = ("adicional_ia_menor" if m_pj > m_ia else "adicional_ia_maior"), "2.3.1", "P9a"
            elif not p["eh_hora"] and m_ia and m_pj and abs(m_ia - m_pj) > 0.005:
                padrao, no, etapa = "percentual_diverge", "2.3.1", "P9a"
            else:
                padrao, no, etapa = "multiplicador_diverge", "2.3", "P9a/P9b"
            add(no, padrao, etapa, a["multiplicador"], rot, f"{nm}: multiplicador IA {m_ia} × PJC {m_pj}")
        # 2.4 pago
        if abs(a["pago"]) >= MIN_RS and th == "7a_8a":
            # 7ª e 8ª do bancário: o abatimento costuma ser a gratificação de função (S.109 / cláusula da CCT)
            s109 = ((p9a.get("flags_sumulas") or {}).get("aplica_s109"))
            add("2.5.2", "he_7a8a_compensacao_gratificacao_diverge", "P9a/P9b", a["pago"], rot,
                f"{nm}: abatido IA {p['pago_ia']:,.2f} × PJC {p['pago_pjc']:,.2f}; P9a aplica_s109={s109}", tipo_he=th)
        elif abs(a["pago"]) >= MIN_RS:
            if p["pago_pjc"] > MIN_RS and p["pago_ia"] < MIN_RS:
                padrao = "pago_pjc_nao_abatido_pela_ia"
            elif p["pago_ia"] > MIN_RS and p["pago_pjc"] < MIN_RS:
                padrao = "ia_abate_o_que_pjc_nao_abate"
            else:
                padrao = "abatimento_diverge"
            add("2.4", padrao, "P7/P9b", a["pago"], rot, f"{nm}: pago IA {p['pago_ia']:,.2f} × PJC {p['pago_pjc']:,.2f}")
        if abs(p["residuo"]) >= MIN_RS:
            add("2", "residuo_conciliacao", "painel", p["residuo"], rot, f"{nm}: total do painel ≠ soma das competências")
        # 4.1 potencial
        if ia < 0:
            add("4.1", "saldo_negativo_abate_total", "P10", None, rot, f"{nm}: total IA {ia:,.2f} entra negativo na soma",
                rs_potencial=round(-ia, 2))

    # 3 reflexos por família: herdado = razão IA × variação da base devida
    for f, r in refl.items():
        dR = r["R_pj"] - r["R_ia"]
        if abs(dR) < MIN_RS:
            continue
        her = (r["R_ia"] / r["B_ia"]) * (r["B_pj"] - r["B_ia"]) if r["B_ia"] else 0.0
        regra = dR - her
        razao = lambda R, B: round(R / B, 3) if B else None
        if abs(her) >= MIN_RS:
            add("3.1", "reflexo_herda_erro_principal", "herdado", her, f, f"família {f}: principal devida IA {r['B_ia']:,.2f} × PJC {r['B_pj']:,.2f}")
        if abs(regra) >= MIN_RS:
            padrao = "reflexo_sem_principal_na_ia" if not r["B_ia"] else "reflexo_regra_diverge"
            add("3.2", padrao, "P10", regra, f,
                f"família {f}: reflexo/principal IA {razao(r['R_ia'], r['B_ia'])} × PJC {razao(r['R_pj'], r['B_pj'])}",
                reflexos=sorted(set(r["nomes"]))[:12])

    # qualitativos de caso, sem R$
    if jornada_faltas and not any(a["padrao"] == "jornada_descricao_nao_estruturada" for a in achados):
        add("2.1.1", "jornada_descricao_nao_estruturada", "P9a", None, None,
            f"descrição da jornada cita {jornada_faltas} sem regime correspondente")
    if (c.get("jornada") or {}).get("cartao_nao_usado"):
        add("2.1.3", "cartao_deferido_nao_usado", "P9b", None, None, "decisão manda apurar por cartão e a memória não tem batidas")

    total_ia = sum(num(v.get("total_ia")) for v in c["verbas"])
    total_pj = sum(num(v.get("total_pjc")) for v in c["verbas"])
    gap = total_pj - total_ia
    soma = sum(a["rs"] for a in achados if isinstance(a["rs"], (int, float)))

    nos = defaultdict(lambda: {"rs": 0.0, "padroes": Counter()})
    for a in achados:
        n = nos[a["no"]]
        n["rs"] += a["rs"] or 0
        n["padroes"][a["padrao"]] += 1
    return {
        "schema": "arvore_divergencia/v1",
        "processo": cnj,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "rodada": {"data_processamento": c.get("data_processamento"), "versoes": c.get("versoes"), "safra": c.get("safra")},
        "caso": {"apto": c.get("apto"), "categoria_inaptidao": c.get("categoria_inaptidao"), "tipo_calculo": c.get("tipo_calculo"),
                 "extracao_confiavel": c.get("extracao_confiavel"), "tipo_jornada": (c.get("jornada") or {}).get("tipo_decisao")},
        "ancora": {"camada": "nominal (sem correção e juros)", "total_ia": round(total_ia, 2), "total_pjc": round(total_pj, 2), "gap": round(gap, 2),
                   "painel_total_ia": (c.get("quadro") or {}).get("total_ia"), "painel_total_pjc": (c.get("quadro") or {}).get("total_pjc")},
        "conferencia": {"soma_achados": round(soma, 2), "nao_explicado": round(gap - soma, 2),
                        "obs": f"achados abaixo de R$ {MIN_RS:.0f} por verba e nó ficam em nao_explicado"},
        "nos": {k: {"rs": round(n["rs"], 2), "padroes": dict(n["padroes"])} for k, n in sorted(nos.items())},
        "achados": achados,
        "ponte_por_verba": pontes,
        "reflexos_por_familia": {f: {k: (round(x, 2) if isinstance(x, float) else x) for k, x in r.items() if k != "nomes"} for f, r in refl.items()},
    }


# ----------------------------------------------------------------- resumo de padrões
def resumo_padroes(saidas):
    por = defaultdict(lambda: {"casos": set(), "rs": 0.0, "rs_abs": 0.0, "rs_potencial": 0.0, "n": 0, "no": None, "etapa": Counter(), "verbas": Counter()})
    nos = defaultdict(lambda: {"casos": set(), "rs": 0.0, "rs_abs": 0.0})
    gap_abs = sum(abs(o["ancora"]["gap"]) for o in saidas)
    for o in saidas:
        for a in o["achados"]:
            p = por[a["padrao"]]
            p["casos"].add(o["processo"]); p["n"] += 1; p["no"] = a["no"]
            p["rs"] += a["rs"] or 0; p["rs_abs"] += abs(a["rs"] or 0); p["rs_potencial"] += a.get("rs_potencial") or 0
            p["etapa"][a["etapa"]] += 1
            if a.get("verba"): p["verbas"][a["verba"]] += 1
            n = nos[a["no"]]
            n["casos"].add(o["processo"]); n["rs"] += a["rs"] or 0; n["rs_abs"] += abs(a["rs"] or 0)
    linhas = sorted(({"padrao": k, "no": v["no"], "casos": len(v["casos"]), "ocorrencias": v["n"], "rs": round(v["rs"], 2),
                      "rs_abs": round(v["rs_abs"], 2), "rs_potencial": round(v["rs_potencial"], 2),
                      "etapa": v["etapa"].most_common(1)[0][0], "verbas_top": v["verbas"].most_common(6),
                      "exemplos": sorted(v["casos"])[:5]} for k, v in por.items()), key=lambda x: -x["rs_abs"])
    return {
        "casos": len(saidas), "gap_abs_total": round(gap_abs, 2),
        "padroes": linhas,
        "nos": {k: {"casos": len(v["casos"]), "rs": round(v["rs"], 2), "rs_abs": round(v["rs_abs"], 2)} for k, v in sorted(nos.items())},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="data_processamento da rodada (AAAA-MM-DD) ou intervalo AAAA-MM-DD..AAAA-MM-DD")
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = ap.parse_args()
    d = json.loads(JSON_PAINEL.read_text(encoding="utf-8"))
    ini, _, fim = args.data.partition("..")
    fim = fim or ini
    casos = {k: v for k, v in d["casos"].items()
             if ini <= (v.get("data_processamento") or "") <= fim and not v.get("sem_pjc")}
    if not casos:
        sys.exit(f"nenhum caso com PJC processado em {args.data}")
    pasta = args.saida / args.data.replace("..", "_a_")
    (pasta / "casos").mkdir(parents=True, exist_ok=True)
    saidas, erros = [], []
    for cnj, c in sorted(casos.items()):
        try:
            o = analisa_caso(cnj, c)
        except Exception as e:  # um caso estranho não derruba a varredura
            erros.append((cnj, repr(e)))
            continue
        (pasta / "casos" / f"{cnj}.json").write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
        saidas.append(o)
    r = resumo_padroes(saidas)
    r["erros"] = erros
    (pasta / "padroes.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(saidas)} casos em {pasta}  ({len(erros)} com erro)")
    for cnj, e in erros[:10]:
        print("  ERRO", cnj, e)
    print(f"\n{'padrão':48} {'nó':6} {'casos':>5} {'R$ líquido':>14} {'R$ |abs|':>14}")
    for l in r["padroes"][:40]:
        print(f"{l['padrao'][:48]:48} {l['no']:6} {l['casos']:5} {l['rs']:14,.0f} {l['rs_abs']:14,.0f}")


if __name__ == "__main__":
    main()
