# Estado atual — EletroProjeto 0.25.2 / motor 0.13.0

Atualizado em **29/10/2026**. Branch `main`; entrada da vistoria `35c0936`. Commit final no Git e checkpoint em `.checkpoints/latest.json`.

## Estado dos dados

O usuário excluiu todos os projetos antes desta vistoria. Na conclusão da vistoria, o banco local `backend/eletroprojeto.db` continha **0 projetos ativos, 0 na lixeira e 0 históricos**. No encerramento posterior, há **1 projeto e 2 históricos**, preservados sem alteração; integridade e chaves estrangeiras aprovadas. Permanecem 12 revisões técnicas, 2.082 documentos, 51.324 páginas e 3.788 fontes. Integridade/FK aprovadas; schema Alembic **0007**, sem migração pendente.

Checkpoint inicial **20261028T214022868431Z** capturou a base já vazia e foi restaurado isoladamente. As 12 tabelas reais foram comparadas ao ponto inicial e permaneceram idênticas. Testes usaram bancos/portas/contextos separados; nenhum projeto de exemplo foi salvo no SQLite real, nem foram restaurados projetos excluídos.

## Correções da vistoria

- Comparação conserva a referência capturada ao abrir/primeiro salvar, mesmo após autosaves anteriores ou posteriores à comparação. Trocar projeto reinicia a referência; botão explícito adota a versão salva mais recente. Edições continuam ocultando/cancelando resultados antigos.
- PUT idêntico com metadados legados sem `id` deixou de causar erro, tanto na API quanto no Pyodide. Metadados permanecem opacos; números NaN/infinito são rejeitados antes da gravação, sem validar regras normativas.
- Indicadores identificam subtotais parciais e potência desconhecida. Custo pede dados de consumo quando a tarifa já existe. Ambientes vazios mostram Sem aparelhos.
- Consumo declarado em kWh não torna potência obrigatória: o campo fica opcional e a pendência de potência é informativa, sem invalidar o consumo disponível. Valores manuais, zero declarado e aritmética Decimal preservados.
- Guia/E2E alinhados ao município opcional. Chaves distintas mantêm identidade dos painéis React.

Aplicação 0.25.1; fórmulas e motor 0.13.0 inalterados. Sem instalação/upgrade, migração, reset ou exclusão de acervo/checkpoints.

## Verificações efetivas

**601 pytest + 85 subtestes e 128 testes frontend aprovados.** E2E amplo: **41 aprovados**; o caso adicional de consumo parcial e repetições dos afetados cobrem **42 cenários**, com 8 e depois 7 aprovações nas rodadas direcionadas. **1 E2E HTTPS de duas contas aprovado**. Axe/teclado e telas de 320/390/768/1440 px nos fluxos registrados; capturas fictícias inspecionadas.

Contratos por `npm run types:sync`, TypeScript, ESLint, Prettier, Ruff/checkformat, pip check e conferência npm aprovados. Builds Webpack nativo e estático aprovados; bundle com 24 arquivos, sem módulos normativos. Chromium com Pyodide real executou 36→72 kWh/mês, tarifa fictícia 0,80, autosave, diferença de 36 kWh, PDF e reabertura após reload, sem backend local/rotas normativas ou erros de página. Teste estático temporário encerrado; serviços do usuário preservados.

## Ambiente e próxima ação

API e interface mantidas em **http://localhost:8000/docs** e **http://localhost:3000**, com HTTP 200 confirmado. API reiniciada graciosamente para carregar as correções, versão 0.25.1/motor 0.13.0. Código 0.25.1 sincronizado em `fe8d0e8`; implantação Pages concluída com sucesso e versão publicada conferida. Release ZIP v0.25.1 publicada a pedido do usuário em 28/10/2026, gerada do commit documental correspondente; manifesto e SHA-256 conferidos contra o download público.

Nenhuma implementação interrompida. Próximo passo: usar o sistema limpo e atender ao próximo pedido, mantendo o foco em consumo residencial. Limites em [KNOWN_ISSUES](KNOWN_ISSUES.md) e prioridades em [roadmap](roadmap.md).

Não revalidados: Windows/macOS/ARM, Docker e PostgreSQL reais, carga/pentest ou leitor de tela real. Tarifa segue manual, consumo depende das premissas, comparação é edição versus referência em memória (não persiste essa escolha ao recarregar). SQLite e Pages/localStorage são independentes; buffers/rascunhos externos não são capturados pelo checkpoint e não houve cópia externa.

