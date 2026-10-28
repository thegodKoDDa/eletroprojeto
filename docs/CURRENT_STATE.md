# Estado atual — EletroProjeto0.25.0 / motor0.13.0

Última sessão: **28/10/2026**. Branch **main**; entrada `6b55071`. Commit final e ponto verificado em Git e `.checkpoints/latest.json`. Escopo oficial: **estimativa e análise de consumo energético residencial**, para imóveis planejados, em construção, prontos ou em reforma.

## Entregue

- Engine reutiliza cálculos existentes de potência, energia, custos, agregações e ranking, sem executar normas/demanda/circuitos/entrada/geometria. Salvamento/exportação usam revisão própria do motor, sem registro normativo.
- Tipo/estágio do imóvel, localização contextual e distribuidora manual opcional. Município opcional; kWh independem de distribuidora/tarifa. Valores manuais válidos prevalecem.
- 03 Resultados e Estimativas: potência, energia diária média/mensal/anual, custos, distribuições e ranking visual. Memória secundária, avisos úteis e comparação explícita da edição com a versão salva, calculada em Python.
- API/Pyodide alinhados; rotas de execução normativa removidas. PDF/JSON2.0 de consumo, parâmetros/fórmulas/fontes/premissas, sem fornecimento. Contratos gerados via types:sync.
- UI de instalações removida. Pesquisa/acervo e módulos matemáticos históricos independentes preservados; documentação anterior arquivada em docs/history. Leitura de revisões históricas continua disponível, sem executar normas.

## Preservação

Checkpoint inicial **20261028T204650342615Z** restaurado antes das mudanças. **12 tabelas reais comparadas integralmente e idênticas**;14projetos ativos/0lixeira,42históricos,12revisões,2.082documentos/51.324páginas/3.788fontes. Os14projetos reais abriram/validaram/recalcularam somente em memória, sem gravação nem alteração de valores manuais. Campos normativos antigos são metadados opacos preservados em snapshots; novas propriedades são aditivas, sem migração SQL ou atualização em massa. Alembic0007, sem migração pendente. Catálogo/originais/checkpoints preservados, sem reset, exclusão de dados ou dependência nova.

## Verificações

**588pytest +85subtestes,122frontend aprovados.** Typecheck, ESLint, Ruff/checkformat e contratos oficiais aprovados. Build Webpack nativo aprovado.40cenários E2E exercitados:27passaram na execução ampla; após correções,16/17afetados passaram e os5últimos (incluindo profissional e comparação nos3perfis) passaram. Isso cobre os40cenários, com repetições proporcionais. Testes de acessibilidade/teclado e320/390/768/1440px; capturas fictícias inspecionadas. Build estático Pyodide aprovado; bundle reduzido a24arquivos, sem módulos normativos. Teste isolado do bundle aprovado para calcular, salvar, comparar e exportar PDF sem app.technical/standards disponíveis. Fechamento final conferido pela saída da rotina desta sessão.

Regressões detectadas/corrigidas: identificador de conferência perdido; aviso de espera acrescentava16px no resultado; memória com números longos ultrapassava320px; fixtures e contrato da nova unidade diária ajustados. Testes antigos exclusivos de funcionalidades retiradas foram substituídos por isolamento/compatibilidade/consumo; funções puras de pesquisa continuam testadas.

## Limites e próxima ação

Não validados novamente: Windows/macOS/ARM, Docker, PostgreSQL, HTTPS de duas contas, carga/pentest, leitor real ou inspeção física. Sem tarifa automática ou inferência de ciclos. Comparador usa edição versus versão salva; relatórios exportam cenário atual. Release ZIP permanece0.24.1. A reformulação foi sincronizada em405b507 com[skip ci]; o pedido posterior de corrigir a entrega retoma o fluxo normal de publicação Pages, cujo resultado é conferido nesta tarefa. Acervo/configuração privada permanecem locais e fora do ZIP do checkpoint; buffers externos e localStorage não entram no backup SQLite. Sem cópia externa.

Nenhuma implementação interrompida. Próximo passo: usar a nova estimativa e atender ao próximo pedido; ampliações em [roadmap](roadmap.md), limites em [KNOWN_ISSUES](KNOWN_ISSUES.md). Não retomar pendências normativas como bloqueios de consumo.

Retomar: **RETOMAR ELETROPROJETO** ou `python3 scripts/continuity.py retomar`. Dependências existentes backend/.venv e frontend/node_modules; API8000 e interface3000 iniciados no pedido posterior, com HTTP conferido antes da entrega. Iniciar: `python3 scripts/start_local.py --no-browser`; confirmar HTTP antes de anunciar localhost, conforme [setup](setup.md). Encerrar: `python3 scripts/continuity.py encerrar --sync`; verificar recuperação: `python3 scripts/continuity.py verificar`. Detalhes em [continuity](continuity.md).

## Correção da entrega — 28/10/2026

Revertidos os efeitos documentais específicos das duas ordens de encerramento acidentais(1d2c53e/6b55071), preservando a reformulação0.25.0 e o sistema de continuidade que já existia antes. Não interpretar fim de implementação como ordem de encerrar serviços. GitHub e localhost devem acompanhar a entrega autorizada; sincronização/publicação atuais são conferidas na saída da tarefa.
