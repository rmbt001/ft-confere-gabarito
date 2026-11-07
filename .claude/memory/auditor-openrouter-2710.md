---
name: auditor-openrouter-2710
description: "Agente auditor via OpenRouter (27–28/10): prompt de 3 níveis só na alta do apto valor (78→87%); sim/não e média testados e descartados; achados de premissa"
metadata:
  node_type: memory
  type: project
  originSessionId: 8c35cfc5-1235-4a09-9388-f249c033065c
  modified: 2026-10-30T16:02:50.177Z
---

Testes de 27–28/10/2026 em ft_agente_auditor/gemini/ (OpenRouter, teto US$ 100, gasto US$ 88,50; teto US$ 300 desde
30/10, ver [[score-estado-3010]]). Só casos **aptos**
(a Raíra corrigiu: gabaritos de 18/10 tinham inaptos), arquivo sem CNJ e com o reclamante anonimizado, gabarito do painel
atual (28/10, depois da correção PJC × PDF, ver [[pjc-pdf-calculos-diferentes]]).

**Versão escolhida**: `instrucoes/auditor_sobrecalculo.md` — só risco de sobrecálculo (cessão de crédito; a menos não
interessa), premissas do manual entram, sem estimar R$, três níveis (alto/médio/baixo); **só "alto" tira o caso da
alta**. Opus 5.5, ~US$ 0,19/caso, só na alta do apto valor. Resultado em 28/10: alta do apto valor 81 casos 78% → 67
casos 87% com 80%+, a mais 15 → 8; alta total 181 (75%) → 167 (78%).

Descartados (medidos): prompt antigo com R$ e erro dos dois lados (marcava bons por erro a menos, valores ~2× a
diferença real); sim/não (sem o "médio" o agente diz sim a 23 bons); Jev nas perguntas do "não verificável" (liberou
os piores); Gemini 3.1 Pro (pega menos a mais) e Flash; agente na média com os motivos do score (sobe 5 bons e 2 ruins
de 44 — não compensa).

**Why:** a Raíra quer só flagar sobrecálculo e achou 3 níveis complexo; o 3 níveis vence porque o "médio" absorve a
dúvida. **How to apply:** o rótulo para o usuário é binário (alto = sobrecálculo), a IA mantém 3 níveis.

Premissa (manual 04.2026.02), conferida com a Raíra em 28/10: item 18.0 restringe a **natureza salarial** do prêmio
pós-2017 (reflexos/integração), não o prêmio fixado em si (0010369 está certo na IA; a regra restr_premio_2017 do score
restringe a verba inteira — erro conhecido, não corrigido); SRV é meta; 19.6 bancário: reflexos de comissão não apuram
(lista de 20 casos com comissão/SRV na base de HE levada aos calculistas); art. 62 com controle indireto = Tema 300
restrito. Restrita: simulei corrigir prêmio/pensão parcela única/Adobe/RMNR — 19 saem e a alta piora (75→74%); ela
decidiu deixar a restrita como está por ora. Turno ininterrupto talvez não seja restrição (manual manda seguir CCT) —
decisão pendente.
