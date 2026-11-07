---
name: painel-copia-enxuto-1810
description: "Painel cópia (desde_2026-10-14) redesenhado em 18/10: 3 telas gerais, template próprio, backup do antes; o que ela pediu para manter"
metadata:
  node_type: memory
  type: project
  originSessionId: 4ef2053e-65b4-47d2-aab1-f28c8dfccaf6
  modified: 2026-10-20T17:29:56.496Z
---

Em 18/10/2026 a Raíra pediu para enxugar o painel cópia (`ft_paineis_parciais/desde_2026-10-14`), "é só para mim por ora".

**Como ficou:**
- Três telas gerais:
  - **Rodada**: Placar mais o resumo da Elegibilidade, com direção ▲/▼, score de confiança e não aptos por motivo.
  - **Problemas do agente**: substitui "Onde o erro nasce" e "Acurácia por verba".
  - **Premissas do manual**: os problemas do agente agrupados pela seção do manual que eles citam, com a situação de cada item na esteira, tirada de `premissas_situacao_esteira.json`.
- Saíram: Elegibilidade, Confiança do dado e Versões de prompt.
- Lista de casos: 4 filtros (casos, direção, confiança, agente) mais a busca por CNJ. A ordenação é pelo clique na coluna.

**Segunda leva, ainda em 18/10 (pedido dela):**
- Funil na Rodada: entraram → aptos → apto valor → apto valor com confiança alta, com a assertividade de cada degrau.
- Subcategorias na tela do agente: categoria → verba → o que errou. As duas últimas são montadas por palavra-chave (verba pelo campo verba, o que errou pelo título) e 88% dos problemas caem num grupo com nome.
- Período (7/15/30/90 dias e datas) de volta em todas as telas.
- As setas ‹ › do caso andam na lista filtrada.

**Tela do agente virou árvore com colunas fixas** (problemas, casos, ▲, ▼):
- Níveis: categoria → verba → o que errou → verba específica. O último nível só existe em HE e reflexos; nos reflexos há o grupo "herdado do erro do principal".
- A etapa (P4, P9a…) foi descartada como subcategoria: o agente cita a etapa em só metade dos problemas, e "P1" às vezes é "problema 1".

**Terceira leva (18/10):** aba **Verbas** de volta, como gráfico de faixa por verba:
- Traço fino do pior ao melhor caso, traço grosso para a metade do meio, bolinha na mediana, meta de 80% tracejada.
- Chips de categoria com várias escolhas. O reflexo entra na categoria da verba-base.
- Filtros: natureza, mínimo de casos, ordem, busca e dano moral fora.
- Reflexo medido pelo **erro próprio** como padrão (decisão dela, 18/10, "não é fair" medir com o erro da base). A conta é 1 − |(refl IA ÷ base IA) ÷ (refl PJC ÷ base PJC) − 1|. Há uma chave para ver "como está".
- Nos aptos: 923 comparações com mediana 69,8% como estava; 804 com mediana 90,8% no erro próprio. O DSR sobre HE continua ruim mesmo assim.

**19/10 — o score de 18/10 à noite mudou o painel** (feito em outra sessão, no `aplica_score_jev.py`):
- Faixa nova "restrita". A faixa passou a ser decidida pelo lado do erro. O caso inapto ficou sem selo.
- O template da cópia não quebrou com isso. Foram ajustados só dois textos da Rodada que descreviam a regra antiga ("1 ponto = média", "média + baixa").

**20/10 — aba "Não calculadas"** (perfil das verbas sem valor da IA; só principais e rescisórias, sem reflexo):
- Seis situações: caso travado antes do P10; deferida e o PJC calculou; P9a não calculável; depende de documento; nenhum dos dois calculou; o PJC calculou e a IA nem deferiu.
- A "travado" foi separada porque engolia quase tudo de "deferida e o PJC calculou" (936 → 24).
- Mostra por verba: vezes, casos, % sem valor (sobre as vezes em que a IA deferiu) e R$ no PJC.

**O que ela pediu para manter:** as abas do caso (Resumo, Quadro, Jornada/Cartão, Histórico Salarial, Rodadas), a tela da verba com os prompts e o score de confiança com filtro, que ela vai usar em reunião.

**Onde está:**
- A cópia tem template próprio: `desde_2026-10-14/template_telas.html`. O template de produção não foi tocado.
- O `jev_testes/aplica_score_jev.py` usa esse template quando ele existe e injeta as premissas.
- Backup da página, do template e do script de antes: `desde_2026-10-14/antes_redesenho_1810/`.
- Para voltar ao antes: apagar o template da cópia e rodar o aplica_score_jev.py de novo.

**Why:** havia telas e filtros demais, e coisa que o agente já faz. A aba Premissas antiga lia as observações do PJC, e só 4 de 322 casos citam premissa ali.

**How to apply:** mudança na cópia é feita no template da cópia, nunca no de produção. Ver [[painel-revisao-ux-pendente]] e [[score-confianca-calculo]].
