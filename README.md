# EletroProjeto

Estimativa de consumo elétrico residencial para leigos, estudantes e profissionais. Serve para uma moradia pronta ou planejada: **01 Projeto → 02 Ambientes → 03 Conferência**. Cadastre aparelhos e informe horários ou o consumo da etiqueta. Com a tarifa, o motor estima também o custo mensal; horários, ciclos e tarifas não são presumidos.

[Repositório privado](https://github.com/thegodKoDDa/eletroprojeto) · [Estado atual](docs/CURRENT_STATE.md) · [Documentação](docs/README.md) · [Continuidade](docs/continuity.md)

## Uso local

Ambiente desta instalação: Python3.14.4 e Node24.22.1; compatibilidade declarada Python3.11+/Node20.9+. Reaproveite ambientes e dependências existentes. A partir de `backend`, inicie a API:

```sh
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

A partir de `frontend`, inicie a interface:

```sh
npm run dev
```

[Aplicação](http://localhost:3000) · [API documentada](http://localhost:8000/docs). Confirme os processos existentes antes de iniciar outros. No Windows, use o Python do ambiente correspondente (`.venv-windows/Scripts/python.exe` nesta instalação).

Somente em uma instalação nova, crie o ambiente Python, instale `backend/requirements.lock` e o pacote local com `pip install -e . --no-deps`, execute Alembic `upgrade head` e, no frontend, `npm ci`/`npm run types:sync`. Os comandos Python são executados em backend com seu ambiente ativo ou interpretador explícito. Não instalar/atualizar tudo em cada retomada.

Configurações e exemplos em `backend/.env.example` e `frontend/.env.example`. Backend usa SQLite em `backend/eletroprojeto.db` ou DATABASE_URL absoluto; frontend aceita NEXT_PUBLIC_API_URL. A aplicação não cria tabelas automaticamente. PostgreSQL possui driver e validações anteriores; migrações0001–0007 são preservadas.

## O que oferece

- Projetos salvos/versionados, duplicação, histórico e lixeira com restauração. Autosave após primeiro salvamento manual, rascunhos locais e recuperação de conflitos.
- Ambientes e catálogo referenciado de aparelhos, com quantidades, potência manual e consumo por horários ou etiqueta. Referências são sugestões; editar aparelho não altera catálogo.
- Consumo/custo mensal em destaque e detalhamento por aparelho. Potência W/kW, VA/corrente quando há dados suficientes, memória e fontes em detalhes. Campos desconhecidos continuam nulos, sem zeros fictícios.
- Relatórios PDF/JSON com entradas atuais, consumo, hipóteses e pendências. Alterações invalidam resultados/exportações antigos; debounce/cancelamento preservam a edição.
- Biblioteca técnica local pesquisável: guias, modelos, diagramas e originais, com fontes e rastreabilidade. Importar/OCR não habilita regras elétricas.
- **Estudos técnicos opcionais**, recolhidos após a conferência: previsão residencial quantitativa de iluminação/tomadas, demanda NDU-0017.0 d1–d5 em escopo revisado e estudos limitados de circuitos/proteções/entrada ESS. Fontes, condições e limites em [standards](docs/standards.md) e [calculations](docs/calculations.md).

Os resultados são estimativas e estudos condicionados aos dados; não representam medição, fatura completa ou dimensionamento final da instalação. Não se infere potência elétrica de BTU/h ou kWh. O mesmo motor Python Decimal atende as apresentações simples/técnica; frontend não replica fórmulas.

## Retomar, encerrar e salvar

Peça ao agente **RETOMAR ELETROPROJETO** ou **ENCERRAR SESSÃO DO ELETROPROJETO**. Ele cuida das rotinas autorizadas sem transferir comandos de terminal para o usuário.

```sh
python3 scripts/continuity.py retomar
python3 scripts/continuity.py encerrar --sync
python3 scripts/continuity.py verificar
```

Encerrar pressupõe documentação/testes proporcionais e um commit revisado. Sincroniza somente com o GitHub privado conhecido, sem force-push, e salva/revalida o checkpoint local. Sem rede, preserva o checkpoint e informa a sincronização pendente. Retomar consulta o origin sem mesclar edições; `--offline` evita a consulta.

GitHub contém fonte/histórico. Banco de projetos, `.env` privado, checkpoints e acervo técnico ficam locais e ignorados. Os checkpoints preservam recuperação da fonte/SQLite/Git e compartilham armazenamento de bancos idênticos sem apagar versões. Limpeza/doctor são sob demanda; [continuidade](docs/continuity.md) descreve as opções e recuperação. CI hospedado permanece desativado; publicação do site, impressão física e cópia externa de dados estão fora do escopo atual.

## Estrutura

| Pasta | Responsabilidade |
| --- | --- |
| `backend/app` | API, persistência, relatórios e motor puro em `calculations`. |
| `backend/alembic` e `backend/tests` | Migrações e regressões Python. |
| `frontend/src` e `frontend/tests` | Interface, cliente API e testes unitários/navegador. |
| `scripts` | Continuidade, sincronização, manutenção e QA. |
| `docs` | Documentação responsável; registros antigos em `history`. |
| `references` | Fontes/acervo local; originais fora do Git. |
| `.checkpoints` | Recuperação privada verificada, fora do Git. |

Histórico de versões em [CHANGELOG](CHANGELOG.md), sessões em [SESSION_HISTORY](docs/SESSION_HISTORY.md). Não replicar fórmulas/normas em documentos novos. `backend/.venv`, `.venv-windows`, `frontend/node_modules` e caches úteis são instalações locais, não arquivos para enviar ao GitHub.

## Desenvolvimento e verificação

Backend: `.venv/bin/python -m pytest -q` em backend. Scripts: `backend/.venv/bin/python -m pytest -q scripts` na raiz. Ruff: `backend/.venv/bin/python -m ruff check backend scripts` e `ruff format --check backend scripts`. Migrações QA: `backend/.venv/bin/python scripts/check_migrations.py`.

Frontend, em frontend: `npm run types:sync`, `npm run typecheck`, `npm run lint`, `npm run format:check`, `npm test`, `npm run test:e2e`, `npm run test:e2e:auth` e `npm run build:webpack`. Executar apenas o conjunto relevante à mudança. Contratos gerados nunca são editados manualmente.

Playwright usa portas3010/8010 e SQLite temporário; HTTPS de duas contas usa3011/8010. Não rodar E2E e build ao mesmo tempo. QA não modifica o banco real. Para build isolado, use NEXT_DIST_DIR=.next/qa-build; restaure somente os caminhos gerados de next-env/tsconfig após conferir o diff. A rotina de limpeza conhece as saídas QA e preserva Next ativo/cache.

Modo local restrito a loopback; autenticação remota, sessões, CSRF e isolamento por proprietário permanecem implementados. Não expor o modo local por proxy público. Preparação para eventual implantação em [segurança](docs/security.md); não há implantação ativa.
