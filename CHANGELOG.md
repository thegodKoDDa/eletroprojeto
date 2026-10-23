# Histórico de alterações

## 0.14.1 — 23/10/2026

- Corrigido deslocamento dos botões de equipamento ao abrir opções: cabeçalhos permanecem na primeira linha, conteúdo expandido abaixo em largura completa, inclusive com os três painéis abertos.

- Correção posterior solicitada pelo usuário: aparência antiga do início restaurada, com sidebar sempre presente, marca/logo na lateral, cartões e espaçamentos originais. Compactação das outras telas mantida.

- Tela inicial sem barra lateral; marca, logo, saída da conta e rodapé preservados. Navegação lateral aparece ao entrar em criação, biblioteca ou lixeira; edição mantida ao voltar.
- Espaçamentos e controles mais compactos. Configurações avançadas, consumo mensal e referências dos equipamentos agrupados em disclosures menores com quebra responsiva, sem retirar conteúdo.
- Regressão:348backend+85subtestes,92frontend,16E2E,1E2EHTTPS, contratos/tipos/lint/formatação/build e Alembiccheck aprovados. Sem mudanças de dependências, dados, fórmulas ou migrações.

## 0.14.0 — 23/10/2026

- Biblioteca SQL leve, busca compartilhada por nome/município, projeto completo só ao abrir; listagem real328.785→2.827bytes (-99,14%).
- Salvamento idêntico sem nova versão/histórico e primeiro POST idempotente; resposta perdida/recarga preservam rascunho e evitam duplicação. Serialização por snapshot e escrita local agrupada com flush na saída.
- Checkpoint publicado atomicamente, hashes em blocos/dump sem retenção em RAM, reutilização de ponto idêntico após restauração completa, latest.json estável e retomada compacta. Fluxo de encerramento com um commit seguido do checkpoint, sem ciclo documental extra.
- Doctor/limpeza com simulação, allowlist e manifesto, modos privados corrigidos; cerca49,7MB de gerados removidos, dependências e checkpoints únicos mantidos. Wrappers Windows testados em ambiente isolado.


## 0.13.1 — 23/10/2026

- Polimento geral: títulos das etapas, formulários, seleções, checkboxes, disclosures, botões, bordas, raios, espaçamentos, hover/foco e estados desativados.
- Salvamento automático visível com estado e explicação; observações maiores, sempre visíveis e com contador. Comportamento de salvamento preservado.
- Mais ações alinhado, com ícones, estado aberto e fechamento por clique fora/Escape; agrupamento de avisos acessível corrigido.
- Indicador Next de desenvolvimento retirado para não sobrepor controles locais. Motor0.8.0, normas e dados preservados.


## 0.13.0 — 23/10/2026

- Demanda NDU-0017.0 d1–d5 integrada ao inventário do projeto, com classificação e revisão explícitas, reservas e confirmações de escopo/ausências.
- Revisão vinculada ao hash do inventário; mudanças invalidam a confirmação e bloqueiam resultado/exportação desatualizados. Sem inferência automática de grupos.
- PDF/JSON1.3 com inventário, demanda, memória por grupo/faixa, declarações e limites. Projetos legados preservados; sem migração ou mudança de fatores.
- Escopo local definido pelo usuário: publicação/CI hospedado, impressão física e backup externo retirados das tarefas atuais.


## Organização de arquivos — 23/10/2026 (sem alteração de versão)

- Referências normativas fora da raiz, revisões antigas em docs/history e índices de documentação/referências. Hashes dos PDFs preservados.
- Removidos caches regeneráveis e marcadores de download; preservados dados, instalações, backups e serviços.
- Estado atual separado dos registros históricos; README e pendências corrigidos quanto a lint, autenticação, PostgreSQL e Windows já implementados/verificados.


## 0.12.0 — 23/10/2026

- NDU-0017.0 fornecida pelo usuário revisada e registrada por arquivo/hash;6.3 mantida apenas como referência histórica substituída. PDFs não incorporados ao Git/ZIP de código.
- Novo método API parametrizado de demanda residencial individual Energisa Sul-Sudeste/SP, d1–d5, tabelas5–8/10, faixas cumulativas, simultaneidade, reserva e memória por grupo/faixa; Decimal sem arredondamento intermediário.
- Grupos especiais/centrais/escopos não suportados retornamnull; ausências precisam ser declaradas. Sem classificação automática dos projetos, potências presumidas, mudança de catálogo ou dimensionamento final.
- Contratos e descoberta de métodos regionais atualizados. Motor0.7.0 rastreia a nova matemática; projetos/históricos preservados.

## 0.11.0 — 23/10/2026

