---
name: calculos-da-integra-s3
description: "07/11: gabarito tirado da íntegra recortada (S3) para os 2.621 CNJs de insalubridade/periculosidade — regra de busca, piloto de 50, .pjc do ged é da esteira"
metadata:
  node_type: memory
  type: project
  modified: 2026-11-11T12:58:25.923Z
  originSessionId: 0d063384-33d1-4029-875f-1f7135335bd0
---

Lista `entradas/df_cnjs_com_pedidos_contendo_insalubridade_ou_periculosidade.csv` (2.621 CNJs, 07/11/2026). Objetivo:
achar na íntegra recortada um cálculo do PJe-Calc para usar como gabarito no `compara.py`.

- **`ged-files-bucket-prod/pjc/<CNJ>/<uuid>.pjc` NÃO é gabarito**: o uuid é o `id_processado` da execução da esteira
  (gravado logo após a execução). Comparar com ele dá ~100%.
- Nome da peça nos recortes: `<categoria>-<posição>-<Tipo>.pdf`. Posição = ordem na íntegra (mais alto = mais
  recente); a data do S3 é igual para todas. Categorias: 1 sentença, 2 acórdão, 27 cálculo/anexos (mista),
  37 impugnação, 38 atualização de cálculo, 39 apresentação de cálculos, 40 laudo, 42 planilha de cálculos.
- PJe-Calc se reconhece por "PLANILHA DE CÁLCULO" + "Resumo do Cálculo"; o rodapé da última página traz
  "Cálculo liquidado por X" (nome = PJe-Calc do tribunal, servidor ou perito; "offline" = PJe-Calc Cidadão, parte
  ou perito) e "Assinado eletronicamente por".
- Piloto 50 (busca_calculos_s3.py, 2,3 min): 47 rodaram na esteira; 19 com PJe-Calc, 5 só com planilha que não é
  PJe-Calc, 23 sem peça de cálculo. A mesma conta aparece re-juntada; cálculos de posição baixa são da inicial.
- Na comparação dos 5 primeiros, a lista de casos do HTML ficava vazia: o template abria em "aptos validáveis" +
  score "alta". Na cópia daqui abre em "Todos" (template_telas.html).

- **Regra B (decidida pela Raíra em 07/11):** a conta do tribunal mais recente; sem ela, o PJe-Calc mais recente.
  Conta offline antes da 1ª sentença (inicial) fica fora; a do tribunal não (sentença líquida, ex. 0000352).
  Baixa todas as candidatas e apaga logo depois tudo o que não foi escolhido (pedido dela).
- **Filtro antes do S3:** a última execução precisa ter linha no P10a/P10b na Nekt. Dos 2.621: 2.413 rodaram e
  1.512 chegaram ao P10. O `.pjc` do ged (1.463 da lista) perde caso bom (0000480 tem P10 e não tem .pjc).
- compara.py tirava o CNJ juntando todos os dígitos do nome e errava em "40-184-RELATORIO_PROCESSO_<CNJ>…";
  corrigido para buscar o padrão do CNJ.

- Lote 07/11 (1.512 com P10): 549 com PJe-Calc, 253 só planilha não PJe-Calc, 710 sem peça de cálculo.
- **Por que falta cálculo em processo transitado:** nos 2 conferidos (0000475-94.2021.5.14.0004 e
  0020724-75.2018.5.04.0028) a íntegra do ged é a do **2º grau** (capa "Recurso Ordinário Trabalhista", Relator) e o
  sumário (últimas páginas) termina em "TST - Certidão de Trânsito em Julgado" + "Termo de Remessa ao TRT". A
  liquidação acontece depois, na vara (1º grau), e não entra nessa íntegra.

- Resultado 08/11: 548 comparados, 213 aptos, 189 com leitura confiável: 32% com 80%+, mediana 61,1%; 38 IA a mais ×
  111 a menos; conta do tribunal 38% × parte/perito 27%. Padrão forte: periculosidade quase zerada na IA (12 casos).
  Página: https://claude.ai/artifact/G6upWA1cn9GqbakTU2qP8z (gerada por scripts no scratchpad da sessão).
- O motor (gerar_telas) é lento aqui: lê o PJe-Calc completo (70–120 págs) com extract_tables; 549 ≈ 1h45. Dá para
  pré-ler em paralelo gravando `.cache/pjc__<CNJ>__v11p<mtime>.pkl` (mesma chave do `_parse_pjc_cached`).
- Analista nesta máquina: pasta `C:\ft\ft_analista_trabalho` (FT_AGENTE_TRABALHO); árvore com
  `codigo/src/arvore.py <intervalo> --saida`; pacotes com `bt-prod-apps/ft/agente_analista/ferramentas/prepara_casos.py
  --painel C:\ft\ft_confere_gabarito`; peças dos recortes do S3 (cats 1,2,5,21) em texto; prompts de produção vêm do
  `.cache/raw__ft_lift_tb_agente.pkl`. Clone do bt-prod-apps em `C:\ft\bt-prod-apps` (branch feature/score-confianca).

