---
name: gerar-telas-lento
description: gerar_telas de produção levava 1h40–2h; causa (filtros quadráticos) achada e corrigida em 15/10 com busca indexada — saída idêntica byte a byte
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-10-15T17:11:39.627Z
---

Pedido da Raíra em 15/10/2026 ~8h10 ("2h para gerar um html é absurdo"); ela pediu para resolver na hora.

**Causa (cProfile de 300 casos, 759 s):** o `gerar_telas.py` junta os recortes de TODOS os casos numa tabela por etapa
(`_concat`) e, para cada caso, filtrava a tabela inteira (`df[df["id_processado"] == idp]`, `set(df["id_processado"])`,
`str.replace` na coluna cnj inteira em `_cons`). Custo quadrático: 44 casos = 20 s, 300 = 12,6 min, ~1.500 = 1h40.
Maiores consumidores: `_ultimo` 242 s, `_rodadas` 195 s, `_cons` 112 s, `literal_eval` 100 s, `json.dumps` 50 s.

**Correção (15/10, só no app de produção):** funções `_indice`/`_linhas`/`_linhas_de` logo depois das tabelas: agrupam cada
tabela uma vez por coluna e devolvem as mesmas linhas na ordem original (a ordenação por criado_em continua no chamador).
Trocados os 13 pontos (inclusive `_erro_execucao`, `_versoes`, `_rodadas`, `_cons`, `montar_caso`, `_idp_vigente`).
Prova: código antigo × novo nos mesmos 150 casos → JSON e HTML idênticos byte a byte.
Medido depois: a geração completa de prod com a correção levou 65 min (não os ~40 estimados).
**Cortes pedidos por ela (15/10 ~14h, só prod, só na geração completa):** caso com execução mais recente antes de
03/08/2026 sai do painel; pendente de PJC com execução de mais de 30 dias sai (constantes CORTE_EXECUCAO e
PENDENTE_MAX_DIAS logo depois de `_SLICES`). O ingerir ainda recorta tudo.
Ainda linear e não atacado: `literal_eval` dos campos texto e o `json.dumps` de ~300 MB.
O app de homologação NÃO recebeu a correção (não foi pedido).

**Why:** cada rodada do painel travava a análise por quase 2 h.
**How to apply:** ao mexer em filtros por caso no gerar_telas, usar `_linhas` e não `df[df[col] == x]`. Ver [[painel-homol-nao-mexer-prod]].
