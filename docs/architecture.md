# Arquitetura — EletroProjeto 0.19.0

Este documento descreve a implementação atual. A evolução e as verificações anteriores estão em SESSION_HISTORY e CHANGELOG; regras/fontes em calculations e standards. Estado operacional e limitações em CURRENT_STATE.

## Camadas e contratos

Monorepositório com Next.js App Router, React, TypeScript e Tailwind no frontend; FastAPI, Pydantic 2, SQLAlchemy 2 e Alembic no backend. Integração REST JSON sob `/api/v1`. `backend/export_openapi.py` exporta o contrato; `npm run types:sync` gera `backend/openapi.json` e `frontend/src/lib/api.generated.ts`. O contrato gerado não é editado manualmente. Sessão, login, projeto recalculado e prévia de revalidação possuem respostas tipadas.

`backend/app/calculations` concentra a matemática com Decimal/contexto de 40 dígitos e unidades explícitas. Funções matemáticas não importam FastAPI, Pydantic ou ORM. O orquestrador engine agrega cálculo, diagnósticos e contexto técnico a partir dos dados validados; não busca normas, equipamentos ou coeficientes pela rede. Nenhuma fórmula elétrica é replicada no frontend.

`schemas.py` define limites e contratos. `validation.py` descreve requisitos condicionais e diagnósticos usados pelo motor e pelos formulários. `technical.py` publica documentos, escopos, procedimentos e digest do registro técnico. `catalog.py` contém as sugestões iniciais; `catalog_store.py` mantém revisões persistentes. CLI administrativas não são endpoints públicos.

## Frontend e requisições

`page.tsx` coordena edição, salvamento, recuperação, conflitos e navegação. `use-workspace-resources.ts` carrega saúde, requisitos, estados, distribuidoras e catálogo independentemente, com cancelamento e nova tentativa sem substituir a edição. Falha em um recurso não bloqueia a recuperação dos demais.

`components/projects` contém biblioteca/lixeira, início, acesso, biblioteca técnica, estudo de circuitos e painel de revalidação. `components/equipment` concentra o cadastro e consumo; `components/calculations` apresenta resultados simples/técnicos, demanda e pendências. Componentes de layout/UI mantêm navegação, ações e requisitos acessíveis. Sidebar e três cartões do início preservados. O editor tem apenas três etapas principais: Projeto, Ambientes e Conferência. Tarifa fica visível; dados complementares e medidas/pontos dos ambientes ficam em disclosures. Consumo mensal é o primeiro grupo compacto de equipamento, seguido de configurações e referência, sem deslocar os cabeçalhos ao abrir.

ResultsPanel prioriza consumo/custo da API, permite completar dados de uso com foco direto no primeiro aparelho pendente e consultar consumo por aparelho. Potência, memória, VA/corrente/previsões e cobertura ficam em detalhes recolhidos. DemandReview, CircuitStudy, BathroomStudy e TerritoryStudy continuam preservados após a conferência, dentro de Estudos técnicos e respectivos subgrupos, fechados inicialmente inclusive para projetos salvos. Nenhuma fórmula, horário, tarifa, FP ou dado normativo é inferido pela interface.

Padrões de interface em `components/ui`: PageHeading centraliza título/descrição/foco das páginas; SectionHeading identifica seções e leitores; Feedback padroniza informação/sucesso/aviso/erro com papéis acessíveis; Pagination compartilha navegação, bloqueio durante carregamento e contador. CSS usa tokens para controles comuns de40px e compactos de32px, bordas, cores e mensagens de campo. Início mantém sua apresentação de três cartões. Não criar variantes locais de botão/paginação/feedback para a mesma operação.

Erros localizados de PDF/JSON seguem o mesmo caminho dos erros de salvamento, vinculados ao snapshot da operação; Corrigir informação abre detalhes e foca o controle. Completar consumo usa os IDs pendentes devolvidos pelo motor e as entradas atuais para escolher o campo faltante, sem calcular energia no navegador. Biblioteca permite repetir leitura/fontes mantendo documento e filtros; requisições antigas são canceladas/rejeitadas.

