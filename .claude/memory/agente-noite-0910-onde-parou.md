---
name: agente-noite-0910-onde-parou
description: Estado em 10/10/2026 ~12:20 da rodada do analista caso a caso nos 239 processos da homol 09→10/10 e das peças do TARS; retomar daqui após o reinício do PC
metadata:
  node_type: memory
  type: project
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-14T12:28:16.177Z
---

Ponto de parada em 10/10/2026, antes de o PC reiniciar. A Raíra quer retomar exatamente daqui.

**Agente analista (foco atual, pedido dela).** Roda o agente [[investigacao-divergencias-pjc-ia]] (`Repos/.claude/agents/analista-divergencias-lift.md`) caso a caso nos processos da homol 09→10/10 e grava `ft_arvore_divergencias/analises_homol_noite/<CNJ>.json` e `.md`.
- Lote 1: 65 processos com pacote e peças, listados em `homol/_agente_lote1.json`. Rodava como workflow `wf_1fc07309-d8c`, que morre com o reinício. Tinha 26/65 gravados às 12:20. Depois do reinício, a retomada (wf_c676b541-93f) parou no limite de uso da sessão, que libera às 13:30. Ficaram 29/65 gravados. Às 18h o lote 1 fechou com 65/65. Achado: a esteira LÊ o cartão de ponto (etapa CARTAO_PONTO), então a definição do agente foi corrigida; casos que o lote 1 marcou como documento_nao_lido por causa do cartão precisam ser reclassificados. Para retomar, rodar só os do lote 1 que ainda não têm `analises_homol_noite/<CNJ>.json`. O prompt por CNJ é o do script do workflow, que está no histórico da sessão.
- Os 10 diagnósticos de piora feitos antes também estão em `analises_homol_noite/`.
- Os 239 processos já têm pacote em `pacotes_homol/`.
- 164 processos não têm peças. Rodar o agente neles (o que depender da decisão sai como `dado_ausente`) ainda espera o OK dela.

**Peças do TARS (pausado por ela: "não vamos focar nas íntegras agora").**
- Desde o processamento de 07/10, a lista do Recorte Íntegra vem vazia. É problema do próprio TARS.
- "Baixar Íntegra" funciona: o arquivo cai em Downloads como `<CNJ>_bluetape.pdf`.
- `ferramentas/tars_integra.py` recorta a íntegra pelo sumário do PDF e grava só o texto das peças lidas. Foi testado com um PDF já baixado. Falta testar o robô baixando sozinho.
- `tars_pecas.py` foi corrigido: o CNJ é preenchido via JS, porque `send_keys` parou de funcionar.
- O agente já sabe que embargos de declaração aparecem no TARS como "Decisão".

**Para ela apagar à mão:**
- em `pecas/`, a pasta com BOM no nome antes de `0000041-39.2022.5.09.0965`;
- os arquivos `Intimação_Acórdão` em `pecas/0000115-20.2022.5.17.0012/`.

**Ajustes de 10/10 (feito).** A Raíra escolheu os alvos de IA a mais 1 (afastamento INSS), 4 (base da HE), 5 (identificação a mais) e 7 (reflexos), com os números que ela deu. As propostas estão em `homol/ajustes_1010/g*_proposta.md` e o artefato "Ajuste prompts v10/10" (764b678b-161e-4d54-a9d8-54e07f687a61) é gerado por `ferramentas/gera_ajustes_1010_html.py`. Achado: a homol da noite rodou o código de reflexos 39abb43c, e não o HEAD da staging (206e97c0 ficou de fora), o que custou R$ 41,6 mil de IA a mais. Resposta sobre subir para produção: ainda não. Antes, rerodar homol com HEAD + ajustes nos 62 aptos e nos que pioraram. Decisões pendentes da Raíra: inflamável (3.0), art. 62 (11.0), BT073 no risco.

**Lote 2 (12/10).** O TARS voltou. Os 31 processos que pararam com ERRO na noite ficaram fora (lista em `homol/_noite_parados.txt`). b01 a b03 rodaram com peças. Os outros 113 (b04 a b15 em `homol/_lotes_agente.json`) estão na varredura SEM peças (wf_30cc6452-df0), com `pecas_lidas: false`, e cada problema traz `depende_pecas` e `conferir_nas_pecas`. Quando o download (`_lote2_falta_pecas_sem_parados.txt`) terminar, falta a 2ª passada com peças nesses 113. A comparação por lote sai de `ferramentas/compara_lotes.py`.

