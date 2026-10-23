# Campos obrigatórios, avisos e PDF — 21/10/2026

## O que mudou

- `backend/app/validation.py` define finalidade, condições e limites básicos dos campos. `GET /api/v1/validation/requirements` expõe metadados tipados pelo OpenAPI. A revisão técnica passa a incluir estes requisitos.
- `Field.tsx` reutiliza os rótulos e controles existentes: asterisco vermelho, `required`, `aria-required`, `aria-invalid`, identificação e descrição de erro. Não executa fórmulas; só apresenta condições recebidas da API e verificações comuns de formulário.
- Valores válidos removem o aviso do próprio campo; apagar/invalidar faz o aviso retornar. Espaços não satisfazem texto obrigatório; zero só é aceito nas contagens e parâmetros em que faz sentido. Limites de números, inteiros e textos vêm dos metadados. Campos de preenchimento opcional conservam sua validação de faixa quando informados.
- Campos necessários a VA/corrente indicam a finalidade no asterisco e no aviso. Não são exigidos para somar W nem para salvar um rascunho. FP deixa de exigir preenchimento quando a hipótese resistiva é explicitamente adotada. Dados avançados permanecem recolhíveis, com indicação de pendências no resumo.
- `CalculationResult.field_issues` identifica caminho estável, campo, finalidade, mensagem e estado. Avisos normativos permanecem separados. Alertas antigos não são exibidos como atuais durante o recálculo.
- Área/perímetro podem ficar ausentes (`null`) em um estudo parcial; não bloqueiam a potência conhecida. Valores negativos continuam rejeitados. A documentação normativa não validada continua impedindo previsão normativa final, mesmo com todos os campos preenchidos.
- Correntes/VA não são produzidos para potência zero. Salvar potência zero como carga válida é rejeitado; ausência explicitamente desconhecida permanece permitida no rascunho. A matemática pura conserva zero nos contextos em que é válido.
- Cancelamentos de consulta a requisitos/distribuidoras deixam de criar avisos falsos no Strict Mode; respostas canceladas não atualizam o formulário.
- Campos de pontos de luz/tomadas vazios deixam de virar zero silenciosamente. Identificação/área construída também participam da revalidação das pendências; debounce e cancelamento permanecem ativos.

## Obrigatoriedade por finalidade

- **Salvar/identificar:** nome do projeto, município, área construída, tipo de residência, pavimentos e tensão de referência; nome de ambiente/carga, categoria, quantidade e fonte. Valores padrão válidos já preenchem parte desses campos. Estado identifica localização.
- **Previsão normativa:** tipo, área, perímetro e contagens do ambiente; concessionária para procedimento de demanda. Informações preenchidas não validam a norma pendente.
- **Potência instalada:** quantidade e entrada elétrica positiva; em modo mecânico, saída mecânica e rendimento do motor.
- **VA:** potência e FP conhecido ou hipótese resistiva explicitamente declarada.
- **Corrente:** requisitos de VA, tensão nos terminais/linha e configuração de fases conhecida.
- **Opcionais para a soma em W:** BTU/h, marca/modelo, tamanho de tela, energia mensal, correntes de ficha, potência de saída do micro-ondas. BTU/h não substitui potência elétrica.

## Exportação PDF

A ação principal é **Exportar PDF**; JSON permanece como ação secundária. `POST /api/v1/reports/pdf` recebe entradas, hash esperado e versões esperadas do motor/registro. O backend valida e recalcula as mesmas entradas, rejeitando divergências com HTTP 409. Não aceita resultados técnicos enviados pelo navegador. Quando a interface está exatamente igual a um projeto salvo, a API também confere seu ID, versão e conteúdo; alterações não salvas são identificadas como tal.

Atualização de 22/10/2026: PDF e JSON exportam um resumo de resultados: identificação, totais W/kW e VA/kVA, iluminação nominal incluída, potências conhecidas por ambiente/categoria, situação das previsões normativas e observações do projeto. Sem quadro detalhado de equipamentos, fórmulas, referências, hashes ou memória de cálculo. Esses dados continuam disponíveis na aplicação e no histórico persistido. JSON usa chaves em português, valores/unidades/estados e preserva null; não é cópia completa do projeto para restauração. O PDF apresenta até três casas decimais, com vírgula decimal; JSON conserva valores recebidos do motor sem cálculo ou arredondamento no frontend.

