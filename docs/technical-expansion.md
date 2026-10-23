# Expansão técnica incremental — 21/10/2026

## Alterações efetivas

- Corrigido vínculo indevido da demanda Energisa quando distribuidora não confirmada ou outra distribuidora selecionada. Até a Energisa/SP permanece com demanda nula e pendente.
- Registro técnico com documentos, versões conhecidas, situação da revisão, data de consulta, fórmulas matemáticas, condições e testes associados.
- Tabela `technical_revisions`, migração 0002 sem remoção de dados. Backup prévio em `/tmp/eletroprojeto-before-technical-0002.db` (cópia temporária, não backup externo permanente).
- Cadastro aceita as 27 UFs. Sete candidatas estaduais em SP: Energisa Sul-Sudeste, CPFL Paulista, Piratininga e Santa Cruz, Neoenergia Elektro, Enel SP e EDP SP. Nenhuma tem regras de demanda validadas. Município permanece texto livre; não há associação territorial oficial importada nem seleção automática.
- Interface preservada: estado, candidatas filtradas e verificação de referências; mudança de estado limpa distribuidora anterior. Localização integra a chave de debounce/cancelamento e as entradas de cálculo.
- Recálculo explícito com controle de concorrência, comparação sem alteração do projeto, histórico anterior preservado, duplicação via API. Relatório distingue prévia atual e cálculo histórico.
- Catálogo ampliado: 30 registros, 27 com potência documentada; três entradas personalizadas sem potência sugerida. Acrescentada referência de ar-condicionado 9000 BTU/h: entrada nominal 800 W/220 V, fonte oficial LG; o padrão 12000 BTU/h anterior foi preservado. Não foram revalidadas individualmente todas as fichas antigas.
- Importação local de candidatos com evidência; nada é publicado automaticamente. Validação estrutural não equivale a verificar online as fontes.

## Rotas acrescentadas

- `GET /api/v1/locations/states`
- `GET /api/v1/technical/documents`
- `GET /api/v1/technical/applicability?utility=cpfl_paulista&state=SP`
- `GET /api/v1/technical/rules`
- `GET /api/v1/technical/integrity`
- `GET /api/v1/technical/revisions` e `/{revision_id}`
- `GET /api/v1/projects/{id}/revalidation`
- `POST /api/v1/projects/{id}/recalculate?expected_version=N`
- `POST /api/v1/projects/{id}/duplicate`
- `GET /api/v1/equipment/{equipment_id}`; listagem aceita `q` e `category`.
- `GET /api/v1/utilities` aceita estado e município. Município não reduz candidatas sem evidência territorial.

## Fontes consultadas nesta etapa

- [Energisa — normas técnicas](https://www.energisa.com.br/normas-tecnicas): portal lista NDU-001 v7.0, em vigor 01/11/2024. Tentativa de abrir PDF oficial retornou 403; tabelas não implementadas.
- [CPFL — normas técnicas](https://www.cpfl.com.br/normas-tecnicas): GED-13 listado; edição vigente não confirmada. Não se adotou edição de PDF antigo.
- [EDP — normas e padrões](https://www.edp.com.br/normas-e-padroes-tecnicos/): portal diferencia SP/ES; revisão aplicável ainda pendente.
- [Enel SP — normas técnicas](https://www.enel.com.br/pt-saopaulo/normas-tecnicas.html): localização oficial registrada, documento de fornecimento/revisão ainda pendentes.
- [Neoenergia — documento oficial](https://www.neoenergia.com/documents/d/sp/dis-nor-030-fornecimento-energia-eletrica-tensao-secundaria-distribuicao-edificacoes-individuais-rev3-pdf?download=true): revisão histórica localizada, vigência atual não confirmada; nenhuma tabela habilitada.

ABNT NBR 5410 continua sem edição/texto oficial conferido. Potência instalada, P/FP, correntes mono/trifásicas equilibradas e conversões dimensionais são operações matemáticas; não são validação de previsão normativa ou dimensionamento.

## Uso na interface

Escolha estado, informe município e confirme manualmente a distribuidora quando disponível. Cadastre/edite cargas normalmente. Salve para registrar o contexto técnico; em projeto salvo, “Verificar referências” informa divergência de revisão. A API permite comparar os dois resultados e registrar novo cálculo explicitamente. Nenhuma atualização troca valores manuais ou aplica outra concessionária silenciosamente.

## Pendências reais

Base nacional e territorial municipal, cobertura de permissionárias/cooperativas, tabelas de demanda verificadas, iluminação/TUG normativas, atualização HTTP controlada por adaptadores, revisão granular de impactos e autenticação para implantação externa não estão concluídas. Dados de rede não foram importados como validados. Campos administrativos de revisão continuam locais.

Fonte nova do catálogo: [LG S3-Q09AA33A](https://www.lg.com/br/ar-condicionado-residencial/dual-inverter-split/s3-q09aa33a/), especificações gerais consultadas em 21/10/2026: entrada nominal de refrigeração 800 W, mínima 150 W, 220 V/60 Hz, capacidade nominal 9000 BTU/h. FP não publicado e não presumido. A referência genérica permanece uma estimativa editável baseada no conjunto identificado.

## Verificações executadas

- pytest: **70 testes aprovados, 11 subtestes**. Inclui fórmulas anteriores, isolamento por distribuidora, histórico/revalidação, concorrência, cópia de projeto, nova referência 9000 BTU/h, backup e validação de candidato externo.
- Vitest/RTL: **24 testes aprovados**. Inclui transmissão da localização, limpeza da distribuidora ao mudar UF e preenchimento da variante não padrão sem seletores comerciais.
- TypeScript/typegen, geração OpenAPI e `alembic check` aprovados; `compileall` aprovado.
- Migração aplicada no SQLite existente. Comparação SQL de todos os registros de `projects` e `calculation_history` com backup anterior confirmou conteúdo idêntico. Cópia adicional preservada em `backend/backups/before-technical-0002.db`, ignorada pelo Git; ainda exige armazenamento externo para proteção contra perda do disco.
- Playwright tentado: Uvicorn não conseguiu abrir `127.0.0.1:8000`; cenário não chegou ao navegador. Responsividade visual não confirmada nesta etapa.
- Build Webpack tentado: falhou ao interpretar saída do subprocesso TypeScript `--showConfig`; typecheck direto passou. Build de produção continua pendente.
- Nenhum localhost ativo foi confirmado nesta execução.

## Arquivos principais desta alteração

`backend/app/technical.py`, `schemas.py`, `database.py`, `main.py`, `catalog.py`, `calculations/engine.py`; migração `0002_technical_revisions.py`; `backend/technical_admin.py`; testes API/admin; OpenAPI e tipos gerados; `frontend/src/app/page.tsx`, `lib/api.ts`, `lib/use-calculation.ts`, `components/equipment/EquipmentEditor.tsx`; testes de página/editor e seletor municipal E2E. Documentação de arquitetura e este relatório.
