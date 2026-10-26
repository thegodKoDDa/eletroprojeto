# Memória permanente — EletroProjeto

## Produto e escopo

Estimativa de consumo elétrico residencial com três apresentações escolhidas na abertura: **leigo, profissional e exploração**, para moradia pronta ou planejada. Todos os recursos continuam disponíveis. Preservar produto, dados e identidade visual. Percurso principal: **01 Projeto → 02 Ambientes → 03 Conferência**. Início mantém sidebar/marca e três cartões. Circuitos, entrada e demanda continuam opcionais depois dos resultados. Leigo/exploração os mantêm recolhidos; profissional destaca o grupo, os parâmetros e os atalhos sem tornar os estudos obrigatórios.

Refinamento0.22.1: navegação recolhível no celular/tablet para leigo/profissional, ações de projeto visíveis, alternativas de consumo agrupadas e atalhos que abrem os detalhes antes de focar. Preservar horários ao informar/limpar kWh, inclusive zero.

Consumo/custo recebem destaque, tarifa fica visível e uso dos aparelhos é explícito. Medidas/pontos, dados extras, potência, memória e previsões ficam em detalhes. Catálogo sugere referências, não potências universais; valores manuais válidos prevalecem. A biblioteca técnica serve para melhorar utilidades verificadas, não para exigir novos formulários ou presumir dados.

Uso local. GitHub público distribui a fonte/histórico; dados privados continuam locais; implantação do site, CI hospedado, impressão física e cópia externa de dados privados continuam fora do escopo. O agente executa rotinas de terminal, sem delegá-las ao usuário. Autorização de manutenção/sincronização revisada em24/10/2026 está no AGENTS; não repetir perguntas para essas rotinas.

## Visual e ajuda progressiva — 0.23.0

Usar tokens compartilhados, PageHeading/SectionHeading/Feedback e estados com texto/símbolos além das cores. Superfícies neutras, controles de44px, cartões, tipografia do sistema e espaçamentos comuns em todas as telas; manter responsividade e teclado. Ajuda do leigo acompanha cinco tarefas e destaca automaticamente a próxima, sem roubar foco ou salvar por conta própria. Profissional tem atalhos explicados e acompanhamento opcional recolhido; exploração mantém organização com visual comum e ajuda opcional.

Progresso é derivado de entradas, limites da API e resultado atual; consumo zero válido. Conferência explícita vinculada ao digest/escopo em memória do Workspace, invalidada em edição diferente, nova abertura/projeto; não é histórico técnico nem conformidade. Atalhos de uso aguardam recálculo e erros levam ao campo da API. Não tornar guia obrigatório para salvar/exportar, nem completar normas pendentes a partir de campos preenchidos. Detalhes em forms-and-pdf e usage.

## Invariantes

- Um motor Python em `backend/app/calculations`, funções puras, Decimal, unidades explícitas e sem arredondamento intermediário. Frontend valida/formata; não replica fórmulas.
- W, VA, kWh, BTU/h e potência mecânica são distintos. Desconhecido/regra não validada é null com motivo, nunca zero fictício. Corrente por aparelho não dimensiona circuito. Não declarar conformidade final/aprovação da distribuidora.
- Regras novas exigem fonte oficial, edição, condições, cláusulas, limites, exemplos independentes e testes; registrar em standards/calculations. OCR/importação não habilita regra automaticamente.
- Preservar SQLite, migrações0001–0007, histórico e snapshots. Editar instância não muda catálogo global. Não resetar banco nem atualizar projetos antigos silenciosamente.
- Resultados antigos ficam ocultos para entradas novas, com debounce400ms, cancelamento/rejeição de respostas antigas e exportações vinculadas ao snapshot atual. Metadados não devem refazer matemática sem necessidade.

## Projetos e recuperação

Início, edição, biblioteca e lixeira são independentes; navegar mantém a edição na aba. GET summaries traz metadados; abrir busca payload completo. PUT idêntico na mesma revisão não gera versão/histórico. POST inicial com Idempotency-Key UUID permite repetir após resposta perdida sem duplicar; payload diferente retorna409. Preservar edições feitas durante o envio.

