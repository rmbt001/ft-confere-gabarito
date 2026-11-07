---
name: apresentacao-1910-pptx
description: "Deck de assertividade de 19/10/2026 em PPTX (pasta apresentacao_assertividade_1910): resultado primeiro, gráfico de faixa como linguagem visual, gerador python-pptx sobre o modelo do board"
metadata:
  node_type: memory
  type: project
  originSessionId: 69b23582-ab8f-4216-8985-45c63e73ae9d
  modified: 2026-10-19T17:38:30.260Z
---

Em 19/10/2026 a Raíra pediu para refazer a apresentação de assertividade **em PPT**, para ir editando junto. O feedback da anterior: pouco intuitiva e sem mostrar onde estamos. Ela pediu um deck **bem visual, sem tabelas**.

**Onde está:** `Repos/apresentacao_assertividade_1910/`.
- `base_ppt/`: o .pptx dela, com o modelo do board e slides de exemplo.
- `dados/`: `casos_1910.json`, extraído da cópia do painel (desde_2026-10-14) por `extrai_dados.py`.
- `gera_deck.py`: roda no venv do `ft_analises`, onde o python-pptx foi instalado com uv. Mantém a capa do modelo, descarta os exemplos e monta a moldura do board (migalha em Sora 13, título em Sora 28 com prefixo em negrito, logo copiado de um slide de exemplo, número da página tirado do layout).
- `versoes/`: os decks com data e hora.
- A conferência visual é pelo PowerPoint via COM: `Slides(i).Export` para PNG. LibreOffice e poppler não estão instalados.

**NUNCA sobrescrever nem apagar o deck que ela edita** (ela reclamou em 19/10: "da última vez você sobrescreveu").
- Antes de mexer: copiar o arquivo dela para `versoes/backup/` com o horário.
- Slides novos entram numa **cópia** (`acrescenta_slides.py <deck dela>` grava `<nome>_com_novos_<hora>.pptx`), na posição da narrativa e com "NOVO" nas notas.
- Conferir pelo hash que o arquivo dela não mudou.

**Estilo dela, tirado das edições:**
- Texto todo em grafite, nada em preto.
- Título da caixa em linha própria, 15 pt negrito; corpo 14 pt; fecho em vermelho.
- Rótulos das faixas em vermelho.
- Fonte sem "(cópia)".

**v7 (14h38, `monta_v7.py`), feedback de um revisor:**
- **Um denominador só no funil:** −91%, sobre os 689 com cálculo.
- **676 = 689 − 12 com gabarito a corrigir − 1 sem gabarito legível**, explicado na fonte do slide 3.
- **Restrita:** é questão de regra, não de acerto. A aptidão ainda não a tira, e por isso ela está nos 152.
- **Slide 7:** os 95 da faixa alta são de qualquer valor; os pontos fora da faixa sombreada são só referência.
- **Slides 8 e 9:** títulos mais modestos. O 8 diz que o gráfico mostra todos os aptos; o 9 cita a cauda (saldo de salário 57%, indenização 67%, férias 69%).

**v6 (13h02):** o slide 3 ganhou a caixa "mesmo resultado com 3× mais processos".
- **Na apresentação anterior:** o anexo de 15/10 era um teste em homologação com um recorte de casos de 2026. Eram 271 rodados, 37 apto valor e 19 na faixa alta, com 79% de 80% ou mais.
- **Agora:** 1.031 rodados, 152 apto valor e 61 na faixa alta, também com 79%.
- O "44" daquela época era outro recorte: aptos de qualquer valor, na comparação antes × depois.

**v5 (19/10, 12h45, `monta_v5.py`):**
- **Tom:** passar a impressão de que a faixa alta está pronta para virar, sem dizer explicitamente.
- **Erro mapeado, não "jornada":**
  - horas extras 100%: a IA zera o feriado quando não sabe que foi trabalhado;
  - horas extras: ainda não tiramos férias fora da ficha nem faltas nos dias com hora extra;
  - 7ª e 8ª: a gratificação é deduzida inteira, e não até 55% do salário.
- **Média e baixa erram para lados opostos:** a média tem 48% do valor calculado a menos; a baixa, 40% do valor a mais.
- **A restrita não barra processo bom:** tem 20% do a mais, 2% do a menos e nenhum processo >20% abaixo.
- **A faixa alta fica com só 17% do a mais.**
- **Slide 7:** três exemplos destacados no gráfico.

