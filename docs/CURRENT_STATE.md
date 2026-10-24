# Estado atual — EletroProjeto 0.15.0 / motor 0.8.0

## Escopo, dados e serviços

Uso LOCAL; publicação/CI hospedado/impressão física/backup externo fora do trabalho atual. API/frontend0.15.0, motor0.8.0, JSON1.3, schema0006. Nenhuma fórmula, regra validada ou potência de catálogo alterada.9projetos (8ativos/1lixeira),30históricos e8revisões técnicas: todas as colunas idênticas ao checkpoint `.checkpoints/20261023T231538279667Z`. QA em bancos isolados.

API atualizada/reiniciada PID833563/sessão7759,localhost8000; Next existente PID572313/localhost3000 preservado. Smoke real abriu guia e diagrama, fonteSVG1080×720,sem overflow390px/pageerrors. Conferir processos ao retomar. Git local revisado e checkpoint final só confirmados após execução; ponteiro `.checkpoints/latest.json`, sem novo commit apenas pelo caminho.

## Biblioteca técnica integrada

- As duas pastas recebidas em references/elétrica e references/normas tinham3.856arquivos e13.851.788.079bytes. Foram lidos/inventariados também todos os membros dos5ZIPs;6.231entradas e2.395objetos únicos,8.546.299.070bytes. Todos os bytes únicos retidos por SHA-256; ZIPs redundantes substituídos por membros e inventário. Primeira e última verificação integral aprovadas. Pastas de entrada excluídas somente no final via verify--remove-inputs,conforme pedido; Energisa anterior preservada.
-2.281documentos:2.244PDFs,27guias,6modelos/checklists,4diagramas.83.424páginas PDF+37unidades didáticas=83.461.80.995com texto extraído;2.466sem texto extraível.3.788registros de fontes:310falhas,83não-PDF,5inválidos/cifrados na coleta anterior,27links e3.363registros de PDF recebido. Estrutura válida não equivale a revisão técnica.
- Migração0006 cria knowledge_documents/pages/sources com SQLAlchemy portável. Busca literal normalizada (acentos/caixa), filtros e paginação; leitura por páginas, busca dentro do documento, fontes e arquivos originais. Respostas tardias canceladas/ignoradas, sem resultado antigo sob filtro novo. Downloads pendentes não contados como documentos locais. Nenhuma gravação de projeto ao consultar.
- Biblioteca técnica no aside; guias/modelos com formatação segura, SVGs como imagem sem executar scripts, PDFs abertos em sandbox/CSP e caminhos por hash. Conteúdo local em references/library/objects fora do Git/ZIP de código; SQLite e inventários de auditoria entram no checkpoint. Não limpar library como cache. Administração/detalhes em references/README.md.
- Classificação preliminar:37educacionais,7históricos,2vigência-futura-candidata,1minuta,199fora-do-escopo e2.035pendentes de revisão. UF/grupo de catalogação não habilita associação territorial. Nenhuma nova regra normativa foi habilitada pela importação. Leitura automática de páginas não constitui revisão semântica humana integral; OCR não realizado.

## Verificações desta entrega

354backend+85subtestes;6novos testes repetidos após acabamento do importador.92frontend;17E2E completos e repetição dirigida da biblioteca após formatação/leitura/fontes.1E2EHTTPS de duas contas aprovado.99API/auth/biblioteca PostgreSQLQA em schemas isolados; migração0006/checagem aprovadas em SQLite temporário e PostgreSQLQA. Tipos/contratos/lint/formatação/buildwebpack/Ruff aprovados.15scripts continuidade/manutenção aprovados, inclusive exclusão dos objetos e inclusão dos inventários no ZIP. Windows/leitor de tela real/OCR não executados nesta entrega.

Consultas locais medidas:chuveiro0,714s,DR0,157s,NDU0,166s; medição pontual,sem promessa universal. Capturas QA e reais em/tmp/eletroprojeto-library-real-{1440,390}.png. Originais protegidos por hash,docs/contratos/código revisados,sem push.

## Funcionalidades anteriores preservadas

Início com aside e aparência antiga restaurada; não voltar a ocultá-lo. Equipamentos compactos, três cabeçalhos estáveis ao abrir painéis. Salvamento manual/autosave após primeiro envio, idempotência no POST, PUT sem mudanças sem nova versão/histórico, drafts250ms+flush e recuperação sem envio, conflitos guiados, biblioteca leve de projetos e checkpoints atômicos/reutilizáveis preservados. Catálogo persistente e NDU7.0 d1–d5 em escopo Energisa Sul-Sudeste/SP residencial≤75kW continuam com revisão explícita. Selecionar concessionária não basta.

## Próximas prioridades locais

Revisão técnica documental específica antes de novas regras; dimensionamento de circuitos/proteções/queda/padrão, geometria/localização e associação territorial oficial completos continuam pendentes. Não declarar conformidade final. Usar acervo como evidência de pesquisa,com edição/cláusula/condições/exemplos/testes,conforme AGENTS. Referências rastreáveis e limites em standards.md/roadmap/KNOWN_ISSUES. Retomar lendo docs e continuity.py retomar; backup final em latest.json após verificação real.