Autosave somente após primeiro salvamento manual, debounce1,5s; renomeação/conflito pausam. Falha não aparece como Salvo nem cria repetição infinita. Conflito409 permite copiar edição local ou carregar servidor preservando rascunho.

Rascunhos por conta/aba/slot em localStorage, escrita agrupada250ms e flush ao ocultar/sair/desmontar. Recuperar não envia automaticamente. Limpeza do navegador, outra máquina e término abrupto sem eventos limitam recuperação; SQLite/checkpoints não capturam dados ainda não enviados ao servidor.

Remover cargas/ambientes limpa associações atuais; histórico/catálogo permanecem intactos. Referências ausentes em projetos antigos têm reparo explícito. Revalidação compara edição salva e registra nova versão conscientemente, preservando entradas manuais. Histórico ordenado por versão resolve timestamps iguais.

PDF principal/JSON secundário incluem consumo, hipóteses, cobertura e pendências; JSON de relatório não é backup completo. Assinatura inclui circuitos/proteções/entrada. Horários públicos America/Sao_Paulo; armazenamento/checkpoints UTC.

## Motor e acervo

Versões e contagens atuais em CURRENT_STATE; fontes/condições em standards/calculations. NDU-0017.0 d1–d5 exige inventário/classificação/escopo e revisão vinculada por digest; somente residência individual Energisa Sul-Sudeste/SP até75kW. Na0.19.0,d6/d7/centrais têm parâmetros/fontes próprios revisados; dados ausentes ou ordenaçãoW/VA conflitante emd7 mantêm demanda nula; reservas saem da demanda, mas entram na instalada do limite. Não inferir grupo, distribuidora municipal, FP ou converter VA/BTU/energia em W.

Estudos condicionais de circuitos Cu/PVC70/A1/A2/B1/B2/C,mono ou tri equilibrado sem neutro (seções1,5–95mm² na0.19.0), proteção e entrada ESS220/127V/tabela16 permanecem limitados às condições documentadas; não equivalem a dimensionamento final universal. Sem inferir DPS, seletividade, geometria, ensaios ou parâmetros do produto.

Acervo local:2.196objetos técnicos,2.082documentos/51.324unidades/3.788fontes. OCR recuperou963páginas,97vazias; nenhuma falha. Método/confiança separados de validação normativa.199objetos sem utilidade foram descartados com autorização/auditoria anterior; não reimportar inventário histórico nem tratar `library/objects` como cache. Originais Energisa7.0/6.3 e quatro JSONs de auditoria permanecem locais. Revisão humana integral do acervo não concluída.

## Estrutura e continuidade

Backend: REST/main, schemas/contratos, projects/histórico, database/ORM, reports, calculations. Frontend: page orquestra; componentes projects/equipment/calculations/layout e hooks em lib. Pesquisa explícita do catálogo considera todos os equipamentos encontrados, sem excluir pelo ambiente; sugestões ficam para busca vazia. Pendências/resultados de consumo identificam ambiente/aparelho, com atalhos individuais e para tarifa. Descrições de consumo e tarifa são vinculadas aos controles; validação com leitor de tela real foi explicitamente descartada pelo usuário em25/10/2026 e não deve voltar como pendência sem novo pedido. Preservar acessibilidade implementada e testes automáticos/teclado. PageHeading/SectionHeading/Feedback/Pagination e tokens CSS padronizam páginas,seções,avisos e navegação; reutilizar esses padrões. Erros de exportação preservam notificações localizadas como no salvamento; leitura/fontes possuem retry sem perder filtros. `use-workspace-resources` carrega recursos independentemente; cliente centraliza erros/cabeçalhos/CSRF. Modo local loopback e autenticação remota/HTTPS/isolamento já implementados são preservados.

Fonte de dependências são manifests/locks. Reutilizar `.venv`, `.venv-windows` e node_modules; não reinstalar por hábito. Contratos somente por `npm run types:sync`. Não rodar build e E2E simultaneamente; QA usa bancos/portas e diretórios próprios.

