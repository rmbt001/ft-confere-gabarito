---
name: rodar-em-lotes-de-500
description: "rodada longa (gerar_telas, busca no S3, Nekt) vai em lotes de 500 com saída gravada por lote; conferir o que já roda antes de estimar tempo"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-11-10T23:19:34.206Z
  originSessionId: 0d063384-33d1-4029-875f-1f7135335bd0
---

Rodada longa vai em **lotes de 500**, cada lote gravando a própria saída (ex.: `gerar_telas.py @lote_01.txt` e copiar o
`saidas/validacao_calculos.json` para `saidas/<rótulo>/lote_01/` antes do próximo). Pedido da Raíra em 10/11/2026.

**Why:** em 10/11 o `gerar_telas` dos 6.931 CNJs com P10 rodou 17 h, chegou a 73% e foi morto sem número nenhum,
porque ele guarda tudo na memória e só grava o JSON no fim. Ele ainda disputou os 4 núcleos da máquina com a busca no
S3 da leva nova; a estimativa que dei (1h–1h30) virou 3–4 h porque não conferi o que já estava rodando.

**How to apply:** antes de disparar ou estimar tempo, listar os `python.exe` vivos (`Get-CimInstance Win32_Process`) e
a carga da CPU (a máquina tem 4 núcleos). Dividir a lista em lotes de 500; resultado parcial sempre aproveitável. Ver
[[calculos-da-integra-s3]].
