---
name: auditor-oscila
description: "Auditor de sobrecálculo (Opus 5.5, temp 0) oscila: em 12 de 20 casos o \"alto\" não se repetiu em 3 rodadas; Raíra decidiu deixar como está (07/11)"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-11-07T20:30:35.397Z
---

Teste de 07/11: os 20 casos do lote que caíram da alta para a baixa só pelo auditor foram rodados mais 2× com a mesma
entrada (pastas `ft_agente_auditor/gemini/rodada_claude-opus-5.5__auditor_sobrecalculo_rep1/_rep2`, não entram no score).
Resultado: "alto" 3/3 em 8, 2/3 em 4, 1/3 em 8. Dos 8 consistentes, metade está com IA a menos ou perto do PJC (premissas
que nem esteira nem PJC aplicam: 18.0, art. 62, gratificação de caixa). Regra "2 de 3" devolveria 8 à alta, ~3× o custo.

Também: no score, um único risco "a mais" (auditor, HE em alguns dias, base que salta) leva direto à baixa; riscos "a menos"
sozinhos (gratificação, verba zerada) tiram da alta. Regra sem_base conta reembolso de combustível (BT072, componentes_fixos)
como competência sem salário (ex. 0001092-79, 99,8% na média). Nada disso foi alterado.

Gasto OpenRouter após o teste: US$ 254,03 de 300.

**Why:** Raíra disse "vamos deixar assim por ora" — não mexer no auditor nem no score sem pedido.
**How to apply:** se ela retomar, opções prontas: 2 de 3 no auditor (~US$ 35 para a alta toda), risco "a mais" isolado → média, excluir BT072/BT076 do sem_base, conferir por que a trava 17.2 não pegou 0001092-79 (terceirizada enquadrada como bancário). Ver [[auditor-openrouter-2710]], [[score-confianca-calculo]].