`lib/api.ts` centraliza credenciais, CSRF, erros HTTP e exportações. Aceita todas as formas de HeadersInit. Erros estruturados de formulários e relatórios compartilham a mesma interpretação; 401 remoto dispara bloqueio de acesso. Não armazenar tokens em localStorage.

`use-calculation.ts` identifica entradas por escopo/assinatura, espera 400ms, cancela requisições anteriores e ignora respostas obsoletas. Circuitos, proteções e entrada participam da assinatura. O último snapshot permanece montado para preservar memória/disclosures, mas os valores ficam ocultos enquanto desatualizados; resultado atual e exportação ficam indisponíveis até a resposta correspondente. Totais de equipamentos/ambientes também aguardam a resposta atual. Abrir outro projeto muda o escopo e impede exibir números do anterior. Decimal é transmitido como string; Number é usado somente em apresentação e validação de formulários.

## Projetos e persistência

Banco padrão em `backend/eletroprojeto.db`; DATABASE_URL absoluto seleciona outra instalação. SQLite tem foreign keys ativas; PostgreSQL utiliza psycopg. Migrações 0001–0007 e testes QA dos dois bancos são preservados. Não copiar arquivo SQLite para substituir uma migração de dados PostgreSQL.

Projetos armazenam UUID, proprietário, versão otimista, timestamps, exclusão lógica, revisão técnica e snapshot JSON completo. Alterações criam histórico com entradas/resultados na mesma transação. `projects.py` centraliza leitura, apresentação, validação, comparação normalizada, registro e consulta do último histórico. A ordem por versão do projeto evita escolher histórico antigo quando timestamps coincidem.

Listas `/projects/summaries` retornam somente metadados e têm busca/paginação/ordenação; abrir busca o payload completo. Endpoints legados de lista completa permanecem disponíveis. PUT exige versão; entrada idêntica na revisão atual não cria gravação/histórico redundante. POST aceita Idempotency-Key UUID: repetição idêntica converge ao mesmo projeto, entrada diferente retorna 409, sem expor registro de outra conta. A chave não substitui autenticação.

Excluir move para a lixeira. Restaurar exige versão atual. Exclusão definitiva exige exclusão lógica anterior e remove somente o projeto e seu histórico em transação. Duplicação renova o ID do projeto; ambientes/cargas pertencem ao snapshot da nova instância. Duplicar ambiente renova IDs dos ambientes/cargas, mantendo dados manuais e referências independentes.

Remover uma carga/ambiente pela interface limpa suas associações aos circuitos na edição atual. Histórico e catálogo não são alterados. Registros antigos com associações ausentes continuam legíveis e possuem reparo explícito no estudo de circuitos. A interface impede uma nova associação simultânea de carga a dois circuitos; o motor também detecta duplicação em clientes externos.

## Salvamento e rascunhos

Autosave começa depois do primeiro salvamento manual, com debounce de 1,5s. Renomeação e conflito pausam o processo. Falha não é exibida como sucesso e o mesmo snapshot não é repetido indefinidamente. Edições feitas durante uma gravação permanecem locais para o próximo salvamento.

Rascunhos em localStorage têm escopo de conta/aba/slot, agrupamento de escrita em 250ms e flush ao ocultar/sair/desmontar. O identificador de criação é protegido antes do POST. Recuperar não envia dados automaticamente; conflitos permitem preservar uma cópia ou carregar o servidor mantendo o rascunho. Esses mecanismos não recuperam dados após limpar o navegador nem garantem flush em término abrupto sem eventos. Backup do servidor não captura edições não enviadas.

## Referências, revalidação e relatórios

Uma revisão técnica é identificada por SHA-256 e persistida em technical_revisions. Histórico guarda entradas/resultados originais. Alterar catálogo/regras não modifica automaticamente os valores manuais ou os projetos antigos.

GET `/projects/{id}/revalidation` devolve ID/versão do projeto, revisões, motor registrado, resultado histórico original e prévia atual. É consulta sem gravação. O painel exige edição salva para comparar e descarta a apresentação se a edição/versão mudar. POST `/recalculate?expected_version=N` registra explicitamente nova versão e histórico, preservando entradas manuais. A detecção é conservadora por motor/registro, ainda sem análise seletiva por cláusula.

