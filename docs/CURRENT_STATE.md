# Estado atual — EletroProjeto 0.25.1 / motor 0.13.0

Atualizado em **28/10/2026**. Branch `main`; entrada da vistoria `35c0936`. Commit final no Git e checkpoint em `.checkpoints/latest.json`.

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

## Encerramento solicitado — 28/10/2026

Estado mais recente: 1 projeto e 2 históricos no SQLite, integrity_check ok e foreign_key_check vazio; API/interface HTTP200, 920GiB livres. Nenhum dado apagado ou restaurado. Vistoria concluída; nenhum código alterado após as verificações registradas. Encerramento com revisão de Git/disco e banco, atualização deste estado/histórico e execução de `continuity.py encerrar --sync`. O resultado final verificável fica em `.checkpoints/latest.json`; não restaurar projetos que o usuário excluiu. Nenhuma tarefa interrompida. Na retomada, executar a rotina registrada acima e seguir o próximo pedido. Buffers externos e dados não enviados do navegador não são verificáveis por esta rotina.