Os arquivos recebem o nome atual do projeto com extensão .pdf/.json; caracteres inválidos de caminho/controle são neutralizados. PDF via API inclui filename* UTF-8 para acentos. Estudos permanecem preliminares; totais incompletos e resultados normativos não disponíveis continuam explícitos. Exportar exige resultados atuais, e PDF conserva todas as verificações de snapshot/versão anteriores.

`backend/app/reports/pdf.py` é um renderizador A4 restrito a texto/tabelas, sem execução de HTML nem acesso à rede. Incorpora DejaVu Sans Mono e mapa ToUnicode para acentos, fórmulas e extração textual. A licença está junto da fonte, incluída no pacote Python. Glifos ausentes são representados pelo código Unicode visível, sem descarte silencioso. Textos quebram por largura monoespaçada; tabelas extensas repetem cabeçalho e continuam em novas páginas. A tentativa de instalar ReportLab não encontrou distribuição disponível neste ambiente; o serviço não depende dela.

O PDF identifica alterações posteriores ao início da exportação sem misturar os dados novos no documento já solicitado. A exportação não grava nem troca valores do catálogo/projeto.

## Arquivos afetados

Schemas, requisitos, cálculo de equipamentos/engine, registro técnico e rotas FastAPI; serviço PDF e fonte licenciada; componente reutilizável de campo; editor e página existentes; integração/API/hook; contratos gerados e testes. Sem migração de banco nesta alteração.

## Verificação

- Backend: **80 testes aprovados, 11 subtestes**; frontend: **29 testes aprovados**.
- TypeScript/typegen, OpenAPI, compileall e consistência Alembic aprovados.
- Testes verificam ausência/preenchimento/invalidação, campos condicionais, zero, resultados parciais, origem estimada, foco, cancelamento, JSON e PDF, versão salva, HTTP 409/422, texto Unicode, estrutura/xref, limites das páginas, 35 ambientes e tabela de 120 equipamentos. Valores esperados incluem 4 × 9 = 36 W e 120 × 4 × 9 = 4320 W calculados independentemente.
- Playwright tentado: API não conseguiu abrir porta 8000; fluxo não executado no navegador.
- Build Webpack tentado: falha ao interpretar saída do subprocesso TypeScript `--showConfig`. Typecheck direto aprovado.
- `npm run lint` tentado: projeto ainda sem script/dependência de lint disponível. Lint não aprovado.
- Não foi possível conferir visualmente o PDF em leitor/navegador neste ambiente. Testes de estrutura, extração e limites de layout não substituem essa conferência.

## Limitações preservadas

NBR 5410, tabelas de demanda e procedimentos específicos continuam pendentes de verificação; não há resultado normativo final. Autenticação para implantação pública permanece fora desta alteração. Não foi confirmado localhost ativo.

## Complemento — 22/10/2026: dimensões e fuso

PDF/JSON incluem área construída m²; por ambiente, área m², perímetro m, pontos de luz e TUG cadastrados. Ausências são indisponíveis/null, sem inventar dimensões ou previsão normativa. Emissão usa America/Sao_Paulo (Brasília); JSON identifica o fuso explicitamente. Biblioteca/lixeira e datas públicas da API usam o mesmo fuso. UTC permanece somente no armazenamento e identificadores técnicos de checkpoints para preservar instantes e ordenação.

## Revisão 0.7.0

Equipamentos comuns solicitam referência, quantidade e potência; tensão fica avançada e reaparece no básico quando requisitos de corrente são selecionados. Energia tem seção opcional própria por equipamento: consumo mensal unitário ou horas/dias sem padrões presumidos. Consumo mensal declarado prevalece, e horários válidos ficam desabilitados conservando seus valores; horários inválidos continuam corrigíveis. Tarifa opcional em Outros dados do projeto, sem padrão.

Removidos inputs de tela/tecnologia genérica/saída de micro-ondas/potência máxima/correntes informativas, preservando seus dados históricos no detalhe de origem. Não aparecem no PDF simplificado. Matriz individual e justificativas em audit.md.

PDF/JSON incorporam consumo mensal conhecido/estimado, custo pela tarifa informada e cobertura incompleta. Não incluem fórmulas/referências ou uma fatura simulada. Nome do projeto e fuso de Brasília preservados. Interface apresenta valores monetários com centavos; JSON preserva os valores do motor. Motor/referências/digest atualizados continuam exigidos antes do PDF.

