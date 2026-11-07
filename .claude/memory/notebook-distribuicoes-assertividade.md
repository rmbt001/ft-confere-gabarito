---
name: notebook-distribuicoes-assertividade
description: "Notebook de distribuições da assertividade (17/10) em Repos/ft_analises — grupos, gráficos, ambiente uv, cuidado com score de 16/10 aplicado duas vezes"
metadata:
  node_type: memory
  type: project
  originSessionId: 81f8c132-a155-43c5-aabf-e02934646060
  modified: 2026-10-19T13:57:56.877Z
---

Em 17/10/2026 a Raíra pediu um notebook para ver a assertividade como distribuição (histograma claro + KDE, curvas isoladas e sobrepostas, "descolar para a direita"): aptos, não aptos, apto valor, faixas do score.

Fica em `Repos/ft_analises/assertividade_distribuicoes.ipynb`, com ambiente uv próprio (`ft_analises/.venv`, pyproject). O venv do app não tem matplotlib e não deve ser mexido. Lê `ft_paineis_parciais/desde_2026-10-14/validacao_calculos.json`, e o caminho da homol fica comentado na célula de parâmetros. Comparável = `comPJC` do painel. O gráfico corta em −100%. Ele cobre a curva de sobrevivência (% ≥ x), a função de deslocamento por decil, a razão IA/PJC em log2, o bootstrap com Mann-Whitney e δ de Cliff, as faixas de valor da IA, os pontos do score, os motivos de inaptidão e as listas de escapes.

**Score de 16/10:** o notebook importa `score` de `jev_testes/aplica_score_jev.py` e só aplica se `confianca.versao` não começar com "2026-10-16". Às 08h34 de 17/10 outra sessão rodou o aplica_score_jev no JSON, e reaplicar contava em dobro (gerente geral, travas). O gerador do notebook ficou no scratchpad da sessão. Para mudar, editar o .ipynb direto.

**Preferências dela (17/10):** usar o Visual Guide LIFT nas análises (fontes Onest/Sora em ft_analises/fonts; aptos salmão, apto valor preto, não aptos cinza). Faixas do score com 3 matizes distintos, validados para daltonismo: alta #2160a8, média #e8a33d, baixa #c0484f, e formatos ●■▲ no gráfico de dispersão (o azul ordinal não dava para distinguir). KDE com `ADJUST = 2`, como o adjust do density() do R. Quer sempre o recorte apto valor × faixa.
Às 08h54 de 17/10 o JSON ganhou a faixa `a_calcular` (16 aptos), mostrada como grupo próprio.

**19/10:** o notebook foi atualizado para o score de 18/10 à noite (faixa pelo lado do erro, faixa "restrita" em cinza tracejado com ◇, porque uma 4ª cor não passa no teste de daltonismo). Ele usa a faixa gravada no JSON e só importa o aplica_score_jev se faltar score: o import exige `dotenv`, que não está no venv do ft_analises. O gerador continua no scratchpad da sessão de 17/10 (`gera_nb.py`). Leitura: 264 aptos; alta 78% ≥ 80, média 37%, baixa 23%, restrita 50%. Sobrecálculo: baixa 26%, restrita 39%, alta 5%. Mas a média (47%) não tem mais subcálculo que a baixa (51%).

Primeira leitura (prod 14–17/10, 150 aptos): alta 75% ≥ 80 · média 50% · baixa 23%, com todos os pares significativos (Cliff 0,37–0,59). Apto valor 64% × fora do valor 34%. Aptos com IA < R$ 20 mil: 13% (n=22). 4 dos 7 escapes da alta têm IA de R$ 2–5,5 mil contra PJC de R$ 79–305 mil.

**18/10:** segundo notebook, `ft_analises/score_dois_selos.ipynb`: pontos × assertividade, forest plots (Fisher + BH e
logística conjunta) para "bate 80%" e "calcula a mais", árvore, os dois selos (acerto × risco de sobrecálculo) com
densidades, matriz da compra e listas de casos. `statsmodels` foi adicionado ao pyproject do ft_analises (uv add, com
UV_LINK_MODE=copy por causa do OneDrive). Gerador no scratchpad da sessão (gera_nb_selos.py); para mudar, editar o .ipynb.

Ver [[score-confianca-calculo]], [[apto-valor]].
