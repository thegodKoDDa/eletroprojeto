# Contribuir

Descreva o problema, a mudança proposta e as verificações executadas. Use exemplos e capturas com dados fictícios. Para preparar uma cópia nova, consulte [instalação](docs/setup.md); para decisões de implementação, [arquitetura](docs/architecture.md) e [AGENTS.md](AGENTS.md).

## Organização

- `backend/app/calculations`: matemática elétrica pura, com Decimal e unidades explícitas.
- `backend/app`: API, contratos, persistência e relatórios.
- `frontend/src`: formulários, apresentação e cliente da API; não replica fórmulas elétricas.
- `backend/tests`, `frontend/tests` e `scripts/test_*.py`: verificações da aplicação e continuidade.
- `docs`: documentos responsáveis por assunto; revisões antigas ficam em `docs/history`.

Preserve migrações, snapshots e valores manuais. Editar uma instância de aparelho não altera o catálogo. Uma regra não conferida retorna valor nulo e estado pendente; fontes oficiais, edição, condições e testes ficam em [standards](docs/standards.md) e [calculations](docs/calculations.md).

## Verificações

Execute o conjunto proporcional à alteração usando as dependências existentes. Não reinstale ou atualize versões para executar verificações rotineiras.

### Backend

A partir de `backend`:

```sh
.venv/bin/python -m pytest -q
```

A partir da raiz:

```sh
backend/.venv/bin/python -m ruff check backend scripts
backend/.venv/bin/python -m ruff format --check backend scripts
backend/.venv/bin/python -m pytest -q scripts
backend/.venv/bin/python scripts/check_migrations.py
```

No Windows, substitua `.venv/bin/python` pelo interpretador do ambiente existente. Mudanças de cálculos exigem exemplos independentes e testes de resultados e limites. Testes usam dados de QA; não rode experimentos sobre o banco de projetos.

### Frontend

A partir de `frontend`:

```sh
npm run typecheck
npm run lint
npm run format:check
npm test
npm run test:e2e
```

Playwright exige um navegador instalado. E2E usa banco temporário e portas 3010/8010; o cenário HTTPS de duas contas usa `npm run test:e2e:auth` e portas 3011/8010. Confira as portas antes da execução. Capturas e relatórios de testes não entram no Git.

Não execute build e E2E simultaneamente. Para um build isolado no Linux/macOS:

```sh
NEXT_DIST_DIR=.next/qa-build npm run build:webpack
```

No PowerShell, defina `$env:NEXT_DIST_DIR = '.next/qa-build'` antes do comando e remova essa variável ao terminar. Inspecione as alterações de `next-env.d.ts`/`tsconfig.json` geradas pelo Next antes de restaurar somente esses caminhos temporários.

### Contratos da API

Quando alterar schemas ou rotas, execute em `frontend`:

```sh
npm run types:sync
```

Isso atualiza `backend/openapi.json` e `frontend/src/lib/api.generated.ts`. Não edite o arquivo TypeScript gerado manualmente.

## Enviar uma alteração

No pull request, explique o comportamento esperado, os testes efetivos e qualquer limite restante. Atualize o documento responsável e o changelog quando houver mudança de comportamento. Para capturas de apresentação, use um contexto de navegador separado e dados fictícios, sem gravar projetos reais.

Banco, credenciais, `.env`, dependências, checkpoints e originais técnicos permanecem locais e ignorados. O workflow de qualidade está versionado em `.github/workflows`, mas GitHub Actions permanece desativado neste repositório; não apresente uma execução local como CI hospedado aprovado.

Continuidade, sincronização privada e recuperação estão em [docs/continuity.md](docs/continuity.md). Vulnerabilidades devem ser tratadas conforme [SECURITY.md](SECURITY.md).
