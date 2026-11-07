---
name: restricoes-lista-unica
description: "Lista única das verbas restritas do manual (trânsito, sempre, por condição) em jev_testes/restricoes.py; simulação de 22/10 e decisões pendentes"
metadata:
  node_type: memory
  type: project
  originSessionId: 4ef2053e-65b4-47d2-aab1-f28c8dfccaf6
  modified: 2026-10-22T18:10:00.750Z
---

Em 22/10/2026 a Raíra pediu que toda verba afetada por trânsito em julgado, ou restrita em cenário específico, tenha uma pergunta que a enderece. No caso do trânsito, a regra é **travar**: a esteira não sabe se o processo transitou.

**O que foi feito:**
- `jev_testes/restricoes.py` tem 40 regras em três grupos: transito, sempre e condicao. Cada regra diz a pergunta do Jev ou a regra de tabela, se o alcance é de verba ou de caso, e a exceção quando houver (gratificação especial com dispensa antes de 2012).
- Três perguntas novas foram escritas e ainda não rodaram: vínculo com reclamada da mesma atividade-fim, recurso de revista pedindo redução do dano moral e verba de representação com valor fixado.
- `jev_testes/simula_restricoes.py [--sem ids]` simula nos aptos do painel cópia sem mudar nada. O score (`aplica_score_jev.py`) NÃO foi alterado.

**Resultado de 22/10** (274 aptos, sem art. 62 e sem Tema 300):
- restrita passa de 40 para 64;
- alta passa de 93 para 81 casos (de 76% para 78% com 80%+);
- alta do apto valor passa de 55 para 47 (de 78% para 81%);
- a trava segura R$ 3,0 mi dos R$ 5,95 mi calculados a mais.

**Decisão de 22/10 sobre pensão:**
- A pensão em **parcela única pode seguir**; a pensão mensal continua restrita.
- A regra só libera quando o Jev diz parcela única E a IA lançou valor fixo (no máximo um mês com valor). Assim não se confunde a parcela única com o valor mensal fixado na decisão. Exemplo dela, "aquele de 2k": 0000491-30.2024.5.10.0012, "Pensão Mensal" de R$ 1,7 mil, que continua travado.
- Resultado: dos 17 casos, 12 seguem e 5 travam.
- Testado em 22/10 com `jev_testes/pensao_pu_jev.py`: as perguntas sobre vincendas, valor arbitrado, nexo concausal, percentual e recurso pendente NÃO separam os casos que acertam dos que erram (as 12 parcelas únicas caíram em baixa). O que separa é o valor: os 4 erros estão fora do apto valor e as 6 parcelas únicas dentro dele têm 98,8–100%. Proposta: parcela única segue sem baixa.
- Antes do teste, a questão em aberto era se a parcela única deveria cair na faixa **baixa**. A IA não separa vencidas de vincendas nem aplica o redutor da seção 14, e 0000334, 0022557 e 1000534 saem muito acima do PJC.
- Atenção: a decisão costuma chamar de "danos materiais" a pensão convertida em parcela única (art. 950 do CC), e a IA lança como BT051. A regra acende pelo Jev, não pelo código.

**Simulação final de 22/10** (`simula_restricoes.py --sem art62,tema300 --caso transferencia,grat_especial,gerente_geral,pensao,ats,ctva,rp52,representacao`; parcela única segue; quem sai da restrita volta à faixa dos outros sinais):
- restrita passa de 40 para 62;
- alta dos aptos passa de 93 para 92 (76% para 76% com 80%+, mediana de 93,0% para 93,9%);
- **alta do apto valor fica em 55** (saem 8, entram 8 parcelas únicas): de 78% para **82%** com 80%+, mediana de 91,3% para 94,8%.

Os "61 no apto valor alta" eram de 19/10 (dados da apresentação, casos_1910.json). Os 55 de hoje vêm de mudanças no score depois disso: inflamável no prédio (3), recurso de revista admitido (2), HE em alguns dias (1) e deferida não calculada (2).

**Art. 62 e Tema 300 reescritos em 22/10** (`jev_testes/art62_jev.py`, 118 aptos com HE e peças, 2,1 mi de tokens):
- art. 62 = trabalho externo + art. 62 discutido + (norma coletiva, contrato ou ausência de norma) e não motorista → 9 aptos;
- Tema 300 = externo + controle indireto reconhecido → 29 aptos;
- as perguntas antigas pegavam 99 aptos.

Com as duas regras: restrita 86; alta dos aptos 77 (75%, mediana 95,2%); alta do apto valor 43 (84%, mediana 97,2%). Sem as duas: alta do apto valor 55 (82%).

**LIGADO em 22/10 (tarde), versão sem art. 62 e sem Tema 300** (decisão dela: falsos positivos):
- O score do painel cópia vem do pacote da engenharia `ft_score_confianca`, e a lista entrou lá: `score_confianca/restricoes.py` (32 regras, componentes `restr_*`), 26 perguntas novas em `config/perguntas.json` (blocos restritas, restritas_premissa, restritas_jornada, restritas_processo), gatilhos em `caso.py`, `faixa.py` lendo `restr_*`, 15 testes passando, README com a seção "Lista de restrições".
- Os sinais antigos de transferência, gratificação especial, gerente geral e pensão saíram de `sinais_jev.py`.
- Pensão é regra de verba (o Jev sozinho não acende, regra de desenho do pacote).
- Jev: 588 chamadas, US$ 0,38.
- Resultado: restrita 40 → 62; alta dos aptos 93 → 92 (76% → 78%); **alta do apto valor 55 → 56 (78% → 84% com 80%+, mediana 91,3% → 95,5%)**.
- Backup do antes em `Repos/ft_score_confianca_backup_2210/`.

**Pendências:**
- As perguntas atuais de art. 62 ("a reclamada alegou") e de Tema 300 ("controle indireto, sem cartão") são mais largas que o manual: somadas, travariam 58 aptos a mais.
- O alcance "de verba" (só trava se a IA calculou a verba) perde casos em que a IA deu outro nome à verba: 12 dos restritos de hoje sairiam, entre eles gratificação especial lançada sem código com assertividade de −5696%.
- 56 aptos estão sem nenhuma resposta do Jev.

**Why:** o score só travava 5 das restrições do manual.

**How to apply:** ligar no score só com o OK dela. Ver [[score-confianca-calculo]] e [[premissas-de-calculo-bt]].