**v4 (19/10, 12h30, `monta_v4.py <deck de trabalho>` → `versoes/assertividade_ft_v4_<hora>.pptx`):** a narrativa é uma história só, não slides soltos (pedido dela).
- Cada caixa abre ligando no slide anterior; nada de "Como ler:" repetido.
- Sequência:
  1. score (como a assertividade se distribui nas faixas);
  2. distribuição ("o erro é consistente ou espalhado?", sem o exemplo da fome);
  3. faixa alta ("o erro tem direção?": IA abaixo em 61%, acima em 28%, mediana 98%; errar para menos é o lado seguro da compra);
  4. verbas mensais e verbas de valor fixo, no estilo da aba Verbas, em PNG;
  5. passo a passo;
  6. próximos passos (ajustes, mapeamento, fechar score, revisar casos no painel).
- Faixas de assertividade nas cores dela: ≥ 95% vermelho, 80–95% salmão claro, 50–80% cinza, < 50% grafite.
- A curva de acerto ficou oculta no fim; os slides antigos 12 e 13 saíram.
- Ao tirar slides com python-pptx, **salvar e reabrir antes de acrescentar**, senão o .pptx sai com nomes de parte repetidos.

**v3 (19/10, 12h):**
- Slides novos:
  - "Score: um guardrail", que explica o porquê com o fluxo e ressalta que está em desenvolvimento;
  - "Distribuição: na faixa alta, quem fica abaixo de 80% fica perto", que responde ao "se eu tenho muito e você passa fome, na média todo mundo come";
  - "Verba a verba" (HE 49→52→70%);
  - "Passo a passo" (árvore: verba achada 84%, base 73% dos meses, horas 70%, valor da verba 78%).
- O **período ficou fora da árvore**: o período do lado do calculista muitas vezes é o contrato inteiro.

**v2, feedback dela em 19/10:**
- Os slides precisam **contar história**, como os do board: uma caixa narrativa (fundo cinza, borda vermelha) com a amostra, como ler e a conclusão, ao lado de um gráfico limpo.
- **Funil primeiro**, com seta de quebra (oval "−94%") e **cobertura** explícita: 61 = 9% dos 689 com cálculo. Não aptos = 344 por verba que a esteira não calcula ("verba não calculada" + "nenhuma verba calculada" juntas, porque ela não via a diferença), 62 por cálculo crítico e 19 por outros.
- "Onde estamos" vira colunas de % com 80% ou mais por recorte, com a linha "Objetivo – 80%", como o slide dela do board.
- **Faixa de valor:** só dentro × fora, sem categorias de valor.
- **Score:** as barras 100% das faixas de assertividade do HTML do painel (≥ 95, 80–95, 50–80, < 50), com ▲ a mais e ▼ a menos.
- **IA × calculista:** no estilo do notebook 7a (log, faixa ±20%), como PNG em `graficos/`, porque ela aceita gráfico colado do Python.
- **Verbas:** dois slides, "o que fazemos bem" (valor fixo e adicionais) e "onde ainda erramos" (jornada).
- **Sem** slide de próximo passo.

**Narrativa da v1 (substituída):**
1. onde estamos;
2. funil em cascata;
3. faixa de valor;
4. score no apto valor;
5. curva de acerto (sobrevivência);
6. faixa alta, IA × calculista;
7. próximo passo: aumentar a amostra, com o intervalo de confiança de Wilson.

**Linguagem visual:** o "gráfico de faixa" da aba Verbas, que ela gosta.
- Traço fino do p10 ao p90, barra grossa no intervalo interquartil, bolinha na mediana e 80% tracejado.
- A % com 80% ou mais fica à direita.
- É feito com formas, para dar para editar. Destaque em vermelho #D24955; o resto em grafite e cinza.

**Números de 19/10:**

| Grupo | Processos | Com 80% ou mais | Mediana |
|---|---|---|---|
| Rodados | 1.031 | — | — |
| Com cálculo e gabarito | 676 | 35% | 61% |
| Aptos | 264 | 50% | 80,5% |
| Apto valor | 152 | 61% | 85,4% |
| Apto valor, faixa alta | 61 | 79% | 92,9% (IC 67–87%) |

- No apto valor, as outras faixas ficam em: média 46%, baixa 42%, restrita 68%.
- Os números que ela pôs no rascunho do funil (181; 60/60/61) eram de exemplo.

Ver [[apresentacao-staff-assertividade]], [[notebook-distribuicoes-assertividade]], [[mensagens-titulo-e-corpo-unico]].
