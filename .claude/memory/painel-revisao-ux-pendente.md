---
name: painel-revisao-ux-pendente
description: "Pedido de 16/10 para depois — revisar o painel de validação (muitas abas, muita informação por aba, caso começa por problema em vez da tabela)"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-10-16T13:22:08.072Z
---

Em 16/10/2026 a Raíra pediu, para depois da apresentação de segunda (19/10), revisar o painel de validação em si: tem muita aba, muita informação em cada aba, e a análise do caso começa pelos problemas em vez de começar pela tabela de verbas (PJC × IA). A ordem desejada é tabela primeiro.

Junto com isso foi aprovada a arquitetura em etapas fora do gerador do painel: (1) tabela do PJC por processo, uma linha por verba como está no PJC (tudo que o PJC separa fica separado, inclusive fatias de período); (2) conferência da leitura contra o Resumo do PDF; (3) tabela da IA; (4) tabela comparativa com a regra de casamento; (5) medidas; (6) o painel só desenha. Passos 1–2 começaram em 16/10 nos aptos; 3–6 ficam para a semana seguinte.

**Why:** hoje leitura, casamento, teto e totais vivem dentro do gerar_telas (3.270 linhas), e só dá para conferir um caso gerando a página inteira.

**How to apply:** ao mexer no painel, perguntar se a mudança cabe numa das etapas separadas; ao revisar a UX, abrir o caso pela tabela. Ver [[apresentacao-staff-assertividade]].
