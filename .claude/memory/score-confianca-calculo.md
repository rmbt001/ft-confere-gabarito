---
name: score-confianca-calculo
description: "Score de confiança do cálculo FT (14/10/2026) — componentes escolhidos pela Raíra, o que foi descartado e por quê, onde vive no app"
metadata:
  node_type: memory
  type: project
  originSessionId: 8c35cfc5-1235-4a09-9388-f249c033065c
  modified: 2026-10-28T00:24:54.743Z
---

Em 14/10/2026 a Raíra pediu um score de confiabilidade do cálculo (o chefe indicou o post do Jev/TypeSafe; a ideia
aproveitada foi só a de confiança **calibrada** contra o gabarito, não o modelo). Escopo: **só casos aptos**.

Componentes que ELA escolheu: travas = verba sem código no glossário ("Não encontrado"), reflexo acima do teto (13º>1/12,
férias>1/9), HE duplicada; riscos = gratificação de função, comissões, Súmula 340, cobertura salarial. **Total negativo
fica de fora** ("é erro, vamos corrigir"). "Não calculável" já é inaptidão, não entra.

Holerite foi redefinido para "competências com base zero": no 0020064 o P7 leu holerite em 6/40 meses e a acurácia foi
87% (salário veio de outro doc). Com "sem base" o sinal aparece (≥50% sem base → 71% subcálculo).

Implementado em `app_validacao_Calculos/codigo/src/confianca.py` (só lado LIFT), campo `confianca` no JSON, selo no
Resumo, coluna/filtro na Lista, seção no Placar (② média com piso −100% por faixa). `ferramentas/aplica_confianca.py`
reaplica sem reprocessar. Correções de 14/10 depois do 0001460 (falso "baixa"): honorários/custas/perícia fora pelo nome;
gratificação/comissão só se entram na base/verba (não pelo histórico do P7); "sem salário" só conta mês que o LIFT
calculou. Depois, a pedido dela, entrou "ficha de registro sem férias" (P1 `datas_ferias_concedidas` vazio, 12+ meses;
campo `ferias_p1` no JSON) com peso +1 (o +2 sujava a faixa baixa) e só com verba de jornada (0017053, valor fixo
mensal, caía à toa). "Sem salário" ignora verba de valor fixo/salário mínimo; zeros no fim do período CONTAM (testado:
ignorá-los piora a alta); aceita base fixa/variável (comissionista, 0000081) e ignora mês sem dia trabalhado. Regra nova
"afastamento longo" (6+ meses com 0 dia e afastamento no P8, +1): 8 aptos, 0% na meta, 75% sobrecálculo. Casos bons
inaptos só por BT062 (honorários do advogado da reclamada): 0020064, 0000081 — proposta de rever a aptidão. Rodada ≥07/10 (48 aptos do Placar): alta 25 · mediana ② 88% · 68% na meta; média 14 · 63% · 21%;
baixa 9 · 13% · 11%; 89% do sobrecálculo fica fora da alta. Artefato: claude.ai/code/artifact/5f27eb0a-ee43-44df-bfb8-9278eb1f192a. Achado lateral: os 4 casos "Não encontrado" eram aptos
(furo da regra de aptidão, ~R$ 1,5 mi de sobrecálculo).

**Medir sempre na HOMOL, não na produção** (a Raíra, 14/10: "prod tá atrasado"; usar prompts e casos de homol para as
causas). O score está também no app `app_validacao_Calculos_homol` (cópia de confianca.py + aplica_confianca.py; o app usa
o Python do app de prod). Alavancas novas saem de cruzar a árvore/dossiês da homol (`_consolidado_1410.json`) com a faixa:
entrou verba de representação (+1); saiu a trava "reflexo acima do teto" (PJC também passa). Insalubridade+periculosidade
separava, mas a Raíra disse que a correção "ainda vai entrar" (prompt) → fora do score, como o total negativo: **erro que
vai ser corrigido não vira regra do score**.
7h20 multi-regime e adicional na base do intervalo não separam (são ajuste de prompt). Homol 52 aptos: alta 23 · 74% na
meta · 17% sobrecálculo; 91% do sobrecálculo fora da alta.

