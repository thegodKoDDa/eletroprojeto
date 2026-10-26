# Estado atual — EletroProjeto 0.18.0 / motor 0.9.2

Atualizado em 25/10/2026. SQLite/schema0007 e JSON de relatório1.4 preservados. Esta entrega atende parte do pedido de resolver as pendências; **não conclui cobertura territorial, demanda de grupos especiais ou dimensionamento/localização integrais**. Detalhes históricos em SESSION_HISTORY/CHANGELOG/Git.

## Encerramento solicitado — 25/10/2026

Encerramento reiterado pelo usuário em25/10/2026: conferência em f6a7fa7, main limpa e sem divergência com origin; integridade e contagens abaixo reconfirmadas, API/frontend HTTP200 e cerca933GiB livres. Apenas registro documental atualizado; sem mudança funcional ou repetição de suítes. Sincronização e restauração isolada serão verificadas pela rotina final.

Sessão encerrada por solicitação do usuário. Código/docs já sincronizados em3547394 antes deste registro; botão inferior Adicionar ambiente está à direita e validação com leitor de tela real foi descartada. Banco atual íntegro/FKok: **11projetos/36históricos/10revisões**, schema0007. Os totais34/9 abaixo são a fotografia da validação anterior; cadastros/revisões adicionais foram preservados. API8000 efrontend3000HTTP200, cerca933GiBlivres. Sem alteração funcional, exclusão, limpeza ou reinstalação neste encerramento; suítes não repetidas. Serviços preservados.

Próxima sessão: RETOMAR ELETROPROJETO e seguir as pendências técnicas abaixo conforme o pedido atual, preservando o fluxo simples. Código/docs no GitHub privado; dados/acervo/checkpoints locais. Sincronização e restauração do checkpoint final devem ser confirmadas pela rotina e`.checkpoints/latest.json`, sem commit extra pelo caminho. Rascunhos não enviados do navegador e buffers externos não são capturados.

## Produto entregue

Estimativa de consumo residencial para leigos primeiro, profissionais depois. Início/sidebar/três cartões e fluxo **01 Projeto → 02 Ambientes → 03 Conferência** preservados, com estudos técnicos opcionais e recolhidos.

- Adicionar ambiente também aparece ao final da lista, alinhado à direita, após existir ao menos um ambiente. Usa a mesma ação e bloqueios do botão superior e acompanha a criação sucessiva; conferido no navegador em390/1440px, sem overflow ou gravação de projetos.
- Pesquisa explícita do catálogo agora considera correspondências em todos os equipamentos; sugestões do ambiente não escondem o resultado. Listas vazias orientam a repetir/limpar a busca.
- Conferência identifica aparelhos com consumo pendente por ambiente e oferece atalho para cada dado faltante. Consumo por aparelho também identifica o ambiente; nomes iguais deixam de ser ambíguos.
- Tarifa ausente tem atalho com foco; zero informado permanece válido. Campos de consumo/horários e tarifa possuem descrições acessíveis vinculadas, com prioridade da etiqueta/medição e consumo por unidade/quantidade explícitos.
- Editores de aparelhos são grupos acessíveis; link de salto foca o conteúdo. Teclado/nomes/descrições/axe foram verificados; isso não representa teste com leitor de tela real. Por decisão explícita do usuário em25/10/2026, a validação com leitor de tela real foi retirada do escopo; não é pendência nem bloqueio. Melhorias e testes automáticos de acessibilidade permanecem.
- Sem fórmulas no frontend, horários/tarifas presumidos, alteração de catálogo, regravação de projetos ou nova etapa técnica obrigatória. Autosave/rascunhos/conflitos e resultados antigos ocultos/debounce/cancelamento preservados.

## Ampliação técnica limitada

B1/B2 cobre/PVC70°C/dois condutores carregados agora contempla50/70/95mm², mantendo os critérios anteriores e teto95mm² sem extrapolar. Condutor de proteção para S>35 segue PE≥S/2 com próxima seção padronizada:50→25,70→35,95→50mm². Fonte/edição/condições/conferência visual e exemplos em standards/calculations; testes independentes de resultados/limites em test_circuits.py. Motor0.9.2 identifica a alteração para novos cálculos/prévias/revalidação explícita. Histórico existente permanece inalterado.

