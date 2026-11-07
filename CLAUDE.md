# Contexto para o Claude

Quem usa este repositório é a Raíra, do Fast Track (squad Precificação, BT Créditos). Responda em português,
direto, em prosa explicativa. Ela usa Windows e PowerShell.

Antes de qualquer trabalho no Fast Track, leia o índice das memórias e abra as que tocam o assunto:

@.claude/memory/MEMORY.md

As memórias são um retrato de 07/11/2026. Os caminhos que elas citam (`Repos\...`, `%LOCALAPPDATA%\bt_auto_pjc`) são
da máquina dela e podem não existir aqui. Confira antes de usar.

## Referências

- `contexto/premissas/premissas_calculo_04.2026.02.txt`: o manual "Premissas de Cálculo". É a regra da casa e
  vale mais que a leitura literal da decisão no tema que trata.
- `contexto/premissas/glossario_ft_producao_2026-10-06.csv`: o glossário de verbas BTxxx de produção.
- `contexto/premissas/premissas_situacao_esteira.json`: quais premissas a esteira já trata.
- `contexto/modelos/pagina_rodada_lote_0611.html`: modelo de página no visual LIFT (Onest/Sora, salmão #e26970,
  capa preta). Use o mesmo `<style>` em relatório ou artefato novo para ela.
- `.claude/agents/`: o agente analista de divergências e o auditor de etapas.

## Regras que valem sempre

- Nunca commitar segredo (token da Nekt, chave do OpenRouter); o `.env` fica fora do Git.
- Nunca fazer operação de escrita em banco de dados nem mexer em secrets.
- Em mensagem para outros times: "Fast Track" ou "squad Precificação", nunca "LIFT". Nunca usar "bater" para
  assertividade.
- Thread para o time: um título e uma mensagem só, curta, na primeira pessoa do singular.
- Calcular a mais pesa mais que calcular a menos: ordenar os problemas por isso.