- 08/11 tarde: analista nos 38 aptos com IA a mais (todos): 19 IA, 16 gabarito, 3 os dois; 102 erro_ia, 77
  gabarito_questionavel, 16 metodo (painel não soma quadro de multas, FGTS, seguro-desemprego do PJe-Calc). Em 3
  (1000727, 0020708, 0010698) a homologada é muito maior e a IA está abaixo dela. Famílias novas: férias/afastamento
  fora do calendário (só vêm da ficha), cartão (intervalo pré-assinalado, teto 2h, dias do calendário). Limite de 20
  subagentes simultâneos. Página publicada já está compartilhada com a organização.
- Analista nos 15 maiores sobrecálculos (08/11), todos prontos em `C:\ft\ft_analista_trabalho\analises_ip` e levados ao
  painel (`agente/agente_por_caso.json`, fora do Git). 8 IA, 5 gabarito, 2 os dois. Maior erro da IA: P9b v8 item 2.4
  "valor fixo não compensa" (piso, prêmio, SRV/PPE; R$ 221 mil em 4); base de HE inflada (47 no lote). O "a mais" do gabarito (sentença líquida reformada pelo acórdão; conta de parte rejeitada) →
  a regra B precisa exigir conta posterior ao último acórdão e preferir a citada na homologação. Erros da IA: diferença
  salarial pelo piso sem descontar salário (P9b valor fixo), periculosidade sem abater o pago (12 no lote), base de
  horista, limitação à inicial (Premissa 13.0).

- **Íntegras de 1º grau (chegaram 08/11 à noite):** pedido de 1.297 (710 sem cálculo, 334 só conta de parte, 253 só
  planilha). Vieram só no bucket de recortes (não no `integra/` do ged); 1.246 ganharam peças. Busca nova em
  `saidas/insalub_peric_1grau`, base combinada em `pecas_s3/_escolhidas/insalub_peric_total` e
  `saidas/insalub_peric_total`: 1.157 com PJe-Calc, 1.156 comparados, 480 aptos, 442 com leitura ok → 38% com 80%+,
  mediana 69,7%; insalub. 70% (134), peric. 53% (196, 30 quase zeradas); 67 IA a mais (37 já com analista, 30 sem).
- **Jev nos 480 aptos (09/11 madrugada):** chave em `bt-prod-apps/ft/score_confianca/.env` (o Bloco de Notas salvou
  `.env.txt`; renomeado). Registro montado do comparacao.json sem nada do PJC + PROV/DEF do `.cache/caso_raw__*.pkl`;
  peças dos recortes em `C:\ft\ft_analista_trabalho\pecas_jev` (nomes normalizados p/ Petição_Inicial, Sentença,
  Acórdão, Decisão, Decisão_Recurso_de_Revista; anexos de jurisprudência fora). Custo < US$ 1. Faixas sem auditor:
  alta 143 → 55% com 80%+ (apto valor 69%), média 42%, baixa 19%, restrita 34%. Trava inflamável no prédio (29) tira
  casos bons (peric. mediana 92,8%); trava turno ininterrupto (38) acerta (mediana 39%).
- **Auditor OpenRouter na alta (09/11 manhã):** 147 casos, US$ 25,25, 0 falhas (chave OPENROUTER_API_KEY no mesmo
  `.env` do score). 28 "alto" saíram para a baixa. Alta (442 confiáveis) 143 → 117: 55% → 61% com 80%+, mediana
  83,6 → 88,5%, a mais 14 → 6. Apto valor alta 32 → 25, 69% → 68% (não melhorou). Os 26 "alto" confiáveis: 31% com
  80%+, 8 a mais e 14 a menos (muitos reflexo acima do teto e período descontínuo). Painel `saidas/insalub_peric_total`
  lê `confianca_jev.json` da pasta (compara.py --so-pagina); o sem auditor ficou em `confianca_jev_sem_auditor.json`.
- **Analista nos 8 da alta apto valor abaixo de 80% (09/11):** 6 são IA, 2 gabarito (0001459 sentença líquida
  reformada; 0010178 gabarito = líquido final corrigido em linha única, mais 4 assim no lote → tirar da régua).
  Erros da IA que se repetem: vincendas "até implantar em folha" (15.0-b, P1 para no ajuizamento; 0000144, 0102145);
  adicional cheio no mês de férias + reflexo em férias (sobrecálculo; 3 dos 8, padrão em ~400 árvores); periculosidade
  deferida fora da base (HE pelo P9b; estabilidade pelo P9a v13 2B.2); pago não abatido (0010694, R$ 62 mil a mais);
  exceção 18.0-b "transitou, segue o deferido" ausente. Painel soma FGTS da estabilidade. Análises em
  `ft_analista_trabalho/analises_ip`, árvore da base toda em `rodadas/arvore_total`.