**13/10.** A varredura bateu no limite de uso com 43 de 113 gravados e foi retomada no mesmo run (wf_30cc6452-df0). Quando terminar, a Raíra quer o relatório completo da rodada. Para isso: rodar `ferramentas/agrega_rodada_0910.py`, revisar os itens fixos de regressão em `ferramentas/gera_rodada_0910_html.py` e publicar `homol/rodada_0910.html`. O download de peças parou de novo (Chrome fechou) com cerca de 66 baixados; a 2ª passada com peças ficou para depois.

**Páginas de 13/10.**
- "Rodada 09→10/10" (8a125727…): gerada por `gera_rodada_0910_html.py`, com dados de `agrega_rodada_0910.py` e `categoriza_nao_erro.py`. Tem as seções "o que não subiu" e "o que conta como erro e não é".
- "Ajuste prompts v2" (242c844d…): gerada por `gera_ajustes_v2_html.py` (escreve em homol/ajustes_prompt_homol.html). Organizada por família, com o estado de cada item e os prompts da sala.
Quando a varredura terminar, rodar de novo os três scripts e republicar as duas páginas.

**13/10, fim da manhã.** A varredura terminou: 208 de 208 processos com dossiê, 113 deles sem peças. As duas páginas foram republicadas com os números finais e sem nada de painel (pedido da Raíra: o painel fica à parte). Um agente corrige o painel nos apps de produção e homologação, com cinco correções; o resultado ainda está pendente. Falta a 2ª passada com peças nos 113.

**13/10, tarde.**
- As duas páginas foram reescritas porque a Raíra achou a leitura truncada e cheia de remendos:
  - **Rodada:** resumo, 8 seções curtas, lista de exceções de um processo só e anexos recolhidos.
  - **Ajustes v2:** organizada em camadas A (entra direto) / B (decidido, falta texto ou teste) / C (sala decide) / D (exceções a validar) / E (decisões suas), com os prompts da sala no fim.
- Cards medidos só no componente que mexem (`ferramentas/mede_cards_componente.py`), para não confundir com compensação de erros.
- Novo item B: valor que a decisão manda pagar a terceiro (0020906, R$ 1 mi de dano social para o sindicato), ajuste no INFOS (P2).
- Em 12/10 rodaram mais 24 processos em homol (lista em `homol/_rodada_1210_cnjs.txt`): todos novos, com PJC, mesmas versões da noite, mas P7 v8. Falta ingerir (ingerir.py --fresh do app homol, depois que o agente do painel terminar), gerar a árvore e rodar o analista.

**Rodada de 12/10.**
- São 24 processos, que o painel registra como 13/10.
- Os dados foram puxados com `ingerir --fresh` no app homol, depois de incluir 10 processos na amostra. Árvore em `homol/2026-10-13`, pacotes já feitos.
- 6 pararam (lista em `homol/_1210_parados.txt`): 3 por jornada mista, 1 porque o motor do cartão não gerou verba, 2 por falha técnica.
- Agente sem peças rodando nos 18 (wf_1e6b0961-2a4), gravando em `analises_homol_1210/`.
- O painel foi interrompido a pedido da Raíra (prioridade baixa). O gerar_telas de prod e homol tem mudanças parciais do agente, que compilam.
- Commits: o código instalado na noite é o de 08/10 19h33 (39abb43c). Nada de código de 09/10 subiu. Os prompts das 20h43 rodaram.

**Correção de versão (13/10).** O histórico salarial (PROVENTOS) rodou na **v8** (criada em 06/10) tanto na noite de 09→10 quanto em 12/10. A v9 foi criada em 09/10 às 7h20, mas nenhuma execução de homol a usou. O filtro rodou na v7, e o painel chama o filtro de "P7". Os dossiês dizem "v9" porque esse número veio do contexto que passei aos agentes; ao ler, considerar v8. Em produção, o último PROVENTOS é a v6 e o filtro está na v5. Antes de citar a versão de uma etapa, conferir execução a execução na tabela de resultado × agente.

