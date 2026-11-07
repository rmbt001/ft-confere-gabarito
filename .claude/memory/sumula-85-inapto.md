---
name: sumula-85-inapto
description: "Decisão de 26/10: processo com Súmula 85 aplicada (campo compensacao_jornada do editor de decisões v12) é inapto"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-10-26T17:47:38.265Z
---

Em 26/10/2026 a Raíra decidiu: **Súmula 85 aplicada = processo não apto.** O editor de decisões v12 (23/10 15h06) marca por verba de horas o campo `compensacao_jornada` (sumula_85_aplicada, sumula_85_inaplicavel, art_59b_aplicado, acordo_compensacao, so_adicional_horas_compensadas, banco_de_horas, compensacao_de_valores); pelo prompt, HE com sumula_85_aplicada / art_59b / acordo / só adicional sai do cálculo automático.

Medido em 26/10: 72 processos com sumula_85_aplicada na última execução, 57 no painel cópia, só 3 aptos (os demais já caíam por verba não calculada). Ainda não aplicado no painel (aguardando onde aplicar).

**Why:** com a súmula aplicada a hora extra depende de compensação que a esteira não apura; o caso não é calculável no automático.
**How to apply:** ao montar aptidão no painel, ler `compensacao_jornada` da saída do editor (tabela postgres_ft_lift_tb_resultado_editor_decisoes_ia, coluna `verbas`, texto em repr Python). Ver [[premissas-de-calculo-bt]], [[frequencia-cartao-jornada-fixada]].
