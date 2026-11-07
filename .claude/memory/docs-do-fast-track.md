---
name: docs-do-fast-track
description: Onde estão os documentos do Fast Track — ler o arquivo certo em vez de varrer o código
metadata: 
  node_type: memory
  type: reference
  originSessionId: fe4b566a-8786-4a87-9180-1d27b6d0f396
  modified: 2026-10-15T17:47:44.177Z
---

Documentação do Fast Track, toda dentro de `Repos/bt-prod-apps/`. Ler o arquivo
certo antes de sair varrendo código:

| para | arquivo |
|---|---|
| visão do repositório e o que fica fora do Git | `bt-prod-apps/README.md` |
| arquitetura, árvore completa, contratos entre as peças, onde mora o estado | `bt-prod-apps/ft/README.md` |
| instalar, rodar, agendar, destravar quando quebra | `ft/app_validacao_Calculos/docs/operacao.md` |
| o que a página mede: as três medidas de acerto, as 8 telas, as camadas de valor | `ft/app_validacao_Calculos/docs/conceitos.md` |
| mapa do app de validação, arquivo por arquivo | `ft/app_validacao_Calculos/README.md` |
| o robô do Zeev | `ft/busca_pjcs/README.md` |
| transformar `.pjc` em tabelas | `ft/extrator_pjc/LEIA-ME.md` |
| agente analista (rodada de ponta a ponta, definição, premissas) | `ft/agente_analista/README.md` (no Git desde 15/10, commit c0a2e50) |

Fontes externas e autenticação: **Nekt** (token pessoal no `.env`, sem filtro no
servidor — cada leitura traz a tabela inteira, daí o cache de 12 h), **Zeev**
(SSO sem senha, Chrome headless) e **BomTrato** (token Bearer, API REST).

**Para ir à raiz de um erro de cálculo** (a Raíra pediu para não parar no sintoma):
- **Texto dos prompts de produção**: tabela Nekt `raw.ft_lift_tb_agente` (nome_agente, versao_agente,
  prompt), já em cache em `app_validacao_Calculos/.cache/raw__ft_lift_tb_agente.pkl`. Nomes: P1 DADOS_INICIAIS,
  P4 EDITOR_DECISOES, P7 HIST_SALARIAL_FILTRO, P8 CALC_CALENDARIO, P9a CALC_QUANTIFICADOR_ROTEAMENTO,
  P9b CALC_QUANTIFICADOR_MENSAIS, P10a CALC_PRINCIPAL_MENSAIS, P10b CALC_PRINCIPAL_RESCISORIAS.
- **Código do pipeline**: `Repos/bt-lift-fast-track-back` (uma pasta por etapa; ler o CLAUDE.md dele).
  Os `resources/prompts/*.txt` de lá são uma rodada MAIS NOVA que a de produção — para explicar uma
  rodada, use a versão da tabela de agentes, não o arquivo do repo.

**Cadeia das decisões (verificado no código em 06/10/2026):** a lambda `infos_decisoes` roda
INFOS_DECISOES → GLOSSARIO → reclassificação de HE em código e grava `tb_resultado_infos_decisoes_ia`
(é a tabela "DEF" que o painel baixa; o "P4 vN" do painel é a versão do GLOSSARIO). O P4 de fato
(EDITOR_DECISOES) grava `tb_resultado_editor_decisoes_ia`, que é o que o P9a lê. Na Nekt é
`raw/postgres_ft_lift_tb_resultado_editor_decisoes_ia` (colunas `verbas`, `jornada`; cada verba com
`id_verba`). Em 14/10/2026 deu 404 até a Raíra incluir a tabela no token — 404 da Nekt pode ser
falta de permissão no token. O painel passou a ler essa tabela (alias EDT) para nomear as verbas.

Ver [[projeto-fast-track-ft]].
