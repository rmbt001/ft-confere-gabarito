---
name: frequencia-cartao-jornada-fixada
description: "Mesmo com jornada fixada, o time usa o cartão para a frequência; o backend não faz isso (Ramo A ignora o cartão, Ramo B vira mista e é recusado)"
metadata:
  node_type: memory
  type: project
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-26T18:50:42.846Z
---

**O que o time faz.** Mesmo com a jornada prefixada pela decisão, o time interno usa o cartão de ponto para aferir a frequência: horário da decisão, dias do cartão. A Raíra disse isso em 13/10/2026, e os dados confirmam. Nos processos de jornada fixada com cartão nos autos, a IA conta 11% mais dias que o PJC (R$ 60 mil de efeito em 19 processos). Exemplos: 0010615, 0001043, 0010341.

**O que o backend faz (origin/staging, 13/10).** Nenhum caminho usa o cartão só para os dias:
- **Ramo A** (dias explícitos na decisão): vira `fixo_diario`. O `_is_dependente_documentos` não aciona o cartão, e o calendário conta a escala cheia. O 0000955 caiu aqui mesmo com "observar os dias efetivamente trabalhados" no critério.
- **Ramo B** (a decisão remete a frequência ao cartão): vira `mista_documental_e_fixada`, e `cartao_ponto_split_service._verificar_jornada_mista` recusa o processo.

**Proposta na página "Horas extras".** Duas opções, a decisão é da Raíra:
- um modo "frequência" na etapa do cartão;
- tornar o processo não calculável.

**Alcance (14/10/2026, Raíra).** A mesma ideia de usar o cartão para a frequência, mesmo com jornada fixada, também deve resolver os feriados e domingos em dobro (BT011) que hoje saem não calculáveis. O cartão diz quais feriados foram trabalhados. Caso: 0020129, com R$ 2,9 mil a menos. Nos relatórios, contar esses casos como "já endereçado: frequência pelo cartão".

**Entrou em produção em 23/10 ~23h (visto em 26/10).** O P9b ganhou o campo `total_horas_antes_frequencia_cartao`: as horas da jornada fixada passam a ser reduzidas pela frequência do cartão (ex.: 0000299-77.2025.5.06.0011, 06/2022: 71,0h → 56,8h; a memória do cálculo ainda diz 71h). Em 204 de 1.301 execuções do P9b desde então (~16%). Mudança de código do back, sem prompt novo. Efeito: HE ~12% menor em casos que estavam com 95–99% de assertividade, ou seja, nesses o PJC NÃO usou a frequência do cartão.
**Raíra, 26/10: o ajuste pela frequência do cartão deveria valer só quando a decisão NÃO prefixa a jornada.** O back faz o contrário: os 204 processos ajustados são todos de jornada `fixada` (regime fixo_diario), 96 deles com os cartões declarados inválidos na decisão; 26% das horas cortadas (89 mil de 348 mil). No painel: 46 aptos afetados, 35 com IA abaixo do PJC. Lista: Downloads\frequencia_cartao_jornada_fixada_2610.csv. Isso substitui a leitura de 13/10 acima ("time usa o cartão mesmo com jornada fixada").
**Correção no mesmo dia (26/10), lendo o código (BT-2227, commit 93be50da, Filipe Pereira):** o back usa o cartão só para os DIAS (escala da decisão − ausências do cartão) e escala as horas da decisão pela proporção de dias — que é o que a Raíra quer ("uma coisa é dias trabalhados, outra é horas"). O defeito está no que conta como ausência: `STATUS_TRABALHO` deixa de fora `falta_sem_registro` e `descanso`. Nos 257 processos com o ajuste: 18.128 dias tirados por `falta_sem_registro` (dia sem batida, em todos os dias da semana), 11.694 por `descanso`, contra 2.640 `falta` real. Ex.: 0000299-77.2025.5.06.0011, sentença fixou sábados 7h–13h por invalidar os cartões e todos os sábados saíram como `falta_sem_registro`. Já 0000375-51.2024.5.10.0003 tem ausências reais (afastamento/falta) que o PJC não descontou.

**Why:** a contagem de dias é a maior causa do volume a mais de hora extra (R$ 97 mil nos 56 processos medidos).

**How to apply:**
- Ao propor ajuste de dias ou frequência, partir daqui.
- Lembrar que mexer nisso altera a regra [[jornada-mista-nao-calculavel]].
- Antes de virar regra, confirmar em 2 ou 3 processos que os dias do PJC batem com o cartão.
