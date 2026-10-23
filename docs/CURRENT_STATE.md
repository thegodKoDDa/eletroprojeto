# Estado atual — EletroProjeto 0.12.0 / motor 0.7.0

## Produto e dados

API/frontend 0.12.0, motor 0.7.0, migração 0005. SQLite local com 9 projetos (8 ativos e 1 na lixeira), 29 históricos e 7 revisões técnicas no checkpoint anterior à organização. Nenhuma fórmula, configuração privada, migração ou dado de projeto foi alterado pela limpeza de 23/10/2026.

NDU-001 7.0 fornecida pelo usuário sustenta o endpoint parametrizado `/api/v1/calculations/energisa-demand`, no escopo residencial individual Energisa Sul-Sudeste/SP, até 75 kW, parcelas d1–d5. Classificação automática do cadastro, d6/d7/centrais presentes e dimensionamento final seguem pendentes. Fontes/condições/testes em [standards](standards.md) e [calculations](calculations.md); não declarar aprovação pela concessionária ou conformidade final.

Rascunhos recuperáveis, conflitos guiados, autenticação HTTPS/CSRF com isolamento por proprietário, catálogo persistente e portabilidade PostgreSQL foram implementados. A entrega anterior registrou 320 testes backend + 85 subtestes, 90 frontend, 12 E2E locais e 1 E2E HTTPS; são evidências da entrega funcional anterior, não nova execução da limpeza. Windows e PostgreSQL também foram verificados naquela entrega; ver [sessões](SESSION_HISTORY.md).

## Organização — 23/10/2026

Inventário dos arquivos próprios, leitura automatizada com hashes/validação sintática Python e JSON, revisão de configurações, documentação e saídas locais. PDFs movidos para `references/energisa/`, com edição 6.3 em `historico/` e hashes preservados. Cinco revisões movidas para `docs/history/`; [índice](README.md) define o papel de cada pasta/documento. O antigo estado cumulativo foi preservado integralmente em `history/state-before-organization.md`, com ajuste de links relativos; não usar suas afirmações históricas como estado atual.

Removidos apenas caches regeneráveis Python/pytest/Ruff/TypeScript, relatórios temporários de testes e dois marcadores de download Zone.Identifier. Ambientes Linux/Windows, node_modules, Next ativo/build, bancos, backups históricos, fontes, migrações, Git e checkpoints preservados. Manifesto privado de movimentações/exclusões: `.checkpoints/cleanup-20261023.json`. PDFs continuam excluídos de Git/ZIP de código; precisam de cópia externa própria.

Ponto de recuperação anterior: `.checkpoints/20261023T181839782078Z`, 156 arquivos, hashes/ZIP/banco/bundle Git verificados com restauração SQLite e clonagem Git isoladas. Verificações e checkpoint final desta limpeza serão registrados abaixo e em SESSION_HISTORY.

## Próximo trabalho

Consultar [pendências](KNOWN_ISSUES.md): integração automática da demanda, dimensionamento e geometria completos, associação territorial oficial, implantação remota, execução hospedada do CI, backup externo protegido, impressão física e leitor de tela real. Não houve push ou publicação. Checkpoints no mesmo disco não protegem contra perda física.

Retomar por AGENTS e `python3 scripts/continuity.py retomar`; conferir processos e HTTP antes de iniciar serviços. Frontend 3000/API 8000 estavam ativos na inspeção anterior à limpeza; disponibilidade final depende da verificação abaixo.

## Verificação final da organização

Backend320 testes+85 subtestes, frontend90, continuidade/backup8, tipos/lint, Alembic check, links locais e hashes aprovados. Dados comparados integralmente ao checkpoint anterior e preservados. API8000 health0.12.0/motor0.7.0 e frontend3000 HTTP200 confirmados. Não repetidos build/E2E/PostgreSQL/Windows nesta alteração documental e de arquivos locais, sem mudanças no código de execução. Detalhes e limitações em SESSION_HISTORY.


Checkpoint final da organização: `.checkpoints/20261023T182530510469Z`, 159 arquivos; hashes/ZIP/banco/bundle Git e restauração SQLite/clonagem Git isoladas aprovados. Commit da organização `2eaeb21`; registro do caminho feito após a geração, em commit documental separado. Banco preservado (9 projetos/29 históricos/7 revisões,0005). Sem push ou cópia externa; PDFs locais não integram o ZIP de código.
