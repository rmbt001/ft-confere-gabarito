---
name: apresentacao-perfil-2110
description: "Deck separado \"Perfil do processo × assertividade\" (21/10) para o CCO — pasta apresentacao_perfil_2110, gerador python-pptx no modelo do board"
metadata:
  node_type: memory
  type: project
  originSessionId: 65294aac-f40b-43ce-aeee-cf666f5b8658
  modified: 2026-11-04T21:37:23.770Z
---

Em 21/10/2026 a Raíra pediu um deck **separado**, no estilo do deck de assertividade de 19/10 ([[apresentacao-1910-pptx]]), com os achados de [[perfil-reclamante-assertividade]]. É só para tirar insights. O perfil **não** entra no score: ela disse "não quero usar no score".

**Onde está:** `Repos/apresentacao_perfil_2110/`.
- `base_ppt/`: cópia do v8 de 19/10, usada só como modelo.
- `dados/extrai_perfil.py` gera `perfil_2110.json`. Ele junta o painel cópia, o P1 e o agente analista (`analises_prod_1510`).
- `gera_deck.py` grava `versoes/perfil_assertividade_<hora>.pptx` e nunca sobrescreve. Os dois scripts rodam no venv do ft_analises.

**Os 7 slides:**
1. Capa.
2. Em uma página: cards "calcula bem" e "erra", com o resumo da faixa alta.
3. Quem acerta e quem erra.
4. Banco ou gerente.
5. Jornada fixada, simples ou complexa.
6. Cartão: as 4 causas do agente, cartão × fixada.
7. Dentro do score: perfil bom × fora, por faixa.

**v 13h07 (21/10), pedidos dela:**
- ▼ e ▲ passaram a mostrar o **número de processos**, não %.
- Slide novo, "Cartão ou turno?" (`dados/turnos_cartao.py`), para testar a hipótese dela de que o que pesa são os turnos complexos. Os dados não confirmaram: no cartão, com turno 7 de 27 e sem turno 4 de 14, e os sem turno são em boa parte bancários (0 de 7). Com jornada fixada e turno, 58%.
- Nas causas, "sábado no DSR" saiu: é regra da casa (ver [[premissas-de-calculo-bt]]).

**v 13h11 (21/10): o cartão saiu do deck inteiro.** Ela: "não tem a ver com perfil e sim com método".
- O perfil bom passou a ser só: não é gerente de banco e não é operacional (207 aptos).
- Na alta: 82% × 43%.
- O deck ficou com 6 slides.
- A causa do cartão vai ser investigada no código do back (bt-lift-fast-track-back).

**v 13h46 (21/10): versão narrativa, 11 slides** (pedido dela: "falta coisa para além dos dados").
- Ordem: capa → como ler (régua de R$ 100 mil) → em uma página → quem acerta → caso fácil → banco ou gerente → caso gerente → jornada → caso operacional → dentro do score → para levar.
- Caso fácil: 0001258-46.2024.5.07.0014, 99%.
- Caso gerente: 0000752-81.2022.5.10.0006, 44%. A IA abateu a gratificação inteira; o acórdão limita a 55%.
- Caso operacional: 1000991-22.2023.5.02.0082, 43%. Prescrição fixada na sentença + salário de 2020 em dobro; o score já mandou para a baixa.
- O 0010375 (Santander) NÃO serve de exemplo de erro: pela Premissa 10.0, abater a gratificação inteira está certo ali.

**v 13h51 (21/10), feedback dela:**
- O "Como ler" (régua) saiu: "ficou pior".
- Ela gostou do caso que acerta.
- O caso do gerente "veio do nada", então virou "Um caso que a IA erra" logo depois do que acerta. O operacional virou "Outro caso que a IA erra".
- "E a jornada?" ficou depois do operacional.
- Cada caixa abre ligando no slide anterior, porque a narrativa "não estava fluida". São 10 slides.

**04/11: o chefe dela rejeitou o deck.** Pediu "focar no que fazemos bem", quase como um press release. Ela: "não é venda", e o perfil tem de aparecer.
- Virou a página de press release `apresentacao_perfil_2110/press_release.html` (gerador `gera_press_release.py`, dados de `dados/extrai_press.py`, painel desde 23/10).
- Publicada em https://claude.ai/artifact/2cXbKQGjKH4RQQ34ycyEmj.
- Eixo: perfil do PROCESSO (o do reclamante deixou de separar).
- Responde ao medo do Rafa (CCO) de média que esconde compensação: erros somados sem compensar 18% na alta × 42% nos aptos, e verba a verba.
- A citação ficou como espaço a preencher.

**04/11 noite: press release v5 + deck.**
- Pedidos dela na página:
  - exemplo dos dois processos de R$ 100 mil antes do número e tabela em reais;
  - sem a seção "melhorando" e sem anexos ("não dá para investigar caso a caso");
  - sem cartão;
  - "Como a conta é feita": valor devido sem correção e juros, FGTS e honorários fora, regras da casa;
  - 6 casos com um mês do cálculo.
- Deck: `gera_deck_press.py` → `versoes/press_release_<hora>.pptx`, 12 slides. Moldura do gera_deck e números do gera_press_release, para os dois sempre baterem.

**Formato:** barras 100% feitas com formas (editáveis), nas faixas de assertividade do deck de 19/10. A conferência visual é pelo PowerPoint via COM (Export PNG).

**How to apply:** se ela editar o deck, fazer backup antes e criar os slides novos numa cópia, como no deck de 19/10. Os números mudam se o painel cópia for regerado: rodar `extrai_perfil.py` de novo.
