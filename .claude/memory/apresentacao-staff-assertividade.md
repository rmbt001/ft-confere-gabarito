---
name: apresentacao-staff-assertividade
description: "Apresentação de assertividade FT para CEO/COO/CCO (out/2026): mensagem 'já aptos para produção num conjunto de casos', meta 80%, só mudanças de código e prompt, slides, 1h"
metadata:
  node_type: memory
  type: project
  originSessionId: 69b23582-ab8f-4216-8985-45c63e73ae9d
  modified: 2026-10-15T15:34:39.653Z
---

Em 14/10/2026 a Raíra pediu o storytelling de uma apresentação de assertividade do Fast Track para a staff (CEO, COO, CCO): slides, 1 hora no total.

- **Mensagem central:** a meta para entrar em produção é 80% de assertividade, e já estamos aptos para um conjunto de casos (recorte pelo score de confiança, ver [[score-confianca-calculo]]).
- **O que fizemos = só código e prompt.** Não citar as correções do painel de medição ([[painel-correcoes-0810]]) como avanço. Não tirar pedidos improcedentes nem nada da conta. Comparação apenas do que é comparável (mesmos casos, mesma régua dos dois lados).
- **Sem slide de pedidos/decisões para a staff.**
- **"Onde falta":** frequência pelo cartão de ponto nas verbas de jornada prefixada ([[frequencia-cartao-jornada-fixada]]) e verba com saldo negativo puxando o total.
- **Anexo:** diagnóstico por caso com a categoria do problema (premissa não endereçada / erro da IA / gabarito questionável).

- **Números provisórios:** tudo (funil, comparativo, faixas do score, anexo) será revisado com os novos casos que rodarem em produção. Montar o deck gerado a partir dos dados da rodada, para atualizar sem refazer à mão.

- **Deck v1 (14/10):** https://claude.ai/code/artifact/d176cc81-0cd9-410e-a7b0-327951a89932. Gerador `ft_arvore_divergencias/ferramentas/gera_apresentacao_staff.py` (+ `apresentacao_staff.css/.js`). A régua é o PJC do painel de produção de hoje para todos os momentos. O "antes" vem do retrato `historico/validacao_calculos_20261005_1324.json` (estado de 02/10).
- **Achado:** o ganho de 62% para 80% de mediana (181 processos) veio dos prompts de 06/10, que já estão em produção. O pacote do hackathon em homologação fica em 74% nos mesmos processos, por causa de três regressões.
- **Pergunta dos 80% (em aberto):** a faixa alta do score tem mediana de 88%, mas só 68% dos processos dela ficam em 80% ou mais.

- **Feedback de 14/10 sobre a v1 ("pouco executiva"):**
  - Explicar o que a conta 1 − |IA − PJC| ÷ PJC significa na prática: 80% quer dizer até 20% para mais ou para menos, e nota negativa quer dizer mais que o dobro.
  - Mostrar a faixa de nota negativa nos gráficos de distribuição.
  - No gráfico por verba, só verbas elegíveis (diferença salarial não é elegível).
  - Uma conclusão por slide, com pouco texto.
  - A fórmula aparece como erro relativo, (estimado − real) ÷ real, e quanto mais perto de 0, melhor.
  - Na acurácia por verba entram só verbas principais (sem reflexos), as mais frequentes (10+ processos).
  - Trazer métricas de desvio explicadas: mediana × média, média aparada, erro com sinal, nota negativa e soma da carteira.
  - "Calculado a mais" é o excesso somado, não o saldo. O saldo aparece ao lado.
  - **Não falar de regressão no deck da staff.**
  - **"Hoje" é a versão do hackathon (homologação), não a produção de 07–08/10.** Os ajustes mostrados são só os do hackathon. O score e o mês negativo são medidos nessa versão.
  - O funil e a acurácia por verba usam o recorte **desde 03/08/2026**.
  - Mensagem do funil: os aptos dão a nota do total, que é a régua de produção. Todos os calculados com gabarito, inelegíveis inclusive, entram na nota verba a verba. Não citar o BT062 isolado.
  - Ordem do deck: medir → funil → 02/10 → como achamos o que mexer → principais ajustes → resultado. O resumo fica no fim.
  - Não chamar de "hackathon": usar "principais ajustes" e "versão ajustada".
  - Gráfico por verba: versões anteriores (de 03/08 a 01/10) × versão atual de produção (desde 02/10), em gráfico de pontos ligados. Ela gostou desse formato.
  - O score é apresentado pela primeira vez à staff. Explicar mais: a ideia em 3 passos e a nota típica com e sem cada sinal.
  - Métricas viram perguntas simples. A tabela de métricas não ficou intuitiva.
  - O vocabulário é "assertividade". "Nota" confundiu.
  - Segmentar o erro que sobra em: erro da IA, premissa não endereçada, gabarito questionável, decisão de negócio (teto do dano moral, prescrição), documento, medição e em investigação. Fonte: as análises do agente da rodada mais recente de cada processo (rodada da noite 09→10/10 ou rodada de 13/10).
  - **Narrativa fechada em 14/10, em 5 atos com contracapa:**
    1. A régua
    2. De onde partimos
    3. O que fizemos e o que mudou
    4. O que ainda falta
    5. Como entramos em produção, com o score no fim
  - **Duas fontes, com etiqueta em cada slide:**
    - produção desde 03/08, só no funil;
    - os mesmos 223 processos 02/10 × versão ajustada (79 aptos) para todo o resto, inclusive verbas e score.
  - Mostrar a assertividade em todos os valores e no recorte até R$ 200 mil. Score para todos e para os aptos.
  - **Regra fixa: só cálculo de Risco Real entra em qualquer recorte.** Usar o campo `tipo_calculo`; quando vier vazio, conta como Risco Real.
  - "O erro que sobra" e "Por que a IA erra" usam só a última rodada de homologação (13/10), porque vários problemas já foram corrigidos. O caso de R$ 1 mi (0020906) é verba de sindicato ou terceiros.
  - Pensar no desconto da proposta: a proposta é a IA × (1 − desconto). A métrica é "propostas acima do real". O desconto cobre o processo típico, mas não a cauda.
  - O gabarito diverge entre o painel de produção e o de homologação em 26 processos. Exemplo: 0001517-95.2025.5.09.0872, em que a IA bate com o gabarito de homologação e o deck acusava R$ 190 mil a mais. Conferir esses 26 antes de fechar os números.
  - Usar linguagem acessível: "nota do processo típico", "quanto a IA erra, para mais ou para menos". Nada de "distância mediana". O pacote do hackathon aparece só com o que funciona, sem a mediana de homologação e sem "piorou" no anexo.

