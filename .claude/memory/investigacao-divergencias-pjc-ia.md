---
name: investigacao-divergencias-pjc-ia
description: Série de investigações caso a caso PJC × IA para achar ajustes de prompt; começou em 05/10/2026 pelo 0000525-37.2023.5.12.0027
metadata:
  node_type: memory
  type: project
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-08T13:03:13.219Z
---

Em 05/10/2026 a Raíra começou a investigar, caso a caso, as divergências entre o
gabarito (PJC) e a IA (LIFT), com o objetivo de **achar ajustes de prompt**
(P4, P7, P9a, P9b, P10). Primeiro caso: `0000525-37.2023.5.12.0027` (acurácia global 10%).

Padrões achados no 525, para conferir nos próximos casos:
- P9a: `jornadas[].regimes` guardou só seg–sex e perdeu sábados/domingos alternados e
  acionamentos que estavam na própria `descricao` → zera interjornada e corta HE pela metade.
- P9b ignora `componentes_explicitos: adicional_periculosidade` do P9a (base sai só com salário).
- P9b multiplica adicional noturno por 1,20 em vez de 0,20; sobreaviso sai sem o 1/3 que o P9a citou.
- P7 repetiu o último salário (2.763,61) em todos os meses.
- PJC deixa fora do principal a verba com saldo negativo; a IA soma o negativo.

Furos do painel (não são prompt): "ADICIONAL DE SOBREAVISO" não pareia com BT002; a frase
"não desconta férias — 01/2022…" se repete igual em toda verba; "o percentual bate" aparece
mesmo com multiplicador errado.

Causas na raiz confirmadas em 05/10 (prompt de produção + código do back): 7h20 = P9a v9 Fase 2
Prioridade 1 Caso B (contradiz P4); noturno ×1,2 = P10a v3 regras 2.3/2.4 (fórmula única 1+adicional);
férias sem proporcionalizar = P10a v3 regra 2.1 (só 1º/último mês); 7ª-8ª = P9a "dupla_imputacao"
fixa, aplica_s109 não é lido por ninguém; P8 conta férias em dia útil DE PROPÓSITO (não é erro).
"Meses sem cálculo" (06/10, cruzando saídas brutas P9b × P10a no cache): NÃO é perda entre etapas na
maioria — o mês já não sai do P9b. Maior grupo: período da verba definido mais curto pelo P9a (~R$ 100 mil);
depois cartão cobrindo só parte do período (~R$ 80 mil). Perda real P9b→P10a só quando a base vem vazia
(~R$ 17 mil). Script: scratchpad meses_sem_calculo.py (refazer se precisar). Quick wins combinados:
noturno (P10a), gratificação 7ª/8ª (P9a, esforço baixo), limite 7h20 (P9a); honorários = "café com leite".

Regras de negócio dadas pela Raíra (06/10): (1) gratificação na 7ª/8ª é SEMPRE descontada — a IA está
certa, divergência é do gabarito, tratar à parte; (2) o cálculo se restringe ao período com holerite nos
autos (P9b hoje cai nos Dados Iniciais quando falta holerite). Ao falar de prompt, sempre trazer o ajuste
sugerido (texto atual × proposto) com o MENOR impacto possível e dizer o que não muda.

