# EletroProjeto 0.13.1

NDU-001 7.0 integrada ao cadastro e aos relatórios: ative o painel de demanda, confirme o escopo, classifique cada carga e revise o inventário. No escopo residencial individual Energisa Sul-Sudeste/SP até75kW, d1–d5, o motor calcula a demanda estimada. Qualquer mudança relevante exige nova revisão. Selecionar a concessionária sozinho não habilita resultado. Limites/fontes em [standards](docs/standards.md); não há dimensionamento final.

Desde0.11.0 há recuperação local de rascunhos, resolução guiada de conflitos, sessões de usuário para implantação HTTPS e catálogo persistente versionado. Projetos existentes permanecem locais e sem proprietário até atribuição administrativa explícita. Motor atual0.8.0; demanda exige classificação/revisão explícitas; dimensionamento completo continua pendente.

Escopo atual definido pelo usuário: uso local. Publicação remota, execução hospedada de CI, impressão física e backup externo ficam fora do trabalho atual. Recursos existentes foram preservados. [Estado atual](docs/CURRENT_STATE.md), [roadmap](docs/roadmap.md) e [segurança](docs/security.md) descrevem funcionamento e limites.

Estudo de cargas residenciais com Next.js App Router, TypeScript e Tailwind; Python/FastAPI, Pydantic, SQLAlchemy, SQLite e Alembic. Toda matemática elétrica fica no backend.

**Etapa 1 parcial:** potência cadastrada e grandezas derivadas disponíveis. Previsão residencial de iluminação/TUG disponível por seleção explícita, em escopo limitado; demanda Energisa d1–d5 disponível mediante inventário e escopo revisados. Nenhum resultado é apresentado como dimensionamento final.

## Execução local

Python 3.11+ e Node.js 20.9+. Ambiente verificado: Python 3.14.4 / Node 24.22.1. Instalação exige acesso a PyPI/npm.

Backend, a partir da raiz:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, em outro terminal:

```bash
cd frontend
npm ci
npm run types:sync
npm run dev
```

