---
name: memoria-centralizada-em-repos
description: "Toda memória deve ser gravada na pasta Repos/.claude/memory, nunca espalhada por subprojeto"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fe4b566a-8786-4a87-9180-1d27b6d0f396
  modified: 2026-09-10T18:26:12.278Z
---

Toda memória — inclusive a que nasce trabalhando dentro de `bt-prod-apps/ft/` ou
de qualquer outro subprojeto — deve ser gravada em
`C:\Users\RaíraMarottaBastosVi\OneDrive - BT Créditos\Repos\.claude\memory\`.
Não criar `.claude/memory` dentro de subpastas.

**Why:** a Raíra pediu explicitamente memória única e centralizada, para não ter
que caçar contexto em várias pastas. O `Repos/.claude/settings.local.json` já
fixa isso com `autoMemoryDirectory` apontando para essa pasta.

**How to apply:** ao aprender algo em qualquer repositório abaixo de `Repos/`,
escrever o arquivo na pasta central e indexar no `MEMORY.md` da raiz. Se um
subprojeto tiver documentação própria (README, `docs/`), a memória aponta para
ela em vez de copiar o conteúdo — ver [[projeto-fast-track-ft]] e
[[docs-do-fast-track]].