## Diagnósticos separados — 0.8.0

A seção C mostra somente dados e alertas técnicos do projeto, com correção quando houver alvo. Pesquisas/limites ficam em Recursos normativos ainda indisponíveis, recolhido inicialmente. Fontes e verificações restantes vêm da API; não há card de demanda sem resultado no resumo nem cards vazios de mínimos. Trocar concessionária atualiza a pesquisa aplicável; nenhuma fonte Energisa é emprestada à CPFL.

Campos de geometria, pontos e distribuidora continuam salvos/editáveis e validam valores fornecidos, mas não solicitam preenchimento obrigatório para cálculos normativos indisponíveis. Contratos legados são aceitos e nenhuma edição manual válida é sobrescrita. No PDF a seção é Cobertura normativa, com explicação de que indisponibilidade não indica falha cadastral. JSON conserva os resultados/status nulos e inclui resultado_disponivel; não incorpora referências extensas ou fórmulas. Nenhum resultado normativo foi liberado por essa alteração de apresentação.


## Previsão residencial — 0.9.0

Requisitos para oferece “Previsão residencial (luz/TUG)”, aplicável a ambientes internos de habitação. A API calcula as dependências condicionais e retorna normative_environments tipado: área para iluminação, perímetro conforme destinação/área para TUG; banheiro não pede perímetro. Campos manuais são preservados, e botões de correção apontam geometria/pontos quando necessário. Cards mostram previsão VA, mínimos, cadastrados, base e notas; dados residenciais anteriores ficam ocultos durante stale. Externo/outro não recebe mínimos presumidos. Fontes institucionais ficam recolhidas; demanda continua na cobertura indisponível.

PDF acrescenta tabela resumida por ambiente (VA de luz/TUG e mínimos de pontos); JSON inclui previsao_residencial_por_ambiente sem referências ou fórmulas. Totais continuam separados dos W cadastrados e nulos quando incompletos. Nenhuma alteração do nome do arquivo, fuso, guardas de snapshot ou histórico. Fontes e limites em standards.md; testes efetivos em CURRENT_STATE. As seções anteriores descrevem os marcos históricos até 0.8.0.


## Vistoria visual e duplicação de ambientes — 22/10/2026

Polimento sobre a interface existente, mantendo a identidade escura/verde e os fluxos do produto. globals.css consolidado com variáveis de cor, controles/ações consistentes, bordas e espaçamentos moderados. Shell responsivo: aside fixado à rolagem em desktop, navegação em grade no celular; marca compacta, projeto atual sem repetir o nome no bloco de ações, rodapé com identificação/conexão separados do alcance do estudo. Cabeçalhos, biblioteca/lixeira, cards iniciais, artigos de ambiente/equipamento, detalhes e resultados usam o mesmo padrão. Foco visível, link para pular ao conteúdo e redução de movimento preservam acesso por teclado.

Adicionar ambiente tem ícone SVG, destaque primário e barra sticky limitada à seção de ambientes; em telas pequenas ocupa largura inteira. Artigos recebem cabeçalho e ações Duplicar/Remover separados dos campos. Grid de dimensões/pontos reorganizado por largura. Referências dos equipamentos passam a ocupar linha própria em celular, evitando colunas excessivamente estreitas. Botões secundários recebem área de toque maior e estados hover/foco/desabilitado consistentes.

Duplicar ambiente usa lib/environments.ts, sem fórmulas elétricas: cópia profunda de geometria, pontos, cargas, parâmetros, origens, flags manuais e snapshots. Novos UUIDs para ambiente e cargas; IDs do catálogo preservados. Nome único com sufixo de cópia respeitando 200 caracteres, inserção após o original e foco no novo nome. Ambas as instâncias seguem editáveis, recalculáveis e persistidas pelo fluxo existente. Nenhuma alteração de API, norma, migração ou dado real.

Validação: testes de cópia independente/nomes/IDs; E2E salva e lê as duas instâncias com valores manuais diferentes, verifica recálculo e largura sem overflow em 320/390/768/1024/1440. Capturas desktop/celular inspecionadas, além da página inicial. Resultados efetivos em CURRENT_STATE. Build e E2E devem ser executados sequencialmente: o build limpa .next, que contém .next/e2e, podendo reiniciar o servidor de teste se rodarem juntos.


