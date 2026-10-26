# Referências e validação normativa

## NDU-001 enviada pelo usuário — 0.12.0 / motor0.7.0, 23/10/2026

Foram examinados os dois PDFs locais: identificação, escopo/vigência, demanda, tabelas/notas e erratas. Nome/metadados do arquivo não definem vigência:

| Exemplar | Identificação e uso | SHA256 |
| --- | --- | --- |
| Nome longo, mencionando agrupadas até três unidades |162p; corpo **7.0/novembro2024**. §1: unidade individual até75kW, agrupamentos remetidos à NDU003; §2 revoga anteriores. Base do método limitado. |`940b4aab66afc741e2f1f20d88ef2630672dcac2499928af31d807ac8d7442e2`|
| Versão6.3 |189p; corpo6.3/outubro2020, erratas/adendos até novembro2023. Título nos metadados diverge do conteúdo. Somente comparação histórica; nenhuma distribuidora seleciona essa edição no motor. |`733fb17b8597e36ef325c0c5aefa7d54ebc27e97fc45298eb3073d27ae3253ba`|

Autoria Energisa identificada no exemplar enviado. Fontes oficiais indexadas corroboram título/edição/§9.1/tabelas; portal/download seguem403. Hash identifica a cópia local, **não comprova igualdade binária com o download oficial nem ausência de atualização posterior**. API registra `user_supplied_full_text`, arquivo/hash/data/seção, sem afirmar download oficial bem-sucedido. PDFs e Zone.Identifier são preservados localmente, excluídos de Git/ZIP de código, sem redistribuição pelo aplicativo.

Implementado **POST `/api/v1/calculations/energisa-demand`** para residência individual, Energisa Sul-Sudeste/SP, inventário completo revisado e até75kW. Cada carga exige grupo, W unitários e quantidade; ausência de grupo é declaração explícita. Sem associação territorial automática, classificação por nome/catálogo ou atualização de potências pela Tabela4. Essa tabela é orientativa (notas p62), não substitui placa/fabricante; Tabela9 não é conversão BTU→W.

Conferidos visualmente/implementados: §9.1 pp56–57 e tabelas5–8/10 pp63–67. d1 usa faixas residenciais **acumulativas** (Tabela5 notaIII), não fator da última faixa sobre toda a carga. Simultaneidade declarada exige100% (notaI); desconhecida deixa pendência. Letreiros/vitrines (notaII) ficam fora de escopo. d2 aquecimento de água; d3 secadora de roupas/micro-ondas/lava-louças/hidromassagem; d4 fogões/fornos; d5 AC janela/individual. Soma por grupo usa W×quantidade uma vez e quantidade total de aparelhos, inclusive potências heterogêneas. Reservas são excluídas da demanda por declaração explícita (9.1 notaVI); limite instalado conferido conservadoramente incluindo todas as cargas declaradas.

Demanda emkVA = soma das parcelas emkW /0,92. Esse divisor pertence ao método; não é FP medido/universal dos aparelhos. VA da previsão NBR, BTU/h e kWh nunca são tratados como W. Sem arredondamentos intermediários, Decimal/contexto40. Resultado inclui memória por grupo/faixa, unidades e motivos. Não determina categoria de fornecimento, cabos, disjuntor, entrada ou aprovação final.

Tabelas12–14/notas/exemplos lidos, mas d6/d7 presentes permanecem **null/out_of_scope** neste método; não se generalizou classificação/demanda de motores/solda/raios-X sem parâmetros próprios. Unidades centrais de AC (9.1 notaI) também ficam fora de escopo e não recebem automaticamente Tabela10. Grupos omitidos, potência desconhecida/zero em carga ativa ou inventário não revisado deixam totalnull/pending. Ausência explicitamente confirmada pode resultar emzero; nunca é preenchida silenciosamente.

Cadastro geral/relatórios existentes ainda não têm classificação revisada suficiente: **selecionar a distribuidora não habilita demanda automática**. Método parametrizado é descobrível em `technical/rules.regional_methods`, separado dessa integração pendente. Projetos/históricos anteriores não são regravados; novo registro/motor afeta a consulta de revalidação.

Exemplos manuais independentes em test_energisa.py: d1=4.500W→3.120W por faixas; d2=2×5.500W→8.250W; d3=1.400W; d4=7.000W; d5=2×800W×0,88→1.408W. Instalado25.500W; demandado21.178W; D=21,178/0,92=23,019565217…kVA. Exemplo simples1.000W luz/TUG +5.500W chuveiro→(0,860+5,500)/0,92=6,913043478…kVA. São exemplos próprios, não exemplos oficiais completos de instalação. Cobertos todos os limites das tabelas implementadas, simultaneidade, reservas, ausência/zero/desconhecido, modelos heterogêneos, extrapolação de75kW e aplicação indevida a outra distribuidora.

## Reconsulta de 23/10/2026 — demanda e território

Dimensionamento/instalação: relidos no exemplar NBR identificado §§5.3.4–5.3.5,6.2.5–6.2.7,9.5.3–9.5.4 e7.3. Circuitos/traçados/materiais/agrupamentos/temperatura/curto-circuito/esquema de aterramento/dispositivos ainda não são modelados no produto. Implementação integral continua necessária; não foi inferida seção ou proteção pela somaW. Verificação física e ensaios exigem dados e inspeção da instalação, além do cadastro atual.