- Recuperação de rascunhos locais sem envio automático, slots independentes e separados por conta; falhas de armazenamento informadas. Conflito409 pausa autosave, mantém a edição e oferece cópia independente ou versão do servidor.
- Sessões revogáveis com Argon2, HTTPS, cookie protegido, CSRF e isolamento por proprietário; administração local de contas sem senhas em argumentos. Projetos legados preservados e sem atribuição automática.
- Catálogo persistente em revisões imutáveis, independente dos snapshots dos projetos; migrações0004/0005 não destrutivas. PostgreSQL real e backend Windows testados.
- Workflow CI ampliado para Ubuntu/Windows/PostgreSQL, contratos, qualidade, E2E e build sequenciais; Git inicializado. Rotina de backup GPG com destino explícito e teste de restauração, ainda sem cópia externa real.
- Motor/normas e cálculos existentes preservados. Demanda, dimensionamento e verificação física/territorial completos continuam em revisão; não foram habilitados por suposição.

## Encerramento de sessão — 22/10/2026 22:56:21 -03

- Código 0.10.1, projetos e históricos preservados; documentação de continuidade atualizada e verificações de banco/serviços/backup realizadas. Sem mudança funcional, exclusão de dados, migração, commit ou push.

## Novo exemplo residencial — 22/10/2026

- Residência do CODEX criada pela interface e salva separadamente: apartamento70m², oito ambientes, referências oficiais de equipamentos e hipóteses de uso registradas. Projetos anteriores preservados; sem alteração de código ou cálculos.

## 0.10.1 — 22/10/2026

- Revisão de uso real da Casa do Codex: restauração de referência preserva consumo/horários; variantes documentadas selecionáveis sem sobrescrever potência manual válida.
- PDF corrige centavos, títulos isolados no caso revisado, características da casa e contagem de cadastros/unidades; identifica potência máxima e limites da estimativa. JSON 1.2 acrescenta vínculo por IDs e corrige a indicação de potência personalizada.
- Hipóteses do projeto esclarecidas pela interface; valores e demais projetos preservados. Motor, regras normativas, catálogo e migrações mantidos.

## Projeto demonstrativo — 22/10/2026

- Casa do Codex criada e salva pela interface real: nove ambientes, equipamentos, características, uso mensal e previsão luz/TUG; hipóteses de consumo e tarifa identificadas. Projetos anteriores preservados.

## 0.10.0 — 22/10/2026

- PDF/JSON ampliados com consumo/custo/tarifa/cobertura, consumo por ambiente/categoria, equipamentos e uso considerado, pendências objetivas e orientação concisa para atendimento da distribuidora. Medidas/resultados anteriores e nomes dos arquivos preservados.
- Preparo único no backend e endpoint reports/json com os mesmos guards de snapshot/versão do PDF, JSON 1.1 aditivo e indentado; frontend usa um único fluxo de download. Cabeçalho no-store sem duplicação e progresso adequado aos dois formatos.
- Potência parcial, ausência e zero explícitos, valores manuais e consumo informado prioritário preservados. Motor 0.6.0 sem alteração de fórmulas/normas; relatório não aprova ligação nem substitui dimensionamento final.

## Polimento de interface após 0.9.0 — 22/10/2026

- Revisão visual de aside, navegação, cabeçalhos, seções/cards, formulários, ações, biblioteca/lixeira, resultados e rodapé; tokens de cores e proporções consistentes, foco/hover/áreas de toque e responsividade.
- Adicionar ambiente com destaque e barra sticky; nova ação Duplicar ambiente preserva dados manuais e snapshots, renova UUIDs, cria nome único e posiciona o foco na cópia.
- Referências dos equipamentos reorganizadas no celular; sem alteração de regras, API, migrações ou projetos existentes.

## 0.9.0 — 22/10/2026

- Pesquisa ampliada em IPAAM/AM, acervo docente PUC Goiás e diretrizes oficiais da Polícia Federal; critérios residenciais cotejados com correção de 2008. Demanda Energisa continua pendente por acesso integral/tabelas não conferidos.
- Motor 0.6.0 implementa previsão residencial quantitativa de iluminação e TUG, com Decimal, condições por ambiente, testes independentes e de fronteira. Seleção explícita; externo/outro sem inferência.
- API tipada, resultados por ambiente, avisos corrigíveis e PDF/JSON integrados. Valores manuais e histórico preservados, previsão VA separada da instalada W. Não há certificação integral, proteção ou dimensionamento final.

## 0.8.0 — 22/10/2026

