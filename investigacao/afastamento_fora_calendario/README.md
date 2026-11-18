# Afastamento fora do calendário

> **Decisão de 18/11/2026:** a regra pelo Jev **não** entra no score. O **auditor v2, na versão apertada** (só marca
> alto por afastamento citando o trecho da decisão que manda excluir), **entra**: o parágrafo foi levado à instrução do
> auditor do score. Resumo do que foi medido está no fim deste arquivo.

Simula uma checagem nova para o score de confiança: a IA paga adicional de periculosidade ou de insalubridade em
meses de afastamento (INSS, lay-off, suspensão da pandemia) porque o afastamento não chegou ao calendário (P8).

Só leitura. Não muda o Jev, o pacote do score nem o back. Lê a comparação de uma rodada (`comparacao.json`) e,
se houver, a faixa do score de cada processo.

## A regra simulada

Por verba, sinal do lado a mais. Acende quando acontecem as três coisas:

1. a IA calculou adicional de periculosidade ou de insalubridade;
2. o critério do P4 dessa verba manda excluir ou descontar afastamento, licença, auxílio-doença ou suspensão.
   Quem responde é o Jev, lendo só o critério: "O critério da verba {n} manda excluir ou descontar do cálculo os
   períodos de afastamento, licença, auxílio-doença ou suspensão do contrato de trabalho?";
3. o calendário da verba não tem nenhum dia de afastamento em nenhum mês. Se tem, a ficha chegou e não há
   descasamento.

Processo marcado em alta, média ou a calcular vai para a baixa. Restrita e baixa não mudam.

Fica só como informação, fora da regra: os meses em que o salário de contribuição do holerite (P7) some ou cai
abaixo de metade do salário-base, 2 ou mais meses seguidos, com a IA pagando o adicional.

## Por que essa regra (painel de 23/10, 1.335 aptos)

| Sinal | Marcados | Adicional a mais | Com 80% ou mais |
|---|---|---|---|
| Critério manda excluir afastamento e calendário sem afastamento | 12 | 6 (50%) | 3 |
| Salário de contribuição cai 2+ meses seguidos | 18 | 5 (28%) | 11 |
| Holerite zerado ou mês sem holerite | 13 | — (o PJC pagou 206 dos 207 meses) | 8 |

Nos 221 aptos com adicional, ele sai a mais em 22%. Nos testes, a decisão foi lida por busca de texto; aqui
a pergunta vai ao Jev.

## Rodar na VM

Uma vez: ponha a chave do Jev no `.env` da raiz deste repositório (o mesmo do token da Nekt, fora do Git):

```
TYPESAFE_API_KEY=<chave>
```

Da raiz do repositório:

```powershell
git pull
$env:UV_LINK_MODE = "copy"

# primeiro sem o Jev (busca por texto, sem custo)
uv run --with "typesafe-sdk>=0.7.5" --with python-dotenv python investigacao\afastamento_fora_calendario\afastamento_fora_calendario.py `
  --comparacao <caminho do comparacao.json da rodada de 16/11> `
  --faixas <caminho de saidas\rodada_1611\confianca_jev.json> --sem-jev

# depois com o Jev (uma chamada por processo com adicional; centavos no total)
uv run --with "typesafe-sdk>=0.7.5" --with python-dotenv python investigacao\afastamento_fora_calendario\afastamento_fora_calendario.py `
  --comparacao <comparacao.json> --faixas <confianca_jev.json>
