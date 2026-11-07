---
name: perfil-reclamante-assertividade
description: "Perfil de reclamante/reclamada × assertividade (21/10, pergunta do CCO) — gerente de banco e cartão pesam; dentro da alta o perfil quase não separa"
metadata:
  node_type: memory
  type: project
  originSessionId: 65294aac-f40b-43ce-aeee-cf666f5b8658
  modified: 2026-11-04T21:07:38.929Z
---

Em 21/10/2026 a Raíra pediu, por causa de uma pergunta do CCO, para ver se existe um perfil de reclamante ou de reclamada nos casos de alta assertividade. A base foram os 273 aptos comparáveis da cópia `desde_2026-10-14`, processados entre 16 e 19/10. O cargo, a idade e o contrato ativo vieram do P1 (`raw__ft_lift_tb_resultado_dados_iniciais_ia`, ligado por `cnj_processado`). 73% dos casos têm cargo.

**Todos os aptos (50% com ≥ 80%):**
- Banco 39% × fora de banco 55%. O efeito se mantém na logística (OR 0,42).
- O que pesa no banco é o gestor: o bancário gestor (gerente, coordenador, supervisor) fica em 18%. O bancário não gestor fica em 58%, igual a quem é de fora.
- Por reclamada: Banco do Brasil 0/7, Caixa 25%, Bradesco 29%, Itaú 48%, Santander 60%.
- Jornada pelo cartão: 27% (OR 0,24). É o sinal mais forte, no banco e fora dele.
- Período de até 24 meses: 86% (n = 22). Contrato ativo: 36%. Trabalhador operacional ou de fábrica: 36%. Com dano moral: 61%.
- Idade e salário não separam.

**Dentro da alta (99 casos, 77% com ≥ 80%):** o perfil quase não separa mais (banco 72% × fora 79%). A exceção é o bancário gestor, com 33% (n = 6). No apto valor ∩ alta ele fica em 1/5, sempre calculando a menos.

**Jornada fixada (123 casos, 55% com ≥ 80%):** a complexidade quase não separa.
- 5 dias: 59%. 6x1: 55% (n = 11). 1 regime: 52%. 2 ou mais regimes: 60%.
- Horas por dia e trabalho noturno: sem efeito.
- A exceção é a fixada sem dias da semana no regime (15 casos, 27%).

**Por que o cartão fica em 27%:** pelos dossiês de `analises_prod_1510`, os problemas somam 94% do PJC no cartão, contra 43% na jornada fixada. Quase tudo é a menos, e não há uma causa única:
- 56% dos casos: regra da apuração sobre o cartão. Limite semanal ignorado (33h36, 30ª), sábado como repouso no DSR, intervalo pago só nos minutos suprimidos, quantidade arbitrada ignorada.
- 54%: abatimento do que foi pago, dos dois lados. É a OJ 415 ou a Súm. 109 aplicada quando a decisão não manda, ou o abatimento incompleto.
- 46%: leitura do cartão incompleta. Com menos de 12 dias por mês, só 18% batem.
- Também aparecem reflexos negativos herdados.
- Quem tem cartão é Petrobras, banco e turno: as regras são mais difíceis.

**Notebook (21/10, pedido dela):** `ft_analises/perfil_reclamante_jornada.ipynb`, no Visual Guide.
- Barras de composição (bate em verde, a menos em cinza, a mais em salmão), a logística e a jornada fixada.
- Mecanismos do cartão × jornada fixada, pelo agente, com os CNJs.
- O `pyarrow` foi adicionado ao ambiente do ft_analises para ler o cache do app.
- O gerador ficou no scratchpad da sessão (gera_nb_perfil.py). Para mudar, editar o .ipynb.
- Com o cargo mais amplo, os bancários gestores passaram a 30, e 17% deles batem.

**04/11 — refeito no painel desde_2026-10-23 (1.110 aptos, 23/10–03/11): o perfil do RECLAMANTE deixou de separar.**
- Contrato curto: 86 → 52%. Escritório: 62 → 46%. Gerente de banco: 17 → 39%. Bancário não gerente: 40%.
- "Perfil bom" × fora: 49 × 41%. Na faixa alta: 80 × 73%.
- O que separa é o PROCESSO:
  - cartão 25% × fixada 50% × sem jornada 57%;
  - sem hora extra 58% (na alta, 83%);
  - só verbas de valor fixo 78% (n = 51);
  - contrato ativo 39%.
- Medo do CCO (Rafa: "um sobra comida, o outro passa fome, na média estamos sem fome"):
  - **na alta**, os erros somados sem compensar entre processos ficam em 18% do PJC, contra 42% nos aptos;
  - 168 de 194 com 80%+ seguem com 80%+ sem compensar verbas;
  - mas com 4 ou mais verbas, só 20 de 36 seguem.
- Números em `apresentacao_perfil_2110/dados/` (extrai_press, numeros_press, combos_press).
- Press release pedido pelo chefe dela em 04/11: "focar no que fazemos bem", não venda.

**Why:** o score já absorve a maior parte do perfil (cartão, restritas). O que sobra é o gerente de banco: 7ª/8ª hora, cargo de confiança, gratificação.

**How to apply:** para o CCO, a resposta é que o perfil explica quem entra na alta, e não o acerto dentro dela. A única exceção é o gerente de banco, candidato a sinal no score se ela pedir. O n é pequeno: conferir com rodadas novas. Scripts no scratchpad da sessão: monta_perfil.py, analisa_perfil*.py. Ver [[score-confianca-calculo]] e [[apto-valor]].
