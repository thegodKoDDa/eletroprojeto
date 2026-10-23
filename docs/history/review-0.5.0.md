# Revisão de interface, referências e recuperação — 0.5.0

Aplicação/API/frontend 0.4.0 → 0.5.0. Motor 0.4.1 → 0.4.2 (diagnósticos; fórmulas preservadas). Evolução sobre o repositório existente, sem troca de stack ou dependências.

## Diagnóstico e decisões

| Área | Decisão | Resultado |
|---|---|---|
| Ações principais | Reconstruir | Salvar em destaque; PDF diretamente acessível; Novo, Salvar como, JSON, verificação e exclusão em Mais ações. Menu com Escape, fechamento ao perder foco e retorno de foco. |
| Lixeira | Reconstruir | Diálogo próprio, separado de ativos, com data de exclusão, pesquisa, paginação, restaurar e excluir definitivamente. Respostas de outro filtro não aparecem como registros excluídos. |
| Resultados | Reconstruir | A: resumo; B: memória expansível; C: pendências reais. Mesma resposta Python em ambas apresentações. |
| Avisos de referência/manual | Remover do fluxo de pendências | Diferença do catálogo e origem estimada não geram aviso genérico por equipamento. Origem, estado estimado, edição e fonte continuam no projeto, memória e PDF. |
| FP, configuração e rendimento | Manter/corrigir apresentação | Participam de VA/corrente/entrada mecânica. Ausência de FP não é destacada quando o objetivo é somente W. |
| Dados de placa/energia/saída útil | Simplificar e conectar | Grupo informativo opcional. Agora constam no PDF; não substituem W de entrada nem corrente calculada. |
| Dimensões e pontos | Manter como documentação | Usados no relatório; limitação de previsão normativa explícita. Novos ambientes não recebem dimensões fictícias 12/14. |
| Tensão geral de referência | Remover controle sem efeito atual | Valor antigo preservado e exibido como informativo, sem fingir alimentar a tensão das cargas. Cada equipamento mantém tensão editável própria. |
| Duplicar dentro do formulário | Remover duplicação de ação | Salvar como e duplicação na biblioteca preservam a capacidade, sem dois fluxos locais diferentes de cópia. |
| JSON bruto de referências na tela | Simplificar | Rastreabilidade apresentada por regra/estado/motivo. Exportação JSON continua integral. |
| PDF/Decimal/debounce/contratos | Manter | Cálculo atual obrigatório para exportar, cancelamento de respostas obsoletas, precisão decimal e contratos gerados preservados. |

## Funcionalidades e persistência

- Novo projeto continua criando registro independente. Salvar usa o ID atual e versão otimista. Salvar como cria outro ID; quando o nome não foi alterado, acrescenta “· cópia” para identificá-lo. Edições realizadas durante a gravação são preservadas.
- Exclusão comum permanece lógica. `Project.deleted_at` expõe a data já existente no banco; adaptador frontend remove esse metadado ao preparar entradas de gravação/exportação.
- Novo `DELETE /api/v1/projects/{id}/permanent?expected_version=N`: somente projetos já na lixeira, com versão atual. Operação transacional com cascade de histórico por FK; projetos ativos e registros de outros projetos são preservados. Confirmação explícita no frontend identifica projeto e irreversibilidade.
- Não houve migração de schema: deleted_at já existia. Backup íntegro criado antes das alterações em `/tmp/eletroprojeto-before-050.db`; comparação SQL integral confirmou preservação dos 3 projetos, 11 históricos e 4 revisões técnicas existentes; PRAGMA integrity_check retornou ok. Nenhum projeto real foi excluído definitivamente pelos testes.
- A aplicação segue local, sem autenticação/autorização multiusuário. A rota permanente, assim como as demais mutações, exige proteção por proprietário antes de publicação externa. Não foi introduzida uma chave fixa para simular autenticação.

## Configurações: finalidade concreta

Potência/quantidade entram na soma; FP em VA/corrente; tensão/configuração na corrente; potência mecânica/unidade/rendimento na entrada elétrica; tipo/capacidade/compressor na escolha de referência compatível e conversão térmica informativa. Categoria afeta a agregação cadastral, sem equivaler a grupo normativo de demanda. Natureza distingue iluminação e usos cadastrados. Identificação/fonte/origem afetam rastreabilidade/relatório/estado estimado.

Consumo mensal, corrente de placa/partida/máxima, potência máxima, saída útil e tamanho de tela são dados informativos. O relatório os identifica separadamente. Não foi inventada fórmula para torná-los artificialmente influentes. A potência adotada para o computador não é automaticamente substituída pela capacidade de sua fonte.

## Política de referências e cálculos

