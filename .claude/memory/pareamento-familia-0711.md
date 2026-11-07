---
name: pareamento-familia-0711
description: "Correção do pareamento IA×PJC no gerar_telas (07/11, ok da Raíra): vetos de família, HE genérica→BT089, sobras por família, SOBREAVISO não é reflexo"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-11-07T20:39:09.638Z
---

Em 07/11, com ok da Raíra, mudei `bt-prod-apps/ft/app_validacao_Calculos/codigo/pipeline/gerar_telas.py` (não commitado):
- `_incompat` ganhou vetos: intervalo × HE sem intervalo (exceto art. 384 dos dois lados), 467 × 477, saldo/retido × 13º,
  salário por fora × saldo/retido/13º/férias/aviso;
- nome genérico de HE do PJC ("HORAS EXTRAS 50%") casa com BT089, ou BT081 se não houver (mesma regra do src/matcher_verbas.py);
- passo novo "mesma família que sobrou dos dois lados" (intervalo, férias, aviso, saldo, 13º, FGTS), `pareado_por: familia`;
- `parse_pjc.py` e `parse_pjc_xml.py`: reflexo só com "SOBRE" palavra inteira (HORAS SOBREAVISO). NÃO subir `_PJC_SCHEMA`
  (ficou v11): o bump relê ~4.700 PJCs a ~2/min (~40 h). Por isso o gerar_telas corrige o SOBREAVISO logo após `_parse_pjc_cached`;
- `_match_pjc` prefere o nome com mais palavras em comum antes do valor (saldo × salário retido).
Antes: 107 aptos com par trocado ou perdido (4 na alta apto valor). Assertividade não muda (total × total).
**Painel AINDA NÃO regerado** (07/11 17h40 a Raíra pediu para parar; volta à noite). Pronto para rodar:
`%LOCALAPPDATA%\bt_auto_pjc\fecha_pareamento_0711.ps1` (lista todos_pareamento_0711.txt, 4.726; painel_incremental agora
divide em quantas partes a linha de comando exigir, ~5). Leva as 46 análises do agente ao painel junto. Só rodar com ordem dela.
Backup em `%LOCALAPPDATA%\ft_paineis_parciais\antes_pareamento_0711`.

**Why:** a tabela por verba e o gráfico de faixa enganavam (ex. 0100275-60: HE pareada com intervalo).
**How to apply:** o app de produção tem essa mudança local; avisar antes de qualquer pull/commit no bt-prod-apps. Ver [[pareamento-he-uma-linha]], [[painel-homol-nao-mexer-prod]].
