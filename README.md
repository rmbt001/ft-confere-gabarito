# Confere gabarito do Fast Track

Compara o cálculo que a IA do Fast Track fez para um processo com o gabarito do calculista em PDF (o "Resumo do
Cálculo" do PJe-Calc). Funciona para um processo ou para um lote de milhares.

O motor de comparação é o mesmo do painel de validação (pasta `codigo/`, cópia de
`bt-prod-apps/ft/app_validacao_Calculos` de 07/11/2026): mesma leitura do PDF, mesmo pareamento das verbas da IA
com as do PJC, mesma assertividade. A diferença está na entrada: em vez de baixar as tabelas inteiras da Nekt
(cerca de 15 GB), este repositório lê só as linhas dos processos pedidos.

## O que você precisa

- Python 3.12 e o [uv](https://docs.astral.sh/uv/);
- um token da Nekt (Data Access Token).

## Instalar (uma vez)

```powershell
git clone <url deste repositório> C:\ft\ft_confere_gabarito
cd C:\ft\ft_confere_gabarito
$env:UV_LINK_MODE = "copy"
uv sync
copy .env.exemplo .env      # e cole o token da Nekt no lugar de cole_seu_token_aqui
```

Deixe a pasta **fora do OneDrive**. Um `.venv` dentro de uma pasta sincronizada entre duas máquinas quebra as duas.

## Comparar

Ponha os PDFs dos gabaritos numa pasta e rode:

```powershell
uv run python compara.py "C:\Users\<você>\Downloads\a_avaliar"
uv run python compara.py "D:\gabaritos_lote" --rotulo lote_nov
```

O CNJ de cada PDF sai do nome do arquivo (os 20 dígitos, com ou sem pontuação), do nome da subpasta ou, se não
estiver em nenhum dos dois, do texto da primeira página do PDF.

O resultado fica em `saidas/<rótulo>/`:

| Arquivo | O que tem |
|---|---|
| `comparacao.html` | a página de cada processo, igual à do painel: verbas da IA × PJC, mês a mês, motivos de inaptidão |
| `resumo.csv` | uma linha por processo: apto, motivo, assertividade, total da IA e total do PJC |
| `verbas.csv` | uma linha por verba de cada processo: nome na IA, nome no PJC, código, totais e acurácia |
| `comparacao.json` | tudo o que a página mostra, para análise em Python |

A página usa o layout do painel dos parciais (Rodada, Problemas do agente, Premissas do manual), de
`codigo/src/template_telas_parciais.html`, cópia do template de `ft_paineis_parciais/desde_2026-10-14`. O score de
confiança é o que o motor calcula; o score com Jev e auditor que o painel dos parciais aplica depois não roda aqui.

### Opções

- `--rotulo <nome>`: nome da pasta de saída. Sem ele, usa o CNJ (um processo) ou `lote_<n>`.
- `--so-pagina saidas/<rótulo>`: só remonta a página de uma saída já gerada (depois de trocar o template).
- `--sem-nekt`: não baixa de novo os processos que já têm recorte em `.cache` (útil para rodar a comparação de novo
  depois de trocar um PDF).
- `--pjc-gabarito`: usa também o `.pjc` da pasta como gabarito. **Sem essa opção, todo `.pjc` é ignorado**, porque
  em geral é o PJC que a própria esteira gerou do cálculo da IA (o nome traz a data e a hora da execução, por
  exemplo `00116289720165150093_2026-11-06_215330.pjc`). Comparar com ele dá 100% sempre.

## Só baixar as saídas da IA

```powershell
uv run python baixa_cnj.py 0011628-97.2016.5.15.0093
uv run python baixa_cnj.py --lista cnjs.txt
```

Grava `.cache/caso_raw__<CNJ>.pkl`. Cada tabela da esteira é lida uma vez, filtrada por todos os processos pedidos,
então 1 processo ou 2.000 levam quase o mesmo tempo (alguns minutos). Vale a última execução de cada processo.

## Como a assertividade é medida

Total da IA contra o total do PJC, nominal, sem honorários, como no painel. O que está fora do principal no PDF
("Verbas que não compõem o Principal") fica fora dos dois lados. Dano moral acima de R$ 5.000 é limitado no lado do
PJC quando a IA aplicou o teto.

## Contexto do Fast Track

O repositório também leva o contexto de trabalho, para o Claude da VM partir do mesmo ponto:

- `CLAUDE.md`: carregado automaticamente pelo Claude Code quando ele abre esta pasta; aponta para o resto.
- `.claude/memory/`: as memórias (retrato de 07/11/2026), com o índice em `MEMORY.md`.
- `.claude/agents/`: o agente analista de divergências e o auditor de etapas.
- `contexto/premissas/`: manual de Premissas de Cálculo, glossário de produção e situação das premissas na esteira.
- `contexto/modelos/`: modelo de página no visual LIFT.

Para atualizar as memórias depois, copie de novo a pasta `Repos\.claude\memory` (sem os arquivos `*-EC2AMAZ-*`) e
faça um commit.

## O que não sobe para o repositório

`.env` (token), `casos/` (os PDFs), `.cache/` (saídas da IA) e `saidas/` estão no `.gitignore`.
