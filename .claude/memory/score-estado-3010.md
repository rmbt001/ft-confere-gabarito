---
name: score-estado-3010
description: "Score de confiança em 30/10: o que está aplicado, como rodar no painel de 23/10, regra nova dos valores não abatidos (holerite), medições de 30/10 e pendências"
metadata:
  node_type: memory
  type: project
  originSessionId: c0084f0e-29e2-4299-96d5-c56d353595b7
  modified: 2026-11-04T11:01:21.471Z
---

Estado do score em 30/10/2026 (painel `ft_paineis_parciais/desde_2026-10-23`, 916 aptos, 388 apto valor). Histórico e
decisões antigas: [[score-confianca-calculo]]; auditor: [[auditor-openrouter-2710]]; pausa: [[pausa-score-agente-2910]].

**Como o painel ganha score:** `jev_testes/aplica_score_jev.py desde_2026-10-23` chama `ft_score_confianca`
(`pipeline.pontuar`) com o cache do Jev e o auditor. Regra mudou → mudar NO PACOTE. Score só sai quando ela pede (pausa):
`%LOCALAPPDATA%\bt_auto_pjc\score_2310.ps1` (peças + Jev dos "a calcular" + score) e depois `score_2310.ps1 -auditor`
(auditor nos apto valor da alta + score). O `Score` do ps1 refaz antes `bt_auto_pjc\prov_cnj.py` (proventos). Gravação em
fluxo desde 30/10: json.dumps de ~700 MB estourava a memória e zerava o JSON (aplica_score_jev e painel_sem_score).

**Regra nova aplicada em 30/10 (aprovada por ela): "Valores pagos não abatidos" (`criterio_abatimento`, risco +1).** Só
aciona se o critério manda deduzir, a IA abateu R$ 0 E o holerite completo tem rubrica paga do mesmo tipo da verba (HE,
intervalo, comissão/prêmio/variável, noturno, salário; férias só "em dobro"). Fonte = tabela da esteira
`tb_resultado_hist_salarial_proventos_ia` (todas as rubricas; o P7 quase nunca traz HE paga), gravada em
`ft_score_confianca/dados/proventos_holerite.pkl`; campo `proventos_holerite` no caso; sem ele, vale a regra antiga.
Caiu o atalho "o critério cita quitado/recebido/TRCT". Medição antes: 157 aptos marcados, o PJC abateu em só 14 (9%); as
14 tinham a rubrica no holerite; 88 verbas sem rubrica = 0 abatimento no PJC. Férias quase sempre têm rubrica paga (todo
ano) → não separa; mas férias em dobro seguram o 0001111-59.2019.5.09.0654 (−139%). Efeito no apto valor: 13 subiram
para a alta (auditor rodado: 4 alto, que voltam a sair — 1000788 45% acertou; 0001150, 0001361, 1000503 eram 90–93%);
5 bons caíram (holerite mostra HE paga e o PJC também não abateu). Alta apto valor 100 → 104, 81% com 80%+.
Pendente: entender os ~94 "holerite tem, PJC não abateu" (decisão do calculista? só mesma rubrica/mês?).

**Medido em 30/10:**
- Alta do apto valor 61 (19/10) × 100: base 3,4×, apto valor 2,6×, alta 1,6×; precisão da alta 79% → 82%. O score ficou
  mais rigoroso (restrições 22/10, calibração 27/10, auditor). Dos 24 apto valor que eram alta em 19/10 e saíram: 3 pelo
  auditor, 11 por trava, 10 por risco; 18 têm 80%+.
- Inflamável no prédio (premissa 3.0): **inegociável** (Raíra, 30/10), fica travando.
- **Prêmio 18.0 refeito e aplicado em 30/10 (decisões dela):** o 18.0 restringe só a NATUREZA SALARIAL pós-10/11/2017
  (reflexos do prêmio e prêmio na base de outra verba); **o prêmio deferido em si NÃO é restrito**; **comissão pura não
  é prêmio** (bancário é 19.6); leitura conservadora: PPE, SRV, AGIR, GERA, PIV, remuneração/gratificação variável,
  produtividade, bônus, incentivo CONTAM como meta. Regra `restr_premio_2017` em restricoes.py
  (`_premio_natureza_salarial`), sem Jev (a pergunta "condena a pagar prêmio?" perguntava a coisa errada); a própria
  diferença de prêmio/comissão com RV na base não conta como integração. Backup restricoes.py.bak_3010. Antes: 73
  travados, 47 só com o prêmio principal, comissão pura entrava pelo código BT024 (= comissão E SRV). Depois: 67 (38
  saem, 32 entram). Apto valor alta 104 → 106 (79% ≥80%); auditor nos 5 que subiam: 0000796 (−51%) alto ✓, 1000846
  (94%) alto ✗. Pendente: 0010369-17.2025.5.03.0051 (PPR 100%) cai na baixa pelo auditor (erro do auditor de novo).
