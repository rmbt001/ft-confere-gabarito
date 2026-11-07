---
name: madrugada-1510-rodadas
description: "Rodadas da madrugada de 15/10/2026 (1h, 3h, 6h) — Nekt /fresh + painel + agente analista nos comparáveis de 14/10 em diante + artefato após as 6h; como retomar se a sessão cair"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-10-15T17:47:46.939Z
---

Pedido da Raíra em 14/10/2026 ~23h. Se a sessão cair ou o limite de uso acabar, ela quer que eu **retome assim que a sessão voltar**, sem perguntar.

**O que roda sozinho (Agendador do Windows, não depende do Claude):** tarefas `BT painel validacao 01h/03h/06h 15-10`
executam `%LOCALAPPDATA%\bt_auto_pjc\painel_madrugada.ps1` = `atualiza_painel.bat /fresh` (Nekt rebaixada + painel).
Log: `%LOCALAPPDATA%\bt_auto_pjc\painel_madrugada.log` (linha "OK em N min" ao fim). Foto do painel de cada rodada:
`%LOCALAPPDATA%\bt_auto_pjc\painel_20261015_<HH>h.json`. Cada rodada leva ~1h05.

**O que é meu, depois de cada painel (em `Repos/ft_arvore_divergencias`):**
1. `ferramentas/rodada_madrugada.py <rotulo>` (rotulo r01h/r03h/r06h; python do venv do app). Lê o painel de `saidas/`
   — rodar ANTES que a rodada seguinte regenere o painel (janela: fim da rodada até ~1h depois do início da próxima).
   Alvo = comparável (LIFT + PJC) **e** data_processamento ≥ 2026-10-14 **e** sem dossiê em `analises_prod_1510/`.
   Sem gabarito não roda agente (regra dela). Grava `prod_1510/<rotulo>_cnjs.json` e `_arvore.txt`, monta `pacotes/`.
2. Se a lista não for vazia: Workflow `ferramentas/wf_analista_prod_1510.js` com args
   `{cnjs, arvore, rotulo}`. Dossiês em `analises_prod_1510/<CNJ>.json/.md`. Retomar = relançar só os sem dossiê.
3. Depois da rodada das 6h e do último workflow: artefato consolidado (formato de [[relatorio-de-rodada-linear]],
   [[sobrecalculo-primeiro]], [[artefatos-sem-ambiente-local]]).

Em 14/10 20h48 só 1 comparável era de 14/10+; 18 processados de 14/10+ estavam sem PJC (sem agente).
**Andamento:** r01h — painel OK às 2h52 (112 min, não ~1h); 72 alvos (33 sem pjc.txt); workflow wf_79423461-750 lançado ~3h17 e concluído às 3h54: 72/72 dossiês, 0 erros.
r03h — painel OK às 4h39 (99 min); 103 comparáveis desde 14/10, 31 alvos novos (16 sem pjc.txt); workflow wf_247a925a-593 lançado ~5h e concluído: 31/31, 0 erros (103 dossiês no total).
r06h — a Nekt foi rebaixada às 6h21, mas o gerar_telas foi MORTO (tarefa 0xC000013A) por outra sessão do Claude que
mexeu no gerar_telas de prod às 7h20 e relançou o painel às 7h53. Não há foto 06h nem "OK" no log. Fazer r06h quando o
saidas/validacao_calculos.json for regravado depois das 7h53 (o painel dessa outra sessão usa a Nekt das 6h).
A geração das 7h53 também morreu (a outra sessão reverteu prod ao commit local 8052792, que tem o fix do NaN).
Às ~8h05 relancei o gerar_telas de prod (sem /fresh, Nekt das 6h); ao terminar grava a foto 06h e o "OK" no log.
A Raíra cobrou (com razão) eu ter esperado o painel: o agente não precisa do painel inteiro. Gerei só os 44 executados
depois das 3h numa pasta isolada (%LOCALAPPDATA%\bt_auto_pjc\painel_r06h, junctions para codigo/.cache/casos, saidas própria)
em 20 s; 36 comparáveis → pacotes → workflow wf_4f9981ca-053 lançado ~8h20 (r06h_cnjs.json gravado).
**Lição:** quando uma etapa da qual o agente depende falhar, avisar na hora e propor o atalho (gerar só os CNJs novos).
19 dos 36 dossiês r06h saíram "só pela árvore" (eu passei a árvore r03h, que não tinha esses casos); refeitos (wf_5ada1d64-b86)
com aviso explícito do pacote e `arvore_caso`. **Concluído ~9h05:** 139 dossiês (1h 72, 3h 31, 6h 36); artefato
"Madrugada de 15/10 no LIFT" publicado (claude.ai/code/artifact/56f047c4-80c7-4ba1-bd79-3ab6a1b574ad), gerado por
`ferramentas/gera_madrugada_1510_html.py`. Cron da madrugada apagado.
**15/10 ~14h45:** o fluxo virou código no repositório: `bt-prod-apps/ft/agente_analista/` (rodada.py, painel_parcial.py,
wf_analista.js genérico, agente_para_painel.py, relatorio_rodada.py, caminhos.py). Os originais em ft_arvore_divergencias/ferramentas
continuam lá, mas para rodadas novas usar os do repositório; listas de rodada agora em <trabalho>/rodadas/.
**Depois do artefato (pedido dela, 15/10 ~7h20):** baixar o acórdão de 0011281-57.2023.5.15.0113 direto no TARS (NÃO ir ao Zeev)
e rerodar o agente nesse caso — intervalo 30 min (IA) × 20 min (PJC) e divisor 200 × 220 dependem do acórdão.
Ela NÃO quer o auto_pjc nas rodadas: o agente roda no que já for comparável quando a Nekt trouxer.
Pacotes sem PDF do PJC não têm pjc.txt (casos do PV/Milena vindos só com .pjc): o agente usa o PJC estruturado.

**Why:** a sessão e os crons in-session somem num reinício; o Agendador do Windows não.
**How to apply:** ao voltar, ler o log do painel, ver quais `<rotulo>_cnjs.json` existem e quais dossiês faltam, e seguir do primeiro passo pendente.
