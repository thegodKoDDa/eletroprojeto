# Revisão funcional 0.4.0 — 22/10/2026

Aplicação/API/frontend: 0.3.0 → 0.4.0. Motor: 0.4.0 → 0.4.1 para corrigir classificação de estado; fórmulas matemáticas preservadas. Nenhuma dependência substituída.

## Diagnóstico e correções

### Projetos

O banco auditado possui dois projetos com UUIDs distintos: um ativo e um excluído logicamente, recuperável. Não foi encontrada evidência de sobrescrita entre esses registros. Foram identificados problemas concretos no fluxo:

- Renomear o projeto aberto mantinha seu ID e podia disparar autosave, dando a impressão de substituir uma residência por outra. Agora há Novo projeto e Salvar como novo explícitos; mudar o nome pausa o autosave até escolher entre renomear e criar outro registro.
- A lista inicial aguardava o catálogo via Promise.all e podia substituir uma lista mais nova obtida após salvar. As cargas foram separadas; contador de sequência rejeita respostas anteriores.
- Não havia limite na listagem visual nem consulta completa organizada. O frontend busca três recentes e oferece Ver todos, pesquisa por nome, ordenação e páginas de 20 registros. A API aceita limit/offset/q/sort, preservando o contrato anterior sem filtros.

Criação usa POST/UUID novo; atualização mantém PUT/ID/versão otimista. Uma trava local evita duas gravações simultâneas do mesmo formulário. Duplicação/exclusão/restauração continuam por ID e versão. A consulta completa cancela buscas obsoletas, desabilita ações durante carga e oferece nova tentativa após falha.

Não houve migração ou alteração de schema SQLite nesta entrega. Backup íntegro: `backend/backups/before-0.4.0-20261022.db` (ignorado pelo Git); cópia inicial em `/tmp/eletroprojeto-before-040-20261022.db`. Comparação SQL integral confirmou preservação dos 2 projetos, 6 históricos e 3 revisões técnicas. O projeto excluído não foi restaurado automaticamente, preservando a intenção de exclusão anterior.

### Navegação e avisos

O destaque de Projetos e cargas era fixo. SectionNavigation agora utiliza o hash da URL, atualização por navegação/volta e aria-current, com somente uma opção ativa. Corrigir informação sincroniza a seção, abre detalhes ancestrais, rola e foca o campo por ID estável.

Falhas de salvamento passam a disponibilizar diagnósticos navegáveis; a resposta de potência inválida também contém localização, solução e alvo. Avisos já apresentados pelo cálculo são deduplicados. Limitações internas não recebem botão falso de correção. Foco por teclado de links e summaries foi reforçado. O botão Corrigir informação possui nome acessível explícito, sem depender da concatenação de spans ocultos.

### Catálogo por ambiente

`equipment_relevance.py` concentra associações por tipo/categoria/exceção de equipamento. `recommended_environments` é retornado pela API e utilizado pelo seletor de cada ambiente. Quarto/cozinha não sugerem chuveiro; banheiro sugere chuveiro, aquecimento, iluminação, secador pequeno e exaustor. A busca geral continua disponível; não existe proibição no backend para instalações excepcionais. Alterar tipo de ambiente preserva as cargas.

Foram acrescentadas quatro referências genéricas Enel (secador pequeno, exaustor de parede, carregador e aparelho de som) e três variantes de AC Midea. Total verificado: 37 registros, 34 com potência documentada; os três restantes continuam sem potência inventada. Novos equipamentos ainda dependem de referências próprias; não foi criada uma potência arbitrária para notebook ou outro tipo ausente.

### Ar-condicionado e reatividade

Capacidades rápidas incluem 7/9/12/18/24/30/36 mil BTU/h e o campo aceita valores personalizados. Existem referências elétricas de 9/12/18/24/30 mil BTU/h. 7 mil, 36 mil ou capacidades personalizadas sem correspondência continuam exigindo potência elétrica informada.

Mudança de capacidade, tipo ou compressor procura uma referência compatível. Na ausência, a sugestão automática é invalidada, sem transformar BTU/h em W elétricos. Potência manual é preservada; também são preservados nome personalizado e parâmetros manualmente diferentes da referência. FP não deriva da capacidade térmica. Troca de tensão não altera W.

Os testes existentes de quantidade, tensão, FP, motores/rendimento, micro-ondas, energia mensal e classificação cadastral foram reexecutados. O frontend continua sem fórmulas elétricas; resultados provêm da API e respostas obsoletas continuam rejeitadas.

## Demanda e iluminação: o que mudou e o que continua pendente

O card de demanda exibia um texto fixo. Agora usa valor, unidade, estado e motivo retornados pela API, incluindo suporte de apresentação a resultado calculado/estimado quando houver regra implementada.