- Pesquisas normativas integradas à API/registro técnico com evidências, fontes, finalidade, verificações pendentes e cobertura por distribuidora/UF; contratos gerados.
- Correções do usuário separadas das limitações do sistema. Removidos alertas normativos repetidos, cards sem resultado e exigências de campos para operações indisponíveis.
- Fonte da Energisa não é aplicada a outra distribuidora; dados antigos e histórico preservados. PDF/JSON distinguem resultados normativos indisponíveis de falhas de cadastro.
- Motor 0.5.1 altera diagnósticos/metadados, sem novas fórmulas ou fatores normativos habilitados. Falta acesso às fontes completas autorizadas para liberar iluminação/TUG/demanda.


## 0.7.0 — 22/10/2026

- Consumo mensal por horários explícitos ou etiqueta/medição e estimativa de custo por tarifa informada, com cobertura independente e relatórios resumidos. Motor 0.5.0, sem regra normativa habilitada.
- Formulários mais contextuais; removidos inputs informativos sem efeito nos cálculos atuais, preservando os dados já salvos. Matriz campo a campo em docs/audit.md.
- Correções de estado/renderização, foco, links de referência, hover e proteção por headers; proteção de resultados atuais mantida.
- ESLint/Prettier/Ruff configurados e fonte formatada; migrações históricas intactas. Dependências de teste vulneráveis corrigidas; auditorias npm/Python consultadas.
- Plano de segurança/recuperação atualizado, cache e metadados gerados excluídos dos novos checkpoints.


## 0.6.1 — 22/10/2026

- Removidos Recentes do aside e sua consulta inicial. Biblioteca/lixeira passam a telas principais, sem impedir navegação lateral.
- Foco, indicação da edição atual e navegação por teclado revisados; filtros reiniciados entre biblioteca e lixeira.
- Estados vazios/erro/carregamento e paginação melhorados, incluindo exclusão do último item da página.
- Ações e menus bloqueados durante operações, mensagens de andamento e salvamento de versões anteriores mais precisas.
- Polimento responsivo, alvos de toque, nomes longos e menu expansível sem corte no aside. Motor 0.4.3 e dados preservados.


## 0.6.0 — 22/10/2026

Aplicação/API/frontend MINOR; motor 0.4.3 e migrações 0001–0003 preservados.

- Tela inicial com Novo projeto, biblioteca e lixeira; continuidade da edição ao voltar ao Início.
- Navegação e ações organizadas no aside; memória de cálculo somente dentro do projeto. Layout responsivo e ícones SVG locais.
- Cálculos não são solicitados na tela inicial; debounce, cancelamento, autosave, versões e exportações preservados.
- Biblioteca permanece aberta após erro/cancelamento de abertura; feedback no diálogo; recentes ativos independentes da lixeira.
- Recuperação de falhas de inicialização com nova tentativa sem perder edição; falhas de rede traduzidas.
- Playwright isolado em portas 3010/8010, diretório de build e banco próprios; cobertura de navegação, duplicação, restauração, exclusão definitiva e JSON.
- Importação da versão corrigida, eliminando o aviso de build anterior.


## 22/10/2026 — revisão de cálculos, motor 0.4.3

- Corrente calculada diretamente pela expressão P/(V×FP), evitando arredondamento intermediário de VA; mesma condição para trifásico equilibrado.
- Referência do ventilador Mondial VSP-40-W corrigida de 60 para 140 W conforme fabricante; snapshots antigos e valores manuais preservados.
- Categoria manual de AC preservada ao escolher automaticamente uma referência compatível com nova capacidade.
- Documentação da API distingue cálculos disponíveis de regras normativas pendentes; edição NBR 5410 identificada no catálogo ABNT sem habilitar cláusulas não conferidas.
- Ampliação da cobertura de defaults, recálculos, limites e preservação do catálogo/histórico.


## 22/10/2026 — dimensões e horário de Brasília

- PDF/JSON incluem área construída, área/perímetro por ambiente e pontos de luz/TUG cadastrados.
- Emissão, interface e datas públicas da API usam horário de Brasília; instantes internos preservados em UTC.


## 22/10/2026 — exportações simplificadas

- PDF e JSON apresentam resultados gerais, ambientes/categorias, estados normativos e observações, sem fórmulas ou referências.
- Nome dos arquivos acompanha o projeto, com suporte a acentos e limpeza de caracteres inválidos.
- Preservadas verificações contra resultados desatualizados, matemática e dados persistidos; JSON exportado passa a ser resumo, não snapshot completo.

## 0.5.0 — 22/10/2026

Aplicação/API/frontend MINOR; motor 0.4.2 com diagnósticos mais objetivos, sem fórmulas novas.

- Ações principais reagrupadas; biblioteca/lixeira em diálogo próprio, data de exclusão e exclusão definitiva com versão/confirmacão.
- Resultados reorganizados em resumo, memória e pendências; estimativas e edições mantêm proveniência sem avisos genéricos por equipamento.
- Parâmetros informativos separados e exportados no PDF; remoção do controle de tensão geral sem efeito atual e de dimensões fictícias em novos ambientes.
- Regressões de computador manual, recuperação/purge, ações, cache da lixeira e layout documental. Limites e resultados em `docs/review-0.5.0.md`.

