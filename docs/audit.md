# Verificações e evidências

Este documento organiza os resultados conhecidos. A fotografia operacional está em [CURRENT_STATE](CURRENT_STATE.md); regras e condições de aplicação estão em [standards](standards.md). Uma suíte aprovada verifica os cenários exercitados e não declara conformidade elétrica integral.

## Vistoria completa — 29/10/2026

Revisados os 276 arquivos versionados, organização local, motor/API de estimativas, schemas legados, pacote Python estático, formulários, persistência, comparação, relatórios, testes, scripts e publicação. Os módulos normativos preservados não foram reintegrados ao motor. Nenhum arquivo privado/gerado indevido no Git, link documental local ausente ou padrão de credencial encontrado na varredura dos arquivos versionados. Mantida a organização por responsabilidade e o arquivo histórico; não houve movimentação cosmética de fontes.

Correções: o build do iniciador local restaura `tsconfig.json` e `next-env.d.ts` mesmo em falha, evitando alterações automáticas versionadas; duas regressões exercitam sucesso/falha. HTTPS QA passa a usar API 8011 e saída `test-results-auth`, ignorada no Git e contemplada na limpeza permitida. Descrição pública do GitHub alinhada ao consumo residencial. Fórmulas, contratos, dependências e versões 0.25.1/motor0.13.0 preservados.

Verificações: 601 pytest/85 subtestes e 128 frontend aprovados; depois da correção, 8 testes do iniciador e 14 testes combinados de iniciador/manutenção aprovados. 42 E2E e 1 HTTPS aprovados em rodada válida. Primeira rodada E2E invalidada por execução simultânea de suítes/build (artefatos compartilhados e reinício de Next), corrigida e repetida em sequência. Contratos regenerados sem diferença; TypeScript, ESLint, Prettier, Ruff/checkformat, migrações QA, pip check e instalações npm aprovados. Build nativo com preservação real das configurações e build estático com 24 arquivos aprovados; Pages HTTP 200 e pacote Python público idêntico ao local. Restauração isolada do checkpoint inicial aprovada; as 12 tabelas reais permanecem idênticas (1projeto,2históricos,13revisões e acervo preservados), integridade/FK aprovadas.

Limites desta vistoria: não executados Windows/macOS/ARM, Docker/PostgreSQL reais, carga/pentest, leitor de tela real nem Pyodide real no navegador. A varredura não equivale a revisão humana integral dos originais do acervo. Quality hospedado permanece desativado; release v0.25.1 preservada. Limpeza permitida removeu 156.027.814 bytes de caches e saídas QA; dados/acervo/checkpoints/dependências/build ativo preservados. Serviços locais permanecem ativos. Sincronização e checkpoint final conferidos pela rotina; referência em `.checkpoints/latest.json`.

## Vistoria de consumo residencial — 28/10/2026, 0.25.1

Vistoria do produto reformulado, com o banco que o usuário já havia esvaziado. As **12 tabelas reais ficaram idênticas** ao checkpoint inicial `20261028T214022868431Z`: 0 projetos/0 históricos, 12 revisões técnicas e acervo preservado. Testes funcionais gravaram somente em bancos de QA e localStorage de contextos temporários.

| Área | Evidência desta vistoria |
| --- | --- |
| Backend e scripts | 601 pytest e 85 subtestes aprovados; exemplos independentes de potência, horários, etiquetas mensais/anuais, zero, cobertura parcial, comparação e relatórios |
| Frontend | 128 testes aprovados; manuais/referências, debounce/abort, identidade, formulários, rascunhos, conflitos, comparação e avisos |
| Navegador local | 41 E2E amplos aprovados; cenário adicional e repetições direcionadas cobrem 42 casos, três perfis, criação/edição/salvamento/reabertura, duplicação, lixeira, PDF/JSON, acessibilidade e geometria |
| Acesso remoto | 1 E2E HTTPS com duas contas aprovado, incluindo isolamento de projetos/rascunhos e cookies |
| Runtime estático | Build e Pyodide reais: cálculo 36→72 kWh/mês, custo pela tarifa manual fictícia, autosave, comparação com diferença 36, PDF e reload/reabertura; sem chamadas ao backend local ou regras normativas |
| Qualidade | Contratos oficiais, TypeScript, ESLint, Prettier, Ruff/checkformat, pip check e npm ls aprovados; builds nativo e estático concluídos |
| Serviços | localhost3000/8000 mantidos e HTTP confirmado; API reiniciada graciosamente; servidor estático de QA encerrado |

Causas/correções confirmadas por regressão:

- A referência da comparação acompanhava `saved.version` e desaparecia no autosave. Agora captura o snapshot por abertura/primeiro salvamento e só muda por escolha explícita; troca de projeto e edição invalidam estados corretamente.
- A idempotência assumia que todo metadado legado de circuito tinha `id`. A guarda agora preserva dados sem identidade, na API e no browser, sem erro 500 ou histórico duplicado.
- Metadados opacos permitiam números não finitos que não pertencem a JSON interoperável. Validação estrutural rejeita NaN/infinito antes da persistência; não aplica critérios de instalações.
- Consumo parcial/ausência de potência e custo sem energia tinham mensagens imprecisas. Subtotais e campos faltantes agora são explícitos; kWh declarados dispensam potência e produzem informação, não erro de consumo.
- O guia mantinha expectativas antigas sobre município obrigatório. Testes agora verificam o município opcional e a edição de nome válido/vazio. Painéis têm chaves React distintas.

