---
name: pecas-so-decisao-e-inicial
description: "Ao baixar peças no TARS para o agente, pegar só sentença, acórdão, embargos (Decisão) e petição inicial — nada de TRCT, ficha, holerite"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 58adf957-8cab-4526-b09c-9ebd4fcf3f3e
  modified: 2026-10-24T12:38:57.884Z
---

Em 15/10/2026, a Raíra questionou o robô do TARS: "por que você está baixando peças como TRCT, se só precisa de sentença, acórdão e inicial?". O filtro `TIPOS` de `ferramentas/tars_pecas.py` foi restrito a sentença, acórdão, embargos/decisão e inicial. As peças extras de 1001536, 1001164 e 0000955 foram apagadas.

Em 24/10 o filtro do repositório ainda incluía TRCT/ficha/holerite (o commit de 15/10 levou a versão larga); restrito de novo a `senten|acórd|embarg|decis|inicial`, a pedido dela. Os PDFs do robô agora vão para `Downloads\pecas_tars_robo\<data>`; 1.384 PDFs soltos em Downloads foram movidos para `pecas_tars_robo\soltos_ate_2410`.
**Why:** a análise do agente usa só as decisões e a inicial. O resto ocupa disco e tempo.

**How to apply:** não ampliar o filtro de novo sem pedido dela. Se um caso precisar de holerite ou ficha, perguntar antes. Ver [[premissas-de-calculo-bt]] e [[esteira-pecas-lidas-e-teste-focado]].
