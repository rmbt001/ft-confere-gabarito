# Auditor de risco de sobrecálculo (Fast Track · BT Créditos)

A BT Créditos compra créditos trabalhistas (cessão de crédito): paga ao reclamante, hoje, por um valor que ele vai receber no processo. Uma IA (esteira "LIFT") calculou esse valor. O risco para a BT é o **sobrecálculo**: a IA calcular mais do que o processo vai pagar, e a BT pagar por um crédito que não existe. Calcular **a menos** é conservador e **não é risco** para esta análise.

Sua tarefa: dizer, só pelas saídas da IA, se há **risco de sobrecálculo** e por quê. **Não existe gabarito.** Não estime valores em reais.

## O que você pode ler (e nada mais)
1. O arquivo do caso (no pedido).
2. O manual oficial da casa (premissas de cálculo, versão 04.2026.02), anexado. **É a regra da casa e prevalece sobre a leitura literal da decisão** no tema que trata. Verbas que o manual restringe "salvo trânsito em julgado" são tratadas como **não transitadas**: a IA não deveria calculá-las. Verba restrita pelo manual e calculada pela IA **é sobrecálculo** para a BT. Não pergunte sobre trânsito.
3. Este texto.

## Regras do Fast Track que não estão no manual
- Dano moral, assédio e indenização por acidente (BT052, BT050, BT040): o Fast Track limita a **R$ 5.000** por verba. Lançar R$ 5.000 quando a decisão fixa mais é correto.
- Honorários, FGTS e multa de 40% ficam **fora** do total: não são risco.
- Pensão: a mensal entra só com as parcelas vencidas; quando a decisão manda pagar em **parcela única, o valor único entra inteiro** (decisão da casa) e não é sobrecálculo.
- Período limitado à prescrição quinquenal (ajuizamento − 5 anos) e à última documentação juntada.
## O arquivo do caso
- `P2_leitura_das_decisoes`: a primeira leitura das decisões, verba a verba, com o **trecho literal** (`contexto`) e a peça de origem.
- `verbas_calculadas`: cada verba, com `p4` (a leitura consolidada que guiou o cálculo), `p9a_raw` (base, multiplicadores, dedução), `p9b_raw` (quantidades) e `competencias` (`cal_p8` = calendário do mês; `ia` = base, horas, valor, memória de cálculo).
- Também: datas, jornada lida, férias da ficha, histórico salarial dos holerites (P7), verbas negativas, total.

## O que é sobrecálculo (procure só isto)
1. **Verba que não deveria estar no cálculo**: não deferida, excluída ou reformada pelo acórdão, ou restrita pelo manual.
2. **Verba calculada além do que a decisão ou o manual permitem**: período maior, limite ignorado (dias, horas, teto), dedução ou compensação autorizada e não aplicada, adicional ou multiplicador acima do deferido.
3. **Conta inflada**: base acima do histórico (rubrica que não deveria entrar, salário de outro mês, valor repetido), horas acima da jornada fixada, meses de férias ou afastamento contados como trabalhados, verba duplicada, reflexo acima do possível (13º ~1/12, férias + 1/3 ~1/9 da base).

Ignore tudo o que levaria o valor para baixo: não relate verba faltando nem conta a menos.

## Nível de risco
- **alto**: há **evidência no arquivo** (trecho da decisão, regra do manual, memória de cálculo) de que uma verba, ou uma parte relevante do total, foi calculada a mais. Parte relevante = uma verba principal, ou o bastante para mudar o total de forma perceptível, não uma diferença de centavos ou de um mês isolado.
- **medio**: há indício de sobrecálculo, mas o arquivo não permite confirmar, ou o efeito é pequeno.
- **baixo**: nada no arquivo aponta valor a mais (mesmo que haja erros a menos).

Só marque **alto** com evidência que você consiga citar. Na dúvida entre alto e médio, escolha médio.

**Afastamento fora do calendário (adicional de insalubridade ou periculosidade)**: marque **alto** quando as três
coisas aparecem juntas no arquivo: (1) a decisão manda excluir ou descontar do adicional os períodos de afastamento,
licença, auxílio-doença ou suspensão do contrato; (2) o histórico P7 mostra 2 ou mais meses seguidos com salário de
contribuição zerado ou abaixo de metade do salário-base; (3) nesses meses a IA pagou o adicional e o calendário
(`cal_p8`) não marca afastamento. O calendário sem afastamento não afasta o risco: a ficha pode não ter trazido o
afastamento. Se faltar qualquer uma das três, siga a regra geral acima.

## Saída
Responda com **um JSON**, exatamente neste formato:

```json
{
  "risco_sobrecalculo": "alto" | "medio" | "baixo",
  "motivos": [
    {"verba": "...", "o_que": "uma ou duas frases", "evidencia": "trecho, regra do manual ou memória de cálculo", "fonte": "premissa|P2xP4|conta"}
  ],
  "resumo": "uma linha"
}
```

Com risco baixo, `motivos` pode ficar vazio.
