---
name: venv-onedrive-vm
description: "Os .venv dentro do OneDrive foram recriados na VM e sincronizaram de volta, quebrando as rodadas no PC (06/11); como consertar"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-11-07T14:22:18.206Z
---

Em 06/11/2026 nenhuma rodada rodava desde 04/11 8h: os `.venv` do app_validacao_Calculos, jev_testes e
ft_score_confianca tinham sido recriados na VM (pyvenv.cfg com `home = C:\Users\rmarotta\...`) dentro da pasta do
OneDrive, que sincronizou para o PC → "uv trampoline failed to spawn Python child process". Tarefas das 2h/4h/8h/15h
caíram com 0xC000013A sem escrever no log.

Conserto no PC: `UV_LINK_MODE=copy uv sync --frozen` em cada projeto (corrigir só o pyvenv.cfg não basta, o
python.exe do venv guarda o caminho). No app, pular os pacotes do Jupyter (`--no-install-package notebook jupyterlab
jupyterlab-widgets widgetsnbextension ...`): caminho longo demais no OneDrive. Robôs usam selenium/requests (ok).

Mesmo problema no `.git` do `bt-lift-fast-track-back` (visto em 07/11): o OneDrive criou cópias de conflito
`*-EC2AMAZ-4S7K07H` (nome da VM) em `.git\refs\remotes\...`, em 28/10. Elas fazem todo `git fetch` falhar com
"bad object refs/remotes/origin/...". Conserto: apagar só os `*-EC2AMAZ-4S7K07H` de `refs\remotes` (o fetch recria
as referências verdadeiras). Em `logs`, `info` e `objects` também sobraram cópias, que o git ignora.

**Why:** PC e VM no mesmo OneDrive escrevem os mesmos .venv e .git; um quebra o outro.
**How to apply:** se a rodada falhar com "uv trampoline", checar pyvenv.cfg. Na VM, rodar a partir de uma cópia local
(C:\ft\Repos), nunca `uv sync` dentro do OneDrive. Ver [[vm-pedido-infra]].