Endereços configurados: [projeto](http://localhost:3000) e [API documentada](http://localhost:8000/docs). Serviços locais verificados na entrega 0.9.0; disponibilidade depende da execução atual.

Configurações: `NEXT_PUBLIC_API_URL` em `frontend/.env.local`; `DATABASE_URL`, `CORS_ORIGINS` e `MAX_REQUEST_BYTES` no backend (exemplos em `.env.example`). Banco padrão: `backend/eletroprojeto.db`, com caminho absoluto consistente entre API e Alembic. Não há criação automática de tabelas. O lock Python registra o ambiente testado em Python 3.14; PostgreSQL possui driver e validação local registrados no estado atual.

## Funcionalidades

- Criar/abrir/editar projetos; salvar com versão otimista e histórico. Duplicar e excluir diretamente na área de trabalho. Lixeira separada com data de exclusão, recuperação com histórico preservado e exclusão definitiva confirmada.
- Salvamento automático após primeiro salvamento manual, com debounce de 1,5 segundo, preservação de edições durante a requisição e sem repetição infinita da mesma falha. Alterações no nome pausam o autosave até escolher entre renomear o projeto e salvar como novo. Pode ser desativado em Outros dados do projeto. Projetos novos ainda precisam do primeiro salvamento; rascunhos recuperáveis dependem do armazenamento do navegador.
- Consulta completa paginada, com pesquisa e ordenação; sem aba Recentes no aside. Novo projeto e Salvar como novo criam registros independentes.
- Sugestões de equipamentos por ambiente, com alternativa de busca geral, sem apagar cargas ao mudar o tipo de cômodo.
- Ambientes com ação de adição sticky, foco no novo nome e preservação dos anteriores.
- Catálogo persistente e versionado, com referências documentadas e valores editáveis. Fonte original preservada; restauração disponível. Cadastro por equipamento comum, sem exigir marca/modelo.
- Decimal: W/kW, potência por ambiente/categoria, VA/kVA com FP suficiente, correntes conforme configuração, conversões térmicas e mecânicas com unidades separadas. BTU/h e kWh/mês não viram potência elétrica de dimensionamento.
- Recálculo com debounce de 400 ms, cancelamento e rejeição de respostas obsoletas. Exportações exigem cálculo atual.
- Tela inicial no Espaço de trabalho: criar projeto, abrir biblioteca ou acessar lixeira. Navegação e ações do projeto no aside; memória de cálculo dentro do projeto. Voltar ao Início mantém a edição nesta aba.
- Ações agrupadas: Salvar e PDF à vista no aside; demais ações em menu secundário. Resultados em resumo, memória e pendências. Apresentações simples/técnica do mesmo cálculo Python.
- PDF principal e JSON secundário com resumo de resultados, ambientes/categorias e situação normativa, sem memória ou referências. Arquivos usam o nome do projeto. Conferência de entradas e versões antes de exportar.
- Registro técnico versionado; seleção manual de distribuidoras candidatas por UF e comparação/revalidação do histórico. Não há associação municipal verificada nem demanda normativa regional completa.

## Verificações

```bash
cd backend
ELETROPROJETO_POLL_TEST_LOOP=1 .venv/bin/python -m pytest -q
.venv/bin/alembic check
```

O temporizador opt-in é uma adaptação apenas dos testes ao sandbox que bloqueia wakeups por socket entre threads.

```bash
cd frontend
npm run types:sync
npm run typecheck
npm test
npm run build:webpack
npm run test:e2e
```

Estado e verificações da entrega atual em [CURRENT_STATE](docs/CURRENT_STATE.md); revisão histórica 0.5.0 em [review-0.5.0](docs/history/review-0.5.0.md). O workflow `.github/workflows/quality.yml` prepara testes, contratos, TypeScript e build em CI; sua execução remota ainda não foi observada. ESLint e verificações de formatação estão configurados.

## Organização e referências

Consulte o [índice de documentação e pastas](docs/README.md) e o [índice dos exemplares normativos locais](references/README.md).

- `backend/app/calculations`: operações, resolução de equipamentos, agregações e referências normativas.
- `backend/app/projects.py`: snapshots e histórico; `main.py`: REST; `security.py`: limite HTTP/CORS; `database.py`: ORM; `reports`: geração documental.
- `frontend/src/components/projects`: área de trabalho; `calculations`: resultados; `equipment`: edição; `lib`: API, contratos gerados, recálculo e formatação.

Documentação de referência: [arquitetura](docs/architecture.md), [cálculos](docs/calculations.md), [normas](docs/standards.md), [segurança e recuperação](docs/security.md), [roadmap](docs/roadmap.md), [histórico](CHANGELOG.md). Relatórios anteriores em `docs/history/review-*`, `audit.md`, `forms-and-pdf.md` e `technical-expansion.md` são registros históricos; seus totais de testes não representam esta versão.

Modo local sem autenticação; modo remoto com autenticação e isolamento por proprietário implementados. Publicação exige a preparação operacional descrita na documentação de segurança. Revisão e responsabilidade técnica de profissional habilitado continuam necessárias.

## Continuidade entre sessões

Pedir ao Codex **ENCERRAR SESSÃO DO ELETROPROJETO** ou **RETOMAR ELETROPROJETO**. A leitura começa por AGENTS, [memória](docs/PROJECT_MEMORY.md), [estado atual](docs/CURRENT_STATE.md), [sessões](docs/SESSION_HISTORY.md) e [problemas conhecidos](docs/KNOWN_ISSUES.md). Scripts e recuperação estão em [continuidade](docs/continuity.md). Checkpoints locais privados não substituem Git nem cópia externa; rascunhos não salvos no navegador e buffers do editor não são capturados.

Os testes Playwright (`npm run test:e2e`, em frontend) usam serviços nas portas 3010/8010, SQLite temporário em /tmp e build separado em .next/e2e. Não reutilizam os serviços normais 3000/8000. A interface oferece nova tentativa para falhas ao carregar conexão, catálogo, projetos, estados e requisitos; a edição atual é mantida.

Na versão 0.6.1 o aside não tem Recentes. Projetos salvos e Lixeira são telas do conteúdo principal, mantendo a navegação lateral disponível. A biblioteca consulta o acervo completo ao abrir, com filtros próprios, atualização e paginação; o projeto em edição continua disponível pelo aside.

## Qualidade e cálculos de energia — 0.7.0

O formulário comum pede equipamento, quantidade e potência; tensão é destacada para corrente. Consumo mensal opcional e custo pela tarifa informada estão integrados ao mesmo motor Python e aos resumos PDF/JSON. Sem horários, tarifas ou ciclos presumidos; valores ausentes continuam desconhecidos. Decisões campo a campo em [audit.md](docs/audit.md), fórmulas/limites em [calculations.md](docs/calculations.md), plano de proteção em [security.md](docs/security.md).

Frontend: `npm run lint`, `npm run format:check`, `npm run typecheck`, `npm test`, `npm run test:e2e`, `npm run build:webpack`. Prettier ignora contratos gerados; gerar com `npm run types:sync`. Python: Ruff com configuração `ruff.toml` na raiz (`ruff check backend scripts` / `ruff format --check backend scripts`), pytest e Alembic. Ferramentas de auditoria Python desta revisão foram instaladas isoladamente em `/tmp/eletroprojeto-audit-tools`; não são dependências de execução da API nem instalação durável garantida. E2E usa banco temporário e portas 3010/8010, sem alterar o banco de uso normal.

## Cobertura normativa — 0.9.0

A API integra as pesquisas de iluminação, tomadas e demanda ao registro técnico: fontes oficiais, nível de evidência, trechos identificados e verificações restantes. `GET /api/v1/technical/rules?utility=energisa_sul_sudeste&state=SP` informa a cobertura para o contexto; `/calculations/full` inclui `normative_capabilities`. Metadados e fragmentos indexados não habilitam fórmulas.

A interface separa **Dados do projeto a revisar** de **Recursos normativos ainda indisponíveis**. Selecione **Previsão residencial (luz/TUG)** em Requisitos para: mínimos e cargas em VA são calculados por ambiente interno, preservando pontos manuais e potência em W. Área externa/outro não recebem classificação presumida. Demanda continua indisponível por falta de conferência integral da NDU; isso não representa um erro identificado na instalação. Fontes, métodos e limites em docs/standards.md. Foram removidas solicitações de preenchimento destinadas somente a operações indisponíveis. Dados manuais, geometrias, histórico e cálculos disponíveis continuam preservados.


## Relatórios de consumo — 0.10.0

PDF e JSON preservam os resultados anteriores e acrescentam cobertura do consumo, tarifa, equipamentos/uso considerado e pendências de preenchimento. Estimam consumo mensal para as cargas/hábitos cadastrados, não medição automática. Consumo parcial é identificado; potência, consumo e demanda permanecem grandezas separadas. A orientação de atendimento não substitui requisitos locais ou aprovação da distribuidora.

Os dois arquivos são preparados/recalculados pela API com proteção contra entradas antigas; JSON 1.2 é aditivo, legível e conserva valores nulos. Preencha consumo mensal por unidade ou potência com horas/dias de uso para obter estimativas; tarifa é opcional para custo. Não há horários, ciclos ou tarifas presumidos. Ver docs/forms-and-pdf.md para conteúdo/contrato e docs/standards.md para cobertura normativa.