Janela 20/09–02/10 (245 casos, relatório https://claude.ai/code/artifact/642afe30-baeb-4b74-bdee-57637b847409)
cruzada com o relatório da Raíra de 04/09 (https://claude.ai/code/artifact/ae46f775-ae1b-4f59-9493-cd5494b678a1, nove
pontos): resolvido só o teto 2h da 7ª/8ª; melhoraram sem regra (salário não chega, TRCT 2x, reflexo pós-Reforma);
persistem base (~35% competências iguais), gratificação (réguas misturadas), dedução; não entraram aptidão e P11.
Os SHAs/PRs #20/#21/#23 do relatório dela NÃO estão em nenhum clone local (outro repo).

Painel (06/10): quando a Raíra mostra print do PAINEL e pede ajuste, aí sim mexer no template_telas.html
(ex.: tela Jornada passou a mostrar as datas do "período imprescrito" e o padrão de horário legível).
Há alterações não commitadas de outra pessoa/sessão no template (telaLista, pareamento) — não tocar.

O catálogo de padrões com `raiz` vive em `codigo/src/arvore.py` (PADROES). A árvore com os números
da rodada vai no ARTEFATO do relatório, não no painel do app (validacao_calculos.html) — a Raíra
corrigiu isso em 05/10; não mexer no template/gerar_telas para a árvore sem ela pedir.

**Why:** o painel gera texto de causa automaticamente e às vezes engana; a leitura mês a mês
(`competencias[].ia/pjc` no `validacao_calculos.json` + texto do `pjc.pdf` via pdfplumber) é
o que confirma a causa.

Formato combinado (05/10/2026): a árvore de diagnóstico (página "Árvore de Divergências PJC × IA",
https://claude.ai/code/artifact/067421c1-bbb3-4eaf-ba07-62d1a8f442f7) é o processo padrão; cada caso
vira **um JSON** (schema `arvore_divergencia/v1`: `nos`, `achados[]` com código `padrao`,
`ponte_por_verba`), não um artefato por caso. Gerador: `codigo/analises/arvore_divergencias.py <data>`.
Saída **fora do repo** (a Raíra pediu, para não subir ao Git): `Repos/ft_arvore_divergencias/<data>/casos/*.json`
+ `padroes.json`. Rodada 2026-10-02 (109 casos) já varrida.

Relatório da rodada 02/10 (artefato, só para relatório — por caso é JSON):
https://claude.ai/code/artifact/90ae1fd2-940f-42ae-bce9-7e8eb88a92cb. Árvore revisada em 05/10 com 2.1.2
férias (meses / dias / proporcionaliza) e ramo 2.5 hora extra por tipo (7ª-8ª × além da 8ª, tipo pelo NOME,
não pelo código). A Raíra quer exemplos, % de casos e R$ por categoria em relatórios.

Padrões confirmados na varredura de 02/10: limite diário derivado 7,33 h (P9a) superconta HE em jornada fixa
(13/13 casos); adicional noturno × (1+adic.) em 11 casos; P9b deixa competências sem apuração (41 casos);
base expandida com rubricas do holerite; intrajornada paga integral com gozo parcial. Nó 3.2 (regra do
reflexo) é ruído do método — razões medianas IA × PJC quase iguais; reflexo herda a principal.

Agente caso a caso (06/10): definição em `Repos/.claude/agents/analista-divergencias-lift.md`; pacotes por caso
gerados por `Repos/ft_arvore_divergencias/ferramentas/prepara_casos.py <pasta_arvore> [cnj...]` (rodar da raiz do app
com .venv) em `ft_arvore_divergencias/pacotes/<cnj>/` (caso.json, arvore.json, pjc.txt) + prompts em `ft_arvore_divergencias/prompts/`;
dossiês em `ft_arvore_divergencias/analises_caso/<cnj>.json/.md`. Piloto de 5 casos da janela 20/09–02/10 antes de escalar
para os 245; depois, relatório consolidado de ajustes por prompt.

Rodada completa (06/10): 46 aptos analisados (workflow, ~9 mi tokens), consolidado em
`analises_caso/_consolidado.json` (ferramentas/consolida_analises.py) e relatório "Ajustes de Prompt LIFT"
https://claude.ai/code/artifact/fd2e15a7-4987-4810-b33c-e70fb8cb3c88 (gerador ferramentas/gera_relatorio_ajustes.py +
temas_ajustes.py, CSS relatorio.css). Teto de dano R$ 5.000 (BT052/BT050/BT040) é regra em CÓDIGO
(TetoDanosMoraisStrategy) — IA = 5.000 é política; painel só capa BT052. Decisões pendentes da Raíra: prescrição com
interrupção/suspensão × 7.2; 24.0 reflexo de verba nunca paga; Súm. 264 implícita; gratificação 7ª/8ª limitada a % da CCT.

Deduções (06/10, ferramentas/deducoes.py + deducoes_grupos.py; o que o PJC abateu vem do vínculo VALOR_PAGO
→ HistoricoSalarial no XML do .pjc): causa comum = "código idêntico" no HIST_SALARIAL_FILTRO (item 1) e na Busca
Padrão do P9b 2.4 — IA não abate HE paga de outro código/percentual (≈45 processos na janela). Bancário: IA deduz
gratificação inteira; PJC ~55% (CCT cl. 11) em 3 processos — decisão pendente da Raíra.

PR #98 (merge em main 28/09/2026 11h40) e #99: BT001 × BT081 pela decisão, BT001 sem teto, CompensacaoFamiliaHeStrategy
(HE paga deduzida por família em código, BT081 nunca recebe). 21 dos 46 aptos rodaram antes disso → teto 2h e
"HE comum como 7ª/8ª" provavelmente já corrigidos. O que sobra no abatimento de HE é o HIST_SALARIAL_FILTRO (item 1,
código idêntico) não deixar a HE paga de outro código chegar. Sempre conferir commits do back × data_processamento
antes de atribuir erro a prompt.

Lote 2 (06/10): 45 inaptos só por honorários da mesma janela (lista em 2026-09-20_a_2026-10-02/lote2.txt, seleção
ferramentas/seleciona_lote2.py), total 91 dossiês. Temas do lote 2 atribuídos por agente em
analises_caso/_temas_lote2.json (lido pelo gerador). Temas novos fortes: sábado bancário como repouso no DSR (P8),
base da HE bancária fechada (Premissa 10.0), não cumulação insalubridade × periculosidade. Painel: ler coluna
"Diferença" do PJC (7ª/8ª zerada). Pendente decisão: multa por embargos protelatórios (BT073) entra no risco?

Feedback da Raíra sobre ajustes de prompt (06/10): texto tem de ser LITERAL e colável (âncora + operação + texto final,
nada de "acrescentar [...]"); o texto do prompt não cita Premissas/PJC (a IA não conhece) nem depende de trânsito em
julgado (a IA não sabe) — sempre versão conservadora; ao final avaliar se o prompt fica mais ou menos eficiente.
Implementado: ajustes_prompts/INSTRUCOES.md, entrada/<AGENTE>.json, <AGENTE>.json (edições), propostos/, checagem
ferramentas/verifica_ajustes.py (âncora tolerante a linhas em branco: os .txt de produção têm espaçamento duplo/CRLF).

Rodada 07–08/10 (08/10/2026): 62 dos 91 rerodaram com versões novas DO TIME (P9a v10, P9b v6, P10a v4, PROVENTOS v6,
FILTRO v5, CALENDARIO v7, INFOS v11) — nenhuma das nossas sugestões estava nelas. Dossiês refeitos (anteriores em
analises_caso/_rodada_ate_0210/), balanço em _antes_depois_0710.json (erro IA R$ 3,56 mi → 2,04 mi; 0100592 sozinho
1,59 → 0,39), temas reclassificados em _temas_0710.json; ferramentas/temas_atuais.py junta lote1+lote2+0710 (substitui
vínculos dos rerodados). Edições reancoradas nas versões novas (antigas em ajustes_prompts/_versoes_antigas/).
Cuidado: tema cujo representante muda pode ficar sem pacote — conferir temas sem edição nem descarte justificado.

Hackathon 08/10/2026: página curta https://claude.ai/code/artifact/47eeb52e-1f81-4ffe-8554-676b30f414ea (gerador
ferramentas/gera_hackathon.py <saida> <url_relatorio>): o que foi feito → árvore por fator → problemas por prompt (R$ desc.)
→ esforço × impacto (B/M/A manual em ESFORCO) → trilhas por prompt → decisões à parte. Só temas com caso atual.
A Raíra achou o "o mais benéfico / não cumulativo" do limite diário complexo demais: ficou só 7,33 (dias iguais) ou
8h/dia + limite do sábado (dias diferentes).

O squad agora se chama **Precificação** (não mais LIFT) — usar esse nome nas páginas (08/10/2026). Formato de card
pedido pela Raíra para cada problema: título · o que aconteceu · o que era para acontecer (+ fonte da regra) · IA × PJC
(exemplo) · sugestão de ajuste (ponto de partida para discutir com a especialista, nunca "pronto para colar") · atenção ·
casos relacionados; o técnico (âncora, texto completo) fica recolhido. Textos em analises_caso/_cards_hackathon.json.

Separar SEMPRE "código da esteira" (muda o valor calculado → desembolso do crédito) de "painel de validação" (só a
medição/assertividade). Furos do painel (classe metodo, ferramentas/painel_metodo.py → _painel_metodo.json): ~R$ 1,7 mi de
distorção, sobretudo pedidos improcedentes somados (R$ 1,18 mi) e 7ª/8ª lida como devido − pago (R$ 266 mil).

**How to apply:** nos próximos casos, testar esses padrões primeiro. Ver [[projeto-fast-track-ft]]
e [[lote-0909-regressao-hora-extra]].
