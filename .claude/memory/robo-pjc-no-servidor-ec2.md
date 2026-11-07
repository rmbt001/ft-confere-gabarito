---
name: robo-pjc-no-servidor-ec2
description: auto_pjc.py no servidor EC2 (ec2amaz-4s7k07h\rmarotta) não tem SSO silencioso; usar --login manual + cookies; lote avulso em pasta separada
metadata:
  type: project
---

Em 28/10/2026 a Raíra também usa um servidor EC2 (`ec2amaz-4s7k07h\rmarotta`, perfil `C:\Users\rmarotta`), além do notebook (`C:\Users\RaíraMarottaBastosVi`). O EC2 **não está no Entra** (`dsregcmd /status`: AzureAdJoined NO, AzureAdPrt NO), então o SSO silencioso do `auto_pjc.py` falha ("SSO silencioso NAO passou").

**Why:** o robô só loga sozinho em máquina com PRT; no EC2 a única sessão é a do `--login` manual (cookies em `.zeev_cookies.json`).

**How to apply:** no EC2, rodar `auto_pjc.py --login` (ela loga na janela) e depois a rodada com `AUTO_PJC_USAR_COOKIES=1`. Se a sessão cair no meio, a rodada aborta; repetir o login e relançar (o robô pula o que já baixou).

Lote avulso que não deve entrar no painel: `AUTO_PJC_PASTA_CASOS=<pasta>` (ambas as variáveis adicionadas em 28/10). Lote `dados/cnjs_sem_pjc_2310.txt` (1.056 CNJs) foi para `ft/pjcs_sem_pjc_2310/casos/`, com tabelas extraídas em `ft/pjcs_sem_pjc_2310/saidas_pjc/`.

O notebook `extrator_pjc` aponta `../app_validacao_Calculos/src`, mas o parser agora está em `app_validacao_Calculos/codigo/src` — o notebook quebra com FileNotFoundError até corrigir. Relacionado: [[docs-do-fast-track]], [[projeto-fast-track-ft]].
