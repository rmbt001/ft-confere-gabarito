---
name: pjc-pdf-calculos-diferentes
description: 28/10 — em 182 casos o pjc.pjc e o pjc.pdf da pasta são cálculos diferentes do PJe-Calc; o painel agora usa o PDF nesses casos
metadata:
  node_type: memory
  type: project
  originSessionId: 5895e8fc-b105-40d4-b76a-6ff324c59bb0
  modified: 2026-10-30T14:04:30.941Z
---

Em 28/10/2026 (pedido da Raíra sobre 1000166-88.2021.5.02.0263, −3.652% no painel cópia) achei que o robô do
Zeev baixa o PDF e o `.pjc` como documentos separados e às vezes traz cálculos diferentes: o PDF diz
"Cálculo: N" na pág. 1 e o `.pjc` tem `<Calculo><id>`. 182 casos com os dois arquivos divergem (169 no
painel cópia, 33 aptos). No 1000166 o `.pjc` (3997) só tinha "dez dias de férias"; o PDF (2166) tinha HE,
intervalo e reflexos.

Correção (gerar_telas `_parse_pjc_cached`, `_PJC_SCHEMA` v11): ids diferentes → caso fora da régua
("gabarito a corrigir") — decisão da Raíra: "melhor tirar os sem gabarito confiável". Só usa o PDF onde foi
conferido: `GABARITO_PDF_CONFIRMADO` (1000166, 0000230-08.2018.5.09.0011, 0020106-92.2024.5.04.0102) ou id do PDF =
curadoria `GABARITO_ID_CALCULO` (0012750). Primeira versão (v10, usar sempre o PDF) foi descartada. Junto: `parse_pjc_xml` lia o id só no formato
antigo (vazio em ~55%: raiz com `<gprec>`/`<dadosEstruturados>` antes do `<id>`); `parse_pjc` passou a ler
o id e o bloco "Verbas que não compõem o Principal". PDF sem "Cálculo: N" legível → fica o `.pjc`.

**Mudou em 30/10 (Raíra):** ids diferentes agora VALEM O `.pjc` e entram na régua, marcados com `*`
(campo `gabarito_pdf_dif`, alerta "* PJC e PDF de cálculos diferentes"). Só se corrige o gabarito dos que
forem aptos/apto valor com assertividade baixa (12 apto valor < 80% em 30/10). `.pjc` de OUTRO processo
continua "gabarito a corrigir" (59).

**Why:** o robô escolhe o PDF Risco Real de propósito; a curadoria manual 0012750 (certo = 551) era
justamente PDF 551 × .pjc 514. **How to apply:** caso com assertividade absurda e PJC "pequeno" → checar os
ids primeiro. O 0000642-51.2023.5.10.0005 NÃO é isso: mesmo cálculo; a IA cobrou como crédito a
EXTRAFOLHA que o PJC usa só como base de reflexo (fora do principal). Ver [[painel-correcoes-0810]].
