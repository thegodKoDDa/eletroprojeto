# Estado atual — EletroProjeto 0.13.0 / motor 0.8.0

## Escopo vigente

Decisão explícita do usuário em23/10/2026: uso LOCAL. Publicação/infraestrutura remota, CI hospedado, impressão física e backup externo foram retirados do trabalho atual. Não solicitar recursos nem bloquear a evolução por esses itens. Recursos existentes de segurança/backup/CI ficam preservados; checkpoints locais continuam em uso.

## Entrega — demanda integrada ao projeto

Painel opcional de demanda NDU-0017.0 entre ambientes e resultados. Classificação explícita por carga, reservas e tipo AC; confirmação de unidade, letreiros/vitrines, simultaneidade luz/TUG e grupos ausentes. O mesmo motor puro d1–d5 atende endpoint parametrizado e cadastro/PDF/JSON, sem fórmulas no frontend ou alteração dos fatores já conferidos.

Revisão vinculada por SHA256 ao inventário/escopo. Mudanças de cargas, potências, quantidades, classificação, reservas, IDs ou declarações invalidam a revisão, inclusive via API ou após salvar/reabrir. Não há classificação presumida pelo catálogo nem conversão de previsãoVA/BTU/kWh emW. Inventário vazio, dados desconhecidos, inconsistências ou falta de revisão mantêm valor nulo. Reservas não entram na demanda, mas entram na conferência de instalada/75kW.

Escopo: residência individual Energisa Sul-Sudeste/SP até75kW, d1–d5. d6/d7, centrais presentes, agrupamentos, outra distribuidora/UF e demais condições incompatíveis permanecem fora do escopo. Não há dimensionamento final ou aprovação da concessionária. Fontes/condições em standards.md e matemática em calculations.md.

Relatórios PDF/JSON1.3 trazem inventário, declarações/revisão, grupos, fatores/faixas, demanda e pendências. Resumo oculta demanda anterior durante recálculo; guard de exportação inclui configurações novas no digest. Contratos gerados por types:sync; API/frontend0.13.0, motor0.8.0, schema0005 sem nova migração.

## Dados e verificação observada

9 projetos (8 ativos/1 na lixeira),29 históricos,7 revisões técnicas. Todas as colunas dessas três tabelas comparadas ao checkpoint anterior e idênticas; SQLite íntegro/FK sem violações. Nenhum projeto legado regravado/classificado/revisado automaticamente; catálogo e potências manuais preservados.

- Backend345 testes+85 subtestes; continuidade/backup8 (execução conjunta353+85 aprovada).
- Frontend92; tipos/lint/formatação; Ruff; Alembic check e pip check aprovados.
- Suíte local13E2E aprovada; repetição direcionada do fluxo final de demanda aprovada, incluindo axe com painel ativo, PDF/JSON, reabertura, edição, exclusão por escopo e telas320/768/1440.
- Build webpack aprovado após alterações finais de frontend. Contratos sincronizados. PDF baixado no navegador, extraído/renderizado independentemente e página de demanda inspecionada, sem cortes observados no exemplo de três páginas.
- Smoke API real:6,913043478…kVA para1000W d1+5500W d2 revisados. Health0.13.0/motor0.8.0; frontend3000 HTTP200 e navegador real sem pageerrors/versão correta. API PID567673/sessão73185; frontend existente preservado. Revalidar processos em cada retomada.

PostgreSQL, Windows e E2EHTTPS não repetidos nesta entrega local; evidências anteriores continuam históricas. Sem nova migração ou dependência de execução. Instalação editável Python atualizada para0.13.0 com build isolado temporário; tentativa sem isolamento falhou por setuptools ausente, resolvida sem adicioná-lo ao runtime.

## Continuidade e próximos passos

Checkpoint anterior à mudança: `.checkpoints/20261023T184620161249Z`, verificado com hashes, restauraçãoSQLite e recuperaçãoGit. Inventários/referências/revisões organizados conforme docs/README.md; PDFs locais em references/energisa, fora de Git/ZIP de código. Caminho do checkpoint final será registrado após geração.

Próximas prioridades locais: ampliar exceções normativas somente após fontes/testes próprios; dimensionamento de circuitos/cabos/proteções/queda de tensão/entrada; geometria/localização dos pontos e associação territorial oficial completa. Ver roadmap/KNOWN_ISSUES. Leitor de tela real ainda não conferido. Retomar por AGENTS e `python3 scripts/continuity.py retomar`; não recriar produto ou regravar dados antigos para atualizar regras. Sem push/publicação.
