# Arquitetura — estimativas residenciais 0.25.1

Next.js App Router/TypeScript/Tailwind apresenta formulários, biblioteca de projetos, resultados e relatórios. Python/FastAPI/Pydantic2 valida contratos; SQLAlchemy2/Alembic preservam SQLite e portabilidade PostgreSQL. Início/sidebar e três perfis permanecem. Fluxo: Projeto/Imóvel → Ambientes/Equipamentos → Resultados e Estimativas → Relatório.

## Módulos e fluxo

- frontend/src/app/page.tsx orquestra edição, conflitos, autosave, rascunhos e exportação; componentes de equipment/projects/calculations apresentam dados.
- use-workspace-resources consulta health, requisitos de formulário, estados, distribuidoras e catálogo independentemente. Não consulta normas. Acervo é acesso explícito e separado.
- use-calculation aplica debounce400ms, AbortController e sequência contra respostas antigas. Edições relevantes invalidam o resultado; números antigos ficam ocultos/inertes enquanto a geometria é preservada. Não há fórmulas energéticas em TypeScript.
- backend/app/calculations/engine.py reutiliza equipment/power/energy/current/units e agrega com Decimal. Não importa/executa demanda, circuitos, entrada, geometria ou registro normativo.
- estimate_metadata fornece revisão/hash do motor, independente de documentos. locations contém candidatos contextuais previamente existentes, sem inferir atendimento municipal. utility_name aceita nome informado em qualquer UF.
- main expõe cadastro/CRUD/histórico, cálculos loads/full, catálogo, localização contextual, relatórios PDF/JSON e acesso independente ao acervo. Rotas de demanda, standards, regras/aplicabilidade/integridade normativa e revalidation foram retiradas. Leitura de revisões históricas e recalculate explícito preservam rastreabilidade; nenhum executa norma.
- reports/summary mapeia resultados para JSON2.0; reports/pdf apresenta identificação, imóvel, equipamentos, energia/custos, distribuições, memória e premissas. Snapshot guarda digest, versão do motor e revisão própria contra exportação antiga; não exige documento normativo.

## Persistência e compatibilidade

ProjectRow.payload é JSON; HistoryRow conserva entradas/resultados de cada versão. Migrações0001–0007 preservadas. Campos antigos energisa_demand/circuits/service_entry/classificações/geometria permanecem nos snapshots, marcados como compatibilidade onde aplicável. Não são exibidos, avaliados ou apagados. property_stage e utility_name opcionais não exigem migração SQL nem atualização em massa. ProjectInput normaliza entradas sem tocar o banco na leitura; edição/salvamento explícitos criam versão com mesmos manuais, referências, IDs e localização.

TechnicalRevisionRow também armazena a revisão própria de estimativas por compatibilidade de armazenamento, sem buscar o acervo. O nome legado standards_version/registry_version no transporte representa agora o identificador estável do motor; não é validação normativa. Históricos antigos conservam seus hashes/resultados originais.

## Browser e distribuição

browser_runtime despacha o mesmo motor Python via Pyodide; store JSON/localStorage, histórico e backup imediato independem do SQLite local. build_pages inclui estimate_metadata e locations; o bundle inclui somente os módulos necessários às estimativas, sem enviar módulos normativos ao runtime. Builds local/standalone e estático permanecem disponíveis. ZIP estável publicado0.24.1 é anterior à reformulação; publicação nova não foi presumida.

## Execução e verificação

Reutilizar backend/.venv e frontend/node_modules. Na raiz: `python3 scripts/start_local.py --no-browser`; execução manual em [setup](setup.md). Serviços só são apresentados como disponíveis após HTTP. Contratos: `cd frontend && npm run types:sync`, nunca editar api.generated.ts. Testes e comandos em [CONTRIBUTING](../CONTRIBUTING.md); E2E usam banco/portas8010/3010 isolados. Não executar build/E2E simultaneamente. Backup/retomada em [continuity](continuity.md). Arquitetura anterior preservada em [history](history/README.md).

## Comparação opcional de cenários

A comparação explícita usa `/calculations/compare` nos mesmos módulos Python; não grava dados nem consulta o acervo. O cliente cancela a requisição e oculta diferenças quando a edição muda.

Ajustes 0.25.1: ScenarioComparison usa fronteira por projeto/abertura e snapshot de referência independente de saved.version, com mudança explícita e cancelamento/ocultação em edições. A idempotência aceita metadados legados sem id; validação desses metadados exige somente números JSON finitos. Potência pendente com energia declarada é informação para W, sem bloquear kWh.
