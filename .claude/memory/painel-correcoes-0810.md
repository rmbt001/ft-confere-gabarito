---
name: painel-correcoes-0810
description: "Correções de medição feitas no painel de validação em 08/10/2026 (fora do principal, zerar negativo, teto de dano, honorários fora, HE somadas) e o efeito"
metadata:
  node_type: memory
  type: project
  originSessionId: 423d7c41-bdaa-4198-a671-1991729a1207
  modified: 2026-10-16T13:38:56.344Z
---

Em 08/10/2026, a pedido da Raíra ("pode endereçar todos"), o painel (`bt-prod-apps/ft/app_validacao_Calculos`, não commitado) passou a:
- ler `<comporPrincipal>NAO</comporPrincipal>` do .pjc e tirar essas linhas do total (pedidos improcedentes, majoração DSR, versões sem teto) — `verbas_fora_principal`; "PEDIDOS IMPROCEDENTES" vira aviso amarelo no caso (`alertas_pjc`): é base de honorários de sucumbência que o reclamante paga;
- respeitar `<zeraValorNegativo>` (opção do calculista, verba a verba) — retirado em 15/10 (d14f55f) e **VOLTOU em 16/10/2026
  com aprovação dela**: a conferência .pjc × Resumo do PDF mostrou que o PDF soma só os meses positivos dessas verbas
  (8 aptos ao centavo, BT081 e HE comum). Regra = ler o PJC como o calculista entregou, não regra por código.
  `_PJC_SCHEMA` v9. A regra do LADO DA IA (BT081 zera mês; demais zeram o total negativo) é da esteira, card Jira
  BT-1559, e não vai para o painel — no painel só o aviso "⚠ neg.";
- capar o PJC em R$ 5.000 também em BT050 e BT040 (mesmas verbas da TetoDanosMoraisStrategy);
- tirar honorários/custas/perícia dos totais e medidas (`fora_comparacao`), sem mudar a aptidão;
- mostrar `familia_he` (7ª/8ª + além da 8ª somadas) no resumo do caso.
`_PJC_SCHEMA` foi para v4 (regerar leva ~1h40 com cache frio). Efeito na rodada 07–08/10: mediana 69,7% → 78,8%; negativos 16,4% → 13,2%; ≥80% 41,8% → 47,1%.

Em 14/10/2026 a Raíra pediu honorários (sucumbenciais, periciais, devidos) fora do painel inteiro, não só da soma: agora somem também da lista de verbas do caso e do `total_lift` das rodadas (o P10a os calcula como verba comum, nome só no P4 via `verba_NN`). A aptidão continua lendo a lista completa. **Correção do mesmo dia:** o "honorário com código BT089" NÃO era da IA — o P4 codifica honorários certo (BT062/BT063/BT079). Era o painel: o nome vem da tabela DEF por posição (`verba_NN`), e ela às vezes não é a lista que o P10a numerou (68 verbas / 31 casos / R$ 610 mil desalinhados). Regra da Raíra: se o código do P10a é de verba real, a verba fica e soma (seria somada automaticamente). O painel agora nomeia as verbas pela tabela do editor (`id_verba`), com o glossário pelo código do P10a de reserva. Efeito no painel de 14/10: 0 honorários na lista; 5 casos com total IA corrigido para cima (verbas reais que estavam com nome de honorário); 35 casos com nome de verba corrigido; mediana geral inalterada (50,1%); total das rodadas inalterado (na prática o P10a não somava honorário real).

**Why:** a medição distorcia o diagnóstico e o hackathon. **How to apply:** antes de culpar a IA, lembrar que esses furos já estão corrigidos; achado lateral: a esteira somou "Honorários devidos ao Advogado da Reclamada" (R$ 229 mil, 1001159) ao crédito — verificar no desembolso. Ver [[investigacao-divergencias-pjc-ia]].
