# Memória duradoura — EletroProjeto

Atualização0.11.0/23-10-2026: Git foi inicializado por autorização explícita do novo pedido; não repetir a afirmação histórica de que status é impossível sem conferir. Migrações0004 identidade/proprietário e0005 catálogo; legado preservado, sem atribuição automática. Modo local continua loopback; modo remoto exige HTTPS e contas/sessões/CSRF, isolando projetos por proprietário. Rascunhos locais recuperáveis e conflitos guiados disponíveis; limites/privacidade em security/forms-and-pdf. Catálogo é publicado em revisões persistidas e carregado na inicialização; editar projeto nunca o publica. PostgreSQL e backend Windows reais testados. CURRENT_STATE registra o trabalho amplo ainda em andamento; não declarar resolvidas as pendências normativas, físicas, hospedagem/CI ou cópia externa sem evidência.

## Produto e história recuperável

Ferramenta de cálculos residenciais: cadastrar residência, ambientes e cargas; obter matemática reproduzível, memória e relatório. Leigos e profissionais usam o mesmo motor; apresentações variam somente em detalhe. Stack: Next.js App Router/React/TypeScript/Tailwind; FastAPI/Pydantic 2/SQLAlchemy 2/Alembic/SQLite, com portabilidade PostgreSQL planejada.

O pedido original relata protótipos HTML/JS MVP 0.1–0.3 e uma Etapa 1 com 36 testes. Esses artefatos/resultados não foram recuperados nem auditados nesta sessão; não assumir equivalência com a implementação atual. O histórico verificável local vem de CHANGELOG e relatórios em docs, não de commits: em 22/10/2026 `.git` estava vazia e somente leitura.

A base anterior 0.1.0 já tinha cargas, catálogo e exportações. Registros de 21–22/10 documentam: 0.2.0 reorganizou PDF, avisos localizados e requisitos por cálculo; 0.3.0 acrescentou exclusão lógica, autosave, componentes separados e proteção HTTP; 0.4.0 corrigiu listagens/renomeação/navegação e sugestões por ambiente; 0.5.0 reorganizou ações, biblioteca/lixeira, resultados e política de valores manuais. Detalhes e evidências nos relatórios `review-*` e CHANGELOG. A continuidade permanente foi introduzida em 22/10/2026, sem alterar matemática ou UI.

## Fluxo real de uso

- A abertura mostra primeiro a tela Início do Espaço de trabalho (0.6.0). Novo projeto, Projetos salvos e Lixeira ficam no aside e na tela inicial. Voltar ao Início mantém o projeto nesta aba, com opção Continuar edição; não há recuperação garantida após fechar/recarregar um rascunho não salvo. Memória de cálculo permanece somente dentro do projeto.
- Novo projeto começa independente; cadastrar nome/localização/concessionária quando necessários para salvar. Ambientes mantêm cargas próprias com IDs estáveis. Adicionar ambiente permanece acessível durante rolagem.
- Escolher equipamento sugerido pelo tipo de ambiente; busca geral permite exceções. O catálogo é somente leitura, separado dos snapshots dos projetos. Não exige marca/modelo.
- Referências são sugestões documentadas. Editar potência/quantidade/tensão e demais parâmetros úteis; potência manual válida diferente da sugestão é aceita. Restaurar referência é ação explícita. A edição não altera catálogo global.
- Salvar cria UUID no primeiro POST e atualiza apenas o atual via PUT/versionamento otimista. Salvar como novo cria cópia independente; Duplicar da biblioteca também cria novo registro. Autosave após primeiro salvamento tem debounce 1,5 s; renomeação pausa até decisão explícita. Rascunhos não enviados NÃO têm recuperação local garantida: aguardar confirmação Salvo antes de fechar.
- Sem Recentes no aside (0.6.1). Projetos salvos e Lixeira são telas principais, com biblioteca paginada e pesquisável; navegação permanece utilizável sem fechar modais. Filtros são reiniciados ao trocar de seção, e o projeto em edição é preservado. Exclusão envia à lixeira; restaurar preserva histórico/ID; exclusão definitiva requer confirmação, versão e projeto previamente excluído, apagando seu histórico.
- Alterações técnicas disparam cálculo Python com debounce 400 ms e cancelamento/ordem das respostas. Resultados anteriores são marcados desatualizados; exportar exige snapshot atual. Metadados administrativos não disparam matemática desnecessária.
- Resultados: A resumo, B memória expansível, C pendências reais. Avisos por operação/local/campo oferecem foco quando solucionáveis; pendência interna não recebe falsa ação de correção. PF/tensão faltantes não impedem soma W.
- PDF é principal, JSON secundário, no menu Mais ações. O PDF recalcula/confere snapshot, identifica estudo preliminar, unidades e estados. PDF/JSON contêm resumo geral, área construída, ambientes com área/perímetro/luz/TUG, categorias e observações, sem fórmulas ou referências, com nome do projeto no arquivo. JSON de exportação não é backup completo; dados e rastreabilidade permanecem na aplicação/banco. Nunca equivale automaticamente a projeto executivo.

