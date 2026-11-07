---
name: visual-guide-lift
description: Sistema de design dos docs LIFT da Raíra (manual_calculistas_lift.html) — usar em todo doc/relatório/artefato novo dela
metadata:
  node_type: memory
  type: reference
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-05T21:38:09.740Z
---

Documento-fonte do estilo: `manual_calculistas_lift.html`. Quando houver um doc/relatório/artefato
novo para a Raíra, copiar o `<style>` inteiro desse arquivo e reusar os componentes.

**Tipografia:** corpo Onest (Google Fonts) 15px, line-height 1.75; títulos Sora 700, line-height 1.25;
mono Courier New.

**Paleta:** --bg #f5f3f3 · --surface #ffffff · --border #e9e9e9 · --ink #161616 · --ink-muted #595959 ·
--accent #e26970 (salmão) · --accent-lt #fdf0f1 · --warn #be6565 / --warn-lt #fdf3f3 ·
--ok #2a6b44 / --ok-lt #e6f2eb · --tag-bg #f0edee · --radius 10px / --radius-lg 16px.

**Layout:** `.page-wrap` max-width 860px, padding 48px 24px 80px. Cover preta arredondada com 2 círculos
decorativos (accent + warn, opacidade baixa); `.cover-label` uppercase espaçado salmão antes do h1;
h1 do cover com `<span>` accent na segunda linha.

**Componentes:** `.section-header` + `.section-number` (badge salmão 32×32, Sora) + h2 · `.card`
(branco, radius-lg, padding 32px 36px) · `.card-title` com `.icon` 30×30 accent-lt + emoji ·
`.pipeline`/`.step` (badge circular 60×60 borda accent, linha vertical) · `.step-tag` · `.callout`
info/warn/ok (border-left 4px) · `.rule-list` (grid 200px/1fr, label salmão Sora) · `.limits-grid` /
`.limit-item` · `.noncalc-item` · `.formula-box` (fundo preto, mono, destaque salmão) · `.sumula-table`
(th preto, linha par bege) · `.tip` + `.tip-num` · `.chip-grid` / `.chip` · `.footer` + `.footer-brand`.
Responsivo: breakpoint 620px, uma coluna.

Feedback de leitura (05/10/2026, relatório de divergências): abrir com um texto curto que explica
o problema antes de qualquer número; sumário logo depois da capa; separar o diagnóstico (árvore/método)
dos problemas encontrados; nada de etiquetas e barras em cada linha — tabela limpa com colunas
alinhadas; item "em investigação" não leva "onde mexer", leva "próximo passo".
Escrever para quem NÃO mexe na esteira todo dia: nada de caminho de arquivo, nome de campo, alerta
ou jargão ("passthrough", "em módulo", "gap", "líquido", "rubrica") no corpo — isso vai num
"Referência técnica" recolhido. Cada problema em blocos separados: números em frase → o que acontece
→ exemplo → por que acontece → o que corrigir → tabela (processo, nome da verba, efeito).

PDF no Windows: abrir no Chrome/Edge → Ctrl+P → Salvar como PDF (paisagem se tiver tabela larga).

Ver [[usuario-raira-bt-creditos]].
