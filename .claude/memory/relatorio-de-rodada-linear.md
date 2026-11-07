---
name: relatorio-de-rodada-linear
description: "Como a Raíra quer relatórios de avaliação de rodada (homol × produção, hackathon, ajustes): leitura linear, crítica, regressão primeiro"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-13T12:50:54.836Z
---

Relatório que avalia uma rodada de ajustes segue esta ordem, igual no hackathon e no relatório de ajustes:
o que fizemos → resultado (números) → diagnóstico (funcionou / em parte / não funcionou) → **primeiro foco: o que não funcionou**,
cada item num bloco só (tema · prompt como era em produção × como ficou · por que piorou ou não resolveu · ajuste sugerido logo abaixo) →
depois os temas ainda não endereçados no mesmo formato. Nada de cards de um lado e "ajustes por prompt" de outro.

Em 13/10 ela reforçou: o centro do relatório é **problema a problema**, cada um com o que é → o que fizemos (ou "nada") →
resultado → por quê (se não funcionou ou funcionou em parte) → o que deveria acontecer → próximo passo, agrupado por família.
Ela rejeitou tabelas de cards separadas de blocos de regressão.
- Resultado medido só no componente que o problema mexe (desconto, salário, base, quantidade, reflexo próprio), nunca no total, para não confundir com compensação de erros. Sempre sobrecálculo e subcálculo separados, com o número de processos.
- Problema que piorou sem card é "efeito colateral de X".
- Problema de um processo só vai para a lista de exceções a validar.
- Detalhe vai em anexo recolhido.

**Why:** em 09/10/2026 ela disse que o relatório misturava problema antigo com problema causado pelos ajustes, que "funcionou e gerou regressão"
é "não funcionou", que empilhar instruções sem dizer como era e o que mudou não é crítico, e que pode ficar longo.

**How to apply:** separar sempre o que veio dos ajustes recentes do que é antigo; regressão vem antes; mostrar o diff real produção → nova
versão e, quando o texto do prompt não mudou, dizer que a causa está fora dele (insumo, código, variação da IA). Prompts de análise no topo
do hackathon. Também pediu (09/10) olhar holístico, como head de produto e principal prompt engineer: ligar problemas que nascem da mesma
mudança (ex.: glossário pondo AGIR/GERA no BT031 → dedução, abatimento, base da HE) em "cadeias", marcando o que é visto nos dados e o que é hipótese.
Depois (09/10) pediu que os ajustes venham **agrupados por família** (problemas que mexem no mesmo dado juntos, na ordem
da esteira, com "ordem de ajuste" no topo), não ordenados por valor nem separados em ontem × novos: senão o time ajusta e
tem que voltar no mesmo texto. Família só junta problemas que **apareceram** na rodada; hipótese de problema que nunca apareceu não entra nem justifica
ligação (sem ligação observada, o item vai para "independentes"). Ela não quer seção genérica de "leitura de produto"; prefere o concreto por família. Diff de versões tem que incluir recursos do código (resources/glossario.json mudou na staging sem o prompt GLOSSARIO mudar). Ver [[ajustes-prompt-foco-unico-enxuto]] e [[paginas-so-rodada-mais-recente]].