## 0.4.0 — 22/10/2026

Aplicação/API/frontend MINOR compatível; motor 0.4.0 → 0.4.1 para corrigir o estado da concessionária ausente, sem mudar fórmulas.

- Proteção contra resposta antiga da lista inicial; Novo projeto/Salvar como novo explícitos e autosave pausado ao renomear.
- Três recentes, consulta completa com pesquisa/ordenação/paginação e ações por ID/versão.
- Navegação ativa por hash; recomendações por ambiente com busca geral.
- Card de demanda consome estado real, separando falta de concessionária de regra não validada. Avisos internos explicam dependência técnica; erros de gravação incluem alvos de campo.
- Referências oficiais Midea para 18.000, 24.000 e 30.000 BTU/h; preservação de parâmetros manuais e nova consulta de referência ao mudar capacidade/tipo/compressor.
- Detalhes, fontes, testes e limitações em `docs/review-0.4.0.md`.

## 0.3.0 — 21/10/2026

Versão MINOR compatível de aplicação/API/frontend; `/api/v1` preservado, motor 0.4.0 inalterado.

- Projetos com duplicação/exclusão na listagem, recuperação e preservação do histórico; migração 0003 não destrutiva e backup verificado.
- Adição de ambiente sticky com foco no nome, salvamento automático após primeiro salvamento e preservação de edições concorrentes.
- Apresentações simples/técnica dos mesmos resultados e separação de componentes/serviços concentrados.
- Limite HTTP real de 4 MiB, CORS explícito, no-store/nosniff e testes de proteção.
- Workflow de testes/contratos/build e documentação consolidada. Detalhes, resultados e impedimentos em `docs/review-0.3.0.md`.

## 0.2.0 — 21/10/2026

Versão MINOR compatível da aplicação/API; rotas permanecem em `/api/v1`. Motor de cálculo: 0.3.1 → 0.4.0. Frontend, pacote Python, OpenAPI, health e apresentação usam 0.2.0.

- PDF organizado em oito seções, com células posicionadas, sombreamento discreto, cabeçalhos/legendas repetidos e blocos mantidos juntos. Fontes numeradas uma vez; normas não executadas não aparecem como referências aplicadas.
- Operações matemáticas idênticas são demonstradas uma vez e vinculadas às cargas por C1/C2 etc. Agrupamento documental não é agrupamento normativo de demanda.
- Apresentação arredondada usa aproximação; entradas de seis casas permanecem integrais em igualdades. Valores internos e exportação JSON conservam precisão.
- Avisos tipados por gravidade, localização, resultado afetado e solução. Ação Corrigir informação abre detalhes, destaca e foca o campo. Erros HTTP 422 também oferecem diagnóstico localizado; entradas brutas/contextos internos não são repetidos na resposta.
- Requisitos por operação: W, VA, corrente e previsão normativa. Área construída, pavimentos, tipo e tensão de referência podem permanecer desconhecidos no rascunho. Ausência de FP/tensão não bloqueia W.
- Edição manual da potência do ar-condicionado fica registrada e protegida mesmo como estimativa; restaurar reaplica a referência. Troca de tensão não altera potência e divergências de variante/faixa documentada geram alerta técnico.
- Versões e última comunicação aparecem discretamente no rodapé; documentação API agrupada por módulo. Novos campos preservam entrada de projetos antigos através de padrões explícitos e normalização antes do cálculo.
- Verificações: 95 testes backend e 34 frontend aprovados, além de 11 subtestes; TypeScript, geração OpenAPI, compileall e Alembic check aprovados. Build, lint e navegador têm limitações registradas em `docs/review-0.2.0.md`.

## 0.1.0 — implementação anterior

Base de projetos/cargas, catálogo referenciado, cálculos matemáticos, histórico técnico, exportação JSON/PDF e validações por campo. Verificações históricas constam nos relatórios anteriores. Essa versão ainda apresentava PDF com tabelas de caracteres e avisos com pouca orientação.

## 22/10/2026 — continuidade do desenvolvimento (sem alteração da versão funcional)

- Adicionadas memória duradoura, estado atual, histórico de sessões e pendências com fontes principais reaproveitadas.
- AGENTS estabelece leitura inicial, atualização contínua, encerramento e retomada.
- Scripts locais criam arquivo de código com hashes e backup SQLite consistente, verificam restauração isolada e coletam Git/dependências; wrappers PowerShell opcionais.
- Backups privados/exclusões no .gitignore; nenhuma alteração de matemática, dados, UI ou schema.
