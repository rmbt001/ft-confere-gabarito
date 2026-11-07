---
name: multiplos-contratos-inelegivel
description: Processo com mais de um contrato de trabalho deve ser inelegível (decisão da Raíra em 14/10/2026); hoje nenhuma regra faz isso
metadata:
  node_type: memory
  type: project
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-14T11:53:56.011Z
---

**Decisão:** em 14/10/2026 a Raíra decidiu que processo com múltiplos contratos de trabalho deve ser inelegível (não calculável), como a jornada mista ([[jornada-mista-nao-calculavel]]).

**Caso que motivou:** 0020998-32.2024.5.04.0221. O P1 pegou só a admissão do 2º contrato (01/2024), e o 1º contrato inteiro (01/2021 a 03/2023) ficou sem cálculo: R$ 59 mil a menos.

**Hoje não existe regra:** em 14/10, a busca por "contrato" com essa ideia não acha nada nos prompts DADOS_INICIAIS v9, INFOS v13 e ROTEAMENTO v18, nas premissas nem no código da staging.

**Why:** a esteira monta um cadastro só (uma admissão), e um contrato fica de fora em silêncio.

**How to apply:**
- Nos relatórios, tratar esses processos como fora de escopo, e não como erro de cálculo.
- Ao propor o ajuste, o lugar natural é o P1 detectar mais de um contrato e marcar o processo como não calculável.
