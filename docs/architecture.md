# Arquitetura

Monorepositório com frontend Next.js App Router/TypeScript/Tailwind e backend FastAPI/Pydantic/SQLAlchemy. O Next executa apresentação, não matemática elétrica. Integração REST JSON; OpenAPI exportado pelo backend gera `frontend/src/lib/api.generated.ts` usando openapi-typescript.

Fluxo: formulário → debounce/cancelamento → validação Pydantic → funções puras → resposta tipada → memória visual. Resultados anteriores permanecem montados, identificados como desatualizados, enquanto o resultado atual e a exportação ficam bloqueados. Respostas obsoletas são ignoradas. Falha de API mantém a indicação de dados desatualizados, sem apresentar números antigos como atuais. Decimal serializa em strings; a UI usa Number apenas para apresentação localizada.

Projetos têm UUID, datas, versão otimista, parâmetros e revisão do registro normativo. Os snapshots completos JSON de ambientes e cargas são persistidos na tabela projects, com histórico de entradas e resultados a cada gravação em transação. PUT exige versão esperada e também usa verificação de versão do ORM para concorrência real. Exclusão lógica preenche `deleted_at`, preservando payload e histórico. Listagens e operações ativas excluem esses registros; recuperação exige versão otimista. Endpoints de cálculo avulso são puros e não geram histórico persistente.

O catálogo inicial é somente leitura e permanece separado das instâncias copiadas para os projetos. Ainda não existe cadastro global persistido de equipamentos, concessionárias e parâmetros. Não confundir essa primeira estrutura com todas as entidades normalizadas da especificação final.

Alembic controla criação de tabelas. DATABASE_URL configura SQLite ou, futuramente, PostgreSQL (instalar driver psycopg e verificar migrações nesse banco). JSON/String/DateTime são portáveis; migração e testes PostgreSQL ainda não foram realizados.

Erros: validação FastAPI 422 com localização do campo, UUID inexistente 404, conflito de versão 409. O cliente converte mensagens da API em texto sem renderização HTML. CORS lista origens explícitas. Sem autenticação: uso local, não publicar a API aberta como serviço multiusuário.

O esquema normativo permite documento, edição, vigência, cláusula, fonte, entradas, procedimento, limites e testes. Regras não conferidas ficam sem coeficientes e retornam valor nulo. O resultado global permanece aguardando validação mesmo quando a soma nominal é calculável.

## Revisão de estabilidade e equipamentos

O painel mantém o último snapshot montado enquanto recalcula e o identifica como desatualizado; o resultado atual e a exportação permanecem bloqueados nesse período. O escopo muda ao abrir outro projeto, impedindo reaproveitar visualmente números de uma residência diferente. Debounce, AbortController e sequência de requisições impedem respostas antigas de substituir entradas novas.

O payload de cálculo e seu digest incluem apenas utility/environments, com cargas e suas fontes. Metadados administrativos não dispararam matemática. CalculationInput permite estudo sem metadados de salvamento; ProjectInput exige cadastro completo. A versão do motor é 0.2.0.

CatalogItem/TechnicalParameters/LoadTechnicalResult são contratos Pydantic; a referência original é copiada para o snapshot JSON do projeto. O backend compara parâmetros para identificar substituições. O catálogo continua estático e separado da instância. Editor reutilizável em components/equipment preserva as classes visuais existentes.

SQLite mantém foreign keys ativas; datas de resposta são UTC mesmo após round-trip SQLite. API e Alembic compartilham o caminho padrão do banco. Endpoints foram testados com HTTPX ASGITransport, banco temporário e validações reais. Ver relatório para a opção de temporizador de teste necessária neste sandbox.

## Cadastro compacto

CatalogItem acrescenta apenas metadados opcionais de apresentação (`selection_name` e `selection_default`), preservando IDs, potências e documentos. O frontend agrupa a seleção por nomes comuns e copia a referência original; o motor de cálculo não mudou. Novas seleções genéricas usam `user_estimate`, sem apresentar uma ficha de modelo como característica exata de toda a categoria.

