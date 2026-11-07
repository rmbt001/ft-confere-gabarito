---
name: lote-0909-regressao-hora-extra
description: "O lote de 09/09/2026 do Fast Track levou 15 casos à meta; a queda de hora extra é política declarada, não bug"
metadata: 
  node_type: memory
  type: project
  originSessionId: fe4b566a-8786-4a87-9180-1d27b6d0f396
  modified: 2026-09-11T13:19:28.846Z
---

Em **09/09/2026** rodou um lote de 152 casos no LIFT, 130 já rodados antes. Dos
125 comparáveis (gabarito confiável + rodada anterior):

- assertividade mediana **61,3% → 80,0%**, Δ mediano por caso **+2,1 p.p.**
- casos **na meta (≥ 80%): 47 → 62**; faixa `< 50%` caiu de 53 para 37
- 61 subiram, 43 caíram
- posição: antes **sobrecalculava** (66 sobre × 46 sub); depois 51 × 58

**Why:** a medida é **assertividade com âncora sem reflexos** — o total do LIFT
por rodada (principal + rescisórias) não tem reflexo, então tem de ser comparado
com o total do PJC também sem reflexo (`quadro.total_pjc_base`). Ancorar no total
cheio inverte o sinal do delta em 23% dos casos: o `1000522-97.2024.5.02.0386`
aparecia caindo 34 p.p. quando na verdade subiu 24.

Das 52 verbas que deixaram de ser calculadas: **33 o P4 parou de deferir**, **17
o P9a declarou não-calculável com motivo escrito**, e só **2 são perda
silenciosa** (`0000299-77.2025.5.06.0011` e `1001166-26.2020.5.02.0242`, ambas
BT089) — essas são bug. Motivo mais repetido (24×, BT011 Horas Extras Domingos e
Feriados): *"Trabalho em DSR/feriado é fato documental. Na jornada fixa a folga
roda (ex.: 6x1) e não há como confirmar se cada domingo/feriado foi efetivamente
trabalhado."*

**How to apply:** o que destrava mais dinheiro não é o motor de cálculo. Dos
R$ 10,4 mi de gabarito não calculado: **insumo ausente (holerite/ficha) 28%**,
**cascata — verba não-calculável porque outra é 15%**, cartão/documento 9%, e
**quantidade fixa / cronoanálise só 0,4%** (2 casos). A cascata é o melhor
retorno por esforço: destravar poucas raízes solta muitos dependentes.

Dois furos de medição conhecidos, ambos abertos: **25 casos** cujo gabarito foi
parseado só como linha de subtotal (`VERBAS TRIBUTÁVEIS`, `CONTRIBUIÇÃO SOCIAL`)
e que estão dentro de todas as médias; e **232 nomes de PJC sem código** no
de-para, cauda longa.

Relatório: `saidas/analises/lote_20260909.html` (gerado por
`codigo/analises/relatorio_lote.py <data>`). Drill no terminal:
`codigo/analises/varre_verbas_perdidas.py <data>`.

Ver [[projeto-fast-track-ft]] e [[docs-do-fast-track]].