**13/10 13h45.**
- A Raíra mandou parar a varredura: o time vai rodar de novo os 125 processos de 02/10 com os ajustes.
- Da rodada de 12/10, só 4 dossiês ficaram prontos, em `analises_homol_1210/`; os outros 14 bateram no limite de uso e não serão retomados.
- O agente do painel foi retomado às 13h45 e vai medir só nos processos comuns às duas bases.

**T35 (limite de 7h20):** a Raíra resolveu via prompt em 13/10. Não tratar mais como pendente. Ela também tirou o T35 da página de horas extras.

**Prêmio pós-Reforma (T07), conferido em 13/10.** O P4 recebe só `jornada_global` e `verbas_deferidas` do P2, sem dados iniciais e sem CNJ. O P9a recebe `{dados_iniciais}`, mas não decide reflexos. O corte por competência no código de reflexos (206e97c0, não subiu) vale só para BT031. Os 3 casos do T07 são BT024. Por isso nem a regra do P4 v12 nem o gatilho por ano/admissão proposto no Ajustes v2 pegariam esses casos.

**Prêmio na base da HE (13/10).** A Raíra decidiu: depois de 11/2017, prêmio e metas sempre saem da base, mesmo que a decisão nomeie ou tenha transitado. A regra já está no MENSAIS 2.2.1 desde a v7, mas falhou em 16 processos (R$ 100,7 mil), sobretudo porque o roteamento manda incluir e o cálculo obedece. A página "Prêmio na base da hora extra" (c3d29be6…, homol/ajuste_premio_base_he.html) traz o texto para MENSAIS v15 e ROTEAMENTO v18. Na versão 2, depois da varredura (homol/_varre_premio.json), ficaram 21 processos:
- 9 com Gratificação Desempenho (BT023): R$ 49 mil estimados;
- 8 com metas lançadas como BT024, contados na página da comissão;
- 4 achados só pelos dossiês.

**Comissão na base da HE, parte fixa × variável (13/10).**
- Página "Comissão na base da hora extra" (dbfd18c2…, homol/ajuste_comissao_base_he.html). Pede à IA:
  - ligar a Súmula 340 também pela OJ 397;
  - com a 340 omissa, comissão fora na HE fixada e cheia na HE do cartão (`fonte_apuracao`);
  - comissão fora dos intervalos.
- Versão 2, depois de varrer todos os processos: 32 processos com comissão cheia na base, sem nenhuma separação entre parte fixa e variável. Em 21 deles o PJC tirou a comissão: R$ 123 mil estimados. Varredura em homol/_varre_comissao*.json.
- Regra conservadora: a comissão só entra pela Súmula 340, com o adicional, e nunca no intervalo nem com o DSR das comissões.
- Pontos para a Raíra bater o martelo:
  - A: a decisão nomeia as comissões. O PJC pôs a comissão cheia em 1000943 e 0100394.
  - B: HE do cartão com a decisão omissa. A premissa diz comissão cheia.
- Erro meu: a 1ª versão olhou só os dossiês e disse que eram 5 processos. Ao dimensionar um problema, sempre varrer todos os pacotes.

**Rodada de homol de 13/10 (14/10).** O lote foi das 17h de 13/10 às 3h de 14/10: 136 processos.
- **Versões e código:**
  - prompts novos: ROTEAMENTO v18 (T35/7h20) e INFOS v13 (terceiro);
  - código: o cartão com o pré-assinalado (ca165e98). A staging foi resetada para a v5.
  - **A OJ 97 não está em nenhum prompt nem em nenhuma branch**, conferido em 14/10.
- **Status do lote:**
  - 18 caíram por falta de crédito no provedor LLM;
  - 8 ficaram presos em "em andamento";
  - 10 pararam por jornada mista;
  - 3 caíram por resposta truncada.
- **No app de homol:** incluí 5 processos na amostra.
- **Arquivos:**
  - árvore: homol/2026-10-13_a_2026-10-14;
  - pacotes: pacotes_homol/ (os da noite ficaram em pacotes_homol_0910/);
  - lista: homol/_rodada_1310_analisar.txt, com 91 processos, só os que chegaram ao GERADOR_PJC.
