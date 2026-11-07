---
name: rodada-1410-tarde
description: "Rodada de homol de 14/10 à tarde (ROTEAMENTO v19 + MENSAIS v15 prêmio, código HE 100%): 50 processos; mudanças funcionaram no componente, total caiu por 0010154 e 0001233"
metadata:
  node_type: memory
  type: project
  originSessionId: 58adf957-8cab-4526-b09c-9ebd4fcf3f3e
  modified: 2026-10-15T18:05:53.798Z
---

Rodada de homol de 14/10/2026, das 15h40 às 18h45 locais (no painel, 18–21h UTC): 50 processos com ROTEAMENTO v19 e MENSAIS v15 (prêmio/metas fora da base a partir de 11/2017) e com o código da v6 (commit c6d8ca94: a HE 100% paga abate só a BT011). O 7h20 é da v18 (13/10). Para 22 dos 50, a execução anterior era a noite (v17).

O "antes" vem do painel de homol de 14/10 13h (`validacao_calculos_antes_1510.json`). A régua é o PJC do painel de 15/10. Dados em `ft_arvore_divergencias/homol/_rodada_1410t.json`. A página é gerada por `ferramentas/gera_rodada_1410t_html.py` e publicada como artefato de72f19a-a16d-4115-a1b1-65fa3e8c7d89 ("Rodada 14/10 tarde").

**Achados (47 comparáveis):**
- Mediana 71,6 → 68,8%. A IA a mais foi de R$ 471 mil para R$ 680 mil, e R$ 146 mil disso vêm só de 0010154 (comissão paga deixou de ser abatida). A IA a menos subiu R$ 202 mil, dos quais R$ 157 mil vêm de 0001233 (a verba BT031 de diferença de prêmio some na leitura das decisões, em 2 de 4 execuções).
- **Abatimento da HE 100%:** o erro caiu 14% e 11 processos ficaram mais perto do PJC.
- **Prêmio:** cerca de R$ 42 mil a menos de sobrecálculo em 5 processos. Efeito colateral em 0000955: a ajuda de custo aluguel entrou na base. Em 0000409, o corte também alcançou meses antes de 11/2017.
- **7h20:** caiu de 15 para 6 processos, mas as horas quase não mudaram. Persiste em 0012343, 1001536, 1001164 e 0000955.
- A variação da IA com o mesmo prompt é grande (horas, horário, abatimento). Proposta: rodar 2× os processos que oscilaram.

**7h20 nas peças (15/10).** O agente analisou 0012343, 1001536, 1001164 e 0000955 com as peças. Os dossiês estão em `analises_homol_1410t/`.
- Nos quatro, o 7h20 está certo ou não muda o valor. Decisão: não mexer no limite.
- O excesso de horas vem de três causas:
  - frequência pelo cartão (1001536, 0000955);
  - jornada "da inicial" que não chega à esteira (1001164, "dois sábados ao mês");
  - intervalo suprimido só em parte do contrato e aplicado ao período todo (1001536).
- 0012343: a planilha do PJC não segue a sentença, que manda 7h20 escrito. A árvore marca "7h20 derivado" à toa quando a decisão traz o 7h20.
- A ajuda de custo em 0000955 veio do P7, que a classificou como BT082, e não da v15. A proposta é uma frase no MENSAIS 2.2 passo 2; há 13 processos com BT082.
- Em aberto para a Raíra: a BT024 de 1001164, um valor arbitrado de R$ 600 que o PJC abate.

**How to apply:** ao avaliar a próxima rodada, comparar com esta. Medir sempre no componente, porque vários processos "pioraram" no total só por perder a compensação. Ver [[relatorio-de-rodada-linear]], [[sobrecalculo-primeiro]] e [[agente-noite-0910-onde-parou]].