## Relatórios de consumo e cargas — 0.10.0 / formato JSON 1.1

Objetivo: permitir entender a estimativa mensal de uma residência existente ou planejada, preservando as medidas/resultados anteriores e distinguindo as exigências de atendimento da distribuidora. Preparação canônica em backend/app/reports/summary.py, sem fórmulas elétricas: mapeia exclusivamente resultados do motor e os dados de uso fornecidos. PDF e JSON usam o mesmo preparo; nenhum cálculo foi duplicado no navegador nem foram presumidos horários, tarifa, ciclos ou demanda.

PDF prioriza consumo mensal kWh e custo estimado R$, informa tarifa BRL/kWh e cobertura em itens cadastrados. Mostra consumo por ambiente; preserva W/kW, VA/kVA, iluminação nominal, área construída, áreas/perímetros/luz/TUG, previsões quantitativas e observações. Acrescenta relação compacta de equipamentos (quantidade, W unitário/total, kWh mensal e base de uso), consumo por categoria e pendências objetivas de consumo. Nome do projeto no arquivo, emissão Brasília, acentos, tabelas paginadas e contagem de páginas preservados. Potência parcial por ambiente é identificada; não é ausência convertida em potência zero. Custos em reais no PDF, BRL/unidades e precisão completa do motor no JSON. Sem fórmulas, referências extensas, hashes ou dumps de parâmetros internos.

JSON 1.1 é aditivo: conserva emissao/projeto/aviso/resultados/ambientes/previsao_residencial_por_ambiente/categorias/previsoes_normativas e seus campos anteriores. Acrescenta consumo (estimado/parcial/nao_estimado, cobertura, tarifa/alcance), equipamentos, pendencias_consumo, atendimento_distribuidora e motivos/condições compreensíveis. Arquivo formatado com indentação, UTF-8 e null explícito. Consumo mensal informado por unidade prevalece sobre horários; a quantidade já integra os resultados. Zero explicitamente informado permanece zero; ausência não vira zero. Consumo pode estar completo para os itens registrados e potência continuar incompleta, e vice-versa. Não é backup restaurável do projeto.

POST /api/v1/reports/json acrescentado; ambos os formatos reutilizam prepare_report e o contrato existente PDFExportInput por compatibilidade, recalculam no servidor e exigem digest/versões do motor/registro e, quando salvo, ID/versão/payload coincidentes. Nenhum histórico é criado pela exportação. Nome do arquivo sanitizado com filename* UTF-8, no-store centralizado no middleware sem duplicar header. Frontend requestReport e um único fluxo de download controlam snapshot/ocupação e avisam alterações posteriores. Dados/entradas novos impedem exportação de resultados antigos. Indicador de progresso agora diz Gerando arquivo, servindo aos dois formatos.

