# Índice da documentação

Comece por [estado atual](CURRENT_STATE.md), [memória permanente](PROJECT_MEMORY.md), [pendências](KNOWN_ISSUES.md) e [roadmap](roadmap.md). Instruções de trabalho permanecem no [AGENTS](../AGENTS.md).

| Documento | Responsabilidade |
| --- | --- |
| [architecture.md](architecture.md) | Componentes, persistência e contratos. |
| [calculations.md](calculations.md) | Matemática, unidades e limites implementados. |
| [standards.md](standards.md) | Evidências normativas, fontes e validação. |
| [security.md](security.md) | Autenticação e operação local/remota. |
| [continuity.md](continuity.md) | Checkpoints, restauração e backup externo. |
| [forms-and-pdf.md](forms-and-pdf.md) | Formulários, relatórios e respectivas revisões. |
| [technical-expansion.md](technical-expansion.md) | Decisões e evolução da expansão técnica. |
| [audit.md](audit.md) | Auditorias e evidências datadas. |
| [SESSION_HISTORY.md](SESSION_HISTORY.md) | Registro cumulativo das sessões. |
| [CHANGELOG](../CHANGELOG.md) | Alterações por entrega. |

Revisões de versões anteriores ficam em `history/review-*.md`. O [estado anterior à organização](history/state-before-organization.md) conserva o documento cumulativo antigo: versões, contagens, processos e tarefas em andamento ali são históricos. Consulte CURRENT_STATE para a situação atual. Registros datados nos demais documentos também devem ser lidos pela data, sem transformar limitações antigas em pendências atuais.

## Pastas do projeto

- `backend/`: API, motor Python, migrações, testes e ferramenta de inspeção PDF. Banco e `backups/` são privados; ambientes `.venv`/`.venv-windows` e metadados de instalação são mantidos.
- `frontend/`: aplicação, contratos gerados, testes e configurações. `node_modules/` e `.next/` são saídas locais necessárias à instalação/execução.
- `scripts/`: continuity.py para retomar/checkpoint/verificar; maintenance.py para auditar instalação/permissões e limpar gerados; backup/QA e testes. Wrappers PowerShell preservados.
- `.github/`: automação CI. `.git/`: histórico local.
- `references/`: índice dos exemplares normativos locais; PDFs ignorados no Git.
- `.checkpoints/`: recuperação privada verificada, sem exclusão automática. Integrações privadas e arquivos `.env` permanecem em seus locais.

Mantenha configurações e instruções na raiz. Guarde novos documentos técnicos em `docs/`, revisões antigas em `docs/history/` e exemplares normativos em `references/`. Caches podem ser regenerados; dados, migrações, referências e backups exigem análise antes de qualquer exclusão.
