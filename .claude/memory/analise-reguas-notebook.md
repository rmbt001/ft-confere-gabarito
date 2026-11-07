---
name: analise-reguas-notebook
description: "Pasta analise-reguas (réguas de recebimento, fora do Fast Track) — notebook que refaz os gráficos do deck Intro BT Réguas Abr26 com a amostra 2025–26"
metadata:
  node_type: memory
  type: project
  originSessionId: 295e1cc5-cd73-40b5-9f91-68aef43b565e
  modified: 2026-10-23T22:31:59.076Z
---

Notebook `analise-reguas/analise_reguas_amostra_2025_2026.ipynb` (uv próprio; sem R nem python global, usar `uv run`). Compara a amostra nova (CSV solto na pasta, sem datas/valor/instância) com a **base da Régua 3.0 = as duas partes juntas**: `regua_30/mercado_dados_bt.RDS` (20 reclamadas da BT) + `mercado_dados_fora_v3.RDS` (mercado), como no analise_final.R. CSVs crus também na pasta; `tratamento_regua30.py` reproduz o analise_interna.R (validado 100% contra os dois RDS).

Réguas de referência = Régua 3.0 (slides 22/23): fase 1 = 23, fase 2 = 6, fase 3 = 20 + tamanho (M +4, G +8) + ministro, fase 4 = 17 + tamanho (G +3) ± vara; total 65 é de 2021.

Achados (23/10, base inteira): fase 3 por tamanho — G ~+4 m sobre P (≈7 na parte BT), M ≈ P; na amostra nova G só +2. Comparando mesmo ano de distribuição: base 3.0 G +2; amostra nova G −2. Tempo de fase segue o ano de entrada (recorte "terminou na janela"); fase 3 subiu 21→32 em boa parte por isso. Parte mercado só tem processos que chegaram ao TST e ≥ R$ 100 mil; parte BT tem 60% < 100 mil e 44% parados no TRT. Ambas começam em distribuídos de 2014.

Origem do 20/24/28 (fase 3): nos scripts não é calculado — aparece fixo como "previsão fixa / cenário atual" (Régua 2.0 vigente) em analise_mercadov2.R ~L1356, só para comparar erro com o modelo; intercepto do modelo também fixado em 20 (L1305). Na base 3.0 cai perto da mediana (percentis 48/55/56).

Base crua da régua 4 (23/10): `df_mercado_regua_4_foto_dl.csv` (Nekt, formato {k=v}) = os mesmos 34.517 CNJs da amostra nova; `tratamento_regua4.py` → dados_tratados/regua4.parquet reproduz as fases do CSV 100%. Montagem: arquivados 2025–26, valor ≥ R$ 50 mil, 12% com acordo (3.0 excluía), 67% chegaram ao TST, 4.172 reclamadas (32% são as 20 da BT). Tempo efetivo por tamanho: P 59 · M 72 · G 90 (3.0: 62 · 71 · 76). Com data exata de AIRR: mesmo ano de AIRR dá fase 3 bem maior na régua 4 (ex. AIRR 2019: ~29 → ~53) e P/M/G quase iguais dentro do ano → efeito de janela confirmado; nenhuma base sozinha mede o prazo.

**Why:** errei antes usando só a parte mercado como "base da 3.0" e cheguei a dizer que o tamanho não pesava; Raíra se perdeu com o excesso de detalhe.

**How to apply:** explicar em linguagem simples, uma ideia por vez. Próximo passo sugerido: pedir ao dono do recorte novo critério de entrada, reclamada/instância/valor por CNJ, datas e casos em andamento (sobrevivência).