A seção para atendimento é curta: distribuidora informada, demanda disponível ou pendente, cobertura territorial não presumida e orientação para conferir requisitos locais. kWh/mês não é potência instalada nem define sozinho tipo de ligação/padrão. Fontes conceituais primárias reconsultadas em 22/10/2026: [Energisa — critérios para ligação nova](https://www.energisa.com.br/ajuda/pergunta/como-solicitar-uma-ligacao-nova) e [Neoenergia RN — ligação nova](https://www.neoenergia.com/web/rn/sua-casa/ligacao-nova). São evidências da necessidade de carga declarada/padrão/requisitos da distribuidora, não normas universais, fatores de demanda ou mapeamento de municípios. Não se aplicaram limites regionais de uma dessas páginas às demais localidades. NDU integral e dimensionamento final continuam pendentes conforme standards.md.

Verificações: casos independentes de 85,4 kWh e R$68,32, consumo conhecido com potência desconhecida, parcial/ausente/zero/sem equipamentos, prioridade de consumo informado, valores manuais e ambientes homônimos. Teste HTTP verifica JSON legível, nome, guards/409/no-store e ausência de gravações; E2E verifica exportações e campos antigos/novos. PDF extraído/renderizado em leitor independente MuPDF instalado apenas em /tmp, além dos testes estruturais de largura/sobreposição/paginação existentes. Estado/testes efetivos em CURRENT_STATE. Sem certificação de aprovação de ligação ou norma nova habilitada.


## Revisão da Casa do Codex — 0.10.1 / JSON 1.2

Revisão baseada no preenchimento real, reabertura e download pela interface. PDF: reais com dois decimais apenas na apresentação (ROUND_HALF_UP), tipo de residência/pavimentos preservados, reserva maior de espaço para títulos e primeira linha das tabelas, contagem separada de cadastros/unidades. Potência máxima e estimativa genérica ficam identificadas onde importam; removida repetição de rótulo para referências nominais. Explicação de VA ausente e limites dos horários/ciclos/standby sem fórmulas ou referências extensas. Valores do motor/JSON mantêm precisão integral.

JSON 1.2 é aditivo: IDs de ambiente/carga relacionam registros mesmo com nomes repetidos; categoria, pavimentos/tipo de residência, unidades cadastradas, classificação/tipo de potência e premissa de consumo. Corrigido potencia_personalizada: depende da edição efetiva de W/flag de potência, não de qualquer manual_override. dados_personalizados mantém a informação ampla de personalização. Consumo ou tensão editados não se tornam alteração de potência. Snapshot e catálogo não são regravados pelo relatório.

Formulário: variantes documentadas passam a ser selecionáveis em Configurações avançadas somente quando há opções do mesmo equipamento. Tensão e valores documentados acompanham a variante; potência manual válida e consumo/horários são preservados. Restaurar sugestão repõe parâmetros técnicos sem apagar estudo de consumo. Trocar a categoria principal para outro equipamento continua sendo seleção de outro aparelho. Rótulos acessíveis explícitos para variante, apresentação e requisitos. Aviso de potência máxima em Consumo mensal; resumo informa que só cobre equipamentos cadastrados. Sem fórmulas novas no frontend, mudança normativa ou migração.
# Recuperação e acesso — revisão 0.11.0

Rascunhos não confirmados no servidor são gravados no navegador em slots por editor/conta. Ao voltar, uma lista permite continuar ou apagar cada rascunho; recuperação não o envia automaticamente. Recuperar usa slot novo para não sobrescrever uma aba ainda ativa. Após salvar no servidor, remove-se a origem apenas se não houver mudado desde a recuperação. Sem armazenamento disponível, a interface informa que a proteção local falhou; não promete recuperação de dados anteriores à gravação, após limpeza do navegador ou em outro dispositivo.

Conflitos409 pausam autosave e preservam os campos locais. A interface consulta a versão atual e oferece salvar a edição como novo projeto ou carregar a versão do servidor, mantendo o rascunho anterior recuperável. Não há fusão silenciosa nem botão de sobrescrita forçada. Debounce/cancelamento dos cálculos e guardas de exportação continuam existentes.

No modo remoto HTTPS, o editor só é montado após autenticação; sair desmonta os dados da conta e remove o token CSRF da memória. Rascunhos permanecem no perfil local, separados por conta na interface; perfis de navegador separados continuam necessários em computador compartilhado. Sessão expirada solicita novo login e mantém a recuperação local. Modo local mantém uso em loopback sem exigir criação de conta.


## Demanda integrada — 0.13.0

Painel de revisão NDU7.0 entre ambientes e resultados, com ativação opcional, classificação explícita por carga, reserva, tipo AC, escopo/ausências/simultaneidade e confirmação de inventário. Confirmação é vinculada ao digest emitido pelo backend; alterações invalidam a revisão e ocultam demanda antiga no recálculo. PDF/JSON1.3 incluem declarações, inventário e memória por grupo/faixa, além de pendências/limites. PDF usa rótulos em português para declarações. As fórmulas permanecem no motor único. Decisão do usuário: operação local; impressão física fora do escopo.


## Polimento geral da interface — 0.13.1, 23/10/2026

Padronização visual mantendo tema escuro, estrutura, dados e motor0.8.0. SectionHeading reúne marcador/etapa, título e descrição; Dados do projeto, Ambientes, Conferência e revisão Energisa usam a mesma hierarquia. CSS consolida raios e estilos de campos, selects com seta consistente, foco, hover, seleção, avisos/erros e desativados; botões mantêm área mínima e disclosures usam indicadores uniformes.

Causa dos checkboxes desarrumados: seletor global de input aplicava padding de campo de texto. Campos de texto agora excluem checkbox; caixas nativas têm18px, padding zero, alinhamento superior e rótulo inteiro clicável, inclusive demanda e hipótese resistiva. Salvamento automático está visível no cartão de preferências, com indicação Após salvar/Ativado/Desativado/Pausado/Salvando e explicação contextual. Mantidos debounce1,5s, pausa em renomeação/conflito e proteção contra repetição de falha; preferências continuam da sessão, sem novo armazenamento.

Observações passaram a área própria sempre visível, cinco linhas redimensionáveis, limite10.000, contador e descrição acessível preservada pelo Field junto com erros. Campos complementares ficam em Outros dados sem intercalar textos no grid principal. Valores e conteúdo não são regravados por layout.

Mais ações mantém details nativo/teclado; rótulo/seta alinhados, estado aberto explícito, opções com ícones e lixeira separada. Fecha por Escape, saída de foco e clique fora; callbacks mantêm retorno de foco ao acionador. Bloqueio inclui saving/busy/exporting e exportações respeitam cálculo atual; títulos explicam indisponibilidade. Role do agrupamento de avisos corrigido para group após axe encontrar aria-label num div sem papel. Indicador Next de desenvolvimento desativado por sobrepor controles no celular; erros de compilação/execução continuam visíveis.

Regressão E2E interface.spec.ts verifica autosave desligado/ligado com consulta real ao banco QA, observações multilinha, cabeçalhos, teclado/Escape/clique fora, axe e layouts320/390/768/1024/1440. Capturas QA em/tmp/eletroprojeto-{project,actions}-polish-{390,1440}.png. Testes e verificações finais no CURRENT_STATE/SESSION_HISTORY. Sem alteração de fórmulas, fontes normativas, migrações ou catálogo.


## Salvamento/rascunhos/retorno — 0.14.0

Biblioteca leve com payload completo somente ao abrir. Rascunhos por conta/aba conservam schema1 e createId opcional, escrita agrupada250ms e flush em pagehide/beforeunload/visibility hidden/desmontagem e antes de trocar contexto. Antes do POST o identificador é persistido imediatamente. Primeiro envio repetido não duplica; se houve nova edição após a resposta perdida, editor recupera o projeto já criado e mantém o input atual para o próximo PUT. PUT idêntico na mesma revisão não gera histórico/versão.

Teste de navegador simula POST recebido com resposta abortada, edição, recarga imediata antes do debounce, recuperação sem envio, reenvio e atualização: um projeto, duas versões reais e notas preservadas. Backend valida ausências de IDs/colisão entre proprietários e biblioteca leve. Sem envio na saída da página, promessa de proteção contra limpeza do navegador/queda abrupta sem eventos ou mudança das regras normativas. Últimas edições anteriores ao flush podem ser perdidas em término abrupto; eventos normais de saída foram testados.


## Início e equipamentos compactos — 0.14.1

Home desmonta somente a navegação lateral, mantendo o estado do editor no componente principal. Marca e logout passam ao cabeçalho inicial; rodapé continua presente. Entrar em criar/biblioteca/lixeira revela aside; retorno ao início o oculta. Cartões iniciais usam ícone lateral e menor espaçamento. Main inicial sobrescreve min-height para evitar empurrar o rodapé para fora da janela por herdar100dvh.

EquipmentEditor agrupa três details nativos em equipment-options flex com quebra, sem alterar cálculos/valores ou conteúdos. Resumos30px desktop/mínimo34px celular; abertos ocupam a linha inteira e crescem com conteúdo. Ações do equipamento em faixa própria com borda. Controles gerais/painéis/títulos recebem espaçamento menor, mantendo estados e foco. compact.spec.ts verifica navegação, recuperação da edição em memória, altura/alinhamento, abertura dos três grupos, axe e overflow320–1440px. Artefatos fictícios em/tmp/eletroprojeto-{home,equipment}-compact-{390,1440}.png.


### Correção solicitada: restaurar somente o início

A alternativa sem aside foi rejeitada pelo usuário. Sidebar volta a ser sempre renderizado; marca/logo, informações e saída da conta ficam nele, sem cabeçalho alternativo. WorkspaceHome e estilos dos cartões retornam à composição anterior0.14.0; padding do main/sidebar/marca/navegação da Home é restaurado por escopo app-shell-home, preservando a compactação das demais telas. Rodapé existente continua abaixo do conteúdo; desktop1440×900 verificado. Testes agora exigem sidebar visível ao abrir e ao voltar ao início; demais regressões dos equipamentos permanecem.
