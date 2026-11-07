---
name: projeto-fast-track-ft
description: O que é bt-prod-apps/ft e as amarrações que quebram em silêncio se alguém mexer sem saber
metadata: 
  node_type: memory
  type: project
  originSessionId: fe4b566a-8786-4a87-9180-1d27b6d0f396
  modified: 2026-09-10T18:26:34.610Z
---

`Repos/bt-prod-apps/ft/` é o **Fast Track (LIFT)**. Não é a esteira de cálculo:
é o que **mede se ela está acertando**. Três pastas, não intercambiáveis:

- `app_validacao_Calculos/` — compara verba a verba e publica `validacao_calculos.html`
- `busca_pjcs/` — robôs que buscam o cálculo de referência (gabarito) no Zeev e no BomTrato
- `extrator_pjc/` — abre o `.pjc` em tabelas para análise externa

**Why:** as armadilhas abaixo não geram erro na tela — a página só para de mudar
de data. Vale ter em contexto antes de propor qualquer refatoração ou mudança de
layout de pastas.

**How to apply:**

1. `app_validacao_Calculos` e `busca_pjcs` precisam continuar **pastas vizinhas**:
   `auto_pjc.py` resolve a outra por `Path(__file__).parent.parent`. Mover uma
   sem a outra quebra a busca em silêncio.
2. Os programas rodam **a partir da raiz do app**, nunca de dentro de `codigo/`.
3. O login do Zeev é SSO da Microsoft **sem senha** e só funciona dentro de uma
   sessão do Windows conectada — máquina dormindo ou sessão desconectada baixa
   zero gabarito, indistinguível de "dia sem processo novo".
4. Fila curta no robô costuma ser **sinal de saúde**, não de falha: busca vazia
   aplica backoff de 1, 2, 4, 8… até 30 dias.
5. Checagem diária de que tudo rodou: o `LastWriteTime` do `validacao_calculos.html`.
6. Antes do primeiro commit num clone: `git config core.hooksPath .githooks`.
   O hook recusa commit com token/credencial — existe porque já vazou token da
   Nekt em texto puro num notebook espelhado.

Detalhe completo (arquitetura, contratos, estado) em [[docs-do-fast-track]].
