---
name: s3-prod-integras-recortes
description: "Acesso só-leitura ao S3 de produção (perfil prod-s3, SSO): íntegras, PJC e cartão no ged-files-bucket-prod; íntegra recortada por peça no lift-fast-track-integras-recortes-prod"
metadata:
  type: reference
  modified: 2026-11-07
---

**Acesso** (testado em 07/11/2026): AWS CLI v2, perfil `prod-s3` (SSO, https://btinfra.awsapps.com/start,
us-east-1), conta 173745507412, papel `AWSReservedSSO_Temp_S3FastTrackIntegras`. Sessão expira em algumas horas:
erro de token → `aws sso login --profile prod-s3` (abre o navegador; quem confirma é a Raíra). Em PowerShell novo,
`$env:AWS_PROFILE = "prod-s3"` ou `--profile prod-s3` em cada comando.

**Só leitura e download** (ls, cp, sync do bucket para a máquina). Nunca apagar, sobrescrever nem enviar ao bucket.

**ged-files-bucket-prod** — pastas pelo CNJ **pontuado** (`0000001-96.2022.5.09.0661/`):
- `integra/` (~11,5 mil): a íntegra inteira num PDF só, `<CNJ>_bluetape.pdf` (pode passar de 90 MB).
- `pjc/` (~6,8 mil), `cartao_ponto/` (~3,5 mil), `outros/` (4).
- `negociacao/` (4 pastas com ID numérico) e `exportacoes/2026-09-29/`.

**lift-fast-track-integras-recortes-prod** (~11,4 mil) — pastas pelo CNJ **só dígitos** (20):
um PDF por peça, `<n>-<código>-<Tipo_da_Peça>.pdf` (ex. `1-135-Sentença.pdf`, `2-156-Acórdão.pdf`,
`5-002-Petição_Inicial.pdf`, `19-043-Cartão_de_PontoControle_de_Frequência.pdf`, `40-097-Apresentação_de_Laudo_Pericial.pdf`).
Pode haver várias peças do mesmo tipo (ex. 3 acórdãos). Acento aparece quebrado no terminal; é só exibição.

Conversão: tirar `-` e `.` do CNJ pontuado dá a pasta dos recortes (`_digitos`/`_formata` em `baixa_cnj.py`).

**Substitui o robô do TARS (Raíra, 08/11):** peças para o analista, o score ou o auditor vêm daqui, não do TARS —
mesmo recorte que a esteira leu, sem Chrome logado. Filtrar pela categoria do nome (1 sentença, 2 acórdão, 5 inicial,
21 decisão/embargos), converter para .txt com pdfplumber e apagar o PDF. Só não traz o 1º grau quando a íntegra é do
2º grau (ver [[calculos-da-integra-s3]]).

Ver [[pecas-so-decisao-e-inicial]], [[confere-gabarito-repo]].
