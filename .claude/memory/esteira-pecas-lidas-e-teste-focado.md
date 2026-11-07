---
name: esteira-pecas-lidas-e-teste-focado
description: "A esteira só lê sentença, acórdão, embargos, petição inicial e ficha de registro (nunca norma coletiva); teste de ajuste mede só o campo que o passo muda"
metadata:
  node_type: memory
  type: project
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-09T17:42:24.511Z
---

A esteira do Fast Track lê só sentença, acórdão, embargos de declaração, petição inicial e ficha de registro. Não lê norma
coletiva nem despachos. Regra ou sugestão de prompt não pode depender de norma, convenção ou especificidade de categoria.

O teste de um ajuste (prompt "Testar" do hackathon/sala) mede só o ponto de medida do passo: o campo que ele altera contra o
equivalente no PJC (dedução → valor deduzido; base → base do mês; quebra → verbas criadas). Para na etapa que produz esse campo.
Não calcula verba inteira, reflexos nem total, porque carregam erros de outras famílias.

O gabarito do teste é sempre o .pjc (verbas, segmentação das horas, bases, valores), nunca a saída de homol: em 09/10 um
teste só avaliou as verbas que homol já tinha identificado como BT081, sem checar se a segmentação das HE batia com o .pjc.

**Why:** em 09/10/2026 o teste da dedução no 0101497 recalculou tudo e o veredito ficou poluído pelo T04 (base sem salário).
A Raíra corrigiu: "se estou testando a dedução, só teria precisado ir no valor a ser deduzido".

**How to apply:** ao escrever prompts de teste ou sugestões, ancorar em campo e peça que a esteira tem. Erro de outra família
fica registrado em uma linha, sem mudar o veredito. Ver [[relatorio-de-rodada-linear]] e [[premissas-de-calculo-bt]].