Os elementos details mantêm campos e memória montados ao recolher. Isso reduz o conteúdo visível sem eliminar parâmetros do estado, do recálculo, do salvamento ou do relatório. A potência total por equipamento é lida da memória Python. Rendimento mecânico indispensável permanece na área essencial; pendências de FP/fases/tensão são identificadas junto à abertura dos parâmetros avançados.

## Registro técnico e preservação histórica (21/10/2026)

`app/technical.py` centraliza metadados de documentos e candidatas por estado, regras matemáticas, testes associados e revisão das regras normativas. O hash SHA-256 do conteúdo identifica uma revisão. Salvar/recalcular um projeto registra uma cópia em `technical_revisions` e a versão no projeto; o histórico de cálculo inclui contexto técnico e proveniência de cada carga. A migração 0002 apenas adiciona a tabela.

`GET /projects/{id}/revalidation` compara a revisão e versão do motor, devolvendo resultado anterior e prévia atual, sem modificar nada. A comparação é conservadora: qualquer mudança do registro sinaliza revisão; ainda não analisa impacto individual por cláusula. `POST /projects/{id}/recalculate?expected_version=N` exige a versão do projeto e cria histórico; não troca as potências das cargas pelo catálogo novo. Relatórios identificam explicitamente a prévia atual e incluem o cálculo registrado anteriormente.

`technical_admin.py stage arquivo.json` é uma importação local de metadados com evidências. Valida formato/tamanho/URL e armazena candidato não publicado, nunca executa fórmulas ou publica regras externas. A publicação continua exigindo revisão do código, testes independentes e nova versão. Não há endpoints administrativos de escrita nem coletor HTTP automático. O comando `backup origem.db destino.db` utiliza a API de backup SQLite, verifica integridade e recusa sobrescrita. Guarde cópias fora da máquina antes de implantar.

A API de projetos continua sem autenticação e destina-se ao desenvolvimento local; não está pronta para exposição pública. Revisões são imutáveis pela aplicação, não constituem um armazenamento inviolável contra alterações diretas no banco.

## Requisitos de entrada e exportação

`app/validation.py` publica dependências de campos por finalidade e diagnósticos estruturados. Não confundir um rascunho com campos desconhecidos com dados inválidos: dimensões ausentes não bloqueiam a soma de cargas; valores incompatíveis são rejeitados ou explicitamente diagnosticados. `Field.tsx` consome estes metadados sem fórmulas elétricas duplicadas.

`app/reports/pdf.py` consome um snapshot recalculado no Python; a rota confere versão de motor, registro e hash de entradas. Para projetos salvos, confere também versão e conteúdo. O renderizador é independente de FastAPI/banco, incorpora fonte licenciada e permite trocar o formato documental sem alterar o motor. Consultar `forms-and-pdf.md` para limites e testes.

## Organização e proteção — 0.3.0

`projects.py` concentra leitura de snapshots e gravação histórica; `main.py` mantém os endpoints. `RequestBoundary` limita bytes reais antes do parser e adiciona cabeçalhos defensivos; CORS valida origens explícitas. Não substituem autenticação. Detalhes em `security.md`.

`ProjectWorkspace` separa ações de listagem/recuperação; `ResultsPanel` apresenta os mesmos resultados nos níveis simples e técnico, sem trocar fórmulas ou requisitos. Formatação numérica compartilhada em `lib/format.ts`. A ação sticky de ambientes fica no fluxo da página e não cria uma sobreposição fixa sobre campos.

Após o primeiro salvamento, a edição pode ser salva automaticamente em 1,5 segundo. A tentativa utiliza a versão otimista, preserva edições durante a requisição e não repete a mesma falha sem nova alteração. Não há persistência local de rascunhos ainda não enviados; fechar antes da confirmação pode perder dados.

## Projetos e seleção contextual — 0.4.0

A listagem REST aceita `limit` (1–100), `offset`, `q` (nome) e `sort=recent|name`, mantendo o retorno anterior quando esses filtros são omitidos. A ordem inclui ID como desempate. O frontend busca três recentes; a consulta completa busca 21 registros, apresenta 20 e utiliza o último apenas para indicar a próxima página. Não carrega centenas de cards.