```

Opções:

- `--corte 0.5`: probabilidade mínima do "sim" do Jev;
- `--cnjs <arquivo>`: só os CNJs do arquivo, um por linha (por exemplo, os aptos confiáveis);
- `--saida <pasta>`: padrão `investigacao\afastamento_fora_calendario\saidas\afastamento_<pasta da rodada>`, fora do Git.

O arquivo de faixas pode ser `{cnj: "alta"}`, `{cnj: {"faixa": ...}}`, `{"casos": {...}}` ou uma lista com `cnj`
e `faixa`. Sem ele, vale o campo `confianca` de cada processo da comparação.

## O que sai

Na tela:

- quantos processos a regra marca e quantos estão na alta;
- acertos × falsos positivos, em que acerto é o adicional da IA acima do PJC em mais de 10%;
- a situação dos quatro processos de 16/11: 0012290-30.2016.5.15.0071, 0001055-93.2015.5.05.0131,
  0010211-93.2015.5.15.0045 e 0000789-64.2021.5.13.0005;
- a alta e a alta do apto valor antes e depois: casos, % com 80% ou mais e quantos calculam a mais.

Na pasta de saída:

- `verbas_adicional.csv`: uma linha por verba de adicional, com resposta do Jev, busca por texto, calendário,
  meses de queda da contribuição, totais e faixa;
- `resultado.json`: os marcados, com a faixa antes e depois;
- `jev_afastamento.json`: as respostas do Jev, para não pedir de novo.

## Testes

```powershell
uv run --with pytest pytest investigacao\afastamento_fora_calendario\tests -q
```

Casos sintéticos, sem Jev nem Nekt: cada parte da regra e uma rodada ponta a ponta com `--sem-jev`.

## Limites conhecidos

- A exclusão que só aparece na sentença de liquidação (0001055-93.2015.5.05.0131) não é lida pela esteira.
- Horista: o holerite mostra horas, e "zero dias pagos" não quer dizer afastamento (0010211-93.2015.5.15.0045).
- Hora extra quase não aparece: no mês de holerite zerado, a base da hora extra também zera e a IA não paga.
- A correção de fato é na esteira: montar o calendário com o holerite e a decisão como segunda fonte quando faltar
  a ficha.

## Resultado da regra pelo Jev (rodada de 16/11) e por que ela saiu

Pelo Jev, a regra marcou 29 dos 317 aptos com adicional, e só 4 tinham o adicional a mais. A alta caiu de 64% para 61%
com 80% ou mais. A frase da decisão é quase sempre condicional ("eventuais afastamentos", "comprovados nos autos"):
quando ela aparece e o calendário não tem afastamento, a IA paga a mais em 17% das verbas, a mesma taxa de qualquer
adicional (16%). Na maior parte das vezes, simplesmente não houve afastamento.

## Auditor v2 (pasta `auditor_v2/`)

O auditor de sobrecálculo já lê a decisão, o calendário e o holerite, e via esse padrão, mas dava "médio". O v2 é a
instrução de hoje (`instrucoes/auditor_sobrecalculo.md` do pacote do score) com um parágrafo a mais: marca **alto**
quando (1) a decisão manda excluir afastamento do adicional, (2) o P7 mostra 2 ou mais meses seguidos de salário de
contribuição zerado ou abaixo de metade e (3) a IA pagou o adicional nesses meses sem afastamento no calendário.

Teste de 18/11 nos 9 casos da alta de 09/11 (`saidas\insalub_peric_total`) com sinal no holerite e que não eram "alto":
mudou só o 0000789-64.2021.5.13.0005 (médio → alto nas duas rodadas do v2; médio na instrução original). O
0000024-65.2020.5.10.0861 ficou médio porque a decisão dele não manda excluir. Os outros dois "alto"
(0001004-33.2017.5.08.0130 e 0024802-62.2018.5.24.0091) deram alto também na instrução original: oscilação, não a regra.

### Rodar

O código do auditor (chamada, limpeza do arquivo do caso, manual) vem do pacote do score; daqui só muda a instrução.
A chave do OpenRouter vai no `.env` da raiz deste repositório (fora do Git), como `OPENROUTER_API_KEY=<chave>`.

```powershell
git pull
$env:UV_LINK_MODE = "copy"
$s = "<pasta da rodada>"   # por exemplo saidas\insalub_peric_total