- Auditor: risco "alto" 61% calcula a mais × 13–14% médio/baixo; os "alto" errados são verba restrita pelo manual (art.
  62/Tema 300) com IA ≈ PJC.

**Regras de 30/10 noite (todas aplicadas no pacote e no painel de 23/10; 19 testes):**
- `dano_material_calculado` (a mais → baixa): dano material/pensão cujo valor não é o fixado no critério do P4, ou com
  vincendas. Alta 266→246, ≥80% 74→76%, a mais 15→12%.
- `inflamavel_armazenamento` (pergunta v2 do Jev, bloco próprio) SUBSTITUI `inflamavel_predio` na trava
  jev_inflamavel_predio: "inflamável armazenado dentro da edificação (tanque, depósito, almoxarifado), não abastecer/
  manusear/transportar, nem contêiner/isotanque/veículo/gás". Marca tudo o que a antiga marcava + 0021441, 1000617,
  0000781. O PJC NÃO serve de gabarito aqui (calculistas apuram contra a premissa 3.0).
- `restr_pensao_fora_do_codigo` (restrita): Jev pensao_qualquer ≥ 0,8 e IA sem BT059/BT051 — pensão sumiu ou caiu
  no teto de dano moral (BT040/BT052/BT050 têm teto de R$ 5 mil por código; 0020486: pensão de R$ 126 mil virou R$ 5
  mil em BT040). Substitui o teste "Jev sozinho não acende".
- `total_ia_baixo` (+3, a menos → baixa): total da IA < R$ 2.000. Treino 97–100% ruins, nenhum bom na alta.
- `he_zero_sem_explicacao` (+1 → média): HE com 0 h em ≥ 20% dos meses trabalhados SEM explicação (descontados
  abatimento ≥ devido, base sem salário, férias/afastamento). A versão "qualquer mês zerado" não separava na alta.
  Princípio dela: **a regra tem que vir do que é errado**, não do sintoma (zeros legítimos fora).
- Sobrestamento (Tema 38 IRR) testado e descartado: a decisão que sobresta não está nas peças baixadas.
Resultado: alta 234 (79% ≥80%), apto valor alta 106 (82%).
- **Concausa na pensão em parcela única (04/11), testada e descartada:** caso 0000154-41.2023.5.05.0133 (fixado R$ 92
  mil, PJC aplicou 50% de concausa). Regex "concausa" tira 10 bons por 3 ruins (nos bons a decisão já embutiu a
  concausa no valor/percentual fixado e IA = PJC). Pergunta do Jev "deixou de descontar a concausa?" em 52 casos: 36%
  de precisão, 0000154 com 0,37. Nada aplicado; bloco removido do perguntas.json.

**Auditor em TODO apto na alta (30/10, decisão dela):** antes só no apto valor. aplica_score_jev lê o auditor de qualquer
apto; auditor_apto_valor.py lista todo apto na alta. 187 aptos na alta fora do apto valor auditados (US$ 58): 39 alto
saem (49% ≥80, 49% a mais), ficam 148 (72% ≥80, 13% a mais; 116 com IA < R$ 50 mil, 32 > R$ 200 mil). Alta total 305
→ 266; apto valor alta 118 (78%). Custo extra por rodada: ~US$ 0,17 por apto novo na alta.

**Gabarito PJC × PDF (30/10):** ids diferentes agora valem o `.pjc`, marcados com `*` ([[pjc-pdf-calculos-diferentes]]);
51 viraram aptos e ganharam score.

**OpenRouter:** teto US$ 300 (Raíra, 30/10) em roda_gemini.py e roda_analista.py, gasto ~US$ 200 em 30/10. Agente do erro
via OpenRouter saiu ~US$ 4,40/caso (não 1,70); 2 casos passaram de US$ 8 sem gravar. Não lançar agente do erro sem ordem.

**Why:** ela pediu para guardar tudo do score (30/10) para não refazer a discussão. **How to apply:** antes de mexer em
regra, simular sem gravar (rodar `pipeline.pontuar` com e sem a mudança nos aptos do painel, comparar faixas, alta do
apto valor, ≥80% e IA a mais), listar quem entra/sai, rodar o auditor nos que entram na alta do apto valor, e só então
aplicar no pacote + `aplica_score_jev`.
