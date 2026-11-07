---
name: apto-valor
description: "Categoria 'Apto valor' nos dois painéis (15/10): apto com valor da IA entre R$ 50 mil e R$ 200 mil; Placar mostra % ≥ 80% ao lado de cada mediana"
metadata:
  node_type: memory
  type: project
  originSessionId: 69b23582-ab8f-4216-8985-45c63e73ae9d
  modified: 2026-10-15T14:48:23.542Z
---

Em 15/10/2026, a pedido da Raíra, os painéis de produção e de homologação (só o template, sem gerar_telas) passaram a ter:
- **Apto valor:** apto com `quadro.total_ia` entre R$ 50 mil e R$ 200 mil. Aparece na célula de aptidão, num card próprio do Placar e como grupo na Elegibilidade; na ordenação da Lista vem antes dos outros aptos.
- **% de casos com assertividade ≥ 80% como número principal** em cada card do Placar, com a mediana embaixo. O time criticou a mediana, e ela pediu a troca em 15/10.

- **Topo do Placar enxuto** (ela achou poluído): duas tabelas lado a lado. Uma tem os recortes (aptos, apto valor, todos, só verbas que casam); a outra tem os aptos por faixa do score. As colunas são casos, na meta e mediana, com uma linha de nota embaixo.
- **Filtro "Score" (alta/média/baixa)** na barra do período, dentro de `casosFiltrados`: vale para todas as abas.
- **O período filtra pela data da última execução.** Na homologação, todos os casos são de 09–14/10, então o período não muda nada, e a tela avisa isso.

Escolhi o valor da IA, e não o PJC, porque é o único conhecido em produção. É o mesmo critério da matriz dos R$ 200k na Elegibilidade. Ela não confirmou essa escolha. Se pedir pelo valor do PJC, basta trocar `aptoValor` no template.

**Why:** recorte de produção que ela quer acompanhar dentro dos aptos.

**How to apply:** ao mexer nos templates, manter a definição igual nos dois apps. Ver [[painel-homol-nao-mexer-prod]].