GitHub: `https://github.com/thegodKoDDa/eletroprojeto`, origin/main, público por autorização explícita em 26/10/2026, Actions desativado. Encerramento autorizado envia commits revisados apenas para esse destino após conferir destino e visibilidade pública; sem force-push ou merge automático. Credencial existente via Git Credential Manager do Windows, sem token em URL/arquivo/log. Código/docs no GitHub; banco, checkpoints, `.env` e originais do acervo continuam locais.

Rotina em AGENTS e detalhes em continuity.md. Retomar lê AGENTS/CURRENT_STATE/esta memória e executa continuity retomar; documentos históricos são consultados conforme necessidade. Encerrar atualiza docs uma vez, testa proporcionalmente, faz commit revisado e executa encerrar --sync. Sem rede, checkpoint local é preservado e sincronização fica pendente. Não criar commit extra pelo caminho do ponto; consultar `.checkpoints/latest.json`.

Checkpoints mantêm fonte/SQLite/bundle, hashes e restauração completa isolada. Bancos idênticos compartilham armazenamento por hardlinks, sem apagar pontos; ausência de suporte mantém cópias independentes. Não editar snapshots; restaurar para arquivo novo. Marker não substitui verificar. Clean/doctor/compact só quando necessário, preservando dados, referências, instalações úteis e recuperação. Exportador GPG fora de uso retirado; versões antigas estão no Git. POSIX0700/0600 nos privados; não mudar política global/ACL Windows indiscriminadamente.

## Ampliação0.19.0 / motor0.10.0

Demanda especial, circuitos/fases e geometria têm limites/fontes emstandards/calculations; não duplicar tabelas aqui. Parâmetros/fontes especiais participam do digest; dados de classificação anterior podem ser preservados, mas a memória usa somente a fonte do grupo atual. W/FP cadastrados não são substituídos por valores normativos. Localização usa envelopes completos e apenas o arranjo de chuveiro dafigura18 sem piso-boxe/rebaixo/delimitação, piso único e sem divisórias intermediárias; não amplia automaticamente a banheiras/cabines ou conformidade final.

Coleta territorial original ANEEL121feições preservada emreferences/territory,ignorada noGit e incluída nocheckpointlocal; não é cache dispensável. app/territory consulta por coordenadasSIRGAS2000 comhash conferido e períodos explícitos. A camada intituladaATUAL inclui registros encerrados/sucessores sobrepostos; não inferir sucessão, vigência jurídica atual, atendimento de imóvel ou mapeamento municipal por essa nomenclatura. Busca opcional não salva coordenadas nem troca distribuidora. Alterações de coordenadas cancelam/ocultam resposta anterior. Sem rede durante consulta; nova coletaCLIcria diretório novo sem apagar originais.

## Apresentação e navegação do repositório

README apresenta o produto e a prévia real; instruções de agente e detalhes da instalação local ficam nos documentos responsáveis. `docs/setup.md` e `docs/usage.md` atendem instalação/uso, `CONTRIBUTING.md` reúne desenvolvimento e testes, e `docs/README.md` organiza os caminhos. Descrição/tópicos do GitHub foram alinhados ao produto usando Minecoord como referência de apresentação; privacidade e Actions desativado preservados.

Revisões anteriores de auditoria/formulários/expansão inicial estão em `docs/history`, com índice e conteúdo preservados. `docs/audit.md` e `docs/forms-and-pdf.md` descrevem o estado atual e apontam para o histórico. Não voltar a apresentar registros antigos como comportamento vigente nem colocar logs de sessão na página de apresentação. Imagens em `docs/assets` contêm somente interface e dados fictícios; manter essa condição ao atualizá-las.

## Distribuição pública — 0.20.0

Usuário autorizou explicitamente tornar `thegodKoDDa/eletroprojeto` público e preparar formas de uso em 26/10/2026. Visibilidade pública passa a ser a condição do sincronizador; destino, main limpa, revisão de arquivos, ausência de divergência e sem force-push continuam obrigatórios. Histórico preservado. Actions permanece desativado; não confundir publicar código/release com hospedar o site ou enviar dados.