- **Cópia com dados de 15/10** (link d706cfcb-8aa4-4dc9-9872-b46a44d41c72; a v18 fica intacta em d176cc81):
  - mantém 02/10 como "antes";
  - usa o painel de produção e o de homologação atuais e o score de homologação das 10h08 (só dados estruturados);
  - **apto vem da mesma execução medida (homologação), e o score só roda em aptos**: decisão dela em 15/10.
  - O gerador escolhe tudo isso por variáveis de ambiente (DECK_PROD, DECK_HOMOL, DECK_SCORE_SRC, DECK_APTO_DE=homol, DECK_SCORE_SO_APTOS). Sem elas, reproduz a v18.
- **Crítica do time em 15/10:** a apresentação ficou pouco intuitiva, e a mediana foi criticada. Na cópia (DECK_SCORE_PAINEL=1) o score virou uma sequência:
  - processos rodados → com cálculo → aptos → apto valor;
  - aptos e apto valor por faixa do score;
  - % na meta (≥ 80%) por faixa.
  - Tudo no recorte do painel de homologação, para bater com o que o time abre: 271 → 234 → 102 → 37; na faixa alta, 45 aptos com 76% na meta.
  - O slide antigo do score, no recorte comparável com 02/10, sai nessa versão.
  - A Lista de casos da homologação abre em "aptos validáveis + score alta + melhor primeiro".
- **Mudança posterior em 15/10:** o funil e o score saíram do deck e viraram o **Anexo A**, uma página própria (link 84c50a99-b4f0-4b20-b556-27c6e3a72699, gerador `ferramentas/gera_anexo_funil_score.py`).
  - O anexo segue o estilo dos slides do board: migalha no topo, título "Anexo A:" em negrito + resto regular, caixa de texto com borda vermelha à esquerda, tabela de cabeçalho rosado, fonte no rodapé e número da página.
  - Tem mais texto, porque ela vai enviar o anexo.
  - **Não chamar de "meta"** o ≥ 80% por processo (a meta não era isso). Também não usar "dentro da margem": ela pediu o termo explícito, **"X processos com assertividade de 80% ou mais"**, ou "abaixo de 80%". Não precisa mais gerar PDF.
- **Anexo reescrito em 15/10** a pedido da pessoa de produto ("não está fluido"). Público: quem não acompanha o problema. Formato:
  - uma ideia por slide, com título em forma de pergunta;
  - uma frase de resumo e poucos bullets curtos;
  - os números ficam no visual, não no texto;
  - pode ficar longo (15 páginas).
  - Ordem: o que responde → termos → como medimos (régua do exemplo de R$ 100 mil) → funil → por que não apto → faixa de valor → score em 3 passos → sinais → divisão em faixas → acerto por faixa (cartões) → na prática (grade dos 37) → os 4 fora → ponte 44 → 45 → 19 → limites.
- **Pacote de 15/10:** fica em `ft_arvore_divergencias/pacote_assertividade_1510/`.
  - Contém a apresentação v18 em HTML e PDF, o anexo em HTML e PDF, e o painel de homologação.
  - Os PDFs saem do Edge sem interface (`--headless --print-to-pdf`), porque o visualizador de artefato bloqueia a impressão. O anexo tem `@page` em 16:9.
  - A Lista do painel de homologação ganhou duas opções em "Mostrar": "Apto valor" (37) e "Apresentação: os 44 aptos da faixa alta". A segunda usa uma lista fixa de CNJs no template.
  - O anexo tem a ponte 44 → 45 → 19 e as causas dos 4 processos da faixa alta fora da margem: 1 erro da IA, 1 gabarito, 1 documento, 1 regra da casa.
- **Achado de 15/10:** o apto depende de a IA identificar as verbas. Pensão (BT059) lida como dano material, ou pensão não identificada, faz o processo passar por apto. Exemplos: 1000702-41.2022.5.02.0465 em produção e 0020277-96.2024.5.04.0733 em homologação. O score não pega verba que a IA não viu.

**Why:** a Raíra corrigiu um primeiro roteiro que misturava ajustes de medição com ajustes da IA e pedia decisões à staff.

**How to apply:** ao montar ou revisar o deck, manter só as mudanças de esteira (código e prompt) e abrir pela mensagem "aptos para um conjunto de casos". Ver [[sobrecalculo-primeiro]] e [[paginas-so-rodada-mais-recente]].