Lista e catálogo carregam independentemente. Um contador de sequência protege a lista contra respostas anteriores ao último salvamento/filtro. Gravações têm trava local e continuam usando a versão otimista do servidor. Renomear pausa o autosave: exige salvar explicitamente ou criar outro registro com Salvar como novo.

`equipment_relevance.py` centraliza recomendações por tipo, categoria e exceções de equipamento. São metadados de UX, sem restrições de instalação nem influência no agrupamento de demanda. O frontend mantém a busca geral como alternativa. Alterar tipo de ambiente não apaga cargas.

`SectionNavigation` controla Início, Novo projeto, Projetos salvos, Lixeira e retorno ao projeto em edição, com aria-current. Memória fica em ResultsPanel, dentro do projeto. Correções de avisos continuam focando IDs de campo. `DemandSummary` lê valor/estado/motivo da API; não possui um estado fixo de validação. Falhas de salvamento também transportam diagnósticos com alvo de campo.

## Interface e recuperação — 0.5.0

ProjectActions centraliza ações e usa disclosure nativo. ProjectWorkspace usa dialog modal nativo para biblioteca/lixeira, com carregamento e resposta associados ao filtro atual. ResultsPanel separa resumo, memória e pendências; estado e origem substituem avisos genéricos de edição/estimativa.

Project.deleted_at é um metadado de saída; projectInputs o remove antes de enviar entradas. DELETE permanent exige exclusão lógica prévia/versão atual e usa cascade do histórico na mesma transação. Acesso segue local, sem autorização por usuário. Parâmetros documentais opcionais são mantidos nos snapshots persistidos. Exportações PDF/JSON são resumos gerais, separados da memória completa e das fórmulas elétricas.

## Continuidade permanente

App 0.6.1 / motor 0.4.3 (menções 0.2.0 acima descrevem revisão histórica). Documentação principal de sessões em PROJECT_MEMORY/CURRENT_STATE/SESSION_HISTORY; scripts stdlib coletam Git e criam snapshots com SQLite backup/restore isolado. Procedimento e recuperação em [continuity.md](continuity.md). Nenhuma migração nova para essa infraestrutura.

## Horários públicos

America/Sao_Paulo é o fuso de apresentação da aplicação, exportações e timestamps de projetos/histórico/revisões na API. Conversão Python em projects.brasilia_time considera timestamps SQLite legados sem tzinfo como UTC; os horários persistidos e nomes técnicos de checkpoints continuam em UTC. Frontend centraliza formatDate em lib/format.ts com fuso explícito, independente do navegador. Não há migração/regravação dos instantes existentes.

## Espaço de trabalho — 0.6.0

page.tsx mantém o estado da edição acima das apresentações Início/projeto. WorkspaceHome oferece as três entradas iniciais; alternar para Início não recria entradas nem salva um novo projeto. useCalculation recebe enabled e não solicita cálculos enquanto o editor está fechado; ao voltar, debounce/cancelamento e identificação de respostas permanecem ativos. ProjectActions fica no aside somente durante edição, sem duplicar Novo projeto. SectionNavigation substitui os antigos atalhos globais por navegação do espaço de trabalho. WorkspaceIcon usa SVG local.

ProjectWorkspace aceita biblioteca controlada pela tela inicial/menu, conservando pesquisa/paginação e modos separados de ativos/lixeira. Abrir projeto retorna sucesso/falha; cancelamento ou erro mantém o diálogo aberto e a edição intacta. Feedback de operações aparece no diálogo; recentes consultam sempre projetos ativos, independentemente do filtro da lixeira. Navegação bloqueia operações durante gravações/exportação, e a confirmação de exclusão do projeto atual explicita alterações não salvas quando existirem.

Falhas de inicialização têm nova tentativa explícita que recarrega serviços, catálogo e recentes sem remontar o estado do projeto. api.ts conserva HTTP/status/avisos e traduz falhas de rede, preservando cancelamento. Versões de aplicação/API/pacotes 0.6.0; motor 0.4.3 e banco/migrações inalterados.