**Revisão de 15/10 (novos casos, BT062 fora dos inelegíveis):** regras iguais nos dois apps (commit 8052792 tem o score).
Homol 88 aptos <200k: alta 38 · média ② 78% · mediana 94% · 76% na meta · 18% sobrecálculo; média 24 · 33% na meta ·
62% sobre; baixa 26 · 8% · 46%; 88% do sobrecálculo fora da alta. Prod 14/10+: só 13 aptos com PJC, faixas invertidas
(prod roda prompts antigos, ex. ROTEAMENTO v11) — não usar para calibrar. Escapes da alta lidos nos dossiês do agente:
única alavanca nova = "limitação aos valores da inicial" no critério do P4 (T45; homol 11 casos, mediana 17 × 74, mas
sobrecálculo 27 × 37%). A Raíra confirmou que o T45 NÃO foi corrigido → entrou como risco +1 (`limite_inicial`,
regex no JSON do p4 das verbas), **só no app de homol** (prod segue sem ela; perguntar antes de levar). Homol 88 aptos com
T45: alta 36 · média ② 79% · 78% na meta · 17% sobre; média 25 · 36%; baixa 27 · 7%; 92% do sobrecálculo fora da alta.
**Regra de 15/10 (Raíra): o score só lê dado que as TABELAS da esteira entregam** (código de glossário, marcas do P9a,
base do P10a, calendário do P8, férias do P1) — nada de interpretação da decisão (limitação da inicial, premissa, tema)
nem de adivinhar pelo nome da verba. Por isso o T45 saiu de novo; sem código = `codigo_glossario == "Não encontrado"`;
HE duplicada = código de HE repetido; gratificação = S109 ou BT025; comissão = BT024 / ids do P9a; honorários fora por
código (BT062, BT063, BT079). Feito só na homol. Resultado homol 88 aptos: alta 38 · 76% na meta · 21% sobre; média 22 ·
36%; baixa 28 · 7%; 87% do sobrecálculo fora da alta (antes, com nome + T45: 36 · 78% · 17% · 92%).
**Retreino de 15/10 (pedido dela: "senti que você só me obedeceu"; testar TODOS os parâmetros estruturados):** treino no
painel parcial de prod `Repos/ft_paineis_parciais/desde_2026-10-14` (185 comparáveis, 516 verbas), validação na homol (230).
O score atual NÃO separa na prod parcial (alta 35% / média 26% / baixa 30% na meta) — estava ajustado à homol caso a caso.
Único sinal de processo robusto nas duas bases: **apuração por cartão** (7×35% prod, 21×48% homol). Fracos mas na mesma
direção: jornada 6h/divisor 180, período 61+ meses, ficha sem férias, afastamento 6+, sem código. Base expandida, S264,
meses sem salário, gratificação: fortes só na homol. Proposta "B" (cartão +2, demais +1) generaliza: prod 38/32/12%,
homol 62/36/22%. Nível verba (para prompt, não score): cartão 12×63%, teto excedente 15×57% (46% a mais), base dinâmica
36×73%, 6h 29×62%, BT004 22×57%; escopo a mais: BT070 83%, BT044 60%, BT073 45% só IA. Scripts no scratchpad:
varre_parametros.py, testa_parametros.py, candidatas.py, modelos.py. Nada implementado ainda — aguardando decisão dela.
**Alvo limpo pelos dossiês (15/10, pedido dela; "premissa também é sinal"):** erro atribuível = erro_ia +
premissa_nao_enderecada + documento_nao_lido (dado_ausente testado à parte); fora: gabarito_questionavel, politica,
metodo, indeterminado. Bate = erro atribuível ≤ 20% do PJC. Prod 135 com dossiê: bate 33% bruto → 53% limpo, 44 trocam
de rótulo. Com o alvo limpo, base dinâmica/expandida, S264, HE, 6h/div180, BT004, comissão, 4+ verbas passam a piorar NAS
DUAS bases; IA total > 150% do valor da causa (P1) prevê sobrecálculo. Campos do P1 de contrato/pessoa e texto
estruturado (cargo, causa) quase não ajudam. Modelo M1 (cartão+2, IA>150% causa+2, base dinâmica+1, 6h+1): prod todos
alta/média/baixa 64/57/39% bate, homol 70/44/14%; M3 pega 71–98% do sobrecálculo fora da alta mas inverte alta×média na
prod. Scripts: alvo_limpo.py, modelos_limpo.py (scratchpad). Não implementado — aguardando escolha dela.
**Foco dela = sobrecálculo e uso em PRODUÇÃO (para decidir compra).** Score de risco de pagar a mais (alvo limpo, IA a
mais atribuível >10% do PJC), modelo S4: IA>150% valor da causa +2, sem código +2, código de alto risco (BT077
transferência, BT059 pensão vitalícia, BT053 in natura) +2, cartão +1, 6h/div180 +1, HE paga em 2+ rubricas no P7 +1.
Marcado (1+ pt): prod 28% a mais × 7% resto, captura 69% do R$ a mais; homol 53×26%, 64%. A lista de códigos de alto
risco foi tirada da prod (só a homol valida sem viés, e lá quase não muda). Cartão erra mais PARA MENOS (cobertura
parcial do cartão, DSR sem sábado, ajustes da sentença ignorados); abatimento incompleto de HE paga NÃO é causado pelo
cartão (8% dos sem cartão também). Não implementado — aguardando o sim dela para mexer em prod.
**Versões prod × homol (15/10, ela corrigiu duas vezes):** a NUMERAÇÃO é independente por ambiente, o TEXTO é o que
importa. Prod P9a v11 = homol v19; P9b v7 = v15; P1 v7 = v9; P10a v5 = v8; P10b v2 = v4 (hash do texto normalizado em
ft_arvore_divergencias/prompts × prompts_homol). Logo o painel parcial de prod 14/10+ e os 170 dossiês analises_prod_1510
JÁ SÃO da esteira atual. Nunca concluir "versão antiga" pelo número: comparar o texto. Estes sim são de prompts antigos:
homol noite 09→10 (v17) — ex. 0020906 dano a terceiro (já tratado no INFOS v13), 0010625, 0000264, 0000652. Jev: estudo feito (API typesafe, Noul/Choice/Score, US$0,042/Mtok, inglês primário, sem LGPD/retenção
zero → aprovação Tecnologia/Jurídico); piloto não iniciado.
**Relatório da rodada de prod 14–15/10** (artefato 2d1a2c34-f6fe-4ff6-80e8-484224b761e8, "Rodada LIFT de 15 de outubro"):
25 famílias com CNJs = rótulos por causa na esteira atual. O S4 pega as famílias quase ao acaso (exceto cartão/composição/
restritas). Detectores por família, com campo estruturado (rótulo da família × resto, prod 135): calendário sem férias ←
"ficha sem férias E hora extra" 62×13%; abatimento ← "HE paga em alguma rubrica no P7" 76×36% (NÃO "2+ rubricas", 14×15%);
pensão ← BT059/BT051 50×3%; restritas (F01, premissa 24.0) ← BT077/BT049 57×1%; composição da base ← S264 86×50%.
Ideia em curso: score como conjunto de detectores por família (risco de sobrecálculo por causa).
**PARCIMÔNIA (Raíra, 15/10): "não posso derrubar muito mais do que vou comprar" — a métrica tem que ser assertiva.** Medir
sempre: % barrado, precisão (barrados que de fato calculam a mais) e captura do R$ a mais. Família só serve de gabarito;
em produção só entram tabelas + peças (Jev). Núcleo que barra pouco e acerta: IA>150% do valor da causa + BT077/BT049 +
verba sem código → barra 6–9%, precisão 56–100% (base 17–37%), captura 42–60% do R$ a mais (prod e homol). Detectores
largos (cartão, ficha sem férias+HE, HE paga, pensão) têm precisão baixa: só servem com confirmação na peça, não para barrar.
**Ideia dela (16/10): Jev para identificar PREMISSAS que majoram o cálculo.** Premissas com mais IA a mais (dossiês atuais):
24.0 (R$907k), 3.0 (R$816k), 11.0 (R$491k), 14.0 (R$450k), 5.0, 7.2, 20.0, 18.0. Desenho: gatilho de tabela (código/base)
+ pergunta Noul do Jev no trecho da decisão (p4.contexto) + código aplica a premissa. Precisão do gatilho SOZINHO (prod/homol):
24.0 BT077/049 60%/100%; 3.0 BT035 20%/47%; 14.0 pensão 17%/33%; 3.0/11.0 base 26%/36% (dispara 76 na prod); 18.0 10%/30%.
O papel do Jev é subir essa precisão. 5.0 e 15.0 são de documento, não de leitura (fora do Jev). Robô de peças só baixa
decisão e inicial: trânsito em julgado (24.0) não tem certidão — Jev teria que inferir da fase pelo texto do acórdão.
**Teste Jev (16/10):** pasta `Repos/jev_testes` (uv, typesafe-sdk 0.7.5, chave no .env; README com passo a passo).
54 itens de premissa com peças (só inicial/sentença/acórdão/Decisão=embargos; fora RR, emenda e jurisprudência anexa),
estado = trechos por palavra-chave, anonimizado, ≤ ~25k tokens. 3 casos: Claude 3/3 (Brier 0,011); Jev com perguntas
longas "estilo Claude" 1/3 (leu Súmula 264 explícita como 0,19); com perguntas ATÔMICAS (um fato por Noul) 3/3, mas perto
do corte (0,58 e 0,55; Brier 0,129). Português não foi o problema (PT ≈ EN). Pergunta de ausência ("não manda deduzir")
fica ~0,4 em qualquer redação. Jev: <1 s e ~US$ 0,001 por caso. Sempre escrever pergunta atômica para o Jev.
**54 itens no Jev (só Jev, pedido dela):** geral sem separação (precisão 50% = base 46%), por culpa de 3.0/11.0 (27 itens,
AUC 0,4–0,56: o erro é a esteira expandir a base pelo holerite, a decisão não muda nada → é prompt, sai do Jev) e de fórmula
minha invertida no 18.0 (risco = decisão DIZER natureza salarial pós-Reforma; AUC 0,94). Periculosidade separa (ambos
adicionais AUC 0,82, S264 0,80, inflamável 0,72). Sem 3.0/11.0 e com fórmula corrigida: 27 itens, precisão 70–75% (base 44%),
92% do R$ — mas fórmula ajustada nos mesmos itens: confirmar em casos novos. Limite real: 1 token ≈ 3 caracteres em PT.
gate_textos da homol já falhava em 8 textos do Placar (template adaptado por outra sessão), sem relação com o score.
Script de medição: scratchpad `mede_score.py <app> <data_min>`.
**Score Jev + tabela nos 162 com peças (16/10, `jev_testes/score_jev.py`, saída saidas/jev_score.json):** 15 perguntas
atômicas (restritas sem trânsito + premissas 3.0/18.0/20.0), sem trânsito, sem comissões. Pergunta "art. 62 afastado" marca
56/148 com precisão 32% (abaixo da base 36%) → inútil, derruba tudo. Política enxuta (transferência, gratificação especial,
gerente geral pelo Jev + verba sem código): aptos <200k barra 6% (7/109), precisão 86%, 50% do R$ a mais; ≥80% sobe só
42,2→44,1%. Premissas e sinais largos de tabela (ficha sem férias+HE, BT081) têm precisão perto da base. Representação
Bradesco e insalubridade+periculosidade barram casos bons.
Ela corrigiu (16/10): **não é barrar, é entrar no score alta/média/baixa.** Faixas só com Jev não separam (≥80%: 45/42/33).
Melhor: score atual do painel + sinal forte do Jev/tabela manda para baixa (regra E, scratchpad faixas_jev.py). Aptos 109:
alta 37 · 65% ≥80 · 20% do R$ a mais; média 30 · 43% · 13%; baixa 42 · 21% · 67% (antes 40%). Sinais fracos (art. 62,
premissas, ficha sem férias+HE, BT081) pioram as faixas → fora. Não implementado no app.
Conferido no painel parcial de prod de 16/10 (96 aptos <200k, só 9 com peças; valor da causa do P1 lido do .cache com o
Python do app, scratchpad faixas_prod_novos.py): rebaixa 4; R$ a mais na baixa 42→64%, alta 27→22%. O score atual separa
pouco na prod (80%+: alta 55 · média 44 · baixa 38%).
Peças dos outros 86 baixadas em 16/10 (1 sem lista no TARS: 0010669-71.2024.5.15.0053) e Jev rodado (só Jev): 95/96 com
Jev. Regra E rebaixa 10: R$ a mais na baixa 42→83%, alta 27→9%; alta 62% com 80%+. Falsos alarmes: 3 por gerente geral
(0011209, 0016384, ...) e transferência 0000769 — gerente geral é o sinal mais ruidoso. Robô do TARS agora manda os PDFs para
Downloads\pecas_tars_robo (só vale ao reabrir o Chrome).
Ideia dela (16/10): cartão sem cobrir o período + verba negativa. Tabela: `jornada.fonte_apuracao=="cartao"` e meses de
`jornada.cartao.competencias` (n_dias>0) < 90% do período do cadastro (periodo_ini/fim lift); `verbas_negativas` com lado
≠ PJC (o campo traz os dois lados!). 96 aptos: cartão parcial 10 (10% com 80%+, 80% a menos), negativa 10 (0%, 90% a menos)
— sinais de SUBcálculo. Regra E + esses dois → baixa: alta 26 · 77% com 80%+ · mediana 94% · 9% do R$ a mais; média 22 ·
59%; baixa 48 · 25%. "Tem cartão mas apurou pela jornada fixada" (F12) não é detectável: com jornada fixada o cartão nem
é lido. Scratchpad: sinais_cartao_neg.py, faixas_prod_novos.py.
Ela mandou TIRAR he_duplicada, comissões e Súmula 340 (16/10). Versão final medida (96 aptos prod): alta 30 · 80% com 80%+ ·
mediana 95% · 9% do R$ a mais; média 22 · 55% · 82%; baixa 44 · 20% · 47% · 83% do R$ a mais. Ainda só no scratchpad, não
no confianca.py de nenhum app.
Depois (16/10, ela aprovou): valor da causa SAI; gerente geral vale +1 ponto; 1 ponto continua = média. O corte "PJC < R$ 200
mil" não serve para produção → medir nos 128 aptos (peças dos 28 restantes baixadas, Jev em 127/128). 128 aptos: alta 42 ·
76% com 80%+ · mediana 95% · 23% do R$ a mais (3 casos: 0022557 pensão por morte R$419k, 1000277 abatimento R$194k,
0020207 jornada achatada R$144k); média 37 · 46%; baixa 49 · 22% · 57% do R$ a mais.
Regra de pensão (ideia dela, 16/10, `jev_testes/pensao_jev.py`): Jev "decisão condena a pagar pensão mensal?" (trecho próprio
com palavras de pensão) ≥ 0,5 E IA com BT051 sem BT059 → baixa. Marcou só 2 em 276: 0022557 e 1000534, os 2 maiores
sobrecálculos de pensão da rodada. 128 aptos com ela: alta 41 · 78% com 80%+ · mediana 95% · 11% do R$ a mais; média 37 ·
46%; baixa 50 · 22% · 69%.
Testado e recusado (16/10): "sem salário só com hora extra" piora (alta 41→49, 78→69%): jogava para a alta periculosidade
com base zero (0020827, 0011304) e casos sem nenhuma verba calculada. A regra já ignora verba de valor fixo/salário mínimo.
Parcela única (Jev "paga de uma vez?" ≥ 0,5, sem pensão mensal, IA sem BT051/BT059): pega 0020486 (pensão convertida em
indenização única, IA lançou BT040 R$5 mil) e 0010175; alta 40 · 80% com 80%+. Ela aprovou a parcela única.
Ela esclareceu: "sem salário" só deve contar verba que depende do salário (dano moral já ficava fora, por valor fixo/sem
meses). Tirar também BT019 (reflexos de PLR/prêmio) e BT024 (comissão/remuneração variável) da conta: alta 43 · 79% ·
mediana 95%; baixa 48 · 19% · 46% · 69% do R$ a mais. MAS o 1001755-26.2019.5.02.0089 (30%) é integração de PLR: base do
BT019 é a PLR lida do holerite, zero nos 21 meses da PR → reflexos da PR não calculados (R$ 66k a menos). Decisão dela
(16/10): MANTER BT019 e BT024 na conta ("sem salário" = verbas cuja base vem do holerite; valor fixo/sal. mínimo/dano moral
já ficam fora). Score final aprovado, 128 aptos: alta 40 · 80% com 80%+ · mediana 95% · 11% do R$ a mais; média 37 · 46%;
baixa 51 · 22% · 47% · 69%. Regras: baixa direto = sem código, cartão <90% do período, verba negativa IA, Jev transferência,
Jev grat. especial, Jev pensão mensal + IA BT051 sem BT059, Jev parcela única + IA sem BT051/BT059; pontos = sem salário
(+1/+2), ficha sem férias, afastamento longo, gratificação de função, representação, Jev gerente geral (+1 cada); 0 alta,
1 média, 2+ baixa. Saíram: HE duplicada, comissões, S340, valor da causa.
Aplicado em 16/10 SÓ na cópia `ft_paineis_parciais/desde_2026-10-14` (pedido dela) por `jev_testes/aplica_score_jev.py`:
parte do `confianca` que o app gravou no JSON, tira as regras que saíram e soma as novas; troca o texto das regras no HTML
gerado (template do app intacto). JSON original em validacao_calculos.antes_score_jev.json. Se o painel parcial for
regerado pelo painel_parcial.py, rodar o script de novo. confianca.py dos apps NÃO mudou (a cópia usa o código de prod por junction).

