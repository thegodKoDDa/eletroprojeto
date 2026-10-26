# Verificações e evidências

Este documento organiza os resultados conhecidos. A fotografia operacional está em [CURRENT_STATE](CURRENT_STATE.md); regras e condições de aplicação estão em [standards](standards.md). Uma suíte aprovada verifica os cenários exercitados e não declara conformidade elétrica integral.

## Base funcional — versão 0.19.0

Validação executada em 26/10/2026:

| Área | Resultado |
| --- | --- |
| Backend | 500 testes e 85 subtestes aprovados |
| Frontend | 109 testes aprovados |
| Navegador | 24 E2E completos aprovados em banco e portas isolados |
| Contratos e qualidade | Geração de tipos, TypeScript, ESLint, Prettier, Ruff e build Webpack aprovados |
| Acessibilidade e layout | Axe e viewports de 320/390/768/1440 px exercitados nos cenários registrados |
| Preservação de dados | 12 tabelas reais idênticas ao checkpoint anterior; SQLite íntegro e sem falhas de FK |
| Recuperação | Restauração isolada do checkpoint e sincronização privada conferidas |

Os cenários incluem consumo, salvamento, rascunhos, conflitos, lixeira, exportação, demanda especial, circuitos trifásicos e geometria de envelopes. A consulta territorial também foi exercitada no navegador com a coleta local, sem gravação de projetos.

HTTPS de duas contas, PostgreSQL, Windows real, carga/pentest e inspeção elétrica física não foram repetidos nessa entrega. Resultados anteriores dessas plataformas permanecem históricos. Validação com leitor de tela real foi retirada do escopo por solicitação do usuário.

## Organização do repositório — 26/10/2026

Apresentação reorganizada a partir do padrão do Minecoord: README focado no produto, prévia real, guias por tarefa e contribuição separada. Modelos de issue/PR são arquivos do repositório; não criam conversas ou publicações automaticamente.

As capturas em `docs/assets` foram produzidas em um contexto de navegador separado. O exemplo de consumo usa dados fictícios e não grava projetos. Banco, credenciais, acervo e checkpoints permanecem ignorados. Não houve alteração de interface, fórmulas ou contratos nesta organização.

Checks proporcionais aprovados: links e âncoras locais, caminhos de imagens, renderização do README pela API Markdown do GitHub e inspeção no navegador, frontmatter dos modelos de issue, comparação integral dos registros movidos (somente links relativos ajustados) e 27 testes de continuidade. Descrição/tópicos conferidos pela API; repositório privado e Actions desativado preservados. A suíte funcional acima é da entrega 0.19.0 e não foi repetida por uma alteração exclusivamente documental.

## Registros anteriores

O [arquivo de auditorias até 0.19.0](history/audit-through-0.19.0.md) preserva causas, correções, casos exercitados e limitações das revisões anteriores. Contagens, processos e pendências ali devem ser interpretados pela data do registro.
