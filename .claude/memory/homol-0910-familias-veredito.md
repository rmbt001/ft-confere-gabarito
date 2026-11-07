---
name: homol-0910-familias-veredito
description: "Rodada de homol da noite 09→10/10 (P9a v17, P9b v14, P10a v8, P4 v12 + código): veredito das 4 famílias, decisões e prioridades (T23 e T07, ambos reflexos)"
metadata:
  node_type: memory
  type: project
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-10T13:49:20.399Z
---

Rodada de homol da noite de 09→10/10/2026: 240 processos (172 da amostra de 07–08/10), 205 terminaram, 35 com erro
(30 no cartão, 23 deles recusa proposital de "jornada mista"). Pacote: commits 6fc83e04 e 206e97c0 (09/10 19:19 e 19:30,
Filipe) + glossário BT031 revertido (20:18). P2 e prompt do filtro NÃO ganharam versão nova.

Veredito (régua: sobrecálculo primeiro, ver [[sobrecalculo-primeiro]]):
- **Família 1 (prêmio/abatido):** glossário BT031 voltou e desfez T47/T48 (0000177, 0001233). T33 em código: saldo positivo,
  mas piorou 0101497 e 1001083. T07 (reflexo de prêmio pós-Reforma) NÃO pegou: verba vem como BT024 e o corte do código é
  só BT031 (`CODIGOS_PREMIO_REFORMA`); regra do P4 depende de data que ele grava como "periodo_global".
- **Família 2 (horas):** nada entrou. Turno ininterrupto e bancário com condenação limitada à 7ª/8ª: decididos como
  EXCEÇÃO, não endereçar. Limite 7h20 (T35): pendente. Súmula 85: a marca aplica_s85 existe só no schema; a ideia é usá-la
  para tornar o cálculo NÃO APTO (regra de aptidão ainda não feita).
- **OJ 97:** a Raíra achava que foi ajustada em 09/10; não está em prompt, branch, commit nem tabela da Nekt (só a regra de
  06/10 do adicional noturno). O P9b já separa HE diurnas/noturnas. Ela vai verificar com quem fez.
- **Família 3 (base):** base fechada do bancário (P9a v17) funcionou (0000691). T25, T05, T04 não entraram (T25 é pequeno).
  Regra de código `CompetenciaSemHoleriteStrategy` zera base de mês sem holerite (lista de salários dos Dados Iniciais não
  conta): decisão pendente se a ficha de registro vale como documentação.
- **Família 4 (mês parcial):** T11 régua funcionou (0001233); T12 misto e pequeno; T13 mês cheio cria base em mês de
  afastamento e soma a lista em dobro (1001334); **T23 piorou**: BT082/BT025 passaram a "variavel" (média × avos do
  contrato) e escaparam da checagem `verba_existe_no_mes` (0001152: 13º R$ 6.000 × PJC 1.000).

**Prioridade escolhida pela Raíra (10/10): T23 e T07, ambos no código de reflexos** (~R$ 87 mil de sobrecálculo na amostra).
Opção do T07: P4 marca `premio_metas` + código corta reflexos ≥ 11/2017 para BT031 ou verba marcada (não trocar o código da
verba para BT031, quebra o abatimento). Ela pediu para ainda não redigir o texto para a Engenharia.

**Why:** registrar onde parou a avaliação das famílias. **How to apply:** ao retomar, partir destas prioridades; a medição
por família está em scratchpad (familia1..4.py) e os dossiês em analises_homol_noite/. Ver [[lote-0710-fila-parou]].
