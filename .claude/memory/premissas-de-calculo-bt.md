---
name: premissas-de-calculo-bt
description: "Manual oficial \"Premissas de Cálculo\" (04.2026.02) é a regra da casa; prescrição quinquenal é premissa interna; cuidado com overfitting ao propor ajuste"
metadata:
  node_type: memory
  type: reference
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-21T16:08:09.135Z
---

A Raíra entregou em 06/10/2026 o manual "Premissas de Cálculo - 04.2026.02" (Backoffice Operacional, 17 págs).
Cópia + texto: `Repos/ft_arvore_divergencias/premissas/premissas_calculo_04.2026.02.{pdf,txt}`.
É a regra da casa e prevalece sobre a leitura literal da decisão no tema que trata.

Itens que já mudaram leitura de divergência:
- 7.2: **prescrição quinquenal é premissa interna** → corte do P1 em ajuizamento − 5 anos está certo
  (a Raíra: "o do período eu quero manter").
- 3.0: periculosidade/insalubridade na base da HE só se Súm. 264 expressamente deferida; nunca na base de
  intervalo, in itinere, sobreaviso.
- 11.0: sobreaviso = 1/3; adicional noturno na base da HE só com Súm. 60/OJ 97.
- 18.0: prêmios/metas (SRV, PPR, AGIR) só natureza salarial até 10/11/2017.
- 15.0: período limitado à última documentação juntada (base da regra "só onde há holerite").
- 14: pensão: vencidas × vincendas com redutor / valor presente.
- **DSR só no domingo** (a Raíra, 21/10, "é uma regra nossa"). A IA tratar o sábado como dia útil no reflexo em DSR NÃO é erro, mesmo quando o PJC conta o sábado como repouso. O agente analista ainda aponta isso como erro_ia (38 aptos na cópia 14/10+) → falta nas premissas do agente.

Glossário de verbas (de-para BT ↔ verba, produção 06/10/2026), dado pela Raíra: `ft_arvore_divergencias/premissas/
glossario_ft_producao_2026-10-06.{pdf,xlsx,csv}`. Pontos-chave: BT081 só com descaracterização de cargo de confiança
bancário ou compensação de gratificação determinada (senão BT001); BT001 sem dedução de gratificação e com dedução de
HE paga; BT089 deduz HE paga uma vez entre as verbas de HE da competência (família).

**Overfitting (feedback da Raíra, 06/10):** sempre perguntar se o ajuste vale como regra geral ou se está
adaptando a um caso de exceção; só levar ao prompt o que generaliza (lei, súmula, premissa, padrão em vários casos).

Peças (sentença, acórdão, íntegra) ficam no site interno TARS (https://tars.btcreditos.com.br/fast-track → consultar
CNJ → Recorte Íntegra). Robô `ft_arvore_divergencias/ferramentas/tars_pecas.py CNJ...` (Selenium no Chrome aberto com
`--remote-debugging-port=9333 --user-data-dir=%LOCALAPPDATA%\chrome_tars_robo`, a Raíra loga via SSO Microsoft) pega
só as peças de decisão e grava SÓ o texto em `pecas/<CNJ>/*.txt` (a Raíra não quer PDFs ocupando disco).
A tela chama `.../PROD/calculo/timeline?cnj=` e `.../calculo/recorte-integra/documentos?id_processado=`; o clique abre
link assinado do S3. Não explorar credenciais AWS (o classificador bloqueia).

Relacionado: [[investigacao-divergencias-pjc-ia]], [[projeto-fast-track-ft]].
