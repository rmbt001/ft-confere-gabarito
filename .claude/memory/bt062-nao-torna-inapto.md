---
name: bt062-nao-torna-inapto
description: "Decisão de 15/10/2026 — BT062 (honorários ao advogado da reclamada) deixou de tornar o caso não apto, nos painéis de produção e de homologação"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-10-15T11:24:06.631Z
---

Em 15/10/2026 ~8h30 a Raíra pediu: "a verba inelegível BT062 — Honorários devidos ao Advogado da Reclamada deve deixar de
tornar o caso não apto, tanto no de homol quanto no de prod". Feito: BT062 saiu de `INELEGIVEIS` no `gerar_telas.py` dos
dois apps (com comentário datado). A cópia da lista em `codigo/analises/relatorio_35_casos.py` ficou como estava (relatório antigo).

Efeito medido no painel de 15/10 3h: 357 casos tinham o BT062 como ÚNICO inelegível; 287 têm PJC e passam a aptos
(12 seguem fora da régua por erro de execução). A régua de aptos sai de ~160 para mais de 400 casos.

Os dossiês do agente da madrugada de 15/10 ainda tratam "inapto pelo BT062" como `politica`: isso era a regra da hora.

**Why:** pedido explícito dela, para os dois apps (exceção à regra de não mexer em prod por pedido de homol).
**How to apply:** não tratar BT062 como inelegível em análise, painel ou relatório daqui para a frente. Ver [[painel-homol-nao-mexer-prod]], [[madrugada-1510-rodadas]].