Retomar: `python3 scripts/continuity.py retomar`. Se serviços estiverem parados: `python3 scripts/start_local.py --no-browser`, conforme [setup](setup.md). Fim de implementação não é pedido de encerrar serviços. Recuperação e salvamento em [continuity](continuity.md).

## Encerramento solicitado — 28/10/2026 (após release v0.25.1)

Estudo completo do projeto e bateria sem alterar código: 560 pytest/85 subtestes, 41 de scripts, 128 Vitest, 42 E2E, 1 E2E HTTPS, builds Webpack e estático, Ruff, ESLint, Prettier e tsc aprovados. Release **v0.25.1** publicada como Latest (ZIP, manifesto e SHA-256 do commit `47f529f`, downloads públicos conferidos); Pages desse commit concluído com sucesso. Banco local: 1 projeto, 2 históricos, 13 revisões técnicas (eram 12 no registro anterior; não investigado, sem relação com os testes, que usam bancos temporários), integrity_check ok e foreign_key_check vazio; nada apagado ou restaurado. Limpeza simulada: 1,8 MB de gerados, não aplicada. 920GiB livres.

A pedido do usuário, API e interface locais foram encerradas graciosamente ao fim da sessão. Para retomar: `python3 scripts/continuity.py retomar` e, se necessário, `python3 scripts/start_local.py --no-browser`. Nenhuma tarefa interrompida. Não revalidados: Windows/macOS/ARM, Docker, PostgreSQL, Pyodide real nesta sessão, carga/pentest e leitor de tela. Buffers externos e rascunhos do navegador não são verificáveis pelo checkpoint. O ponto final verificável fica em `.checkpoints/latest.json`.

## Vistoria completa — 29/10/2026

Revisados os 276 arquivos versionados, organização local, motor/API de estimativas, schemas legados, pacote Python estático, formulários, persistência, comparação, relatórios, testes, scripts e publicação. Os módulos normativos preservados não foram reintegrados ao motor. Nenhum arquivo privado/gerado indevido no Git, link documental local ausente ou padrão de credencial encontrado na varredura dos arquivos versionados. Mantida a organização por responsabilidade e o arquivo histórico; não houve movimentação cosmética de fontes.

Correções: o build do iniciador local restaura `tsconfig.json` e `next-env.d.ts` mesmo em falha, evitando alterações automáticas versionadas; duas regressões exercitam sucesso/falha. HTTPS QA passa a usar API 8011 e saída `test-results-auth`, ignorada no Git e contemplada na limpeza permitida. Descrição pública do GitHub alinhada ao consumo residencial. Fórmulas, contratos, dependências e versões 0.25.1/motor0.13.0 preservados.

Verificações: 601 pytest/85 subtestes e 128 frontend aprovados; depois da correção, 8 testes do iniciador e 14 testes combinados de iniciador/manutenção aprovados. 42 E2E e 1 HTTPS aprovados em rodada válida. Primeira rodada E2E invalidada por execução simultânea de suítes/build (artefatos compartilhados e reinício de Next), corrigida e repetida em sequência. Contratos regenerados sem diferença; TypeScript, ESLint, Prettier, Ruff/checkformat, migrações QA, pip check e instalações npm aprovados. Build nativo com preservação real das configurações e build estático com 24 arquivos aprovados; Pages HTTP 200 e pacote Python público idêntico ao local. Restauração isolada do checkpoint inicial aprovada; as 12 tabelas reais permanecem idênticas (1projeto,2históricos,13revisões e acervo preservados), integridade/FK aprovadas.

Limites desta vistoria: não executados Windows/macOS/ARM, Docker/PostgreSQL reais, carga/pentest, leitor de tela real nem Pyodide real no navegador. A varredura não equivale a revisão humana integral dos originais do acervo. Quality hospedado permanece desativado; release v0.25.1 preservada. Limpeza permitida removeu 156.027.814 bytes de caches e saídas QA; dados/acervo/checkpoints/dependências/build ativo preservados. Serviços locais permanecem ativos. Sincronização e checkpoint final conferidos pela rotina; referência em `.checkpoints/latest.json`.

Próximo passo: atender ao próximo pedido; nenhuma implementação interrompida.

## Distribuição 0.25.2 — 29/10/2026

Release de correção preparada com as mudanças validadas na vistoria: preservação da configuração no iniciador, isolamento de QA HTTPS e manutenção. Versões frontend/backend/lock e OpenAPI alinhadas; motor 0.13.0 preservado. ZIP gerado exclusivamente do commit revisado, manifesto e SHA-256 conferidos antes e após publicação. Release anterior preservada; nenhuma mudança de dados ou migração.