[Neoenergia DIS-NOR-030 rev06](https://www.neoenergia.com/documents/d/rn/dis_nor_030_fornecimento_de_energia_eletrico-pdf?download=true),138p, aprovação05/11/2025, fonte integral acessível. §§4/5.1/6.26–6.28 e tabelas/exemplos lidos: escopo até75kW; demanda trifásica; Elektro identificada emSP/MS, sem mapa municipal. Registro atualizado, sem confundir aprovação com início de vigência. Há remissões/exemplos divergentes nas parcelas b/d/j e fronteiras de tabelas a esclarecer; nenhum fator habilitado. Exige auditoria integral, erratas e exemplos independentes antes de publicar cálculo. Referência regional não se aplica a Enel/Energisa.

NDU001/portal Energisa novamente403 em web/curl. [SIGEL oficial](https://sigel.aneel.gov.br/arcgis/rest/services/DadosAbertos) lista AREA_ATUACAO; acesso ao serviço específico expirou em25s, sem coleta completa/validação territorial. Serviço histórico2018 não foi promovido a mapa atual. Nenhuma associação entre endereço e distribuidora foi inventada.

## Estado atual — 0.9.0 / motor 0.6.0

Iluminação e tomadas residenciais agora têm procedimentos executáveis revisados no escopo limitado abaixo. Demanda da distribuidora permanece pendente. Os registros subsequentes até 0.8.0 são históricos, anteriores à obtenção das novas fontes.


Consultas em 21 e 22/10/2026. Fontes primárias:

- [Energisa — Normas Técnicas](https://www.energisa.com.br/normas-tecnicas): resultado indexado do portal lista NDU-001 versão 7.0, vigência 01/11/2024. Abertura direta retornou HTTP 403. Versão de catálogo identificada; fórmulas, agrupamentos, tabelas e limites NÃO foram auditados no documento completo. Nenhum fator de demanda implementado.
- [Catálogo oficial ABNT](https://www.abntcatalogo.com.br/): catálogo consultado em 22/10 confirma ABNT NBR 5410:2004 Versão Corrigida:2008. Confirmada somente a identificação da edição; exemplar autorizado completo e revisão das cláusulas continuam pendentes. Não se habilitaram regras de iluminação ou tomadas por memória ou fonte secundária.

| Regra | Valor disponível | Estado | Pendência |
| --- | --- | --- | --- |
| Potência instalada cadastrada | Sim, W/kW | Calculado ou estimado | Matemática básica, sem alegação normativa |
| Potência aparente cadastrada | Sim, com todos os FP | Calculado ou estimado | FP e procedência informados pelo usuário |
| Previsão de iluminação | Não | Aguardando validação técnica | Fonte oficial, edição, condições e exemplos |
| Quantidade/potência TUG | Não | Aguardando validação técnica | Critérios por ambiente e parâmetros adicionais |
| Demanda Energisa | Não | Aguardando validação técnica | Auditoria integral das parcelas, tabelas, limites e cobertura |

A expressão histórica `(d1 + ... + d7) / 0,92` NÃO foi adotada. Nenhum coeficiente arbitrário foi usado para completar parcelas. Estados suportados: calculated, estimated, pending, invalid, out_of_scope e awaiting_technical_validation. O motor atual retorna somente estados que pode fundamentar; rejeições de entrada usam HTTP 422.

Antes de habilitar qualquer regra: obter fonte oficial autorizada, confirmar vigência/escopo, registrar cláusula/tabela e parâmetros, implementar condições e limites, comparar com exemplos independentes, adicionar testes de fronteira e revisar tecnicamente. Não reproduzir normas na íntegra.

Referências da stack consultadas:

- [Next.js instalação](https://nextjs.org/docs/app/getting-started/installation)
- [Tailwind com Next.js](https://tailwindcss.com/docs/installation/framework-guides/nextjs)
- [FastAPI — ambiente virtual](https://fastapi.tiangolo.com/virtual-environments/)
- [Pydantic — campos](https://docs.pydantic.dev/latest/concepts/fields/)
- [SQLAlchemy 2 — ORM](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)

## Reconsulta e catálogo — revisão atual

Foram localizados PDFs NDU-001 7.0 no domínio oficial Energisa, mas a leitura integral retornou 403/erro. O registro permanece pendente. Nenhum fator foi habilitado a partir de fragmentos indexados ou da expressão histórica com 0,92. A edição e os requisitos de NBR 5410 continuam sem confirmação em exemplar oficial autorizado.

Fontes de fabricante e tabela pública Enel de equipamentos foram incorporadas ao catálogo com classificação nominal/máxima/estimada, URL, documento e data. Essa tabela Enel fornece apenas referências de potência; não foi utilizada como critério normativo para projetos Energisa. Veja a relação completa de fontes e as informações descartadas por ambiguidade em [review-2026-10-21.md](history/review-2026-10-21.md).

Os testes de bloqueio normativo verificam que valores não auditados permanecem nulos, mesmo com cargas ou grupos informados. Isso não equivale a teste de conformidade com exemplos normativos; tais exemplos e revisão técnica continuam pendentes.

## Reconsulta efetiva — 22/10/2026

O catálogo oficial ABNT identifica 2004 com correção de 2008; metadados registrados em technical.DOCUMENTS e calculations.standards.RULES, sem declarar cláusulas validadas. O PDF oficial Energisa NDU-001 v7.0, caminho sites/energisa/files/media/documents/2025-08, voltou a retornar HTTP 403. Texto indexado/fragmentos não substituem leitura integral, condições, limites e exemplos independentes. Por isso iluminação mínima/TUG/demanda continuam null e aguardando validação técnica, inclusive com valores manuais completos. Nenhum coeficiente ou mapeamento territorial foi inferido.

Fontes de valores padrão reconsultadas: Philips 929001195311 (9 W, FP 0,7, 100–240 V); Samsung AU7700 (130 W máximo); LG S3-W12JA33B (1130 W nominal em resfriamento) e S3-Q09AA33A (800 W); tabela de resistência Lorenzetti Advanced (5500/127, 6400/220 e 7500/220), Loren Easy e Versátil; ficha Midea Xtreme Save Connect C p. 2 (ciclo Frio 18000/24000/30000: 1583/2170/2430 W); ficha Electrolux LE08S p. 2 (1400 W/6,36 A em 220 V, dados declarados distintos de corrente calculada); tabela Enel de estimativas, sem promovê-las a potências universais. URLs estão no catálogo.

Páginas oficiais Mondial confirmaram AFN-40-BI 1500 W, L-99-FB 550 W, C-34-JI-15X 550 W e VSP-40-W **140 W**, divergindo dos 60 W registrados anteriormente. Corrigida somente a referência atual do ventilador e sua data de conferência; valores dos projetos preservados. Cooktop mantém referência histórica 7000 W; manual Midea MRA antigo ficou inacessível nesta reconsulta, logo não se afirma nova conferência integral desse manual. Disponibilidade de página e testes aritméticos não são validação normativa.

[Ventilador — especificações oficiais Mondial](https://www.mondial.com.br/ventilador-de-mesa-mondial-6-pas-vsp-40-w/p), [NIST SP811 — conversões](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b9), [NIST — definição Btu IT](https://www.nist.gov/pml/special-publication-811/nist-guide-si-footnotes). Normas e fabricante preservam escopos diferentes.

## Pesquisa sobre demanda normativa — 22/10/2026, após 0.7.0

Pesquisa solicitada pelo usuário sobre o aviso “Procedimento não validado”. “Não validado” é o estado da implementação/revisão no EletroProjeto, não afirma que a norma da distribuidora seja inválida nem que falte apenas preenchimento pelo usuário.

Demanda é a potência solicitada pela parcela de cargas em operação, considerada em determinado intervalo. Demanda de projeto é estimada segundo o método da distribuidora; não é soma simples de potência instalada nem consumo mensal em kWh, e não se confunde automaticamente com demanda contratada/faturável.

Avanço de pesquisa: indexação de PDFs no domínio oficial Energisa identifica a seção 9.1 (página impressa 56) com D[kVA] = d[kW]/0,92, d = d1+...+d7. O trecho associa d1 a iluminação/tomadas (Tabela 5), d2 a aquecimento de água (6), d3 a secadoras/micro-ondas/lava-louças/hidromassagem (7), d4 a fogões/fornos elétricos (8), d5 a AC janela/centrais individuais (10/11), d6 a motores/solda motor-gerador (12/13), d7 a solda a transformador/raios-X (14). Isto é levantamento da estrutura indexada, NÃO auditoria integral ou autorização para implementar coeficientes. O divisor 0,92 desse método não é um FP medido/universal de todos os aparelhos nem fator de demanda único a aplicar à potência instalada.

Fontes primárias localizadas:

- [Portal de normas Energisa](https://www.energisa.com.br/normas-tecnicas): resultado indexado segue listando NDU-001 7.0, vigência 01/11/2024.
- [PDF oficial, caminho 2025-09](https://www.energisa.com.br/sites/energisa/files/media/documents/2025-09/NDU%20001%20-%20FORNECIMENTO%20DE%20ENERGIA%20EL%C3%89TRICA%20EM%20TENS%C3%83O%20SECUND%C3%81RIA%20A%20EDIFICA%C3%87%C3%95ES%20INDIVIDUAIS.pdf): seção 9.1 em indexação do documento.
- [PDF oficial, caminho 2025-11](https://www.energisa.com.br/sites/energisa/files/media/documents/2025-11/NDU%20001%20-%20Fornecimento%20de%20Energia%20El%C3%A9trica%20em%20Tens%C3%A3o%20Secund%C3%A1ria%20a%20Edifica%C3%A7%C3%B5es%20Individuais_0.pdf): seções 5.7/5.11 (p. 14, conceitos) e 9.1 (p. 56, estrutura) em indexação. Caminho de upload não comprova revisão nova; trecho identifica v7.0/novembro2024.
- [Enel — Cálculo de demanda para medição de cliente em baixa tensão, documento 2018](https://www.enel.com.br/content/dam/enel-br/megamenu/canais/perguntas-frequentes/Padrao%20-%20Calculo%20demanda.pdf): referência conceitual independente para carga instalada/fator de demanda, sem presumir vigência/aplicabilidade para Energisa.

Abertura direta do portal e PDFs oficiais continuou retornando 403/erro na ferramenta. Não foi lido PDF integral, não foram conferidas todas as notas/tabelas, revisões/erratas, condições regionais ou exemplos independentes. Não promover fragmentos de busca a validação normativa. Páginas secundárias/GitHub de calculadoras foram encontradas, mas não adotadas como autoridade de coeficientes ou conformidade.

Próximo passo técnico concreto: obter íntegra oficial, conferir escopo/vigência/erratas e os critérios de entrada; mapear cada equipamento uma vez para a parcela correta, definir a base de iluminação/TUG sem dupla contagem, revisar tabelas/faixas/notas/unidades, criar exemplos independentes e testes de limites, implementar/revisar no backend com versionamento/rastreabilidade. Conservar potências manuais válidas e separar FP cadastrado de conversões impostas pelo método. Até lá, demanda permanece null/awaiting_technical_validation. Nenhuma fórmula, coeficiente, API ou interface foi alterada nesta pesquisa.

## Pesquisa: três alertas em “C · Pendências reais” — 22/10/2026

Verificado o caminho real de emissão: calculations/standards.py mantém lighting/outlets/demand em awaiting_technical_validation, sem procedimento/cláusula/testes normativos preenchidos; pending_rule devolve value null. Em validation.notifications, cada regra com valor null gera aviso normativo; demanda sem concessionária é tratada como pendência técnica separada. ResultsPanel reúne categorias error/technical/normative em “Pendências reais”, e calculations-notices agrupa normative como “Regras não validadas”. Por isso o número 3 conta recursos normativos indisponíveis, não três irregularidades detectadas na instalação. As três regras permanecem pendentes mesmo em cadastro completo; não há comparação implementada de mínimos que sustente afirmar falta de luz/tomadas ou demanda excessiva.

Sentido dos recursos previstos: lighting é previsão mínima de carga/pontos de iluminação por ambiente, distinta da soma nominal das lâmpadas e de estudo de iluminância/lux; outlets é previsão de pontos/cargas de tomadas por características do ambiente, distinta da lista de eletrodomésticos; demand é estimativa pelo método da distribuidora, distinta da instalada e de energia mensal. Não converter essas distinções conceituais em fórmulas habilitadas sem conferir cláusulas/condições completas.

Reconsulta ao catálogo ABNT (https://www.abntcatalogo.com.br/) identificou novamente ABNT NBR 5410:2004 Versão Corrigida:2008, título Instalações elétricas de baixa tensão; somente metadados, sem acesso ao exemplar autorizado completo. Portal Energisa indexado segue NDU-001 7.0/01-11-2024. Referência educativa primária consultada da Schneider: https://blog.se.com/br/data-center/arquitetura/2018/12/11/como-proteger-a-rede-eletrica-e-torna-la-mais-segura/ (2018), sobre separação iluminação/TUG/TUE e critérios de tomadas; não substitui norma integral vigente. Normativa antiga de edifícios coletivos Neoenergia apareceu na busca e não foi tratada como regra automaticamente aplicável à residência individual/Energisa.

Achado de UX: título “Pendências reais” mistura correções do usuário com limitações permanentes da implementação. Recomendação para futura alteração autorizada: separar “Dados do projeto a revisar” de “Recursos normativos ainda indisponíveis”, mostrar escopo/efeito e evitar sugerir que preenchimento resolve uma regra não implementada. Esta pesquisa não alterou interface/API/fórmulas nem habilitou cálculo.

## Integração das pesquisas na API — 0.8.0 / motor 0.5.1

Pesquisas anteriores incorporadas no registro existente de RULES, sem criar catálogo normativo paralelo nem habilitar coeficientes. Cada regra contém label/purpose, evidence (título, URL oficial, constatação, nível de acesso, data, seção identificada) e pending_checks. Cláusula/procedimento executável/testes normativos continuam ausentes quando não conferidos; menção indexada à seção 9.1 não equivale à validação da cláusula completa.

`GET /api/v1/technical/rules` preserva mathematical/normative e acrescenta registry_version/coverage, aceitando utility/state. `POST /api/v1/calculations/full` inclui normative_capabilities, com available=false, estado, finalidade, motivo, fontes e pendências por recurso. Para Energisa Sul-Sudeste/SP aparecem as evidências da NDU; outra distribuidora recebe somente suas próprias referências identificadas, sem emprestar a NDU ou presumir cobertura territorial. Distribuidora desconhecida/sem cobertura não ganha fórmula alternativa.

As limitações deixam de ser notifications de correção do usuário; o resultado normativo permanece null e a informação persiste na cobertura/registro. Notifications conserva erros e alertas técnicos reais; geometrias/pontos/distribuidora não passam a ser campos obrigatórios só por existir um recurso não implementado. Legado analysis_scope=normative preservado, sem solicitar dados para uma operação indisponível. Validação de valores fornecidos continua ativa.

Nova tentativa direta de download HTTPS do PDF oficial 2025-11, com curl normal fora do sandbox, retornou HTTP 403 em 22/10. Catálogo ABNT confirmou metadados, sem exemplar autorizado completo. Nenhuma tabela foi reconstruída de sites de calculadoras ou fragmentos de busca. Fórmulas W/VA/corrente/energia, potências manuais e snapshots de catálogo não foram alterados. Todos os projetos podem indicar revalidação por mudança do registro/motor; consulta não regrava histórico.

Limite concreto para concluir os três cálculos normativos: acesso ao exemplar autorizado completo da NBR 5410 e ao PDF integral vigente da NDU-001, seguido de revisão das condições/limites, exemplos independentes e testes. Código e interface corrigidos nesta entrega não substituem essa evidência.

## Pesquisa ampliada e implementação residencial — 22/10/2026

Pedido: ampliar fontes confiáveis e implementar somente critérios efetivamente conferidos. Pesquisa incluiu órgãos públicos, acervos universitários, fabricante e distribuidora. Fontes completas consultadas:

| Fonte | Conferência e uso |
| --- | --- |
| [IPAAM/AM — NBR 5410](https://www.ipaam.am.gov.br/wp-content/uploads/2021/01/NBR-05410-05-Instala%C3%A7%C3%B5es-El%C3%A9tricas-de-baixa-Tens%C3%A3o.pdf) | Íntegra de 217 páginas; capa identifica segunda edição 30/09/2004, válida em 31/03/2005. Escopo/cláusulas/notas 9.5.1–9.5.2.2, páginas impressas 182–184, lidos. Não identifica correção de 2008 na capa; não foi tratado isoladamente como versão corrigida. |
| [PUC Goiás — acervo docente, NBR 5410](https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/18451/material/nbr_5410.pdf) | Capa/prefácio identificam versão corrigida 17/03/2008/Errata 1. Mesmas cláusulas cotejadas integralmente, inclusive exceções e potências por ponto. Hospedagem institucional de exemplar identificado não é licença de redistribuição. O PDF não foi incorporado ao produto/checkpoint. |
| [Polícia Federal — Diretrizes 2021a](https://www.gov.br/pf/pt-br/assuntos/licitacoes/2022/distrito-federal/tomadas-de-precos/tomada-de-precos-no-1-2022-sr-pf-df/edital-da-tomada-de-precos-no-1-2022-sr-pf-df-uasg-200228/1-1-7-anexo-vii-do-pb-diretrizes-projeto-executivo-e-obra-de-instalacoes-eletricas.pdf) | Documento técnico autoral oficial, pp. 17–21: corroboração dos trechos residenciais. Critérios específicos dos locais de trabalho da PF e FP próprios NÃO foram adotados como norma residencial. |
| [Prysmian — materiais técnicos](https://br.prysmian.com/pt/materiais-de-apoio-tecnico) | Página de fabricante e Dicas de Instalações Residenciais acessíveis; links de manual/guia integral falharam. Tabelas genéricas desse folheto não foram usadas para dimensionar condutores, assumir potências ou liberar demanda. |
| [Energisa NDU-001 7.0 — caminho 2025-05](https://www.energisa.com.br/sites/energisa/files/media/documents/2025-05/NDU%20001%20-%20Fornecimento%20de%20Energia%20El%C3%A9trica%20em%20Tens%C3%A3o%20Secund%C3%A1ria%20a%20Edifica%C3%A7%C3%B5es%20Individuais%20v7.0.pdf) | Novo caminho oficial também retornou 403. Busca por íntegra alternativa confiável não permitiu conferir todas as tabelas/notas vigentes. Repositórios de terceiros, fragmentos e métodos de outras distribuidoras não habilitam a NDU. |

Foram solicitadas capturas das páginas PDF 190/191 (índice zero) para confronto com o texto extraído. A biblioteca ABNT segue como autoridade de identificação da edição; órgãos/universidade hospedam evidências do texto e a PF fornece corroboração institucional, não uma certificação do software. Não foi adotado projeto de revisão como norma vigente.

### Escopo habilitado e limites

Habilitados somente os procedimentos de previsão quantitativa de iluminação e TUG de ambientes internos de habitação, por seleção explícita de `analysis_scope=normative` (“Previsão residencial (luz/TUG)”). A seleção declara a finalidade residencial; não se deduz ocupação pelo nome livre do projeto, distribuidora ou equipamentos. Sala/quarto/cozinha/banheiro/lavanderia recebem seus grupos; corredor/garagem/escritório doméstico usam demais cômodos internos. Externo e outro continuam fora do escopo, sem presumir que externo significa varanda. Sem resultados completos de todos os ambientes, o total correspondente é null, mantendo os resultados individuais conhecidos.

A atribuição TUG aplica o método básico por ambiente; a redução opcional para conjunto de ambientes molhados não foi aplicada. Quantidade considerada é a maior entre mínimo previsto e pontos cadastrados. Duas tomadas de corrente sobre a pia podem compartilhar um ponto: não são dois pontos extras somados automaticamente. Localização, distâncias, volumes de banheiro, distribuição uniforme, quantidade de módulos, lux, circuitos e proteções não são verificações executadas. Notas dessas condições aparecem por ambiente. Não há declaração de conformidade integral nem dimensionamento final.

W de placa/manual continuam intactos; previsão VA não substitui iluminação nominal, não é soma adicional à instalada nem entrada automática no método de demanda. FP não foi inferido. Requisitos de área/perímetro dependem do procedimento e da destinação; banheiro não exige perímetro. Quantidades insuficientes geram alerta técnico corrigível, sem alteração silenciosa do cadastro. Em outras operações, não se exige geometria nem se executa previsão residencial.

### Exemplos independentes, revisão e projetos afetados

`tests/test_residential.py` registra resultados calculados manualmente antes da execução, separados da implementação: quarto retangular 3×4 m, cozinha 3×3 m, pontos manuais acima/abaixo do mínimo, mudanças de área/perímetro, limites 6/10/14 m² e perímetros exatos/frações. Verifica atribuição por ambiente (sem misturar cômodos), nulos/escopo, recálculo, ausência de dupla contagem e PDF. São exemplos aritméticos independentes, não projetos certificados nem exemplos oficiais de aprovação da distribuidora. Teste API verifica contrato, persistência e histórico anterior intacto; E2E verifica seleção, correção, recálculo, JSON e responsividade.

Motor 0.6.0 e hash do registro distinguem estes resultados da versão anterior. Projetos salvos não foram regravados; novos cálculos com escopo residencial podem passar de null a valores ou a pendências de entrada. Histórico e snapshots anteriores preservam o procedimento antigo. Demanda continua null e nunca é substituída por zero, porcentagem genérica ou soma de instalada. As verificações efetivamente executadas estão em CURRENT_STATE.


## Organização local dos exemplares — 23/10/2026

Os dois exemplares anteriormente na raiz estão agora em `references/energisa/ndu-001-v7.0.pdf` e `references/energisa/historico/ndu-001-v6.3.pdf`. SHA256 conferidos após mover; nomes originais/hash nos metadados da API permanecem como proveniência. Sem alteração de regras ou redistribuição dos PDFs. Consulte `references/README.md`.


## Integração ao cadastro — 0.13.0, 23/10/2026

A integração utiliza exclusivamente as regras e fatores d1–d5 já conferidos na0.12.0, do mesmo exemplar local7.0/hash acima: §9.1 e tabelas5–8/10. Não amplia o escopo a d6/d7, centrais presentes, agrupamentos ou outras distribuidoras. Não transforma previsão normativaVA, BTU/h ou consumo em potência elétricaW.

Cada carga recebe classificação explícita e indicação de reserva; escopo, simultaneidade, ausências e inventário são confirmados pelo usuário. O backend vincula a revisão ao inventário por hash. Falta de dados/classificação/revisão produz null/pending; incompatibilidade confirmada produz null/out_of_scope. Sem reclassificação ou regravação de projetos antigos. Condições de instalada/75kW e reservas continuam as mesmas. Matemática e integração em calculations.md; testes de resultados/limites em test_energisa.py e test_project_demand.py, além de persistência/API/PDF/JSON/E2E. Isso não constitui aprovação da distribuidora ou dimensionamento final.

## Acervo local integrado — 0.15.0,23/10/2026

As entradas fornecidas pelo usuário foram inventariadas integralmente, incluindo membros de ZIPs.2.244PDFs distintos e37guias/modelos/diagramas foram percorridos pelo extrator;83.424páginas PDF,mais37unidades textuais.80.995unidades com texto e2.466páginas sem texto extraível. A leitura automática integral de objetos/páginas não significa revisão técnica humana integral do conteúdo, nem OCR/revisão visual de83mil páginas. Guias e modelos residenciais foram lidos como material educacional,diagramas conferidos; exemplos não foram convertidos em potências/fatores universais.

| Conteúdo recebido | Aproveitamento | Condição para cálculo automático novo |
| --- | --- | --- |
| Grandezas,FP,energia e correntes | Guias pesquisáveis e exemplos de estudo; motor existente preservado | Respeitar W/VA/BTU,rendimento,regime e valores manuais. Não duplicar fórmulas no frontend. |
| Previsão de iluminação e TUG | Consulta complementar à previsão limitada já disponível | Distribuição física,exceções e edição aplicável continuam exigindo revisão específica. |
| Cabos,disjuntores,DR,DPS,eletrodutos e queda | Manuais de fabricante,referências históricas e roteiros de levantamento | Métodos,tabelas,fatores,temperatura,agrupamento,curto,desligamento,coordenação e exemplos independentes ainda não qualificados integralmente. Critérios didáticos não habilitam dimensionamento final. |
| Alturas,banheiros,acessibilidade,móveis e aparelhos | Guias e diagramas com limites e contexto | Convenções não são alturas universais; dependem de volumes,alcance,modelo e geometria. Nenhuma verificação física completa foi adicionada. |
| Portais/distribuidoras/UF | Fontes,URLs,grupos e UF de catalogação preservados | Coleta parcial/grupo não comprova concessão municipal nem vigência. Seleção de concessionária não habilita demanda. |
| NR-10 e atualização | Edições históricas/futuras separadas como candidatas à revisão | Conferência temporal não substitui análise da aplicação nem valida normas de dimensionamento. |
| Modelos e checklists | Seis roteiros disponíveis sem preencher automaticamente valores | Responsável deve registrar evidência,pendências e escopo; checklist não é laudo. |

Conferência adicional oficial: [Portaria MTE737/2026 e retificação](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/seguranca-e-saude-no-trabalho/sst-portarias/2026-1/portaria-mte-no-737-nova-nr-10.pdf),consultada23/10/2026,página1,arts.3 e5,publicação01/06/2026. Vigência geral um ano após publicação; a alínea específica citada no art.3 tem prazo adicional para instalações existentes. Portanto,texto publicado não foi tratado automaticamente como vigente nesta data. A comunicação institucional da ABNT sobre consulta até15/10/2026 ([registro](https://pt.linkedin.com/posts/abnt-associacao-brasileira-de-normas-tecnicas_est%C3%A1-em-consulta-nacional-o-projeto-de-revis%C3%A3o-activity-7513297374031794176-PgSq)) não comprova publicação final posterior; edição corrente do catálogo não foi certificada por esta importação.

Classificações do acervo são preliminares e explicitadas:37educacionais,7históricos,2vigência-futura-candidata,1minuta,199fora-do-escopo,2.035pendentes. Não alteram os documentos/regras já qualificados no registro técnico nem a revisão explícita de demanda Energisa. Nenhum projeto teve regra/digest recalculado ou snapshot regravado por esta ingestão;9projetos/30históricos/8revisões preservados integralmente.

Rastreabilidade: referências/objetos originais por SHA-256,manifesto de6.231entradas e3.788fontes persistidas. Não usar métricas antigas dos coletores como contagem atual. Os resultados atuais e procedimentos são os de [referências](../references/README.md). Downloads com falha ou resposta sem PDF permanecem como fontes sem documento,sem zeros ou PDFs fictícios. PDFs/objetos não entram no Git; metadados de consulta não conferem licença de redistribuição nem autoridade normativa.

## Revisão específica de circuitos/entrada — 24/10/2026,0.16.0

Conferidos nesta sessão:metadados atuais do [catálogoABNT](https://www.abntcatalogo.com.br/) listam5410:2004/VC2008;texto institucional [IPAAM](https://www.ipaam.am.gov.br/wp-content/uploads/2021/01/NBR-05410-05-Instala%C3%A7%C3%B5es-El%C3%A9tricas-de-baixa-Tens%C3%A3o.pdf) e [VC2008PUC](https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/18451/material/nbr_5410.pdf),tabelas36/40/42linha1/47/58,§§5.3.4.1,6.2.5,6.2.7,6.4.3.1.3. Valores B1/B2/2carregados e fatores cotejados com manualPrysmian2010doacervo(páginasPDF53/57). Não foi redistribuído texto integralABNTnovo.

[GuiaPrysmian2024](https://asean.prysmian.com/sites/asean.prysmian.com/files/media/documents/241218%20-%20Prysmian%20Electrical%20Information%20for%20Low%20Voltage%20Cables.pdf),§5,páginaPDF18/impressa34:ρCu0,0225eλ0,08mΩ/m,modelo simplificado condicionado,não tabelas brasileiras substituídas por regras estrangeiras. FP não assumido; modelo precisa de aceitação. Fórmula física fase-fase/fase-neutro cotejada no [guiaSchneider](https://www.electrical-installation.org/enwiki/Calculation_of_voltage_drop_in_steady_load_conditions);não foi utilizadoρXLPE23,7/Sdesseguia para PVC.

Proteções:§5.3.5.5.2(energia passante/k²S²),§§5.1.2.2.4.2/tabela25(TN),5.1.2.2.4.3(TT)e5.1.3.2(DRadicional). Sem inventar k,curva,curto presumido,RA,tipo deDR ou dispensa. Valores de produto e condições de aplicação precisam de fonte informada;checagem é de critério declarado,sem certificação integral.

NDU0017.0exemplarjáidentificadoporSHA940b4aab…e162páginas:§6.6pp.22–23,tabela16p.73eTODASnotaspp.74–75 conferidas,imagem da tabela inspecionada. Origem oficial de download continuouHTTP403;não afirmar igualdade binária comnovoarquivo remoto. Aplicação restritaESS/SP220/127V,≤75kW,individual;cargas especiais precisam de revisão. Tabela dá mínimos e disjuntores de limite superior,sem converter tais valores em proteção final. Ausência de demanda revisada bloqueiaT. Outras tabelas/distribuidoras não habilitadas por analogia.

Procedimentos,unidades,limites e exemplos independentes em calculations.md/tests/test_circuits.py. Novos métodos afetam somente prévia/revalidação do motor0.9.0;projetos/históricos não regravados em lote. Regras gerais de dimensionamento final,geometria,DPS/seletividade,outras fases/materiais/métodos e demais distribuidoras continuam pendentes;não declarar revisão humana integral do acervo concluída. OCRnuncafoifontedehabilitaçãoautomática.

## Ampliação limitada e reconsulta — 25/10/2026, motor 0.9.2

O catálogo oficial ABNT reconsultado continua exibindo NBR 5410:2004/VC2008; o portal oficial Energisa lista NDU-001 7.0, em vigor desde 01/11/2024. Isso confirma a identificação publicada, sem comprovar atualização integral dos exemplares locais. As tentativas de obter novamente NDU-001 e os exemplares institucionais IPAAM/PUC retornaram 403/indisponibilidade.

Ampliado somente o intervalo de seções do estudo já qualificado B1/B2, cobre/PVC70°C, dois condutores carregados: 50/70/95mm². Conferência textual e visual no **Manual Prysmian de Instalações Elétricas 2010**, capítulo VI, tabela2, p.52 (PDF53), colunas B1/B2 de dois condutores, e p.56 (PDF57), tabelas6/7 e notas de agrupamento. Exemplar do acervo por SHA256 `65d2fefc0c00b7304e57ad0972f48320d4d836e72d35f4c9b31c5e58239b6912`, proveniência [fabricante](https://br.prysmian.com/sites/br.prysmian.com/files/media/documents/Manual_Instalacoes_Eletricas.pdf). Download oficial novo retornou 403; não se afirma identidade com arquivo remoto atual. A edição de 2010 é evidência de cotejo das tabelas da NBR já revisadas, não uma nova edição normativa nem substituição das condições previamente qualificadas.

B1: 151/192/232A; B2: 133/168/201A, respectivamente, antes dos fatores de temperatura/agrupamento. Condutor de proteção: p.38 (PDF39), quadro correspondente à tabela58 da NBR/§6.4.3.1.3, conferido visualmente; para S>35mm², PE≥S/2 e próxima seção padronizada. Resultados independentes: fase50→PE25; fase70→PE35; fase95→PE50, pois47,5 não é seção padronizada selecionável. Não ampliados fases, isolação, materiais, métodos, agrupamentos ou critérios de aprovação final.

Testes independentes em `tests/test_circuits.py`: igualdades In=Iz/I2=1,45Iz nas seis capacidades, valores imediatamente superiores, teto95mm² sem extrapolação, temperatura/agrupamento e potência desconhecida. Exemplo B1/40°C/2circuitos:50mm²→151×0,87×0,8=105,096A, insuficiente para110A;70mm²→133,632A. Motor0.9.2 identifica a alteração; projetos salvos/históricos não são regravados, revalidação permanece explícita.

Relidos §9/notas e tabelas12–15 do exemplar NDU-0017.0 preservado. **d6/d7 e centrais continuam indisponíveis**: exigem dados próprios de motores/fases/potência de eixo, critérios de agrupamento, correntes máximas, tipos de solda e ligação V-V, além de exemplos e revisão específica. Valores em kVA das tabelas12/13 não podem entrar como kW no somatório; correntes e FP tabelados não substituem placa. Sem implementação/revisão completas desses parâmetros, o resultado permanece nulo/fora de escopo. A leitura de tabelas isoladas não habilita o método.

Território: consulta direta ao [diretório oficial SIGEL](https://sigel.aneel.gov.br/arcgis/rest/services/DadosAbertos) retornou HTTP200 e listou AREA_ATUACAO/FeatureServer e MapServer. Aberturas dessas camadas e camada0 expiraram ou retornaram erro500 de inicialização do serviço. Nenhuma feição territorial válida foi obtida; associação municipal continua não verificada, sem inferência a partir de UF, nome ou fontes históricas. Geometria/localização/volumes de banheiro, DPS/seletividade, outras distribuidoras e dimensionamento final integral permanecem pendentes de modelagem e revisão; não foram marcados como concluídos.

## Ampliação conferida — 26/10/2026, 0.19.0 / motor 0.10.0

NDU-001 7.0: portal oficial continua listando vigência 01/11/2024. Relidos texto integral e imagens das páginas 56–57/68–70 do exemplar local de SHA256 `940b4aab66afc741e2f1f20d88ef2630672dcac2499928af31d807ac8d7442e2`. Habilitadas parcelas d6/d7 e centrais no **mesmo escopo residencial individual Energisa Sul-Sudeste/SP até75kW**, sem letreiros/vitrines; não abrange carga industrial, agrupamentos ou outras distribuidoras.

- d6: Tabelas12/13, notas I–III. Fases e potência de eixo em cv explicitamente identificadas por fonte; somente linhas exatas (mono1/3–10cv; tri1/6–30cv, com as lacunas da tabela preservadas). Quantidade total de motores ativos seleciona coluna; cada motor usa sua própria linha/fase e demanda individual em kVA, multiplicada pelo cos tabelado conforme notaIII e pela quantidade. FP tabelado é exclusivo desta parcela; nunca substitui FP/consumo/corrente cadastrados ou W de placa. Solda motor-gerador é classificada como d6. Sem interpolação, conversão automática HP→cv ou validação de partida pela Tabela15.
- d7: Tabela14 e §9.1 notaVII. Exige tipo, ligação, potência aparente elétrica absorvida, FP no mesmo regime e fonte. Solda V-V invertida tem base aparente duplicada antes de ordenar e aplicar os fatores; mesma condição elétrica converte VA→W por FP declarado. Solda a arco/galvanização compartilham a linha da tabela; resistência e raios-X têm sequências próprias. Quantidades são consideradas individualmente, sem expandir listas gigantes. **Ambiguidade preservada:** se a ordem de grandeza de W e VA divergir dentro do grupo, a tabela não esclarece essa ordenação; retorno nulo/pendente, solicitando esclarecimento da concessionária.
- d5 central: §9.1 notaI exige corrente máxima total do fabricante, tensão, configuração mono/trifásica equilibrada e FP do mesmo regime. Fator100%; não substituir corrente máxima total por corrente nominal, de partida ou MCA. Janela/individual continua na Tabela10, contando somente esses aparelhos, separado das centrais. W nominais cadastrados e base máxima de demanda não são intercambiáveis.

Inventário, fontes e parâmetros próprios participam da confirmação por digest. Ausência explícita, reservas fora da demanda/dentro do limite instalado, nulos, limite75kW e bloqueio por outra distribuidora permanecem. Resultados completos somente após revisão; memória, PDF e JSON identificam bases VA/FP/fatores/referências. Exemplos independentes e limites em `test_energisa_special.py`, integração em `test_project_demand.py` e E2E. Projetos/históricos anteriores não foram regravados; novos cálculos e revalidação explícita usam motor0.10.0.

NBR5410: catálogo oficial consultado continua identificando2004/VC2008. Cotejados texto e imagem da Tabela36, tabelas33/40/42linha1, §6.2.5 e figura18/§9.1.2.1/§9.1.4.3.1–3 no exemplar institucional VC2008 PUC já referenciado. Circuitos Cu/PVC70°C ampliados a **A1/A2/B1/B2/C e dois condutores monofásicos ou três trifásicos equilibrados sem neutro**,1,5–95mm². Agrupamento homogêneo em feixe, sem radiação solar; temperatura10–60°C em passos5°C; demais condições anteriores mantidas. A1/A2 exigem classificação correta da parede termicamente isolante; C não equivale a qualquer arranjo em bandeja. Modelo físico de queda mono/trifásica cotejado no [guia Schneider](https://www.electrical-installation.org/enwiki/Calculation_of_voltage_drop_in_steady_load_conditions), com os mesmos parâmetros Cu/PVC do guiaPrysmian2024 já conferidos. Não introduzido alumínio residencial: §6.2.3.8 condiciona esse uso a estabelecimentos industriais/comerciais e requisitos específicos; uma tabela de ampacidade não autoriza uso indiscriminado. XLPE/outros métodos/neutral/harmônicas e dimensionamento final permanecem fora deste subconjunto.

Localização: implementada somente figura18 **chuveiro sem piso-boxe/rebaixo/delimitação clara, piso único no mesmo nível e sem divisórias intermediárias**. Coordenadas/envelopes completos medidos no mesmo referencial; z=0 no piso de banho. Raios0,60/1,20/3,60m; alturas2,25/3,00/2,25m, incluindo volume2 acima do volume1. Fronteiras recebem classificação mais restritiva. Tomada/interruptor comum interceptando volume1/2 é identificado como vedado por§9.1.4.3.1; exceções, IP, classes, DR/SELV/separação e equipotencialização continuam exigindo análise própria. Não há volume0 presumido nesse arranjo, aprovação de outros componentes ou conclusão de conformidade por estar fora dos volumes. Banheiras, pisos-boxe, divisórias e cabines pré-fabricadas não são extrapolados. Testes de envelopes, diagonais, alturas, fronteiras, dados ausentes e exportação em `test_bathroom_geometry.py`.

Território: o [portal SIGEL oficial](https://sigel.aneel.gov.br/portal/sharing/rest/content/items/70c2bd1464c04484add79a7a6691ec53?f=json) permitiu descobrir [Hosted/AREA_ATUACAO/FeatureServer/5](https://sigel.aneel.gov.br/arcgis/rest/services/Hosted/AREA_ATUACAO/FeatureServer/5). A camada DadosAbertos continuou falhando; na alternativa, consultas com reprojeção/subseleção e uma feição retornaram erro500, inclusive emHTTP200. A consulta integral de geometria/atributos, sem reprojeção, finalmente funcionou: **121feições/1.270anéis/2.604.452coordenadas**,SIRGAS2000/EPSG4674, sem truncamento. SHA256 da geometria `1968ce4e3781e9c2223e0a18b8f664717f132811371413377929f3a8a5f7ff90`; originais/relatório imutáveis em `references/territory/20261026T035935641118Z`, ignorados peloGit, permissões0700/0600. Reprodução: `backend/.venv/bin/python scripts/territory.py`, sem alteração do banco/registro.

**Validação espacial/temporal limitada, não mapa municipal vigente certificado.** A camada intitulada ATUAL contém registros encerrados e sucessores sobrepostos; data da coleta não é data de vigência. Consulta local pontual retorna nomes/CNPJ/atos, interior/fronteira, datas e situação registrada; não infere sucessor nem associa IDs internos ou município inteiro. Testes independentes de polígonos/ilhas/furos/fronteiras e HTTP200comerro em `test_territory*.py`; consultas reais de referência encontraram ENELSP no primeiro ponto, CPFLPAULISTA no segundo, e EDEVP encerrada/ESS sem fim informado no terceiro. Não se trata de teste exaustivo da base nem confirmação do atendimento de imóveis. A UI exige coordenadas SIRGAS2000 e mantém seleção manual da distribuidora; nenhum fator normativo é habilitado por essa consulta. Vigência jurídica atual/qualidade topológica integral e associação municipal continuam pendentes de evidência específica.