Fórmulas e motor 0.13.0 não mudaram. Não revalidados em máquinas próprias: Windows/macOS/ARM, Docker/PostgreSQL, carga/pentest ou leitor real. O teste de Pyodide usa o bundle atual em servidor HTTP temporário e contexto Chromium separado; não verifica dados existentes no navegador pessoal do usuário. Registros abaixo são históricos e não substituem esta vistoria.

## Automação de consumo — 0.24.0 / motor0.12.0

Revisados motor/precisão, parâmetros/validação/contratos, catálogo/instância, edição/ajuda, salvamento/reabertura e relatórios.587testes backend/85subtestes,128frontend,37E2E locais e1HTTPS aprovados, além de contratos/tipos/lint/formatação/Ruff/build isolado. E2E novo cobre os3perfis, minutos/anual, rotina em lote sem substituição, custos/participação/projeção, PDF, persistência, edição, axe e320/390/768/1440px. Erros de relatório/base latente e de correção de unidade foram corrigidos; seletores ajustados à inclusão de details aninhados. Fontes/limites em standards/calculations e resultados operacionais em CURRENT_STATE.

Banco real:12tabelas idênticas ao checkpoint inicial20261026T225824590153Z,integridade/FKok;13projetos/38históricos/11revisões preservados. Não revalida normas ou acervo integralmente; sem inspeção física, medição real, testes nativos Windows/macOS/ARM,Docker/PostgreSQL/carga/pentest nesta entrega. Evidência de sucesso limita-se aos cenários exercitados.

## Base funcional — versão 0.19.0

Validação executada em 26/10/2026:

| Área | Resultado |
| --- | --- |
| Backend | 500 testes e 85 subtestes aprovados |
| Frontend | 109 testes aprovados |
| Navegador | 24 E2E completos aprovados em banco e portas isolados |
| Contratos e qualidade | Geração de tipos, TypeScript, ESLint, Prettier, Ruff e build Webpack aprovados |
| Acessibilidade e layout | Axe e viewports de 320/390/768/1440 px exercitados nos cenários registrados |
| Preservação de dados | 12 tabelas reais idênticas ao checkpoint anterior; SQLite íntegro e sem falhas de FK |
| Recuperação | Restauração isolada do checkpoint e sincronização privada conferidas |

Os cenários incluem consumo, salvamento, rascunhos, conflitos, lixeira, exportação, demanda especial, circuitos trifásicos e geometria de envelopes. A consulta territorial também foi exercitada no navegador com a coleta local, sem gravação de projetos.

HTTPS de duas contas, PostgreSQL, Windows real, carga/pentest e inspeção elétrica física não foram repetidos nessa entrega. Resultados anteriores dessas plataformas permanecem históricos. Validação com leitor de tela real foi retirada do escopo por solicitação do usuário.

## Organização do repositório — 26/10/2026

Apresentação reorganizada a partir do padrão do Minecoord: README focado no produto, prévia real, guias por tarefa e contribuição separada. Modelos de issue/PR são arquivos do repositório; não criam conversas ou publicações automaticamente.

As capturas em `docs/assets` foram produzidas em um contexto de navegador separado. O exemplo de consumo usa dados fictícios e não grava projetos. Banco, credenciais, acervo e checkpoints permanecem ignorados. Não houve alteração de interface, fórmulas ou contratos nesta organização.

Checks proporcionais aprovados: links e âncoras locais, caminhos de imagens, renderização do README pela API Markdown do GitHub e inspeção no navegador, frontmatter dos modelos de issue, comparação integral dos registros movidos (somente links relativos ajustados) e 27 testes de continuidade. Descrição/tópicos conferidos pela API; repositório privado e Actions desativado preservados. A suíte funcional acima é da entrega 0.19.0 e não foi repetida por uma alteração exclusivamente documental.

## Registros anteriores

O [arquivo de auditorias até 0.19.0](history/audit-through-0.19.0.md) preserva causas, correções, casos exercitados e limitações das revisões anteriores. Contagens, processos e pendências ali devem ser interpretados pela data do registro.

## Distribuição 0.20.0 — 26/10/2026

500 testes backend/85 subtestes, 40 testes de scripts, 109 frontend e 24 E2E aprovados. Builds Linux nativo e Docker amd64, contratos, Ruff, tipos, lint e formatação aprovados. Smoke de navegador em ambos: consumo fictício de 6 kWh/mês, salvamento, PDF, axe sem violações e viewports 390/1440 px; projetos isolados preservados após reinício. Imagem runtime passou pip check e contém avisos/licenças de terceiros. Sem execução real em Windows/macOS/ARM. Histórico revisado para arquivos privados e padrões de credenciais; matches de URLs autenticadas são fixtures de segurança. Dados reais/acervo não entram no contexto Docker nem nos pacotes.

ZIP ensaiado em cópia Git isolada antes do commit original, extraído em pasta com espaços e instalado sem dependências prévias nessa cópia. Preparação, migrações, build e navegador aprovados: 6 kWh/mês, salvamento, PDF, axe sem violações. As 12 tabelas reais continuam idênticas ao checkpoint 20261026T043321275895Z, com integridade/FK ok e contagens 11/36/10.


## Revisão de pendências0.21.0 — 26/10/2026

Fonte/condições confrontadas emstandards; casos resolvidos e descartados não reabertos. Métodos/isolação ampliados, verificações documentais DPS/seletividade e relações municipais oficiais entregues com nulos/limites. Verificações atuais emCURRENT_STATE; fontes locais ignoradas e12tabelas reais idênticas ao checkpoint inicial. A revisão não é laudo físico nem revisão humana integral do acervo. O catálogo ABNT lista5419:2026; não foi habilitada análise integral por metadados. Não extrapolar relações INDGER/IBGE para vigência/exclusividade municipal ou atendimento do imóvel.
