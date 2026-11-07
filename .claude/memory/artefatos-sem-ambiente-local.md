---
name: artefatos-sem-ambiente-local
description: "Páginas para o time não citam nada do ambiente local (pastas, scripts, arquivos, linha de prompt) e trazem a lista de CNJs completos em cada problema"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-14T13:21:26.821Z
---

As páginas (artefatos) que a Raíra compartilha não podem citar o nosso ambiente local:
- nomes de pasta (pacotes_homol, analises_homol_*, homol/...);
- scripts (.py) e arquivos (.json);
- "dossiê", subst W:;
- número de linha do texto exportado do prompt.

Pode citar o nome e a versão do prompt (ex.: ROTEAMENTO v18, seção 2.2), premissas e decisões.

Cada problema traz a **lista de CNJs completos**, visível no card e não só dentro de uma tabela recolhida. O CNJ vai sempre completo, nunca abreviado em 7 dígitos.

**Why:** pedido dela em 14/10/2026. Quem lê a página não tem acesso ao nosso ambiente e precisa achar os processos.

**How to apply:**
- Ao gerar qualquer página, trocar os CNJs curtos pelos completos.
- Antes de publicar, procurar por `.py`, `.json`, `homol/`, `pacotes`, `analises_`, `linha N`.
- Ver [[relatorio-de-rodada-linear]].