- **Analista em todos os aptos da alta (09/11 tarde):** fila de 107 (36 <80% + 71 ≥80%) em
  `scratchpad/alta_analista.json`; vereditos em uma linha cada em `scratchpad/vereditos_alta.txt`, progresso em
  `progresso_analista_alta.txt` (conferir pelo arquivo em `analises_ip`). Os 36 <80%: 10 IA, 11 gabarito (5 só por regra
  da casa: prescrição 7.2, piso ACT × mínimo 3.0), 12 os dois, 3 painel (os 2 "a mais" são painel: multa e dano moral
  no bloco Multas/Indenizações, FGTS com outro nome). Erros IA recorrentes: reflexo do adicional em HE/noturno pagos
  (lista fechada de reflexos do EDITOR v14), periculosidade só no salário-base (P9a v13 salario_base_exclusivo; P9b 2.2
  descarta verba nunca paga), vincendas (DADOS_INICIAIS para no ajuizamento), pausa térmica BT080 (cartão em código),
  adicional cheio em férias sem ficha (~157 casos), P8 zerando meses.
- **Por que ficam abaixo de 80% (10/11):** página https://claude.ai/artifact/6EQg2tNeoEw6EieRGPvDXn sobre os 440
  aptos confiáveis (peric. 212 → 45%, insalub. 134 → 36%, 90 sem adicional deferido → 29%). Trocando adicional+reflexos
  pelo gabarito: peric. 45→76%, insalub. 36→58%; trocando as outras verbas: insalub. 36→74% (HE domina). Peric. tem 46
  adicionais zerados: 23 horistas com salário-base = valor da hora (P7, mediana < R$ 100), 12 base zerada sem holerite
  (fonte secundária dos dados iniciais não usada), 4 diferença de grau abatida duas vezes. Corrigir esses 39 → peric.
  58%, total 39→46%. Nenhum desses tinha passado pelo analista. Analista nos 72 abaixo de 80%: 160 erro IA × 160
  gabarito questionável.
- **A Raíra quer a assertividade DA VERBA, não do processo com a verba** (10/11, a página v2 virou isso). Verba
  (linhas do adicional somadas por caso): insalub. 69% com 80%+ (med. 91,6%, n 136), peric. 50% (med. 78,1%, n 206);
  reflexo férias é o pior (35%/46%) e erra mesmo com adicional certo. Causa principal mês a mês das 104 peric. <80:
  horista 24, base zerada 18, base sem variável 15, parou no ajuizamento 10; das 42 insalub.: parou no ajuizamento 11,
  meses a mais 8. Linhas só do gabarito vêm sem código: pegar pelo nome.
- **Horista simulado (10/11), página no formato BT-2532:** https://claude.ai/artifact/H6c9KWS5bkpYRQFAzkawBu. Gatilho
  por verba (base da IA < ½ mínimo em ≥ 50% dos meses com base) pega só as 24; mês a mês ou pelo holerite pega falsos.
  Multiplicar só a parte da hora (a base às vezes soma outra parcela). × 220 reprovado (13/24 a 80%+, 10 acima, R$ 88
  mil). **A conta do calculista está no holerite (Raíra cobrou: "não calcular" não é solução):** base = soma do
  valor das linhas de horas remuneradas (normais, feriados, banco de horas, bonificação de lay-off) + DSR pago
  (premissa 3.0). Conferido linha a linha: Atlas 0000747 (normal+DSR = gab), GM 1001791 (128+8+32 h = gab), Mercedes
  1001156 (linha NORMAL = horas do gab em 28/30 meses, sem DSR), RIP 0010337 (horas normais da ficha, sem DSR).
  P9b da periculosidade grava o percentual como quantidade, não horas. **Decidido 10/11: DSR fora (conservador)**;
  estimativa pelo calendário 9/24 a 80%+, mediana 74,8%; Atlas fica ~20% abaixo.
