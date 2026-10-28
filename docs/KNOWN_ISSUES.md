# Limitações e pendências — consumo residencial 0.25.1

Pendências antigas de NDU, circuitos/proteções, geometria normativa e revisão do acervo não são bloqueios nem tarefas do produto atual. Registro anterior preservado em [history](history/KNOWN_ISSUES-before-consumption-scope.md).

| ID / impacto | Local e reprodução | Estado e comportamento esperado |
| --- | --- | --- |
| ENERGY-01 / limite do modelo | Informar só potência nominal de aparelho cíclico | Não infere ciclos/uso24h. Informar energia declarada ou tempo efetivo. Estimativa depende das premissas e pode diferir da medição. |
| COST-01 / cobertura | Sem tarifa ou fatura com encargos fixos | kWh continuam disponíveis; custo null sem tarifa. Valor estimado não é fatura completa. Não há tarifa regional automática validada. |
| DATA-01 / armazenamento | Limpar localStorage, trocar navegador ou desligar com buffer externo não salvo | Rascunhos/Pages são locais ao navegador, fora do SQLite/checkpoint. Não prometer recuperação externa inexistente. |
| COMPAT-01 / plataformas | Executar nova versão fora do ambiente Linux testado | Windows/macOS/ARM/Docker/PostgreSQL e leitor real não revalidados nesta entrega; não confundir testes históricos com novos. |

Falhas de comparação/autosave, metadados sem id e avisos de consumo corrigidas e testadas em 0.25.1; não permanecem como pendências. Referência da comparação é mantida somente na edição atual e reinicia ao reabrir/recarregar. Escopo de testes efetivamente executados em CURRENT_STATE e audit.md. Pesquisa técnica não equivale a inspeção presencial; não há promessa de aprovação regulatória. Impressão física e cópia externa continuam fora do escopo autorizado.
