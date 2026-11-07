---
name: agente-sempre-atualizado
description: "Regra de 15/10: caso que rodou de novo na esteira ganha nova análise do agente; nunca rodar agente junto com o gerar_telas do painel"
metadata:
  node_type: memory
  type: feedback
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-10-27T19:01:29.729Z
---

As análises do agente analista têm que estar sempre atualizadas: se um processo rodou de novo na esteira (nova execução na Nekt), roda o agente de novo nele. Exceção: se o painel (gerar_telas) estiver rodando, não dispara o agente junto — espera a Raíra dar a ordem de puxar o agente.

**Why:** o painel mostrava diagnóstico de uma execução antiga ao lado da tabela da execução nova (descasamentos como no 0000947-23.2023.5.10.0009); e agente + painel ao mesmo tempo deixam o gerar_telas muito lento.

Reforçado em 24/10 ("se um caso apto rodar de novo o agente tem que rodar em cima da nova rodada"): rodada.py considera defasada a análise com total da IA OU data da execução diferente. Em 20/10 apareceram 5 aptos que rodaram de novo no mesmo dia e com o mesmo total; reanalisados.
Em 26/10: o agente só roda DEPOIS das peças do caso (sentença/acórdão/embargos/inicial) estarem baixadas; análise sem peça não conta como atualizada. Ver [[madrugada-1710-rodadas]].
Em 27/10 (Raíra): o agente passa a rodar SÓ nos aptos de valor (IA entre R$ 50 e 200 mil), por causa do limite de uso (lotes de 100+ casos cortavam no meio). Lista: aptos de valor sem análise, com análise de outra execução, anterior à execução atual ou anterior às peças.
**How to apply:** depois de cada /fresh da Nekt, comparar data_processamento e total_ia da análise com a execução atual (o mesmo teste `_mesma_exec` do gerar_telas) e rodar o agente só nos casos APTOS (tem gabarito PJC, IA rodou e chegou ao P10, não travou) que mudaram ou não têm análise — nada de rodar em inapto ou FT travado. Se o gerar_telas estiver em andamento, avisar e aguardar o sinal. Ver [[madrugada-1510-rodadas]] e [[gerar-telas-lento]].
