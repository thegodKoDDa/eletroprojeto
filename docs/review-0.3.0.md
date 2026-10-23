# Entrega incremental 0.3.0 — 21/10/2026

## Alterações verificáveis

- Área de trabalho: ações de duplicar/excluir em cada projeto, data de atualização, lista de excluídos e restauração. Ações capturam ID/versão, não usam a seleção de outro projeto. Duplicação não troca o formulário em edição.
- Exclusão agora é lógica: `deleted_at`, índice e migração 0003. GET ativo, edição, relatório e histórico ficam indisponíveis enquanto excluído. Payload e histórico são recuperados sem recompor cálculos antigos. Versão desatualizada devolve 409.
- Barra sticky de ambientes no fluxo da página e foco automático no novo nome, sem remontar os inputs anteriores.
- Salvamento automático após primeiro salvamento manual, debounce 1,5 s, opção de desativação, proteção de versão/edições em voo e sem repetir indefinidamente a mesma falha. Não é recuperação local de rascunho: alterações não enviadas ainda podem se perder ao fechar.
- Resultados com apresentações simples/técnica da mesma resposta Python. Fórmulas continuam acessíveis no modo simples; pendências não são ocultadas pela troca de apresentação.
- Refatoração: `ProjectWorkspace`, `ResultsPanel`, formatação compartilhada e serviços de snapshots/histórico em `app/projects.py`. Nenhuma dependência adicionada/removida. Não foi feita uma refatoração integral de todos os módulos.
- Correção de indicação: um ambiente só mostra subtotal incompleto quando contém uma carga de potência desconhecida; a pendência de outro ambiente não o rotula indevidamente.
- Proteção HTTP de 4 MiB sobre bytes reais, inclusive chunks sem Content-Length; CORS com origens explícitas e validação da configuração; respostas sem cache e nosniff. Proteções e limites em `security.md`.
- README/arquitetura/roadmap atualizados; workflow de qualidade acrescentado. Versão aplicação/API/frontend 0.2.0 → 0.3.0; motor mantido em 0.4.0 porque as fórmulas não mudaram.

## Banco e contratos

Backup SQLite íntegro criado antes da migração em `/tmp/eletroprojeto-before-0003.db`. Comparação SQL das colunas originais antes/depois confirmou preservação de 1 projeto, 1 histórico e 2 revisões técnicas existentes. `PRAGMA integrity_check`: ok. Migração aplicada e `alembic check` sem alterações pendentes.

Rotas: `GET /api/v1/projects?archived=true`, `POST /api/v1/projects/{id}/restore?expected_version=N`; DELETE aceita expected_version opcional para compatibilidade, enviado obrigatoriamente pela interface. POST duplicate já existia e agora é usado diretamente na listagem. OpenAPI e TypeScript regenerados pela ferramenta existente. A fixture de resultado frontend foi normalizada pelo schema Pydantic para incluir os metadados obrigatórios da memória e a versão atual do motor; os valores matemáticos da fixture foram preservados.

## Cálculos e referências

Suíte existente reexecutada: Decimal, somas independentes, W/kW, VA/kVA, corrente monofásica/trifásica equilibrada, cv/HP/rendimento, capacidade térmica, categorias e edição de potência/quantidade/tensão/FP. Exemplos incluem 2 × 7.500 = 15.000 W, alteração para 2 × 5.500 = 11.000 W e correntes com tensão alterada mantendo W.

Nenhuma fórmula normativa nova, coeficiente ou referência externa foi introduzido ou declarado validado nesta entrega. A suíte matemática não valida automaticamente aplicação normativa. NBR 5410 e tabelas de demanda das distribuidoras continuam com as limitações de `standards.md`; circuitos, cabos e padrão de entrada não foram implementados. Não houve nova consulta de fontes oficiais nesta fase.

## Verificações executadas

- pytest: 99 aprovados e 11 subtestes aprovados.
- Vitest/RTL: 39 aprovados. Incluem listagem/recuperação, foco ao adicionar ambiente, apresentação simples/técnica, autosave agrupado e falha sem loop, além das regressões anteriores de recálculo/manual/aviso/PDF snapshot.
- OpenAPI/TypeScript: geração e typecheck aprovados.
- compileall Python, integridade SQLite, migração e Alembic check aprovados.
- pip check: dependências instaladas consistentes. pip-audit não instalado.
- npm audit offline: relatório local com zero entradas; não equivale a auditoria atualizada. Consulta online falhou com EAI_AGAIN para registry.npmjs.org.
- Build Webpack tentado: falha ao interpretar saída TypeScript --showConfig neste ambiente, sem build aprovado.
- Playwright tentado: API não conseguiu abrir 127.0.0.1:8000; nenhum fluxo real de navegador executado.
- Next dev tentado: listen EPERM na porta 3000. curl também bloqueado para sockets. Não há confirmação de localhost ativo.
- Lint tentado: script ausente; ESLint não configurado. CI foi escrito, mas não executado em provedor remoto.

## Pendências desta fase

Validação visual real de desktop/mobile, execução completa do build/Playwright, lint, auditoria atualizada de vulnerabilidades, revisão integral restante do código, recuperação local de rascunhos, autenticação/autorização e rate limiting/observabilidade operacional. O refinamento visual foi localizado: hierarquia das ações, apresentação de detalhes e acessibilidade; não foi verificada uma repaginação ampla em navegador.

Não declarar a fase abrangente concluída: estes são incrementos testados sobre a implementação existente, com limites de ambiente e de validação normativa explícitos.