Relidos §9/notas/tabelas12–15 da NDU-0017.0 local. d6/d7/centrais continuam nulos/fora do escopo: parâmetros próprios, integração e exemplos específicos ainda não implementados/revisados. Não se tratam kVA como kW nem se infere FP. Não há dimensionamento final universal.

Reconsulta oficial: catálogoABNT exibe5410:2004/VC2008; portalEnergisa listaNDU0017.0. Novas tentativas de download integral falharam. SIGEL retornou diretórioHTTP200/listaAREA_ATUACAO, mas camadas deram500/timeout; sem feições territoriais verificadas e sem nova associação municipal.

## Verificações efetivas

Alinhamento do botão inferior alterado para a direita por pedido do usuário; conferido no navegador em390/1440px e com criação sucessiva, sem gravação de projetos. Sem mudança funcional, suítes anteriores não repetidas.

Ajuste pontual posterior do botão inferior:104 testes frontend, ESLint/Prettier do arquivo e verificação no navegador com1/2/3ambientes aprovados. Backend/build/suíteE2E não repetidos para esse acréscimo de botão; resultados abaixo correspondem à entrega0.18.0 anterior.

- **401 testes backend +85 subtestes e104 testes frontend aprovados.** Ruff/check eformatação Python aprovados.
- **22 E2E aprovados na bateria completa; o novo23º cenário de teclado falhou por sincronização inicial do teste, foi corrigido e passou em execução dirigida.** Nenhum cenário removido/desativado. Cadastro/consumo/salvamento/rascunhos/revalidação/lixeira/relatórios e circuitos foram exercitados em SQLite/portas QA isolados.
- Contratos regenerados via `npm run types:sync`; só a versão OpenAPI mudou, tipos gerados sem diff. TypeScript/lint/Prettier ebuildwebpack isolado em`.next/qa-build` aprovados. Gerados next-env/tsconfig inspecionados e restaurados ao conteúdo versionado; Nextdev pode regenerar next-env enquanto ativo.
- Axe/teclado eviewport320/390/768/1440px sem overflow no fluxo simples. Capturas390/1440px em`/tmp/eletroprojeto-simple-*`inspecionadas.
- Último checkpoint anterior restaurado isoladamente com sucesso. As **12 tabelas reais** foram comparadas integralmente com20261024T203754927856Z:sem alteração. SQLite íntegro/FKok,11projetos/34históricos/9revisões,10ativos/1lixeira,schema0007. Acervo2.082documentos/51.324unidades/3.788fontes preservado.
- API8000 efrontend3000 iniciados após conferir portas livres; ambosHTTP200,health0.18.0/motor0.9.2. [Aplicação local](http://localhost:3000).

Não executados nesta entrega: leitor de tela real, HTTPS de duas contas (validação anterior preservada), PostgreSQL, Windows real, carga/pentest ou inspeção elétrica física. Sem atualização/reinstalação de dependências, migração/reset, exclusão de dados/acervo/checkpoints ou limpeza de gerados.

## Pendências e próximo passo

Pedido do usuário é resolver as faltas listadas, com a validação por leitor de tela real descartada explicitamente em25/10/2026. Restam:

1. Ampliar demanda d6/d7/centrais com parâmetros próprios, revisão das condições/ambiguidades, integração e exemplos independentes. A leitura de tabelas não basta para liberar cálculo.
2. Ampliar métodos/materiais/fases/proteções/entrada e modelar geometria/localização/volumes/distâncias; seleção atual de seção não verifica distribuição física ou conformidade integral.
3. Obter/validar dados territoriais oficiais utilizáveis antes de associar municípios e distribuidoras. ServiçoAREA_ATUACAO indisponível nesta consulta.

Fontes e limites em standards/calculations; pendências em KNOWN_ISSUES/roadmap; revisão de interface em audit. Código/docs no GitHub privado; banco,.env,originais echeckpoints permanecem locais. Commit/sincronização/checkpoint finais devem ser confirmados pela execução e`.checkpoints/latest.json`; não criar commit extra pelo caminho. Publicação/CIhospedado/impressão física/cópia externa seguem fora do escopo. Buffers externos/rascunhos não enviados não são capturados pelo checkpoint.
