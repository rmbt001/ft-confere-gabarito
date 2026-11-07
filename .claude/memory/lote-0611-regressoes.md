---
name: lote-0611-regressoes
description: "Lote de ajustes 05–06/11 (1.119 rerodados): alta apto valor 82%→75%; 6 regressões; pensão→BT059 é esperado, não regressão; página publicada"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-11-07T20:30:28.466Z
---

Lote 05/11 15h29 → 06/11 (rótulo r_lote_0611c): 1.119 processos com execução anterior + PJC. 163 melhoraram, 190 pioraram,
180 deixaram de ser aptos; alta apto valor de 82% para 75% com ≥80%. Painel novo: `desde_2026-11-03` (painel_0311.py).

Regressões (página https://claude.ai/artifact/Ni2ppAQMSB5M8RczWeMhG2, thread enviada à Raíra em 07/11):
1. BT081 sem compensar gratificação em 25 processos (código só compensa quando ele mesmo põe BT025 na base) — IA a mais R$ 1,67 mi.
2. Diferença com valor mensal fixado zerada pelo abatimento do pago (30 verbas, 27 processos; ex. 0011577-56 99,8%→−42%). Causa provável a recomposição do pago de 30/10; falta confirmar no código.
3. Jornada fixada + dias pelo cartão escrita como mista no P4 v14 → trava (25 de 31).
4. Base da HE vazia no ramo lista_da_decisao (6 processos).
5. Execução parada antes do cálculo (21), falha do modelo sem retry desde o Gemini.
6. Verba que deixou de ter valor (49), causas misturadas.

**Pensão virar BT059 NÃO é regressão** (Raíra, 07/11): é o código certo pela Premissa 14.0; os 64 que saíram só eram aptos por estarem em BT051.

Agente do erro rodado em 07/11 nos 81 apto valor da alta + 46 que saíram da alta (analises_prod_1510; antigas em _anteriores).

**Why:** base da próxima conversa com engenharia e da próxima rodada.
**How to apply:** ao medir a próxima rodada, comparar contra estes números e conferir se as 6 regressões sumiram. Ver [[relatorio-de-rodada-linear]], [[sobrecalculo-primeiro]].