**17/10:** as rodadas regeraram o painel cópia 4 vezes sem reaplicar e ela viu o score antigo ("pq ficou com o score antigo?").
Corrigido: aplica_score_jev.py agora toma como base o JSON recém-gerado (antes reaproveitava a base de 16/10 e voltaria
o painel antigo) e o rodada_1710.ps1 roda o script depois de cada painel_parcial. Regra: **todo painel_parcial da cópia
desde_2026-10-14 é seguido do aplica_score_jev.py.** Casos novos sem peças/Jev ficam só com as regras de tabela.
**18/10 manhã (257 aptos, painel cópia):** a alta caiu de 79% para 69% com 80%+ conforme entraram casos novos; ela disse "vou precisar revisar o score". Alta <80%: 29 casos (12 a mais, 17 a menos; R$ 1,18 mi a mais / 1,15 mi a menos). Maior erro atribuível por fator: composição a mais (4, R$ 491k, ex. pensão vincendas 0000334, comissões na base 0000667), identificação a mais (5, R$ 381k: pensão 0000078, Adobe/Crefisa 0010343, dano material 0011124), quantidade a menos (5). Script: scratchpad escapes_alta.py.
**Revisão 18/10 (pedido dela: "revisar os scores com as novas rodadas em prod"; scratchpad revisao_1810.py):** painel cópia
09h45, 257 aptos, 247 processados em 17–18/10 (os de 16/10 foram rerodados), Jev em 213. Faixas: alta 95 · 69% com 80%+ ·
26% do R$ a mais; média 63 · 54%; baixa 99 · 30%. No APTO VALOR (IA R$ 50–200 mil, o que vai para compra) a alta segue 63 ·
78% · mediana 94% · 9% do R$ a mais; a queda vem de fora: IA < R$ 20 mil (32 aptos, ~15% com 80%+; 8 na alta, 38%) e IA >
R$ 200 mil. Proposta: IA < R$ 20 mil → baixa (todos: alta 87 · 72%). Tirar regras não ajuda (ficha sem férias ≈ base no
apto valor, mas segura sobrecálculo fora dele). Baixa no apto valor tem 46% com 80%+ (falsos alarmes difusos). Escapes da alta
no apto valor (14) são difusos e quase todos 60–79%; maior: 0011124 dano material R$150k × PJC R$5k; 2 periculosidade a mais (P7).
**Recurso de revista no Jev (18/10, pergunta dela; `jev_testes/rr_jev.py`, saidas/jev_rr.json):** texto = decisão de
admissibilidade do RR (TARS "Decisão_Recurso_de_Revista", exceção à regra "só inicial/sentença/acórdão/embargos" para esta
pergunta) PRIMEIRO + trechos de RR das outras peças; reclamante → [RECLAMANTE], empresa mantida. 153 de 371 com a decisão.
Gabarito por bloco "RECURSO DE: <parte>" + DENEGO/RECEBO. Jev: "reclamada interpôs RR?" 98% (129 casos); "RR da reclamada
admitido?" 96% (113; 7/8 admitidos pegos, 4 falsos sim). Erros: confunde quando o RR do reclamante é recebido (0010582,
1000342) e quando há 2 reclamadas (0011124). Armadilha: com a decisão no fim do texto o teto a cortava (52% de acerto).
Sem a decisão nas peças (218) não há como validar.
Ela aprovou RR admitido = +1 (18/10): entrou no aplica_score_jev.py (chave jev_rr_admitido; só com tem_decisao_rr). 16 aptos
marcados, 50% calculam a mais. O rr_jev.py NÃO está no passo de Jev da rodada automática: casos novos ficam sem essa regra
até rodar `rr_jev.py --rodar`.
**Famílias da rodada 14–18/10 × Jev (18/10, `jev_testes/familias_jev.py`, saidas/jev_familias.json; gabarito = CNJs das
famílias na página, scratchpad familias_1810.json):** 6 perguntas (jornada variável, afastamento, frequência do cartão,
quantidade fixa de HE, acórdão excluiu verba, dedução autorizada). Sozinhas não separam. Únicas combinações úteis:
"Jev jornada variável + jornada lida com 1 regime" (24 aptos, 33% com 80%+; +1 ponto → alta 77 · 73%, apto valor alta
53 · 81%, R$ a mais na alta 23→14%) e "Jev quantidade fixa + apuração pelo cartão" (6, 0% com 80%+). Afastamento e
frequência + tabela marcam 3 cada, casos bons. Dedução, acórdão excluiu e inflamável+BT035 = ruído.
**Árvore MECE (18/10, pedido dela; scratchpad arvore_score.py):** ramos 1 decisão (todo caso) · 2 jornada (J) · 3 salário
(J ou S; rescisória é S) · 4 valor fixo (F) · 5 resultado (todo caso). Achado: aplicar cada regra SÓ no seu ramo piorou a
alta (69→64%) — o que disparava "fora do ramo" era caso ruim; e a classe F pelos dados ficou imprecisa (pensão não caiu em F).
Árvore serve para organizar, não para bloquear. Horista (ideia dela) = mediana do "Salário Base (BT090)" do P7 < R$ 200
(valor da hora), em caso com J ou S: 6 aptos, 0% com 80%+, mediana 6% (pega a professora 1000277). Peso testado: verba sem
código só 3 casos (2 bons, o ruim já cai por grat. especial) → sair; verba negativa 22 casos, 1 bom → manter TRAVA (+1
piora a média). RR e gerente só em J: pior (R$ a mais na alta 24→32%) → valem para todo caso. Proposta final (todos):
hoje + horista +1 + jornada variável/1 regime +1 + qtd fixa/cartão +1 + IA<R$20 mil→baixa − sem código: alta 73 · 77% ·
mediana 94% · 14% do R$ a mais; apto valor alta 56 · 80% · 92%. Aguardando o ok dela para aplicar.
**Modelo estatístico (18/10, pedido dela; scratchpad modelo_score.py + score_dataset_1810.json; ambiente
%LOCALAPPDATA%\ft_stats com statsmodels — UV_LINK_MODE=copy, caminho curto):** 257 aptos, Fisher + BH e logística conjunta.
Pontos sem trava: 0 → 69% com 80%+ (89), 1 → 55% (65), 2 → 42% (36), 3+ → 18% (11); cada ponto OR 0,53 p<0,001; 1×0 só
p 0,10. Regras separam em DOIS eixos: acerto (80%+): IA<R$20 mil, verba negativa, gratificação, sem salário ≥50% (q<0,05),
horista e qtd fixa/cartão (0/6 cada). Sobrecálculo: grat. especial (OR 9), gerente geral (4), RR admitido (3), pensão
(6, p 0,06) — os sinais do Jev são de sobrecálculo, não de acerto. Sem efeito em nenhum: ficha sem férias (51×50%),
afastamento, cartão parcial (no conjunto), jornada variável, representação, sem código, transferência (n=4).
**Dois selos testados (18/10, ela pediu testar antes de prod; scratchpad dois_selos.py):** ACERTO A1 = travas verba
negativa, IA<R$20 mil, horista, qtd fixa+cartão; pontos sem salário (1/2) e gratificação (+1). SOBRECÁLCULO S1 = sim se Jev
grat. especial, transferência, pensão→dano material, gerente geral ou RR admitido. 257 aptos: acerto alta 133 · 70% com
80%+ (hoje 89 · 69%); baixa 69 · 16% · mediana 22% (hoje 103 · 32% · 55%). Sobre sim 36: 50% a mais × 18%, pega 55% do
R$ a mais. Compra = acerto alta + sobre não: 111 · 73% · mediana 91% · 23% do R$ a mais (hoje alta 89 · 69% · 23%).
Apto valor: compra 77 · 75% (hoje 58 · 78%). Mesmo nível de acerto com mais casos. Nada aplicado no painel ainda.
**Método (18/10, ela não se convenceu dos dois selos nem da significância com n pequeno):** SCORE ÚNICO, objetivo = custo
por processo 0 bate · 1 a menos · 2 a mais ("a mais pesa o dobro", decisão dela). Regra entra pelo MECANISMO; peso =
(custos reais dos marcados + K × custo esperado) ÷ (n + K), expectativa = % que bate + lado do erro, K = "vale como K casos"
(rascunho meu com K=10; ela precisa corrigir a tabela). Comparar SEMPRE no mesmo volume de compra (os N mais seguros) e
validar no tempo (pesos até 17/10, teste 18/10). Resultado do rascunho: dentro da amostra o novo ganha (todos N=90: 75% ×
68% batem, R$ a mais 18% × 23%); no teste de 18/10 (54 casos) EMPATA com o de hoje (61–62% batem). Scratchpad score_bayes.py,
curva_volume.py. Ficha sem férias e sem salário 10–50% ficam com peso ~0 pelos dados.
Ela achou o método complicado demais: "já defini apto, preciso de sinais de que o cálculo está certo ou errado" — três
fontes: atributos da tabela, Jev nas peças, e AGENTE AUDITOR CEGO lendo SÓ as saídas da IA (sem peças, sem PJC).
**Piloto do auditor cego (18/10, 5 escapes da alta, arquivos em scratchpad/auditor/, sem campo PJC):** 1000953 acertou
(intervalo 1h todo dia × 2x/semana, lado e tamanho); 1000277 parcial (achou adicional noturno sobre todas as horas ~R$38k;
perdeu multa de má-fé R$66k excluída no acórdão porque o P4 da IA já a dava como devida); 0000667 parcial (comissões na
base como risco nº 1, R$60–70k, mas veredito "certo"); 0011124 parcial (desconfiou do dano material, confiança baixa;
"errou" o dano moral por não conhecer o teto de R$5 mil); 0000334 errou (achou certo lançar vincendas da pensão). Pontos
cegos: (1) não conhece as premissas da casa → dar o manual de Premissas; (2) confia no P4 quando a leitura da decisão
está errada. ~50–90k tokens e 15–70 s por caso.
**Auditor cego v2 (18/10, 20 casos: 10 ruins, 10 bons, às cegas; scratchpad/auditor2/ com INSTRUCOES.md, avalia.py):**
recebe manual de Premissas + regras FT (teto R$5 mil, honorários fora, só vencidas) + P2 (DEF, cache do app) + saídas.
Ela perguntou por que não ler o P2: o P2 também errou a multa da professora ("mantida pelo acórdão"). Resultado: acerto
60%; quando diz ERRADO acerta 67% (4/6); pega 40% dos errados (4/10). Ganhou 0000334 (vincendas) e 1000640 com o manual.
Falsos alarmes: 0000868 (aplicou premissa grat. especial que o PJC não seguiu — defensável) e 0011105 (leu errado in
itinere na tabela do manual). Perdas: verba que nem o P2 traz (0001233 prêmios AGIR, R$154k), base inflada (0000904),
inconsistência (pegou grat. especial no 0000868, não no 0010815), sinal trocado no abatimento (0000690), e o "FGTS não
calculado" que vários somam a menos e ANULA o erro a mais (1000277 virou "certo"). Pendências: saber se FGTS entra no
total do FT; separar a mais e a menos sem compensar; tratar "não dá para conferir" como classe própria.
Ela respondeu (18/10): **FGTS e multa de 40% ficam FORA do total do Fast Track.** INSTRUCOES.md atualizado (FGTS fora; a mais
e a menos separados, ERRADO se qualquer lado > 20%; veredito NAO_VERIFICAVEL + `perguntas_para_pecas` sim/não para o Jev
responder). Ideia dela: Jev complementa o auditor nos casos que precisam de peça. Custo estimado por caso (preço de 10/2026):
Opus 5.5 ~US$0,60 (teto, sem cache; ~0,20–0,40 com cache+lote), Sonnet 5.5 ~0,30, Haiku 5.5 ~0,015, Jev ~0,001.
**Auditor v3 + Jev (18/10, Opus, mesmos 20; saida_v3/, jev_testes/auditor_jev.py, avalia_v3.py):** acerto 53%, precisão
56% (5/9), cobertura 50% (5/10) — NÃO melhorou o v2 (60/67/40). Ganhos: 0011124 (dano material R$150k exato), 0000690
(lado certo agora). Ruídos: (1) premissa × PJC: em 3 casos bons o auditor aplicou restrição do manual (grat. especial
0000868, SRV/18.0 0010300, in itinere 0011105 — manual em tabela ambígua) e o PJC calculou a verba (provável trânsito); sem
esses, precisão 5/6; (2) "não compensar" gerou falso alarme no 0020104 (a mais 20,8% e a menos 16%, líquido 99%);
(3) perguntas ao Jev ruins: sobre trânsito (proibido), valores numéricos ("valor da causa ≈ 665 mil?"), vagas — Jev não
ajudou; (4) perdas: multa excluída da professora (perguntou o valor da causa, não se o acórdão excluiu), prêmios AGIR do
0001233 (P2 leu improcedente), base inflada 0000904, grat. especial do 0010815.
**Decisão dela (18/10): o auditor APLICA A PREMISSA** (prevalece sobre o PJC; não precisa rodar de novo). Reavaliado com a
premissa como verdade (0000868, 0010300, 0011105 viram erro): v2 precisão 100% (6/6), cobertura 46%; v3 precisão 88%
(7/8), cobertura 54%, mais 2 "não dá para conferir" que eram erros. Valor marginal sobre o score: nos erros que o score NÃO
mandou para a baixa (R$ 943 mil a mais na amostra), o v3 pegou R$ 559 mil (0000334, 0011124); com os "não dá para conferir"
indo para revisão, R$ 757 mil (~80%). Carteira (257 aptos): alta+média = 154 casos e R$ 1,78 mi a mais (34% do total);
auditor nesses 154 custaria ~US$ 75 (Opus). Recomendação: vale como 2ª camada só em alta/média, com ERRADO/NV → calculista;
falta medir falso alarme numa amostra natural (não 50/50).
**Volume (decisão dela, 18/10):** o agente roda só no APTO VALOR com faixa alta/média do score do painel cópia (16/10 +
RR): 99 do lote 14–18/10 (~10% dos processos que rodam, ~US$ 50). Desses 99, 31 abaixo de 80% (alta 13/58, média 18/41);
13 calculam a mais. "A menos importa menos."
**Auditor v4 nos 13 a mais (18/10; INSTRUCOES com premissa prevalece, limite no líquido, perguntas só sobre o que a decisão
deferiu/excluiu/limitou, sem trânsito nem valores, com efeito_se_sim/nao_rs; saida_v4/, gabarito_v4.json, avalia_v4.py):**
pegou 8/13 e 75% do R$ a mais (R$ 405k de 537k). Achou a causa certa em mais 2 mas subestimou (1000822 salário-base em
dobro; 0010690 intervalo 15 min no contrato todo). Com alerta "a mais estimado > 10% do total" (em vez de líquido > 20%):
11/13 e 94% do R$. Perdeu 1000735 e 0010162. Premissa vai além do PJC: 1000686 periculosidade por inflamável (item 3.0,
Tema 154) → certo seria 0; 0000300 reflexos de pausa art. 72 pós-Reforma (11.0). Jev ajudou em 1000991 (prescrição fixada
na sentença) e 1001135. Próximo: medir falso alarme nos 68 certos do apto valor alta/média.
**Auditor LEVE no Haiku (18/10, pedido dela "precisa estimar a verba?"):** sem API key na máquina → rodado via subagente
Haiku lendo 1 arquivo. `auditor2/monta_leve.py` monta instruções (INSTRUCOES_LEVE.md, só faixa de tamanho, sem R$) +
manual + RESUMO por verba feito em código (P4/P9a cortados, base e horas min/mediana/max, 2 memórias, anomalias: base >
1,5× mediana, base zero com dias, valor negativo, mudança de horas/dia, proporção dos reflexos). Resumo 3–13 KB (antes
60–110 KB); arquivo total ~14 mil tokens (manual = maior parte, cacheável). Resultado nos 13 a mais: Haiku 11/13 e 89% do
R$ (Opus completo 11/13 e 94%). Haiku perdeu 1000686 (não ligou inflamável à premissa 3.0) e 1001135 (achou base alta
"explicável"); pegou 1000735 e 0010162 que o Opus perdeu. Mas marca muito NAO_VERIFICAVEL (6/13) → falso alarme é o risco.
Custo estimado numa chamada de API: ~US$ 0,002/caso no Haiku (vs ~0,50 Opus agente). avalia_haiku.py.
**Pipe que ela definiu (18/10):** score + Jev (padronizado) → agente IA (auditor) → agente IA que ESTRUTURA as perguntas
para o Jev → Jev → score final. NAO_VERIFICAVEL só sai da alta se o Jev confirmar. Com o Haiku escrevendo as próprias
perguntas, o fluxo completo pegou só 6/13 (46% do R$): as perguntas não miravam o erro e o Jev "liberava". Com um
estruturador separado no Opus (`auditor2/ESTRUTURADOR.md`: "sim" = a IA errou, só o que a decisão diz, hipóteses além das
do auditor; entrada = suspeitas do Haiku + resumo, 6–18 KB): 9/13 e 79% do R$ (0011124, 1000735, 1000464 confirmados).
Perdas: 1000686 e 1001135 (Haiku disse CERTO), 0011715 e 0010690 (erro de conta, não de decisão). Falta dar as regras da
casa ao estruturador (perguntou sobre dano moral R$5k × R$50k).
**Haiku não discrimina (18/10, encerrado):** nos 20 BONS o Haiku alarmou 20/20 (6 ERRADO por premissa esticada por
analogia: teto 5k no dano estético, concausa em dano fixo, prêmio na base de PDV, comissão como restrita; 14 NV por dúvida
genérica). Instruções apertadas (CERTO padrão, NV só com fato concreto, premissa só na verba exata): bons alarmados 20→7,
mas os 13 a mais caíram de 11→6 pegos (R$ 478k→177k). Ou seja: o agente sem peça não separa bom de ruim. Decisão dela:
parar o agente e voltar ao Jev com perguntas padronizadas melhores (aprendizados do agente). Teto 5k assumido só para
dano moral/assédio/acidente (dano estético sem resposta dela). Aprendizado: o que a premissa decide é checagem de CÓDIGO,
não pergunta ao Jev; ao Jev só o que a decisão diz.
**Catálogo amplo pelas premissas (18/10, pedido dela):** `jev_testes/catalogo_perguntas_premissas.md` (item do manual ×
gatilho × pergunta × alerta) e `jev_testes/premissas_jev.py` (--contar/--rodar/--avaliar). ~55 perguntas em 9 blocos
temáticos (cada bloco = 1 chamada com recorte próprio), gatilho por verba (código OU nome — muitas verbas vêm sem código),
reclamada, bancário, datas; "exclui_i" por verba principal; 15 conferências só de código (CODIGO). Não refaz as perguntas
de jev_score/familias/pensao/rr. População: 325 aptos com PJC e peças (3 painéis); 7.207 perguntas, 1.157 chamadas,
~13 mi tokens (~US$ 0,56). Saída saidas/jev_premissas.json; avaliação marca ▲ alerta com % a mais ≥ base+15 pp.
Resultado (rodado 18/10, 0 erros, 15,5 mi tokens): resposta do Jev sozinha ≈ base (26% a mais). Cruzada com o P9a/meses
(CRUZA): a IA JÁ segue S85, OJ 394, vincendas, base da insalubridade (cruzamento zera). Sobram com sinal: acórdão excluiu
verba (26; 38%), dif. salarial pós-2017 (8; 50%), turno ininterrupto + limite 6h (10; 40%), S340 (3). Sobre o score do
painel: na ALTA do apto valor acende 11/74 com 27% a mais vs 25% no resto → não melhora; só concentra na baixa (71%).
Conclusão: os escapes da alta não são leitura de decisão/premissa, são conta (base, quantidade) → teto do Jev atingido.
**Sinais do próprio cálculo (18/10, jev_testes/sinais_calculo.py):** interpretação do P9a (limite derivado, intervalo
inferido, sem cartão, reclassificada…) e conta genérica (HE h/mês, reflexo fora da proporção, negativo) ≈ base. Dossiês
dos 28 alta-a-mais: erro_ia R$ 319k (P9a 43%: base com comissões/OJ 397, jornada em todos os dias, limite 44/6, insal +
peric; P7 salário lido 2–4×) e gabarito_questionavel R$ 235k — Raíra tinha razão: é interpretação. Único sinal forte:
**base do mês salta > 1,5× os dois vizinhos** (alta: 9 casos, 56% a mais vs 20%; apto valor alta 6, 67% vs 22%, 22% do
R$ a mais). Insal + peric juntas (3.0) = regra de premissa (3 casos).
**Aplicado na cópia desde_2026-10-14 (18/10, aprovado por ela):** aplica_score_jev.py ganhou trava insal_peric_juntas e
+1 salto_base (versão segue "2026-10-16 tabela+Jev" p/ a detecção de reaplicação). 9 casos mudaram (7 com < 80%).
Apto valor alta 58→55, ≥80% 78% (igual), mediana 90,8→93,8%, a mais 22→20%. Fotos em jev_testes/saidas/faixas_*_1810.json.
**3 iterações (18/10 tarde, pedido dela; "pensão é verba NÃO elegível, não é dano" — já dito antes):** ferramentas
iteracao_score.py (faixas + escapes da alta + bons na baixa), iter_sinais.py (sinais Jev×IA), simula_score.py (variantes
sem gravar). Jev aprofundado: blocos pensao2/multas/jornada2/ferias/deferidas/indeniz2/iter2 em premissas_jev.py (+990
chamadas, ~US$ 0,6 no total). Aplicada a variante 9 na cópia: travas pensão em qualquer forma (pensao_qualquer),
cartão lido mediana < 12 dias/mês, verba deferida não calculada (def_he/reintegra/adicional ≥ 0,4); +1 dobra só do abono,
periculosidade base < R$ 300, HE só em alguns dias + IA ≥ 15 dias/mês, má-fé não contra a reclamada; saiu ficha sem
férias. Resultado todos os aptos: alta 85→80, ≥80% 69→78%, mediana 90,3→93,1, a mais 18→11%; faixas coesas
(78/57/31%). Apto valor alta 50: 80% ≥80, a mais 16%. Testadas e descartadas: OJ 397/comissionista (não separa nem
refinado), adicional da norma coletiva, valor mensal arbitrado, majorou indenização (só encolhem a alta e sobem o a mais).
Sobra: 18 escapes da alta, quase todos a menos (norma coletiva não lida, enquadramento, PDV, P4); a mais: 1001135 (OJ 397),
1000686 (P7 constante), 0011715 (jornada seg–sáb), 1000464 (férias em dobro).
**Refino contra o conservadorismo (18/10 noite, pedido dela: "manter os da alta na alta", ≥ 5 iterações):** baixa tinha
49% dos casos e 31% dos bons. refina_faixas.py testa 15 iterações cumulativas com saldo = Δbons na alta − 2×Δa mais −
Δa menos ruins (aceita se > 0 e alta ≥ 77%). Jev novo (bloco "refina"): def_he_propria, rr_ataca_verbas,
jornada_periodo_sem_cartao. Aceitas: RR só se ataca verbas; gratificação some se grat_compensa; HE alguns dias exige IA ≥
18 dias/mês; sem base só ≥ 20%; travas de a menos (cartão parcial, cartão poucos dias, deferida não calculada) viram +1.
Rejeitadas: deferida refinada, sem base sem afastamento, afastamento × Jev, salto > 2×, salto 2+ meses, gratificação só
com HE ou só com outro sinal. Resultado aplicado: alta 80→93 (78% ≥ 80, a mais 11%), média 43, baixa 127→116 (29%);
apto valor alta 60 (80%, 15% a mais). Pensão "boa" (7 casos) fica travada: não elegível.
**Faixa pelo lado do erro (18/10 noite, decisão dela: "é pior ser baixa do que média em sobrecálculo"):** regras
classificadas por lado (LADO_MAIS em aplica_score_jev.py: caso calcula a mais em ≥ 33%, base 22%). Qualquer sinal de a
mais → baixa; a menos 1–2 pontos → média, 3+ ou verba negativa → baixa; "a calcular" só quando seria alta sem Jev.
simula_lado.py testou 9 variantes; só a "a menos 2+ → baixa" ordena tudo, mas a baixa vai a 51% (conservador). Aplicada a
A: alta 93 (78% ≥ 80, 11% a mais) · média 65 (38%, 18%) · baixa 99 (32%, 35%). Apto valor 60/39/49 com a mais 15/21/41%;
≥ 80% média 49 × baixa 51 (empate, n pequeno; a baixa do apto valor é "a mais com assertividade ok").
**Faixa "restrita" (18/10 noite):** ela estranhou o gráfico (baixa com mais casos ≥ 95% que a média). Causa: 11 dos 18
≥ 95% da baixa eram premissa (pensão, gerente geral, grat. especial — PJC calculou igual). Agora RESTRITA = pensão (3
chaves), grat. especial, transferência, gerente geral → faixa própria "restrita" (⊘), fora da baixa. Aptos: alta 93 (78%
≥ 80, +11%) · média 65 (38%, +18%) · baixa 64 (23%, +31%, ≥ 95% só 9%) · restrita 35. Apto valor: 60/39/31/18.
Template da cópia: Restrita em violeta (RESTR_COR) no gráfico de composição (19/10, pedido dela).
**"A calcular" = sem peças:** baixar pelo robô (abrir antes o Chrome com --remote-debugging-port=9333
--user-data-dir=%LOCALAPPDATA%\chrome_tars_robo), depois score_jev --montar/--rodar, pensao/rr/familias/premissas
--rodar e aplica_score_jev. 19/10: 0000207 → restrita (pensão); 1000746 → alta mas 7% (IA 2× PJC). CORRIGIDO: não é a
limitação à inicial (pedido de HE R$ 368 mil, IA R$ 57 mil). Causa: (1) IA calculou 11/2019–03/2020 (R$ 10,7 mil) — a
sentença indeferiu só 16/03/2020–28/03/2022 e condenou "o restante do período"; PJC começa em 29/03/2022 (gabarito
questionável); (2) IA ~52 h/mês (2,5 h × todos os dias úteis da jornada 9h–20h) × PJC 20–37 h/mês.
Analista (19/10, analises_caso/1000746…json): dos R$ 43,2 mil a mais, R$ 37,8 mil são gabarito questionável (PJC cortou
11/2019–03/2020 e apurou só o excesso semanal de 44 h, sem a 8ª diária que a sentença manda); erro da IA R$ 6,4 mil
(intervalo de 30 min aplicado nos 5 dias, a sentença deu 30 min em 3 e 1 h em 2: P9a não repassa dias_por_semana do
BT007 para a HE; sinal em 19 pacotes). Ficar na alta é coerente.
**Pacote para a engenharia (19/10, pedido dela: "pasta estruturada com README e código"):** `Repos/ft_score_confianca/`
(score_confianca/ um módulo por passo; config/perguntas.json + regras.json; ferramentas/ importa respostas dos testes e
valida contra o painel; tests/ 8 testes; docs/pipeline.html no Visual Guide, publicado em
https://claude.ai/artifact/PcPMQuabhWmMYxmJ8cPaXm). 16 perguntas em 8 blocos (rr_ataca_verbas juntou-se ao bloco de RR,
pensao_qualquer ao de pensão). Validado: 264/264 com as respostas antigas. Rodada nova de ponta a ponta (19/10, US$ 0,63):
1ª tentativa 252/264 — juntar rr_ataca_verbas ao bloco de RR e estreitar o recorte das restritas mudou respostas (gerente
geral 0,07→0,71; ataca verbas 0,35→0,88); voltou o desenho validado (9 blocos, recurso_revista_verbas próprio, recorte
largo nas restritas) → 262/264 (2 por oscilação do Jev perto do corte). Lição: mudar o recorte ou juntar perguntas muda a
resposta do Jev — sempre revalidar. Ao mudar regra, mudar NO PACOTE (e
no aplica_score_jev da cópia, que ainda é quem gera o painel). Ela não gostou do Claude Doc anterior (fora do Visual Guide).
**Inflamável no prédio (22/10, caso 1001261 dela):** o Jev já dizia 0,97 em 16/10, mas a pergunta nunca entrou na regra.
A pergunta antiga era larga (pegava benzeno/contato direto, 0010030). Nova: `inflamavel_predio` ("tanque na edificação,
toda a edificação como área de risco"), gatilho = IA calculou periculosidade → trava RESTRITA (premissa 3.0, Tema 154).
Pega 1001261, 1000686, 1001055, 0000392, 0011516. Aplicada no pacote e no painel. **Desde 22/10 o painel da cópia é
gerado PELO PACOTE** (aplica_score_jev chama score_confianca.pipeline.pontuar com o cache do pacote; a função score()
antiga ficou só como histórico): 274/274. Cache do Jev agora com versão POR PERGUNTA (antes, mudar a versão do arquivo
refazia tudo — custou US$ 0,65 à toa).
**Auditor nos escapes da alta (27/10, pedido dela):** apto valor < 50% = 36 (16 restrita, 9 baixa, 4 média, 7 alta). Auditor completo (Opus, às cegas, resultados/rodada_alta_av_2710) nos 7 da alta: alertou 6/7 — causa certa em 0100259 (base do aviso), 0000642 (BT054 principal), 0100305 (pré-contratação abatida); premissa certa em 1000788 (20.0, reintegração); lado certo em 1000166 (o −3.653% é efeito do pareamento do painel); causa errada mas alerta em 0016637 (viu OJ 397, o maior era HE de trabalho externo). Perdeu 0021441 (periculosidade × insalubridade: só a sentença resolve → Jev). Falso alarme não medido nesta rodada.
**Treino e teste (27/10, pedido dela: "mais dados, restrita talvez mais flexível", ≥ 5 iterações):** 540 aptos com
PJC (60/40 estratificado pelo a mais, semente 2710 + corte temporal até 24/10 × 25–27/10); jev_testes/treino_teste.py +
iter_2710.py. Base: alta 180 (72% ≥ 80, 16% a mais), restrita 157 (36% a mais), baixa só 19% a mais (cheia de a menos).
Passaram (saldo + nos 4 recortes, 0 a mais novo na alta): restrição de verba só trava com peso ≥ 20% do total; liberar
ATS, representação e RP 52 (restrições com 0% a mais); restrição só com Jev ≥ 0,6. Coesão 3a (verba negativa e soma a
menos param na média; baixa = só a mais) — alta igual. Resultado: alta 180→188 (73%, 15% a mais), restrita 157→118
(42% a mais), baixa 30% a mais × média 15%. NÃO passaram: liberar prêmio 2017/gerente geral/pensão/inflamável/grat.
especial/difsal (trazem a mais); parcela única só até R$ 200 mil ou como sinal a mais; 7ª/8ª hora +1; Jev ≥ 0,7/0,8.
Achado: a exceção da parcela única deixa 8 de 26 casos a mais na alta (0022557 pensão por morte, R$ 419 mil) — instável
treino×teste. Não aplicado: aguarda o OK dela.
**Árvore por verba (27/10, decisão dela: "dar um passo atrás", MECE):** página https://claude.ai/artifact/KK2NzJozvzkpt65G2cbaDe
(fonte ft_score_confianca/docs/arvore_score.html). Unidade = VERBA; 0 aptidão (+ restrições do processo inteiro: pejotização,
terceirização ilícita, ACP, cruzeiro, WMS) → A identidade (P2/P4 × P10) → B elegibilidade (premissa) → C fidelidade ao
critério do P4 → D fidelidade à decisão (Jev peças) → E dados de entrada. Trava = verba não pode estar (A/B); ponto = conta
com dúvida (C/D/E); peso pelo R$ da verba. Achados: gerente geral 18/20 travados SEM HE no cálculo (gratificação
especial 10/10, RP 52 5/5, representação 6/15, ATS 5/11) — regra de caso inteiro de 22/10 sobretrava; pensão vaza (5
maiores escapes, ~R$ 1,2 mi); só metade dos 50 escapes da alta é erro da IA. Piloto P4 × cálculo (conferencia_p4*.py):
comparação aberta alarmou 49/78 bons; extração + código pega pouco, só abatimento é preciso. Ordem proposta: gabarito
corrigido → B (ligar à verba, fechar pensão) → A (calculada sem deferimento, acórdão excluiu) → C por parâmetro → peso R$.
Nada aplicado; as 7 rodadas de 27/10 também aguardam.
**Decisões de 27/10 (fim do dia):** por ora TUDO vira regra no score (nada para backlog da esteira) e o score entrega SÓ
a faixa (sem R$/deságio). **Restrição:** "se uma verba está atrelada a uma verba que restringe, o caso fica restrito" —
restrito quando a verba restrita OU atrelada (reflexo, usa na base pelos componentes do P9a, ou verba sem código quando o
Jev confirma) está no cálculo; sem nada disso, não restringe (gerente geral sem HE). Só pejotização, terceirização, ACP,
RMNR, cruzeiro e WMS travam o processo inteiro. **Aplicado no PACOTE (não no painel; backup ft_score_confianca_backup_2710):**
restricoes.atreladas(), bloco criterio_p4 (Jev lê o critério do P4, fonte "p4", pergunta por verba "deduz__n") e sinal
criterio_abatimento (a menos). Retirados após teste: acórdão excluiu (não separa) e limite 6ª×8ª ("7ª e 8ª" lido como 8ª).
Treino/teste/temporal: +4/+5/+2/+7; alta 180→186 (72→74%), restrita 156→129 (27 saíram: 14 alta). 18 testes. Jev US$ 0,33.
**Pasta do agente auditor (19/10):** `Repos/ft_agente_auditor/` — proposta = 2ª CAMADA depois do score, só apto valor
alta/média; instrucoes/ (completo, leve, estruturador), codigo/ (monta_caso, monta_leve, jev_perguntas, avalia — avalia
reproduz 11/13 Opus, 9/13 estruturador, 6/13 Haiku apertado), resultados/ com todas as rodadas e gabaritos. Falta: falso
alarme em amostra natural (~60 da alta), escolher versão, chave da API Anthropic com a Engenharia.
**Doc do pipeline para a engenharia (19/10, substituído pelo pacote):** https://claude.ai/code/artifact/dbfb94e7-b227-4aca-b7d9-d5ac23146daf
("Score de confiança do cálculo — pipeline": diagrama, 6 passos, as 16 perguntas do Jev em uso com gatilho/cruzamento,
11 regras de tabela, regra de faixa, contrato JSON, métricas, custo, o que foi descartado, pendências). Atualizar lá
quando a regra mudar.
**Valor da causa testado e descartado (19/10):** limitação (Jev) × IA vs valor da causa: em nenhum caso com limitação a IA
passa do valor da causa; e IA > valor da causa na ALTA anda com casos BONS (≥ 80% 89–93%, a mais 5–11%). Não entra.
**18/10 tarde:** inapto fica SEM score (confianca = None, selo "—"), escolha dela; antes 143 inaptos apareciam como "A calcular" porque peças/Jev só rodam nos aptos. Obs.: outra sessão mudou as regras do aplica_score_jev.py em 18/10 (lado a mais/a menos) — respeitar.
**Why:** registrar decisões de desenho para não refazer a discussão. **How to apply:** ao mexer no score, partir
destes componentes; recalibrar pesos quando houver mais rodadas. Ver [[sobrecalculo-primeiro]], [[painel-correcoes-0810]].

**Calibração do Jev (27/10):** cada pergunta foi medida contra o PJC (a verba existe?) e contra o desfecho, com `jev_testes/calibra_jev.py`. Ficaram cortes próprios: horas extras deferidas 0,7, adicional deferido 0,8 e representação 0,7. Saíram a pergunta de reintegração (acerto de 20%) e a substituta "parcelas mês a mês" (22%; tirava 25 casos bons da alta). Entrou o sinal `p4_sem_calculo`, que não usa o Jev: o P4 registrou critério e o cálculo deu R$ 0. É o sinal mais forte medido (25% × 60% com 80% ou mais). A alta ficou igual (144, 76%). Lição: alerta falso às vezes "segura" caso a mais por acaso, então tirar ruído pode piorar o saldo. Ainda não aplicado no painel.
