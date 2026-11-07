---
name: ajustes-prompt-foco-unico-enxuto
description: "Como a Raíra quer as sugestões de ajuste de prompt e os cards de problema — um foco por problema, menor mudança, sem campo novo que ninguém lê"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-08T17:02:42.918Z
---

Cada problema (card/tema) tem um foco único; se um tema mistura causas (ex.: base enumerada + RMNR + retroativo + bancário), separar em temas próprios, cada um com sua edição. As sugestões de prompt devem ser a menor mudança possível: preferir campo existente (ex.: `premissa_texto`, `salario_base_origem`, `natureza_juridica`) a criar campo, objeto ou valor de enum novo; campo novo só se alguma etapa ou código for ler. Alertas novos que só registram também saem.

**Why:** em 08/10/2026 ela achou as sugestões "muito complexas e criando campos quando dá para simplificar" e notou "mais de um problema dentro de um problema"; o time no hackathon analisava card a card com a IA e se perdia.

**How to apply:** ao propor ajuste, perguntar "qual etapa lê isso?" antes de criar campo; quando a regra exata exige campo novo, oferecer a versão conservadora sem campo e deixar o exato como código. O mapa de temas separados fica em `ft_arvore_divergencias/analises_caso/_foco_unico.json` (aplicado por `temas_atuais.carregar`). O time usa dois prompts fixos (avaliar / testar num CNJ com caso de controle) publicados no topo da página do hackathon. Ver [[investigacao-divergencias-pjc-ia]].