## Organização e decisões permanentes

`frontend/src/app/page.tsx` orquestra edição; componentes layout/ProjectActions, projects/ProjectWorkspace, equipment/EquipmentEditor e calculations/ResultsPanel isolam responsabilidades. `frontend/src/lib` concentra cliente, formatação e contratos gerados. Executar types:sync ao alterar schemas; não editar api.generated.ts manualmente.

`backend/app/main.py` expõe REST `/api/v1`, `/docs` e health; schemas valida entradas; projects.py controla histórico; database.py configura banco absoluto e FK; calculations contém funções Decimal; validation.py requisitos por finalidade; technical.py registro/revisões; reports/pdf.py documento A4 independente da UI. Catálogo e regras são dados de código, não cadastro normalizado completo no banco.

Dados reais: `backend/eletroprojeto.db` por padrão, ou DATABASE_URL. Tabelas projects (payload JSON, UUID, versão, deleted_at), calculation_history e technical_revisions; Alembic 0001–0003. Snapshots guardam origem, valores manuais e versão técnica. Atualizações de referência não alteram silenciosamente projetos; há consulta de revalidação e recálculo versionado. PostgreSQL ainda não testado.

Matemática e unidades em [calculations.md](calculations.md); arquitetura em [architecture.md](architecture.md); fontes/validação em [standards.md](standards.md); segurança em [security.md](security.md). São fontes principais, não duplicar seu conteúdo. W, VA, energia, potência mecânica e BTU/h são grandezas distintas. Não inventar FP, rendimento, coeficientes, mapas territoriais ou fatores de demanda. Decimal, condições explícitas e resultados intermediários sem arredondamento prematuro.

## Implementação versus validação

Implementados e testados internamente: somatórios W/kW por carga/ambiente/categoria, VA/kVA com FP, correntes quando suficientes, conversões térmicas/mecânicas, persistência/histórico, valores manuais, exportações e proteção contra respostas antigas. Catálogo documentado na revisão 0.5.0; não universalizar exemplos comerciais.

Previsão residencial quantitativa de iluminação/TUG implementada em escopo limitado e por seleção explícita desde 0.9.0; fontes/limites em standards.md. Demanda NÃO validada: retorna null e motivo. Sem edição/cláusulas/tabelas/exemplos independentes oficiais, não habilitar fatores. Nenhuma distribuidora está plenamente validada para demanda. Seleção por UF não é mapeamento municipal verificado. Circuitos, condutores, proteções e entrada são etapas futuras.

Testes atuais, ambiente e próximo passo em [CURRENT_STATE.md](CURRENT_STATE.md); pendências em [KNOWN_ISSUES.md](KNOWN_ISSUES.md); prioridades em [roadmap.md](roadmap.md); sessões em [SESSION_HISTORY.md](SESSION_HISTORY.md). Procedimento de preservar/retomar/restaurar em [continuity.md](continuity.md).

Horários públicos (interface, API e exportações) usam America/Sao_Paulo, Brasília. Armazenamento e nomes técnicos dos checkpoints permanecem UTC, sem alteração de instantes históricos.

