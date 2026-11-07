---
name: cartao-ponto-codigo-back
description: "Leitura do código do back (21/10) sobre por que o cálculo pelo cartão sai a menos — motor antes do P9a, passthrough, abatimento incondicional; ainda não conferido em caso"
metadata:
  node_type: memory
  type: project
  originSessionId: 65294aac-f40b-43ce-aeee-cf666f5b8658
  modified: 2026-10-21T16:22:30.207Z
---

Em 21/10/2026 a Raíra pediu para avaliar no `bt-lift-fast-track-back` o que está errado no cálculo pelo cartão. Ela tirou o cartão do deck de perfil: "é método, não perfil". Um subagente leu o código e os prompts **do repositório**; nada foi conferido em caso ainda.

**Os três achados centrais:**
1. **O motor `cartao_ponto` roda entre o P4 e o P5, antes do P9a.** Lê só as verbas do P4, não a jornada.
   - `leitor_parametros_p4.py:96-100` descarta o limite semanal e usa sempre 44h. A jornada contratual cai no default de 8h.
   - A regra semanal (`extrapolacao_semanal_strategy`) só existe para a BT089, limitada a 8h/dia. BT001 e BT081 não têm regra semanal.
2. **O `aplicar_passthrough_cartao` do P9b** (`passthrough_cartao_utils.py:128-227`) troca a quantidade de toda verba que casa com o cartão, até só pelo código. Ignora `fonte_apuracao` e a quantidade fixada na sentença.
3. **`compensacao_familia_he_strategy.py:20-55` abate a HE paga sempre**, mesmo quando a LLM obedeceu a "não há o que deduzir".

**Outros pontos:**
- O P9a força `dupla_imputacao` (Súm. 109) na BT081 sem consultar a decisão (`P9a:491-499`). Isso provavelmente explica o gerente de banco a menos ([[perfil-reclamante-assertividade]]).
- BT009 (hora noturna reduzida) não é exportada.
- Não há piso zero de HE no P10a e o reflexo é calculado sobre o negativo.
- O intervalo é mínimo menos gozado, com corte na Reforma fixo no código. Com um só par de batidas, dá 60 min suprimidos todo dia.
- Mês sem cartão fica sem média. A trava `JORNADA_MISTA` é intencional ([[jornada-mista-nao-calculavel]]).

**Conferido em 21/10:**
- Código no origin/main de 21/10. O clone local estava em 02/10; usei `git fetch` sem pull.
- Prompts de produção que rodaram: P9a v11, P9b v7, P10a v5, P4 v8.
- Achados confirmados:
  - O limite semanal continua descartado. Em 14/10 só entraram a regra 12x36 e a separação da BT011.
  - O abatimento continua incondicional.
  - O passthrough não lê o P9a; é ele quem carimba `fonte_apuracao`.
  - P9a v11: BT081 com `dupla_imputacao` "obrigatória, em todo o período, sempre".
  - P9b v7: valor integral da BT025 "mesmo que a instrução traga uma janela, data ou condição".
  - P10a v5: negativo permitido, exceto BT081 com BT025.
- Nos casos:
  - 0000740: o P9a resolveu 33,6h semanais, mas a IA apurou 5–12 h/mês contra 14–44 do PJC.
  - 0020824: o P9a mandou para o cartão (fallback 8h/44h); a IA apurou 0,7–6 h/mês contra 17,12 fixadas. Abateu R$ 20,7 mil, o PJC 0, e o total ficou negativo.
  - BT081 nos aptos (21 verbas): IA R$ 39 mil × PJC R$ 606 mil. A IA abateu R$ 2,82 mi, o PJC R$ 0,89 mi. Casos com PJC 0: 0001305, 1001497, 1001947.

**How to apply:** os prompts do repositório podem estar à frente da produção ([[docs-do-fast-track]]). Antes de levar à Engenharia, confirmar cada item contra o texto da tabela de agentes e o JSON de um caso de exemplo.
