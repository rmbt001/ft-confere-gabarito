---
name: confere-gabarito-repo
description: "Repo privado github.com/rmbt001/ft-confere-gabarito (07/11): compara IA × PDF do PJe-Calc por processo ou lote (~2.000) para rodar na VM"
metadata:
  node_type: memory
  type: reference
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-11-07T21:03:46.736Z
---

Repo: https://github.com/rmbt001/ft-confere-gabarito (local: `Repos\ft_confere_gabarito`). Feito em 07/11 para a VM.
- `compara.py <pasta de PDFs> [--rotulo X]`: CNJ do nome do arquivo/subpasta ou do texto do PDF; `.pjc` ignorado por
  padrão (é o PJC gerado pela esteira a partir da IA — dá 100%; `--pjc-gabarito` se for do calculista).
- `baixa_cnj.py`: lê cada tabela da Nekt uma vez via `DeltaTable.to_pyarrow_dataset().to_table(filter=...)` filtrando
  por id_processado de todos os CNJs (o `ingerir.py` do painel baixa ~15 GB inteiro). 4 casos ≈ 3 min.
- `codigo/`: cópia do motor do painel (gerar_telas + src) de 07/11, com o pareamento novo. Mudança no painel não
  chega lá sozinha.
- `.env` (NEKT_TOKEN), casos/, .cache/, saidas/ fora do Git.

**How to apply:** lote de gabaritos novos (Raíra fala em ~2.000) roda por aqui na VM, não pelo painel. Se o motor do
painel mudar, copiar de novo `gerar_telas.py` e `src/`. Ver [[vm-pedido-infra]], [[venv-onedrive-vm]].
