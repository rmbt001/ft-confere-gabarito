---
name: vm-pedido-infra
description: O que a Raíra precisa pedir à Infra para rodar na VM de dados (172.30.0.232) — login BT (Entra) no Chrome para os robôs do Zeev e do TARS; também cloud path do OneDrive e RAM
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-11-05T18:45:38.440Z
---

A VM de dados foi entregue pelo Marcio Alves (eng) em 26/10/2026 (OpenVPN + RDP, usuário local .\rmarotta).

**Pedido principal (o que ela lembra como "o do robô"):** os robôs do Zeev (auto_pjc, busca de PJC) e do TARS (peças, Chrome porta 9333) entram sem senha no PC dela porque o aparelho está registrado no **Microsoft Entra** da BT e o Chrome usa o token do dispositivo. A VM usa conta local, fora do Entra, e a política de acesso condicional pode barrar o login ("dispositivo não atende aos requisitos"). Pedir à Infra: registrar/ingressar a VM no Entra (ou liberá-la na política de acesso condicional) para logar com a conta BT no Chrome da VM no Zeev e no TARS. O teste de login (29/10) não teve resultado registrado.

Cloud path do OneDrive: travou em 31/10, mas em 05/11 ela confirmou que a Repos já sincroniza na VM — resolvido. Pendente opcional: 32 GB de RAM (sugerido em 30/10).

**Why:** sem isso as rodadas seguem no PC dela.
**How to apply:** quando ela perguntar da VM, partir daqui; ver [[pausa-score-agente-2910]] e [[madrugada-1710-rodadas]].
