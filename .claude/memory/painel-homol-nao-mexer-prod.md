---
name: painel-homol-nao-mexer-prod
description: "Pedido para o painel de homologação: mexer SÓ em app_validacao_Calculos_homol, nunca no código do app de produção; diagnóstico do agente no Resumo do caso"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 69b23582-ab8f-4216-8985-45c63e73ae9d
  modified: 2026-10-15T17:11:36.319Z
---

**Regra:** quando o pedido for sobre o painel de homologação, alterar só `bt-prod-apps/ft/app_validacao_Calculos_homol`. Nunca alterar o código de `app_validacao_Calculos`, mesmo para "compartilhar" uma mudança entre os dois painéis.

**O que aconteceu em 15/10/2026:** pus o diagnóstico do agente também no código de produção (gerar_telas e template). A Raíra reclamou forte ("é só para mexer no de homol"). Revertemos a produção para o commit 8052792, que é o commit local das correções de 05–14/10 que ela aprovou. A página de produção não chegou a ser regerada.

**Estado do painel de homologação em 15/10:**
- Código alinhado ao de produção, com as adaptações de homologação: números como texto, colunas "Produção 07–08/10", "② Homol" e "Δ", e marca HOMOL. Também passou a ler a tabela do editor de decisões.
- Bloco "Diagnóstico do agente" no Resumo do caso, mais coluna, filtro e ordenação "Agente" na Lista de casos.
- Os dados vêm de `agente/agente_por_caso.json`, gerado por `ft_arvore_divergencias/ferramentas/agente_para_painel.py <app> analises_homol_1410 analises_homol_noite analises_homol_1210 analises_homol`.
- Cópia do código anterior em `codigo_antes_1510/`.

**15/10, ~9h30 (pedido dela, só homol):** caso que não chegou ao P10 (fora da régua "nao_calculado") passa a NÃO APTO,
categoria "Não chegou ao P10 (FT Travado)" (regra da esteira). Homol: aptos 124 → 102, 37 travados. Em produção NÃO foi
aplicado: esperar o sinal dela. (~9h40 ela deu o sinal: aplicado também em produção e painel de prod regerado.) Também em 15/10: BT062 fora dos inelegíveis e busca indexada (velocidade) nos dois apps.

**15/10 ~10h, regra de status do FT (doc do PV "Classificação de status do Fast-Track", 14/10) — só HOMOL:**
cálculo crítico = BT012/013/022/045/048/059 (sempre bloqueia); não relevantes = BT043/062/071/079 (sem valor não bloqueiam);
BT063 tratado como calculado (painel não lê a etapa dele, como na simulação do doc); verba deferida sem valor com código BT
e dependência não resolvida = "Verba não calculada"; sem código ("Não encontrado") não avalia; faixa R$ 50–200 mil fica
como subcategoria dos aptos (como já era). Homol: aptos 102 → 174 (66 eram só BT062 sem valor).
**~14h ela pediu levar para PRODUÇÃO os 6 ajustes de homol:** regra de status do FT, diagnóstico do agente no Resumo,
filtro/ordenação do agente na lista, score de confiança só com dado das tabelas (confianca.py copiado), padrão da lista
(aptos validáveis, assertividade desc, score alta; filtros "Apto valor" e "Apresentação: 44"), proteções de NaN. A coluna
Confiança FICA na lista de prod. Ficaram só em homol: marca HOMOL, decimais como texto, colunas Produção 07–08/10 / ② Homol / Δ,
ingerir de homol. Em prod o rótulo da situação virou "Ajuste entrou em homologação depois desta análise" e o
agente_para_painel.py marca, para análises de produção, que o ajuste de homol "ainda não estava nesta execução de produção".
Arquivo do agente de prod: `python ferramentas/agente_para_painel.py <app prod> analises_prod_1510 analises_caso` (230 processos).

**A situação de cada problema vem só de marcação estruturada:**
- o código de tema T01–T50 nas análises da noite de 09→10/10;
- as marcas "já endereçado: …" nas análises de 13/10.

Texto livre dava falso positivo, e por isso não é usado.

**Categoria "premissa não endereçada" (correção dela, 15/10):** citar uma premissa não basta. Só conta como premissa não endereçada quando a seção citada está como não endereçada na tabela "Premissas × esteira" (`ft_arvore_divergencias/premissas/premissas_situacao_esteira.json`). O resto é erro da IA, inclusive quando não há número de seção. O exemplo dela: a IA não achou o salário no holerite, é erro da IA. Com essa regra, as premissas caíram para 13 problemas.

**Why:** o app de produção é a régua oficial e é usado por outras pessoas; mudança nele sem pedido explícito quebra a confiança.

**How to apply:** antes de editar qualquer arquivo em `bt-prod-apps`, confirmar qual app o pedido cita. Se a mudança "deveria valer para os dois", perguntar antes. Ver [[apresentacao-staff-assertividade]].