Revisão de 22/10/2026: motor 0.4.3 evita arredondamento intermediário em corrente; catálogo atual VSP-40-W corrigido para 140 W pela fonte Mondial. Projetos/snapshots antigos não são sobrescritos; referência permanece sugestão e edições manuais válidas prevalecem. Categoria personalizada de AC sobrevive à troca automática por capacidade. Edição NBR 5410 2004/correção 2008 identificada no catálogo, texto/cláusulas ainda pendentes. Ver calculations/standards para evidências e CURRENT_STATE para testes.

Preferência permanente de execução (22/10/2026): usuário autoriza todos os testes e verificações de backend/frontend/API/E2E/build/contratos/banco, sincronizações, migrações e reinicializações necessárias às tarefas, sem confirmações repetidas. Agrupar rotinas e usar permissões persistentes delimitadas quando disponíveis. Restrições obrigatórias do ambiente continuam aplicáveis; sem autorização implícita para apagar dados ou fazer push.

Revisão 0.7.0 / motor 0.5.0: campos comuns reduzidos a equipamento/quantidade/potência, tensão destacada para corrente. Inputs informativos sem cálculo retirados, valores legados preservados em origem. `EnergyFields` e `calculations/energy.py`: consumo mensal opcional por etiqueta/medição unitária (prioritária) ou horas/dias explícitos; custo com tarifa opcional, cobertura incompleta separada de W/VA e exportada. Sem ciclos/tarifas presumidos. Lint/formatação configurados; ferramentas de teste vulneráveis atualizadas. Matriz individual em audit.md, próximos passos de proteção em security.md. Não há conformidade normativa, autenticação ou backup externo novos.

0.8.0 / motor 0.5.1: pesquisas normativas agora no registro/API (Rule.evidence/pending_checks e normative_capabilities), sem coeficientes executáveis. Endpoint technical/rules expõe coverage por distribuidora/UF. Notifications e seção C ficam com correções/alertas reais; recursos indisponíveis têm seção informativa separada. Removidos cards sem resultado e pedidos de dados para operações indisponíveis. Energisa não aplicada a outras distribuidoras. Fonte integral NDU continua 403 e NBR depende de exemplar autorizado completo; não declarar três cálculos normativos implementados. Matemática e dados preservados. Estado/testes da entrega em CURRENT_STATE.

0.9.0 / motor 0.6.0: fontes integrais institucionais e corroboração PF permitiram implementar previsão residencial quantitativa. API tipada/ResultsPanel/PDF/JSON integrados, sem alterar cadastro, fórmulas no frontend ou somar previsão VA à instalada W. Demanda segue bloqueada; fontes e limites em standards.md. Histórico anterior não foi regravado.

Polimento visual após 0.9.0 (22/10/2026): globals.css consolidado, shell/aside/rodapé e hierarquia de seções/cards/controles revisados. Adicionar ambiente destacado em barra sticky; Duplicar ambiente faz cópia profunda com UUIDs novos de ambiente/cargas, snapshots/manuais preservados, nome único e foco na cópia. Novo helper frontend lib/environments.ts não contém cálculos elétricos. Não executar build e E2E ao mesmo tempo: .next/e2e fica dentro do diretório limpo pelo build. Detalhes em forms-and-pdf.md.

0.10.0 / motor 0.6.0: PDF/JSON passam a enfatizar consumo mensal, custo/tarifa/cobertura, equipamentos/uso e pendências, mantendo medidas e resultados anteriores. Preparo único backend reports/summary.py; POST reports/json usa os mesmos guards do PDF, JSON 1.1 aditivo/legível, frontend só baixa. kWh não habilita demanda/padrão de entrada: cobertura regional continua explícita e sem coeficientes novos. PDF conferido em MuPDF temporário independente. Dados e histórico preservados, detalhes em forms-and-pdf/CURRENT_STATE.


0.10.1 / JSON 1.2: auditoria real da Casa do Codex corrige restauração que apagava dados de energia e disponibiliza variantes no painel avançado, preservando potência manual. Relatórios corrigem moeda/identificação de potência editada e preservam características/vínculos por ID. Escopo de consumo e potências máximas explícitos; cenários não equivalem a medição. Motor 0.6.0, normas e migrações inalterados.
