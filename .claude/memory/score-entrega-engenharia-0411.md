---
name: score-entrega-engenharia-0411
description: "Pasta bt-prod-apps/ft/score_confianca (04/11): conta o que o score faz para produtizar (vira tabela nova); sem painel, sem proposta de arquitetura; não commitado"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-11-04T11:55:02.849Z
---

Em 04/11/2026 a Raíra pediu a pasta para a engenharia produtizar o score de confiança. Correções dela no caminho:
**não falar de painel nem do fluxo do PC dela** (eles não terão painel); **"nós não damos solução, contamos o que
fizemos"** — nada de handler/template/DDL sugeridos; o resultado é "como se virasse uma nova tabela"; descrever tudo,
inclusive **como baixamos as peças** (robô no TARS → API recorte-integra/documentos → PDF do S3 → pdfplumber → .txt).

Pipe descrito: apto? → consolida (código, tb_resultado_*) → peças → Jev → regras → auditor só se deu alta → grava.
Apto valor NÃO é filtro (é recorte de medida); o score roda em todo apto.

Conteúdo: README + docs/01..09, pacote (com orquestrador.avaliar, auditor.py OpenRouter, proventos.py), config,
instrucoes/auditor, premissas, exemplo sintético, 28 testes. Não commitado (bt-prod-apps é git; esperar ok dela).

04/11 (ok dela): `rubricas_base` saiu também do auditor da validação (ft_agente_auditor/codigo/monta_caso.py) e
`pensao_sobrestada` saiu do perguntas.json da validação. Impacto medido ~nulo (campo era quase sempre "SALÁRIO BASE";
nenhuma resposta do auditor o usou; nenhuma regra lia a pergunta); nada rerodado.

**How to apply:** mudança de regra agora existe em dois lugares (`ft_score_confianca` e a entrega) — manter iguais.
Ver [[score-estado-3010]].
