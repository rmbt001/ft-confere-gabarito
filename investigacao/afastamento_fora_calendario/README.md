# Afastamento fora do calendário

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