PDF principal e JSON de resumo 1.4 são gerados pelo backend. Relatórios exigem correspondência de digest de entradas, motor, registro e, quando vinculado, versão/conteúdo do projeto salvo. O digest inclui circuitos/proteções e entrada. O backend recalcula o snapshot; não aceita números elétricos fornecidos pelo navegador. JSON de relatório não é backup completo. Fontes/condições/pendências acompanham os estudos; não há aprovação de instalação ou ligação.

Apresentação pública de horários em America/Sao_Paulo; armazenamento e nomes de checkpoints em UTC. Timestamp SQLite legado sem timezone é interpretado como UTC, sem regravar os instantes.

## Biblioteca técnica e acesso

`knowledge.py` oferece consulta paginada de documentos, páginas, fontes e originais. Busca textual literal normalizada, com escape de curingas, portável entre SQLite/PostgreSQL; ainda sem índice especializado de busca em texto. A ingestão/OCR é offline pelas CLI, nunca habilita regra normativa automaticamente. Método, nota e confiança de extração são separados de validação técnica.

Originais deduplicados em `references/library/objects/<sha256>`, fora de Git/ZIP de código; não são cache. A API exige hash conhecido, tipo permitido, arquivo real e ausência de symlink, com CSP sandbox/nosniff. Markdown é renderizado como nós React, sem HTML executável; SVG como imagem. Auditoria/tombstones preservam descartes autorizados e impedem reimportação histórica indevida.

Modo local é somente loopback/projetos sem proprietário; modo remoto exige HTTPS, sessão revogável, origem explícita e CSRF em mutações. Consultas de projeto são isoladas por proprietário, incluindo relatórios, histórico e revalidação. Contas são provisionadas administrativamente. Detalhes e limites em security.md; não publicar modo local por proxy.

## Verificação e continuidade

Vitest executa testes `.test.ts` e `.test.tsx`. Playwright usa portas 3010/8010, banco/objetos QA e build separado `.next/e2e`; HTTPS de duas contas tem configuração isolada. Não rodar build e E2E em paralelo. Fixtures PostgreSQL usam schemas descartáveis, sem tocar o banco real. CI inclui contratos, código, migrações, testes, build e auditorias.

Continuidade, snapshots SQLite/Git, restauração isolada e manutenção autorizada estão em continuity.md. `scripts/repository.py` limita sincronização à main limpa no GitHub privado autorizado, sem merge/force-push; falha de rede não impede o checkpoint local. `continuity.py` compartilha backups SQLite idênticos por hardlink quando suportado, sem mudar o formato/restauração ou apagar pontos. `maintenance.py` concentra doctor, clean e compact. `.checkpoints/latest.json` aponta para o último checkpoint concluído. Binários da biblioteca precisam ser preservados separadamente do ZIP; não presumir recuperação de originais apenas pelo banco. Publicação, impressão física e backup externo continuam fora desta entrega local.

## Estudos condicionais e território — 0.19.0

`energisa_special.py` implementa somente os procedimentos conferidos d6/d7/centrais; parâmetros e fontes são valores opcionais dos schemas de classificação e integram o digest do inventário. `bathroom_geometry.py` trabalha com envelopes medidos do componente em um arranjo restrito de chuveiro. Os módulos puros não importam API/validação/ORM. Dados novos são campos aditivos dos snapshots JSON; não exigem migração nem alteram projetos antigos. Memória e exportadores consomem resultados do motor, sem recalcular fórmulas.

`GET /api/v1/locations/territory?latitude=...&longitude=...` lê somente coleta local validada SIRGAS2000. `scripts/territory.py` coleta fontes oficiais em diretório local imutável ignorado; trata erroArcGIS emHTTP200, contagem/truncamento, identidades, anéis e referencial. A leitura confere hash, mantém índice em memória e não faz rede/gravação durante consulta. Sem arquivo retorna pending; com feições retorna awaiting_technical_validation e candidatos com atos/datas/fronteiras, nunca ID de distribuidora ou confirmação automática. A UI usa requisição explícita com cancelamento, esconde dados anteriores ao editar coordenadas e não salva essas coordenadas no projeto. Banco/acervo/credenciais permanecem locais; originais territoriais também são incluídos no checkpoint local pela rotina existente.