Teste independente do computador: referência Enel de 300 W; entrada manual 600 W × 2 = 1.200 W. Com FP 0,8, soma aparente 1.500 VA. O valor é salvo, reaberto, aparece no PDF e não modifica o catálogo. A alteração não gera erro ou pendência apenas por divergir de 300 W.

Regressões de AC entre 9/12/18/24/30 mil BTU/h, preservação manual, conversões, rendimento de motor, correntes, tensões, potências por ambiente/categoria e rejeição de respostas antigas foram reexecutadas. Nenhuma fórmula elétrica foi duplicada no frontend. Nenhuma margem ou fator normativo foi inventado.

## Demanda normativa e fontes

Foi pesquisada novamente a fonte oficial. O índice do documento Energisa NDU-001 7.0 identifica a seção 9.1 e tabelas associadas às parcelas. A abertura integral do [PDF oficial identificado](https://www.energisa.com.br/sites/energisa/files/media/documents/2025-11/NDU%20001%20-%20Fornecimento%20de%20Energia%20El%C3%A9trica%20em%20Tens%C3%A3o%20Secund%C3%A1ria%20a%20Edifica%C3%A7%C3%B5es%20Individuais.pdf) retornou 403. Um trecho indexado não confere todas as condições, classificações, tabelas e exemplos independentes. Assim, não foi habilitada demanda normativa final nem incorporado um coeficiente somente para produzir número.

Previsão mínima NBR 5410, TUG e demanda ainda têm dependências documentais reais; a interface identifica essas limitações sem atribuí-las a valores manuais fora do catálogo. Fontes anteriores de equipamentos continuam rastreáveis no registro; nenhuma potência nova foi inventada nesta revisão.

## PDF

Mantém identificação, resumo, ambientes, quadro de cargas, demanda, memória, pendências e fontes. Dados informativos passam a ser exportados com unidades e ressalva de que não são entrada elétrica. Foram corrigidas quebras que deixavam observação normativa ou título de grupo de avisos isolado na página seguinte, com teste de regressão.

Uma prévia do PDF de três páginas foi gerada e inspecionada via Cairo, usando o parser auxiliar do subconjunto emitido pelo projeto. Isso não substitui inspeção em leitor PDF independente. Os testes estruturais verificam limites de texto, colunas, paginação e operações. Artefatos: `/tmp/eletroprojeto-050.pdf` e `/tmp/eletroprojeto-050-preview/`.

## Verificações

Os totais e impedimentos efetivamente observados são registrados ao final desta entrega. Build, lint e Playwright foram tentados: build Webpack falha ao interpretar saída TypeScript --showConfig; lint não está configurado; Playwright não abre a API na porta 8000. Não há validação visual real do site, aprovação E2E ou build de produção aprovado. Nenhum localhost foi confirmado ativo.

## Principais arquivos

`ProjectActions.tsx`, `ProjectWorkspace.tsx`, `ResultsPanel.tsx`, `DemandSummary.tsx`, `EquipmentEditor.tsx`, `page.tsx`, `globals.css`; adaptador API/contrato gerado; `app/{main,schemas,projects,validation,version}.py`, `reports/pdf.py`; testes de API, PDF, ações, workspace, página e equipamentos, cenários Playwright; versões/lock, README, arquitetura e histórico.

## Pendências

Executar navegador/inspeção responsiva e build fora da restrição atual; configurar ESLint; validar integralmente normas e exemplos de demanda; autenticação/autorização antes de uso externo. A revisão não constitui aprovação normativa nem conclusão integral dos critérios que dependem dessas verificações.

## Resultado final das verificações

- pytest: **112 aprovados + 11 subtestes**; casos de purga verificam também no SQLite a remoção do histórico do projeto-alvo e a preservação dos demais.
- Vitest/RTL: **62 aprovados** em nove arquivos, incluindo computador 300 → 600 W, cópia independente identificável, biblioteca/lixeira, menu, preservação do rascunho ao cancelar e rejeição de registros em cache de outro filtro.
- Contratos OpenAPI/TypeScript sincronizados; typecheck, compileall e Alembic check aprovados.
- pip check: nenhuma dependência instalada inconsistente. Auditoria npm atualizada tentou consultar o registro e falhou por DNS (EAI_AGAIN); não foi declarada ausência de vulnerabilidades.
- Next dev falhou com listen EPERM em 3000; curl de health também foi bloqueado para sockets. Playwright parou antes do navegador ao abrir 8000. Build Webpack e lint continuam com os impedimentos descritos acima.

A interface atual possui uma página principal Next e componentes reaproveitados/reconstruídos; não foi criado outro aplicativo. A comparação integral de snapshots confirma que as alterações desta revisão não modificaram os projetos reais armazenados.
