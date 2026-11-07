---
name: lote-0710-fila-parou
description: "Lote de 07/10/2026 — a fila parou de puxar às 17:12 UTC e 54 execuções nunca rodaram; assertividade mediana 55,3% → 66,1%"
metadata:
  node_type: memory
  type: project
  originSessionId: fe4b566a-8786-4a87-9180-1d27b6d0f396
  modified: 2026-10-08T10:44:59.093Z
---

No lote de **07/10/2026** foram criadas 294 execuções (290 CNJs), das quais 189 eram
re-rodada de caso que já tinha gabarito e só 5 eram CNJ novo. Chegaram ao P10a **194**.
Das 100 restantes: 32 ERRO (28 em `CARTAO_PONTO`, sendo 23 por
*"Jornada mista documental e fixada não é apurável"*), 8 EM_ANDAMENTO, 1 marcada
FINALIZADO em `HIST_SALARIAL_FILTRO` sem linha no P10a — e **54 que nunca iniciaram**.

As 54 são o achado: o orquestrador aceitou enfileirar até 21:22 UTC mas parou de puxar
trabalho às **17:12 UTC**. O corte é limpo — nenhuma execução criada depois disso tem
cálculo *nem* trilha de status. Como não aparecem no P10a, não é atraso de sync da Nekt
(ver [[projeto-fast-track-ft]]): é fila parada, e são re-disparo direto sem investigação.

Resultado medido em 102 casos comparáveis: assertividade mediana **55,3% → 66,1%**,
delta mediano +0,0 p.p. mas delta **médio −139,3 p.p.** — a média está dominada por
poucos casos que despencaram, então aqui a mediana é a leitura honesta e a média serve
só para apontar outliers. Faixa ≥95% subiu de 13 para 21 casos; <50% caiu de 48 para 45.
Sobrecalculado 56→50, subcalculado 39→45. Apenas 1 perda silenciosa.

**Por quê:** o mesmo padrão de hora extra / cartão de ponto que derrubou o lote anterior
([[lote-0909-regressao-hora-extra]]) reaparece aqui como recusa declarada no
`CARTAO_PONTO`, não como quebra — o pipeline viu jornada documental e fixada juntas e
se negou a apurar.

**Como aplicar:** ao avaliar qualquer lote, conferir sempre três contagens separadas
antes de concluir qualquer coisa — execuções criadas (PROC), execuções que chegaram ao
cálculo (P10a) e execuções com trilha (STATUS). E nunca filtrar P10a por data sem
lembrar que a data da linha é *quando o cálculo saiu*, em UTC: o que termina depois das
21h locais cai no dia seguinte e some do filtro. Foi isso que fez o lote parecer ter
107 cálculos quando tinha 194.