# 1) sem custo: o tamanho do lote e o custo estimado
uv run --no-project --with python-dotenv python investigacao\afastamento_fora_calendario\auditor_v2\roda_auditor_v2.py `
  --comparacao "$s\comparacao.json" --faixas "$s\confianca_jev_sem_auditor.json" --base-auditor "$s\auditor_alta" --seco

# 2) a alta inteira com o v2, comparando com o auditor anterior da rodada
uv run --no-project --with python-dotenv python investigacao\afastamento_fora_calendario\auditor_v2\roda_auditor_v2.py `
  --comparacao "$s\comparacao.json" --faixas "$s\confianca_jev_sem_auditor.json" --base-auditor "$s\auditor_alta"
```

Opções:

- `--faixas`: as faixas **sem** o auditor; o lote é a alta desse arquivo;
- `--base-auditor <pasta>`: o auditor anterior da rodada (um `<cnj>.json` por caso), para listar o que mudou;
- `--so-sinal`: só os casos com adicional e 2 ou mais meses de contribuição zerada (os únicos em que o parágrafo novo
  pode agir; cerca de 1 em 10 da alta);
- `--controle`: roda também a instrução original nos mesmos casos, para separar o efeito da regra da oscilação do
  auditor (dobra o custo);
- `--cnjs <arquivo>`, `--limite N`;
- `--pacote <pasta>`: onde está o pacote do score (padrão `C:\ft\bt-prod-apps\ft\score_confianca` ou
  `SCORE_CONFIANCA_DIR`);
- `--saida <pasta>`: padrão `investigacao\afastamento_fora_calendario\saidas\auditor_v2_<pasta da rodada>`, fora do Git.

Custo: cerca de US$ 0,17 por caso e por versão. Caso já respondido não é pedido de novo (um arquivo por caso em
`<saida>\v2` e `<saida>\original`): se cair no meio, é só rodar o mesmo comando.

Na tela: as contagens de alto, médio e baixo de cada versão; a alta sem auditor, com o anterior e com o v2 (casos, %
com 80% ou mais e quantos calculam a mais no total); e cada caso que mudou, com a assertividade, se o adicional sai a
mais e se tem sinal no holerite.

## Teste do auditor v2 em 18 casos com o sinal no holerite (painel de 23/10) e decisão

Os 18 aptos com adicional e 2 ou mais meses seguidos de contribuição zerada ou baixa, rodados com o v2 e com a
instrução original (controle). O v2 marcou alto em 10 casos, contra 7 na original; nos dois, 3 calculam a mais no total.
Mudaram para alto só com o v2:

- 0000786-02.2022.5.23.0004 (91% no total; adicional a mais): citou o acórdão que exclui o adicional nos períodos de
  benefício previdenciário e a contribuição ausente de 02/2020 a 09/2021;
- 1000329-14.2022.5.02.0302 (99%; adicional a mais): citou o critério que torna indevido o adicional no auxílio-doença
  e a contribuição zerada de 06 a 08/2020;
- 0000882-51.2024.5.09.0678 (95%; adicional sem erro relevante): marcou sem a decisão, pela regra geral de descontar
  ausências.

Dos 11 casos com 80% ou mais, a original tira 2 da alta e o v2 tira 5. O erro que o v2 acha é real, mas pequeno perto
do total do processo: os acertos têm 91% e 99% de assertividade. Gasto do teste: US$ 7,71.

**Versão apertada (a que entrou):** o parágrafo passou a exigir que o auditor cite o trecho da decisão ou do critério
que manda excluir o afastamento; sem ele, holerite e calendário sozinhos não bastam. Rodada de novo nos três casos:
0000786-02.2022.5.23.0004 e 1000329-14.2022.5.02.0302 seguem alto, com o trecho citado; 0000882-51.2024.5.09.0678
volta para médio. Somando a medição da VM (9 casos da alta de 09/11, só 0000789-64.2021.5.13.0005 mudou, sem falso
positivo), o v2 apertado acertou os 3 casos que mudou e não marcou nenhum sem a decisão. Gasto: US$ 0,64.
