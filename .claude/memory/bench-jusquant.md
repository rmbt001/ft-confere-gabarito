---
name: bench-jusquant
description: "Bench Fast Track × Jusquant (nov/2026) — amostra 120, onde ficam os arquivos, regras de comparação decididas e resultado com 45 casos"
metadata:
  node_type: memory
  type: project
  originSessionId: daec2377-0c96-4558-b3f7-c09f64109871
  modified: 2026-11-06T20:35:43.724Z
---

Bench da Raíra contra a Jusquant (IA de precificação), iniciado em 04/11/2026.

**Arquivos**
- A amostra está em `Repos/bench_jusquant/amostra_120_v2.csv`.
- Os arquivos devolvidos pelo fornecedor (pjc, PDF de cálculo e memória de cálculo) ficam em `bench_jusquant/pjcs_jusquant/`.
- A página é o artifact https://claude.ai/artifact/QnEtSSuGro14yqhLttLxJN, compartilhado com a org.

**Regras de comparação decididas com ela**
- Tudo em valor nominal, só as verbas da condenação; FGTS, INSS, IR, honorários e custas ficam fora.
- Dano moral, assédio e acidente ficam fora, porque o gabarito tem teto interno de R$ 5 mil (ver [[painel-correcoes-0810]]).
- Pareamento por família (tipo de verba + reflexo), somando as fatias do PJC (ver [[pareamento-he-uma-linha]]). Os 7 primeiros casos foram pareados à mão.
- L'Oréal (0020473): saem as linhas de intervalo que o acórdão excluiu.
- BK (0100615), decisão de 05/11: saem as férias em dobro e os reflexos em férias, com asterisco, porque o PJC usou o período do pedido e não o da sentença.
- Três medidas: composição (ausentes e inventadas), "erro a cada R$ 100" nas verbas certas e total (assertividade + erro somado). Assertividade negativa vira 0.

**Resultado em 06/11 (45 devolvidos, 41 comparáveis)**

| Medida (mediana) | Nós | Fornecedor |
|---|---|---|
| Assertividade | 76,0% | 44,3% |
| Erro somado a cada R$ 100 | 31,1 | 96,5 |

- O fornecedor inventa 100 verbas (R$ 1,05 mi) em 32 processos.
- Nos casos que calculamos mal (10), o total do fornecedor fica mais perto do gabarito: 51% contra 9%. Mesmo assim, o erro somado dele é maior.

**How to apply:** quando chegarem casos novos, rodar `forn.py`, depois `medidas_auto.py` e por fim `gera3.py`. Os scripts estão no scratchpad da sessão e se perdem com ela; se sumirem, recriar a partir desta descrição.