Playwright usa 3010/8010 e NEXT_PUBLIC_API_URL próprio, CORS local restrito, banco temporário e NEXT_DIST_DIR=.next/e2e. A configuração normal permanece .next e 3000/8000. Tipos gerados para os dois diretórios constam no tsconfig conforme configuração do Next. Não há concorrência de testes com banco/serviços reais.

## Polimento do espaço de trabalho — 0.6.1

Recentes e sua consulta inicial foram removidos. page.tsx coordena as telas home/project/library/trash, mantendo entradas e projeto salvo acima das apresentações. SectionNavigation não depende de um diálogo modal: biblioteca/lixeira ocupam o main e o aside continua navegável. Repetir uma opção dá foco ao título; o projeto em edição mostra nome/estado no menu.

ProjectWorkspace é uma seção com título acessível, busca/ordenação/paginação e estados de carregamento/erro/vazio. Consulta somente ao abrir; revision invalida a lista após mutações, sem buscar recentes em segundo plano. O identificador da resposta inclui seção, filtros e revisão; respostas antigas e itens de outro filtro não se tornam acionáveis. Remover o último item de uma página retorna à página anterior. A chave por seção reinicia os filtros ao alternar biblioteca/lixeira, sem interferir nas entradas do projeto.

ProjectActions bloqueia salvar/exportações/ações secundárias durante operações; menu não abre quando bloqueado, fecha ao iniciar uma ação e com Escape, devolvendo foco ao resumo. O menu do aside usa expansão no fluxo, evitando corte de opções por overflow. Conferência de referências agora participa do estado ocupado. Mensagens identificam operações pendentes e distinguem um snapshot salvo de alterações feitas durante o salvamento. Alvos de toque, hover desabilitado, títulos longos, ícones, foco e movimento reduzido foram revistos; cálculo e persistência inalterados.

## Revisão 0.7.0 — energia, formulários e manutenção

`calculations/energy.py` resolve consumo mensal a partir de horários explícitos ou etiqueta/medição por unidade, sem inferir potência elétrica. `engine.py` agrega energia por ambiente/categoria/projeto, mantém cobertura independente de W/VA e aplica tarifa opcional somente ao custo. Novos parâmetros opcionais nos snapshots JSON não exigem migração; históricos não são regravados em lote. Tarifa participa do digest e da chave do hook, mantendo cancelamento e bloqueio de exportações antigas.

`EnergyFields` isola os campos opcionais de uso; EquipmentEditor mantém referência/identidade/potência e parâmetros condicionais. Dados informativos sem operação útil deixam de ser inputs, mas permanecem legíveis para projetos antigos. `Field` deriva erros sem mutar variáveis capturadas. Efeitos de navegação/carga preservam foco/rascunhos; sincronização da entrada para operações assíncronas ocorre em layout effect. Catálogo e matemática continuam únicos; frontend não replica fórmulas elétricas.

ESLint 10/TypeScript/react-hooks, Prettier e Ruff local padronizam revisão. Next docs locais consultadas para headers/lint. Configuração Next de lint foi substituída por regras TS/hooks diretas para evitar uma cadeia transitiva vulnerável; não há lint específico do plugin Next nesta configuração. Regras matemáticas e memória existentes são preservadas, com motor 0.5.0 para energia. Migrações históricas conservadas byte a byte e excluídas da formatação automática. Plano de segurança e limites reais em security.md; decisões campo a campo em audit.md.

## Cobertura normativa — 0.8.0

RULES permanece a fonte única do estado das regras e da pesquisa. Dataclass ResearchEvidence registra acesso a metadados oficiais ou indexação, sem mecanismo para executar expressões pesquisadas. Schemas ResearchEvidence/NormativeCapability/TechnicalRules tipam o contrato. technical.normative_capabilities projeta a cobertura por utility/state; engine a inclui na resposta e o endpoint técnico a expõe com o mesmo registry_version. Registro versionado/snapshots guardam as pesquisas como evidência; não se publica regra apenas por preencher metadados.

