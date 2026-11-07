---
name: jornada-mista-nao-calculavel
description: Processo com jornada mista (documental e fixada) é classificado como não calculável; não baixar peças nem rodar o analista nele
metadata:
  node_type: memory
  type: feedback
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-12T23:49:05.847Z
---

Jornada mista ("mista documental e fixada") torna o processo **não calculável** por regra da casa. A trava do CARTAO_PONTO, com o erro "Jornada mista documental e fixada não é apurável", é intencional. Esses processos não entram no download de peças nem na análise caso a caso.

**Why:** a Raíra disse em 12/10/2026: "jornada mista a gente classifica o caso como não calculável — não precisa ser as peças desses". Na homol de 09→10/10, 23 dos 31 processos que pararam depois do P4 foram barrados por essa trava; a lista está em `ft_arvore_divergencias/homol/_noite_jornada_mista.txt`.

**How to apply:**
- Antes de baixar peças ou de soltar o analista, tirar os processos com status ERRO por jornada mista. Esse status fica na tabela STATUS, dentro de `caso_raw__<CNJ>.pkl` no cache do app.
- Na comparação homol × produção, não contar a queda de erro desses processos como melhora, porque a IA neles vale R$ 0.
- Dossiês que propuseram "separar o Ramo B da mista" são sugestão, não regra. Só levar adiante se ela pedir.

Ver [[agente-noite-0910-onde-parou]].
