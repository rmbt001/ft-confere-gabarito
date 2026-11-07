---
name: sobrecalculo-primeiro
description: "Na avaliação de ajustes e rodadas, a IA calcular a mais (sobrecálculo) pesa mais que calcular a menos; ordenar e decidir por isso"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-10T13:20:14.222Z
---

Errar para menos é melhor que errar para mais. Em qualquer avaliação de ajuste, família ou rodada, mostrar o "IA a mais"
(sobrecálculo) separado do "IA a menos" e ordenar prioridades pelo sobrecálculo. Um passo que troca sobrecálculo por
subcálculo menor conta como melhora; um passo que cria sobrecálculo novo, mesmo pequeno, é regressão a fechar antes de promover.

**Why:** o crédito é comprado com base no cálculo; sobrecálculo vira prejuízo. A Raíra já tinha dito (08/10) que a
preocupação maior é com o que superestima, e reforçou em 10/10 ao ver o veredito da Família 1.

**How to apply:** tabelas de veredito com coluna "IA a mais" e "IA a menos"; "na dúvida, crédito menor" também vale para as
regras propostas. Ver [[premissas-de-calculo-bt]] e [[relatorio-de-rodada-linear]].