- **Código de 09/10 instalado em 13/10 (provado):**
  - reflexos: com o código de 09/10, 13º 148/148 e aviso 120/120 batem; com o de 08/10, 138/148 e 119/120 (replay W:\g7_run.py, W: = subst do scratchpad);
  - filtro: a BT011 paga aparece em 20 de 42 processos, contra 2 de 69 na noite;
  - campo escala_12x36_valida: aparece em 1 processo do lote e em 0 da noite.

  O cartão e o glossário vieram no mesmo deploy da v5. Só a OJ 97 não entrou.
- **Agente:** o 1º workflow tinha o contexto errado e foi parado. O workflow wf_c323c8ba-5a9 refaz os 91 e grava em analises_homol_1410/.
- **Ponto de parada (14/10, ~8h35, antes de a Raíra reiniciar o PC):**
  - estado: 4 processos prontos no workflow novo (homol/_1410_prontos.txt), 87 faltando (homol/_1410_faltam.txt);
  - a pasta analises_homol_1410/ também tem dossiês do workflow parado: valem só os da lista _1410_prontos;
  - para retomar: relançar o workflow só com _1410_faltam.txt e com o mesmo prompt, guardado em ferramentas/wf_analista_homol_1410.js (contexto com o código de 09/10);
  - pedido da Raíra: trazer os resultados em lotes de 10, como no compara_lotes. Na retomada, montar o vigia que avisa a cada 10 resultados no journal.jsonl do workflow.
  - retomado depois do reinício: 7 prontos e 84 no workflow wf_8bb7100f-8ef. Os lotes de 10 saem de `ferramentas/lote_1410.py <journal do workflow>`, que grava cada lote em homol/_1410_lotes.json; ao fim, usar `--fim` para fechar o último lote incompleto.
  - W: é um subst do scratchpad e some com o reinício.
- **Concluído em 14/10, 9h20.** Os 91 dossiês estão em analises_homol_1410, e os 10 lotes em homol/_1410_lotes.json. O consolidado sai de `ferramentas/consolida_1410.py` e grava homol/_consolidado_1410.json. Achados principais:
  - **Código novo, abatimento da HE 100% paga:** regressão em 9 a 13 processos, cerca de R$ 46 mil a menos. O código decide pelo que foi apurado, e não pelo que foi deferido.
  - **Adicional noturno negativo somado ao total:** 3 processos, R$ 46 mil a menos.
  - **Verba sem código, que some antes do cálculo:** 4 processos, R$ 54 mil a menos. É novo e a causa está em aberto.
  - **Bancário, compensação da gratificação na 7ª/8ª:** R$ 227 a 373 mil a menos.
  - **Salário-base zerado no histórico P7:** 8 processos, R$ 108 mil a menos.
  - **Já endereçado:** cartão como frequência R$ 193 mil, OJ 97 R$ 48 mil, múltiplos contratos R$ 59 mil.
  - **Inaptos:** 73 de 91.
- **Página "Rodada 13/10"** (90deb0a2…): gerada por `ferramentas/gera_rodada_1410_html.py`, com os cards curados à mão na lista CARDS e dados de agrega_rodada_1410.py, consolida_1410.py e _1410_lotes.json.
  - O abatimento da HE 100% (16 processos, R$ 52 mil) tem dois grupos:
    - 6 com BT011 deferida sem cálculo, um bug da condição;
    - 10 sem BT011 deferida, onde o PJC nunca abate. Isso põe em dúvida a própria regra.
  - A verba que some (4 processos) atinge 3 HE com cartão e 1 BT024. A suspeita é o código do cartão. Para refazer o replay de reflexos: `subst W: <scratchpad>`.
- **Atenção:** os meses do pacote não são uma amostra aleatória. São os 3 primeiros, os 3 últimos e os 6 de maior diferença. Por isso, as estimativas por período das páginas de comissão e prêmio podem estar altas.

**Depois do lote:** trazer o resumo com as classes de problema, os maiores problemas e quantos casos são `documento_nao_lido`.

**Why:** o reinício derruba o workflow e o contexto da sessão.
**How to apply:** ao voltar, contar o que já foi gravado, retomar o que falta do lote 1 e só então perguntar sobre os 164 sem peças.