validation.notifications passa a representar dados/alertas do projeto; limitações normativas ficam em normative_capabilities. NormativeAvailability apresenta essas limitações em details informativo, com fontes sanitizadas e distinção entre indexação/metadados e leitura integral. Fallback de apresentação aceita resultados legados sem o campo novo. Em stale, detalhes de contexto anterior são substituídos por atualização e fontes são recolhidas; testes reabrem o contexto novo antes de conferir links. DemandSummary só entra no resumo principal com valor calculado/estimado. C passa a Dados do projeto a revisar. Memória, debounce/cancelamento/exportação e histórico seguem existentes.


## Procedimentos residenciais — 0.9.0 / motor 0.6.0

calculations/residential.py concentra as novas funções puras Decimal; engine integra por seleção explícita do escopo residencial, sem alterar as bases instalada/aparente/energia. RULES registra procedimentos, limites, cláusulas e testes conferidos. ResearchEvidence distingue institucional/official_full_text de metadata/index. Disponibilidade de implementação não equivale à completude das entradas: coverage pode available=true e o resultado retornar null/pending por dados/escopo faltantes.

NormativeEnvironment tipa as parcelas individuais no contrato gerado. Validation emite requisitos condicionais e alertas de quantidade do projeto; frontend apenas apresenta esses resultados/formatos, sem replicar fórmulas. Relatórios usam a mesma saída. Hash de registro e versão do motor permitem distinguir resultados novos; nenhuma migração ou regravação de históricos existentes. Escopo normativo completo e demanda continuam sem certificação; detalhes canônicos em standards/calculations.


## Exportação unificada — 0.10.0

reports/summary.py prepara o documento público a partir de ProjectInput/CalculationResult já normalizados, sem fórmulas ou parâmetros presumidos. reports/pdf.py apresenta os resultados e main exporta o mesmo preparo como JSON 1.1 legível. prepare_report centraliza recálculo/guards de snapshot e versão salva; nenhum endpoint de relatório grava projeto/histórico. Contrato de entrada PDFExportInput preservado e reutilizado para JSON. O frontend requestReport baixa arquivos de ambos os formatos com um único controle de exportação, sem manter outro gerador de resumo.

Motor permanece 0.6.0 e normas intactas: a versão 0.10.0 altera documento/API de relatório/apresentação, não matemática. Dados manuais/copias de ambientes são consumidos como instâncias independentes pelos resultados existentes. Fonte canônica dos campos/alcance em forms-and-pdf.md.
# Persistência e acesso — acréscimos 0.11.0

`app/auth.py` concentra sessões opacas/Argon2/HTTPS/CSRF; `accounts.py` é administração local. `get_session` marca escopo de proprietário, aplicado às consultas ORM de ProjectRow; novas linhas recebem o proprietário. As rotas que consultam histórico/relatório continuam exigindo primeiro o projeto acessível. Identidade e sessões na migração0004; owner_id nulo preserva os projetos locais anteriores. Compartilhamento entre usuários não está implementado.

`catalog_store.py` persiste revisões imutáveis e ponteiro ativo na migração0005. Inicialização publica o catálogo de código somente se ainda não houver revisão; depois carrega a publicada, atualizando a lista compartilhada usada por endpoints e hashes técnicos. `catalog_admin.py publish-reviewed --file` é publicação administrativa explícita, com modelos/IDs validados e sem alterar snapshots dos projetos. Reiniciar todos os workers após publicar para que tenham a mesma revisão. Não há atualização silenciosa a partir de fabricante, cadastro de projeto ou edição de potência.

Contratos continuam gerados por types:sync; wrappers Node escolhem Python por plataforma e aceitam ELETROPROJETO_PYTHON para QA isolado. E2E gera banco no diretório temporário do sistema, não em caminho Linux fixo. Testes PostgreSQL usam schemas QA únicos; migrações são verificadas separadamente no banco QA. O banco de produção SQLite não é selecionado por essas rotinas.
