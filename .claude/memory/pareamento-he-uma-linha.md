---
name: pareamento-he-uma-linha
description: "Regra de 16/10 'uma linha do PJC por verba' derruba a assertividade por verba da HE quando o PJC fatia a mesma HE (período, adicional × hora cheia, 50/75/100%); 100 aptos afetados (29/10)"
metadata:
  node_type: memory
  type: project
  originSessionId: c2a87838-1030-4f07-94e5-d99b265ad475
  modified: 2026-11-05T18:19:11.804Z
---

Em 29/10/2026 a Raíra desconfiou do pareamento da hora extra. Casos que ela citou:
- 0000312-48.2025.5.12.0031
- 0010011-13.2025.5.15.0150

**O que está acontecendo.** No `gerar_telas`, desde 16/10, a verba principal da IA casa com UMA linha do PJC:
- a escolhida é a de base mais parecida (`alinha_base`), e as demais viram "só PJC";
- o PJC fatia a mesma HE por período (ATÉ/APÓS uma data), por "ADICIONAL DE HE" × "HE" (Súmula 85) e por adicional convencional (75%/100%);
- os reflexos e as indenizações já somam essas fatias; as principais de HE, não;
- o `familia_he` só é calculado quando a IA tem 2 ou mais HEs ou uma "só IA".

**Medido nos aptos de 23/10 em diante:**
- 100 de 374 casos com BT089 têm linha de HE do PJC solta, somando R$ 3,9 mi.
- Nesses 100 casos: mediana por verba 16% (20 de 86 com 80% ou mais) contra 65,6% somando a família (34 de 100).
- Exemplo: 0010011 vai de 0% a 99,7%.
- O corte por rota se mantém (cartão 21% × fixada 82% somando a família). Já os números da página BT089 ([[refinamento-bt089-2910]]) estão contaminados.

**Status:** a aba Verbas e o gerador não mudaram; a regra de 16/10 foi decisão dela, por causa do 0000740-56.

**Aba "Verba consolidada" (feita em 29/10, a pedido dela)**
- Onde está: só no template da cópia (`desde_2026-10-14/template_telas.html`, função `agregaConsol`). O backup do template está em `antes_verba_consolidada_2910/`.
- Como funciona:
  - cada linha do PJC ganha um código e, dentro do caso, as linhas com o mesmo código são somadas;
  - BT089, BT081, BT001, BT011, BT003, BT004 e BT007 ficam separados;
  - hora extra sem tipo no nome vai para o único tipo de HE comum da IA;
  - quando a IA tem dois ou mais tipos, vira "HE somadas" e fica marcada como atribuída.
- Ela recusou juntar famílias inteiras ("não tão agregado": 8ª separada da 7ª/8ª).
- Página do painel desde 23/10 regerada às 21h54, sem score.
- Aptos: BT089 sobe de 76% (45% dos casos com 80% ou mais) para 79% (49%). O 0010011 fica com 99,7% e o 0000312 com 78%.

**Também acontece com comissão (05/11, bench Jusquant).** No caso 0100615-91.2021.5.01.0039:
- a BT024 da IA (R$ 29.631) casou com a fatia de R$ 278 do PJC, que dá −10451%;
- as fatias "ATÉ 10/11/2017" e "APÓS 11/11/2017" (R$ 24,4 mil) ficaram como "só PJC";
- o mesmo efeito aparece nos reflexos da comissão.

No bench, a comparação foi feita somando por família.

**How to apply:** antes de ler a assertividade por verba de HE, somar as fatias. Corrigir no gerador só com o ok dela, porque afeta o painel de produção. Ver [[painel-homol-nao-mexer-prod]].
