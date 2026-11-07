---
name: refinamento-bt089-2910
description: "Refinamento por verba começou em 29/10 pela BT089: 8 famílias, cartão com mediana 27% × jornada fixada 80%, proposta de 'cartão gerado da jornada fixada'"
metadata:
  node_type: memory
  type: project
  originSessionId: c2a87838-1030-4f07-94e5-d99b265ad475
  modified: 2026-10-30T00:30:33.359Z
---

Em 29/10/2026 a Raíra começou o **refinamento por verba** a partir dos problemas do agente no painel cópia (processos de 23/10 em diante). A primeira verba foi a BT089 (HE além da 8ª). Página: https://claude.ai/artifact/NK4CMKadSHQjUWoLXPrqte.

**Números**
- Aptos: mediana de 70,3%; 135 de 325 verbas com 80% ou mais.
- Pela rota do cartão: mediana de 27% (11 de 80). Pela jornada fixada: 80%.
- Agente: 377 problemas da esteira em 172 casos.

**As 8 famílias, na ordem da esteira**
1. Jornada não estruturada (P4).
2. 7h20 e o limite semanal (P9a, Caso B item 2).
3. Intervalo reduzido em todos os dias: o P9a não lê o `dias_por_semana` da BT007.
4. Cartão: 6 defeitos de código.
5. Horas zeradas no P9b.
6. Súmula 85: o P9a marcou falso e a trava não disparou.
7. Base.
8. Abatimento incondicional.

**Proposta central:** gerar um cartão a partir da jornada fixada e passá-lo pelo motor do cartão. Isso resolve as famílias 1, 2, 3 e 5, mas só depois de corrigir o motor.

**Decisões pendentes dela**
- 7h20 × 8h.
- Usar os PJCs do cartão como gabarito.
- Corte de cobertura do cartão.
- Campo que sinaliza "dedução afastada" no P4.

**How to apply:** nas próximas verbas, repetir o mesmo método:
- Usar `agente_por_caso.json` junto com o painel, filtrando pelo `codigo` da verba.
- Classificar pelo título do problema.
- Ler o prompt da tabela de agentes e o código do origin/main.
- Ver a skill `boas-praticas-prompt` do back, que proíbe regra de cartão em prompt sem gabarito.

Ver [[cartao-ponto-codigo-back]] e [[frequencia-cartao-jornada-fixada]].