ZIP de fontes com iniciadores Windows/Linux/macOS requer Python/Node; Docker contém runtimes e volume SQLite próprio. Não prometer `.exe`, `index.html` independente ou teste nativo Windows/macOS não realizado. Licença ISC do código original; componentes preservam avisos próprios. Iniciadores recusam portas ocupadas e reutilizam dependências compatíveis; não tocam serviços existentes. Native legado usa backend/eletroprojeto.db se presente, cópia nova usa data/eletroprojeto.db, e --data-dir escolhe outra instalação. Nunca remover volume/pasta de dados para atualizar.

Pacote é gerado de commit por scripts/package_release.py, com manifesto/hash e sem arquivos privados. Contexto Docker é uma lista de inclusão; não afrouxar a exclusão de banco/acervo/credenciais. Código compilado sem bloqueios novos; biblioteca/território ausentes permanecem pendentes, não zero. Continuidade de dados e restrições normativas anteriores permanecem.


## Revisão0.21.0 / motor0.11.0

Usuário pediu revisar e resolver pendências, ignorando as já resolvidas/descartadas. Revisão/estado por item em KNOWN_ISSUES; fontes/condições em standards e matemática em calculations. Circuitos acrescentam XLPE/EPR90 e D/E/F/G sob condições explícitas; D distingue temperatura do solo e bloqueia outros arranjos, G somente três fases espaçadas/circuito único. Não liberar alumínio residencial ou neutro/desequilíbrio/harmônicas por analogia. Queda nos novos casos exige impedância documentada própria; valores de fixtures não são sugestões. Divergência do manual C/90°C/10mm² resolvida pela tabela normativa, sem modificar o original.

DPS/seletividade são comparações documentais condicionadas a estudo/produtos/fontes, sem seleção ou análise integral automática. Catálogo ABNT já identifica NBR5419:2026/VC2026; não usar versões antigas como validação da edição atual. Revisão humana integral do acervo e inspeção/ensaios no local não foram executados pelo agente e não podem ser atestados por importação/simulação.

Relações municipais INDGER/IBGE disponíveis por código oficial, preservando múltiplas empresas e mês próprio por CNPJ; atrasos/linhas sem município/código não associado ficam explícitos. Não confundir declaração mensal com vigência jurídica/exclusividade ou atendimento do endereço. Coletas locais em references/municipalities, ignoradas e preservadas; o coletor cria novo diretório, não altera banco. Não alterar o estado jurídico dos IDs internos nem a seleção manual automaticamente. Releasev0.20.0 com três arquivos foi confirmada publicada; esta revisão não criou novo pacote/release.


## Perfis de apresentação — 0.22.0

Pedido explícito do usuário: tela inicial com USUÁRIO LEIGO, USUÁRIO PROFISSIONAL e ESTOU APENAS DANDO UMA OLHADA, preservando todos os recursos nas três apresentações. Motor0.11.0, cálculos, contratos de dados e pendências normativas não mudaram. O perfil é preferência de apresentação, não habilitação profissional nem permissão de acesso.

ExperienceBoundary fica dentro de AccessBoundary, isolada pela conta. sessionStorage por conta/aba lembra a escolha ao recarregar; aba nova começa na escolha. Falha do armazenamento não bloqueia a seleção. Alterar perfil abre diálogo com teclado/fechamento por Escape, mantendo Workspace montado: edição, rascunhos, salvamento, referências e resultados permanecem. O perfil não entra no projeto, assinatura de cálculo ou exportação; trocar perfil não dispara nova matemática.

Leigo destaca requisitos recebidos da API e dados recomendados de consumo/custo, abre Consumo mensal e oferece caminho de três passos. Profissional destaca dados elétricos/medidas/memória e atalhos para todos os estudos, mantendo-os condicionados. Exploração preserva início com lixeira, controles e recolhimentos originais. Biblioteca substitui o atalho principal da lixeira nos novos perfis; lixeira permanece na navegação. O seletor redundante de apresentação nos novos perfis vira controle de detalhamento; exploração mantém o original. Revisão dos grupos de opções em forms-and-pdf; não apagar funcionalidades de recuperação/dados sob pretexto de simplificar.