- **Horista: pipe completo (11/11, página v6 H6c9KWS5bkpYRQFAzkawBu):** a tabela PROV (cache caso_raw) já traz linhas
  com nome/quantidade/valor e salario_base do cabeçalho; o filtro (HOLE) grava o valor-hora do cabeçalho como BT090.
  Horista = cabeçalho R$ 1–100 na maioria dos meses (43/43; recusar 220/200/180/30; corte R$ 100 em vez dos 250 que
  a Raíra sugeriu). Jev "é horista?" nos 440: corte 0,9 acha 12/23 no teste; útil só com cabeçalho vazio (0100868,
  0000307). Base = só horas normais, sem DSR (19 peric.: mediana 0,83, 0 acima); mês sem holerite = valor-hora × p25
  das horas → 9/24 a 80%+, mediana 77,1%, 0 acima. HE/intervalo do horista também quebrados (BT090÷220): usar valor_hora.
  v8 da página (formato BT-2532/2533, pergunta por ajuste, "hoje × sugestão" literal): prompts de produção vêm de
  `.cache/raw__ft_lift_tb_agente.pkl` (HIST_SALARIAL_PROVENTOS v8 item 4 = origem do valor-hora; AGRUPAMENTO v5 copia;
  ROTEAMENTO v13 BT035 já ignora DSR → ajuste 5 só no manual; QUANTIFICADOR_MENSAIS v8 salario_base_exclusivo e "mês
  cheio"; PRINCIPAL_MENSAIS v6 regra 2.1 item 4). Código do back não existe nesta máquina (sem Repos, sem gh).
- **Caminho simples do horista (11/11, seção "Caminho simples" da mesma página, já compartilhada com a org):** um
  passo de código (cabeçalho R$ 1–100 + salario_base = soma das horas normais), sem prompt nem Jev. V1+ (lista +
  "Horas Normais Mensais"/"SAL.HORISTA" + descartar linha copiada idêntica) = 4/24 a 80%+, mediana 61,8%, 75% do R$
  que o pacote com Jev recupera; 0 verba acima, 88 meses acima (R$ 44,9 mil, quase todo gabarito fatiado 0011503 e
  1001716); controle 0. V2 (qtd × valor-hora ≈ valor) descartada: pega licença/13º/férias, 1/24. Pacote sem Jev 8/24.
  Leitura dos holerites duplicou linhas no 1000906 08/2018 (risco da soma).
- **Onde identificar o horista (10/11):** hoje nenhuma etapa identifica (só se a decisão escreve "horista", ex.
  Pirelli 0012558). Inicial testada com treino/teste (372 aptos, 39 horistas): acha 12/18 e 9/21, 40–53 falsos
  alarmes (jurisprudência, pedido de HE); ~14 iniciais só dão salário mensal → teto ~2/3. Recomendado P7. A Raíra
  pediu teste/treino da regra do P7 e lembrou que "horas normais" pode ser "salário normal" de mensalista (separar
  pela quantidade fixa 220/30 × variável). **Parado em 10/11 ~23h:** amostra 43 horistas + 43 mensalistas em
  scratchpad `amostra_holerite.json`; `baixa_holerites.py` (cat 12/13 dos recortes, 2 workers) falhou na 1ª chamada
  com "Access is denied" ao criar processo, e depois Bash/PowerShell também deram EPERM. Nada baixado. Retomar daí. Holerites: categoria 12/13 nos recortes do S3; GM é imagem. Código da esteira não está aqui.
- **Leva nova df_cnjs.csv (10–11/11, 7.413 CNJs, Downloads):** 807 já em `casos` (346 aptos); 6.606 nunca vistos,
  5.292 com recorte. Fila sem os 227 da lista 1 já buscados (os 671 da lista 1 sem P10 em 07/11 nunca tinham sido
  buscados e entraram). Triagem só pelo NOME das peças (ls recursivo do bucket, 418 mil objetos, saída em cp1252):
  2.429 sem peça de cálculo (íntegra para no TRT/TST → candidatos a pedir 1º grau, junto com 1.314 sem recorte);
  2.636 baixados: 570 tribunal, 58 indício de perito, 1.206 offline (**Raíra: offline fica fora**), 802 sem PJe-Calc.
  Peça "27-…-Cálculo" = 89% tribunal. Listas em `saidas/nova_leva_1011/`: `lista_esteira.txt` (974) e
  `lista_esteira_sem_aptos_mista.txt` (600: tira todo CNJ de `saidas/aptos_e_jornada_mista.csv`, inclusive os 346 aptos).
  Busca agora usa boto3 (aws.exe por peça travava a CPU de 4 núcleos); o filtro P10 da Nekt foi desligado com um
  `esteira.json` pré-gravado. Após o reinício de 11/11 o python.exe do uv 3.12 sumiu (quarentena?): `uv python install
  3.12 --reinstall`.
- Paralelismo alto no `aws` logo após o `sso login` corrompeu `~/.aws/cli/cache/*.json`; aquecer com uma chamada só.

**How to apply:** para outra lista, rodar `busca_calculos_s3.py` e depois `compara.py` sobre
`pecas_s3/_escolhidas/<rótulo>`. Ver [[s3-prod-integras-recortes]], [[confere-gabarito-repo]].
