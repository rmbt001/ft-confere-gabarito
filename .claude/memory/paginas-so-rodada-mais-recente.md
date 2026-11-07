---
name: paginas-so-rodada-mais-recente
description: Páginas de divergência PJC × IA (hackathon e relatório de ajustes) só mostram processos da rodada mais recente; nada de dossiê de rodada anterior misturado
metadata:
  node_type: memory
  type: feedback
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-08T17:33:35.181Z
---

Os resultados apresentados (temas, valores, exemplos, casos relacionados, bloco do painel) devem vir só da rodada mais recente analisada — em 08/10/2026, os 62 processos rerodados em 07–08/10 (`ft_arvore_divergencias/rerodados_0710.txt`). Os 29 dossiês que não rerodaram ficam fora até rodarem de novo.

**Why:** a Raíra notou exemplos de rodadas anteriores misturados na página do hackathon; 15 exemplos de card, o bloco do painel e a seção de deduções vinham da janela 20/09–02/10.

**How to apply:** o filtro está em `temas_atuais.rerodados()` / `so_rodada_0710()` e em `painel_metodo.py`; ao gerar as páginas, varrer o HTML por CNJs fora da lista (deve dar zero). Ao rodar uma rodada nova, trocar o arquivo da lista e refazer os exemplos dos cards. Ver [[investigacao-divergencias-pjc-ia]] e [[ajustes-prompt-foco-unico-enxuto]].
