---
name: pausa-score-agente-2910
description: "Desde 29/10 17h as rodadas só pegam PJC e calculam assertividade; sem agente do erro, score, Jev e auditor enquanto existir sem_score.flag"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-10-30T23:39:09.027Z
---

Em 29/10/2026 a Raíra pediu: rodar só PJC + assertividade; confiança fica "a calcular" no painel. Nada de agente do erro, score (aplica_score_jev), Jev nem auditor "por ora".

**Why:** decisão dela enquanto o fluxo migra para a VM; o score/agente voltam quando ela pedir.

**How to apply:** `%LOCALAPPDATA%\bt_auto_pjc\sem_score.flag` faz o rodada_v2.ps1 pular score e rodada.py. Enquanto ela existir, o pós-rodada (cron) NÃO lança agente, peças, Jev nem auditor: só confere a rodada e avisa erro. Para voltar, apagar a flag, só com ordem dela.
**30/10 (VM):** com sem_score.flag o rodada_v2.ps1 já fecha sozinho: entrada_funil → painel_sem_score (23/10); e,
se existir `score_na_rodada.flag`, roda score_2310.ps1 (peças+Jev+score) e score_2310.ps1 -auditor (OpenRouter, só
aptos na alta). A flag do score é para a VM; no PC ela não existe (o pós-rodada do Claude fecha). A busca de PJC
re-tenta os não achados 1×/dia, até 300 por rodada (busca_pjc_recorte.py). Agente do erro segue fora (precisa do Claude).
Fechar cada rodada na pausa: `bt_auto_pjc\entrada_funil.py` (venv do app; funil começa nos CNJs que rodaram na esteira, pedido de 29/10) e depois `painel_sem_score.py mudou_<rotulo>.txt` (venv do jev_testes, cwd jev_testes) → painel desde_2026-10-23. Rodar fora de hora = rodada_v2.ps1, nunca ingerir.py solto ([[madrugada-1710-rodadas]]).