A API também classificava concessionária não confirmada como fora do escopo. Agora retorna pending, com direcionamento para confirmar a concessionária. Após selecionar Energisa/SP, retorna awaiting_technical_validation porque os procedimentos não estão validados. Outra combinação sem cobertura continua out_of_scope. A potência instalada segue calculável independentemente.

**Não foi implementada uma demanda normativa final nesta entrega.** O portal oficial consultado identifica NDU-001 7.0, vigente desde 01/11/2024; a abertura do PDF oficial falhou. Tabelas, condições, parcelas e fatores não foram integralmente conferidos. Não foi adotado fator arbitrário nem expressão preliminar com 0,92.

O aviso de iluminação corresponde à previsão mínima normativa, não à soma nominal das lâmpadas. A regra NBR 5410 ainda depende de edição/cláusulas/texto autorizado e exemplos independentes. O aviso agora identifica regra/documento, efeito e dependência da equipe técnica, sem sugerir que preencher um campo resolve a validação. O resumo não afirma pendência fixa se a API retornar outro estado.

## Fontes consultadas e incorporadas

- [Midea Xtreme Save Connect C](https://www.midea.com/content/dam/midea-aem/br/climatizacao/hiwall/ar-condicionado-split-springer-midea-xtreme-save-connect-c-9-000-btu-h-quente-frio/Manual%20do%20Usu%C3%A1rio_Xtreme%20Save%20Connect%20C.PDF): ficha publicada no domínio oficial, setembro/2022, página 2, ciclo Frio. Entradas elétricas nominais: 18.000 → 1.583 W; 24.000 → 2.170 W; 30.000 → 2.430 W. Tensão publicada 220 V; FP/corrente não publicados permanecem desconhecidos. Metadados incluem conjunto de modelos e consulta 22/10/2026. Dados de um modelo são sugestões de categoria identificadas, não características universais.
- [Tabela Enel de equipamentos](https://www.eneldistribuicao.com.br/Equipamentos.aspx): valores genéricos em kW, armazenados em W e classificados como estimativas, sem supor tensão/FP. Não são fatores normativos de demanda.
- [Portal Energisa](https://www.energisa.com.br/normas-tecnicas): edição/vigência identificadas pela consulta; PDF integral inacessível pela ferramenta. Nenhuma tabela desse documento foi incorporada como validada.

## Arquivos envolvidos

Backend: `app/{main,projects,technical,validation,schemas,catalog,version}.py`, novo `equipment_relevance.py`, `pyproject.toml`, `openapi.json`, testes API/equipamentos.

Frontend: `app/{page.tsx,globals.css}`, `components/projects/{ProjectWorkspace,SectionNavigation}.tsx`, `components/equipment/{EquipmentEditor,RoomEquipmentPicker}.tsx`, `components/calculations/{ResultsPanel,DemandSummary}.tsx`, `calculations-notices.tsx`, contrato gerado, versões/lock, fixtures e testes de página, workspace, navegação, recomendações, resultados, avisos, equipamentos e E2E.

Documentação: README, arquitetura, roadmap, CHANGELOG e este relatório.

## Evidências e limitações de execução

- pytest: 108 testes e 11 subtestes aprovados. Inclui cinco registros distintos, independência de edição, duplicação, exclusão seletiva, reabertura em sessões SQL separadas, paginação e estados de demanda; exemplos matemáticos independentes e valores documentados de catálogo.
- Vitest/RTL: 55 testes aprovados. Inclui cinco projetos na consulta completa, três recentes, navegação exclusiva, sugestões em sete tipos de ambiente, troca de BTU/h, proteção de valores manuais, corrida da lista inicial e salvamento como novo após renomear.
- OpenAPI, TypeScript, compileall, integridade SQLite e Alembic check aprovados.
- Build Webpack tentado: falha ao interpretar saída TypeScript --showConfig neste ambiente. Não há build de produção aprovado.
- Lint tentado: script/ESLint ainda ausentes. Não houve alegação de lint aprovado.
- Playwright: dois cenários listados, incluindo cinco projetos/reload. Execução bloqueada antes do navegador pela impossibilidade de abrir a API em 127.0.0.1:8000. Esses cenários não foram aprovados.
- Next dev: listen EPERM na porta 3000; curl não pôde abrir socket. Nenhum localhost foi confirmado ativo nesta sessão.

Portanto, inspeção visual real, responsividade em navegador e fechamento/reabertura do aplicativo continuam sem execução. A reabertura de registros e consistência matemática foram verificadas em testes de API/ORM, sem serem apresentadas como testes de navegador. Previsão mínima normativa, demanda final, circuito/cabos/proteções e validação completa regional continuam pendentes. Nenhum dimensionamento conclusivo foi fabricado.
