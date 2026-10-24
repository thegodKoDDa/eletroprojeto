# Auditoria inicial — 21/10/2026

O diretório continha apenas diretórios administrativos `.git`, `.agents`, `.codex` e `.aws`, sem arquivos de aplicação retornados por `rg --files`. Não foram fornecidos protótipos nem ZIP.

Consequências:

- Não há funcionalidades, fórmulas ou fatores legados para validar ou reaproveitar.
- Não há estrutura de dados ou componentes anteriores para migrar.
- Não foram encontrados os 36 testes citados no histórico; sua existência ou aprovação não foi presumida.
- Todo o código entregue é novo. A migração efetiva dos protótipos dependerá da disponibilização deles.

Ambiente: Node 24.22.1, npm 11.19.1, Python 3.14.4 (`python3`; comando `python` ausente). Criado venv isolado. Instalação pip e npm bloqueada por DNS/rede. Sem possibilidade de executar serviços dependentes dessas bibliotecas nesta sessão.

Foram consultados os guias oficiais de instalação Next.js/Tailwind, validação Pydantic, SQLAlchemy e FastAPI. O portal Energisa indexado lista NDU-001 7.0 em vigor desde 01/11/2024; abertura direta retornou 403. Nenhuma tabela ou fórmula foi extraída de cópias secundárias. A edição vigente NBR 5410 não foi confirmada na fonte oficial.

## Revisão posterior na mesma data

A implementação acima foi preservada e revisada. Dependências agora disponíveis permitiram executar testes de API, persistência e interface. O estado atual, correções e restrições de execução estão em [review-2026-10-21.md](history/review-2026-10-21.md); os bloqueios históricos de instalação não descrevem todos os testes atuais.

## Simplificação da interface

Refatoração pontual sobre `EquipmentEditor.tsx`, `page.tsx` e os helpers existentes. Nenhuma fórmula do motor, tabela normativa, migração ou identidade visual foi substituída.

- Seleção principal por nomes comuns: Televisor, Geladeira, Chuveiro elétrico etc. Variantes comerciais permanecem nos registros e snapshots, mas não geram seletores redundantes por marca/modelo.
- Catálogo com 29 registros, 27 opções comuns e 26 potências documentadas. Motor, bomba e equipamento personalizado permanecem sem potência presumida. Referências genéricas baseadas em modelo são usadas com origem estimada, mantendo os dados originais da ficha no snapshot.
- Equipamentos comuns mostram quatro controles essenciais: equipamento, quantidade, potência e tensão. AC acrescenta BTU/h; motor permite W/cv/HP e mostra rendimento obrigatório em modo mecânico.
- FP, configuração de fases, classificação, tecnologia, correntes, consumo mensal e informações complementares ficam em Configurações avançadas. Pendências para VA/corrente são indicadas no título recolhido. Potência ausente e rendimento necessário têm indicação visível junto aos campos essenciais.
- Marca/modelo não são campos de seleção ou preenchimento; dados antigos continuam armazenados e legíveis no detalhe de origem. Identificação personalizada da carga continua editável.
- Fonte e documento ficam em Valor de referência, com restauração discreta. Duplicar/remover foram mantidos; total por item vem da memória retornada pelo Python, sem multiplicação elétrica no frontend.
- BTU/h só carrega potência sugerida quando houver referência cadastrada compatível. Capacidade sem referência limpa a sugestão e pede entrada elétrica; não se extrapola nem converte W térmicos em consumo. Valores declarados como placa são preservados ao editar capacidade.
- Pesquisa por equipamento aceita acentos ou sua ausência. A pesquisa para adicionar não restringe as referências disponíveis ao editar equipamentos existentes.
- Avisos detalhados, critério de contagem e memória completa passaram a ser recolhíveis. Outros dados do projeto também foram agrupados; seus valores continuam no payload de salvamento.

Verificação executada nesta etapa: **62 testes backend e 22 frontend aprovados**, TypeScript/typegen e OpenAPI sincronizados. Casos incluem campos avançados fechados e enviados à API, fonte preservada no salvar/reabrir, cálculo independente de potência/VA/corrente, exportação JSON com FP editado, restauração, seleção genérica, potência térmica separada, foco e estabilidade do DOM.

Playwright foi tentado novamente: a API não pôde abrir 127.0.0.1:8000 (bloqueio de porta do ambiente). Não houve verificação visual real nem aprovação do cenário E2E no navegador. As regras normativas que já estavam pendentes permanecem pendentes; esta simplificação não habilita demanda ou previsão mínima normativa.

## Revisão de código e decisões de produto — 0.7.0, 22/10/2026

Revisados os caminhos de schemas/validação, catálogo e seleção de referências, matemática, orquestração, persistência/versionamento/histórico, segurança ASGI/CORS, PDF/JSON, cliente API, debounce/cancelamento, navegação, listas, formulários e ações. Scripts de continuidade e ferramentas também receberam lint/formatação. Isto registra uma revisão de engenharia e testes; não é certificação de segurança, ausência universal de bugs ou validação normativa.

### Avaliação individual dos campos de equipamentos

“Não” significa não solicitar na interface atual; dados/API/históricos continuam compatíveis e legíveis. Não houve descarte de parâmetros existentes nem alteração do catálogo pelo editor.

| Campo/opção | Realmente necessário? | Decisão e motivo |
| --- | --- | --- |
| Equipamento/referência | Sim | Manter seleção comum; variantes documentadas continuam no catálogo/snapshot. |
| Descrição/identificação | Sim | Essencial no personalizado; avançada nos demais para distinguir instâncias. |
| Quantidade | Sim | Inteiro positivo; mantém identidade, foco e valores manuais. |
| Potência elétrica unitária W | Sim | Essencial; desconhecida continua null, sem converter BTU ou kWh em W. |
| Tensão nominal | Talvez | Essencial somente no escopo corrente; avançada nos demais, mesmo valor preservado. |
| Fator de potência | Talvez | Avançado, necessário para VA/A; nunca preencher 1 por conveniência. |
| Configuração de fases | Talvez | Necessária à corrente; não inferir monofásico ou equilíbrio por tensão. |
| Hipótese resistiva FP=1 | Talvez | Declaração explícita para tipos aplicáveis, com alerta; não ativada automaticamente. |
| Tipo de equipamento | Sim | Avançado: determina parâmetros aplicáveis; mudança exige reconferir potência. |
| Natureza iluminação/geral/específica | Sim | Classifica soma de iluminação. Iluminação bloqueada para lâmpadas e não oferecida indiscriminadamente aos demais tipos. Projetos antigos preservados. |
| Origem da potência | Sim | Avançada: estimativa/placa/fabricante sem afirmar verificação independente. |
| Categoria | Sim | Avançada; agrupamento e edições manuais preservados ao selecionar capacidade AC. |
| Fonte técnica | Sim | Avançada para rastreabilidade da entrada manual; nunca substituir silenciosamente placa por referência. |
| Tecnologia da lâmpada | Talvez | Manter: explicita tipo/hipótese resistiva e invalida sugestão incompatível. |
| Tecnologia genérica dos demais aparelhos | Não | Removido input livre sem cálculo; valor histórico preservado. |
| Marca | Não como solicitação | Continuar sem input; referência e dados antigos legíveis. |
| Modelo | Não como solicitação | Continuar sem input; referência e dados antigos legíveis. |
| Capacidade térmica AC BTU/h | Talvez | Manter: conversão térmica e seleção de referência real compatível. Não é consumo. |
| Tipo de AC | Talvez | Avançado: evita aplicar sugestão split a outro tipo. |
| Compressor AC | Talvez | Avançado: evita referência inverter incompatível com convencional. |
| Tamanho de TV em polegadas | Não | Removido input: não há inferência documentada entre tamanho e potência. Valor antigo legível. |
| Modo/unidade do motor W/cv/hp | Sim | Mantido; separa entrada elétrica de saída mecânica, sem presumir rendimento. |
| Potência mecânica | Talvez | Solicitar somente no modo mecânico. |
| Rendimento | Talvez | Obrigatório apenas no modo mecânico; zero/maior que 1 inválidos. |
| Saída de aquecimento de micro-ondas | Não no estudo atual | Removido input sem efeito; dado antigo preservado. Não representa entrada elétrica. |
| Potência máxima de refrigeração | Não no estudo atual | Removido input duplicado/informativo; dado antigo preservado; potência adotada segue editável. |
| Corrente nominal de placa motor/AC | Não como entrada deste cálculo | Removido input informativo; dado antigo legível separado da corrente calculada. |
| Corrente de partida de motor | Não nesta etapa | Removido input sem cálculo de partida/proteção; dado antigo preservado. |
| Corrente máxima AC | Não nesta etapa | Removido input sem dimensionamento; dado antigo preservado. |
| Consumo mensal por unidade kWh | Talvez | Tornou-se útil: opcional para qualquer equipamento, entra no estudo de consumo e prevalece sobre horários. |
| Horas efetivas/dia | Talvez | Novo, opcional, 0–24; sem padrão fictício ou ciclo presumido. |
| Dias de uso/mês | Talvez | Novo, opcional, inteiro 0–31; não presumir mês de 30 dias. |
| Classificação normativa de demanda | Não habilitar ainda | Continua sem input público; preservar valor legado sem alegar validação normativa. |
| Restaurar referência | Sim | Restaura snapshot explicitamente; não automático ao modificar um valor manual. |
| Duplicar | Sim | Nova identidade, cópia independente, quantidade e parâmetros preservados. |
| Remover | Sim | Confirmação identifica a carga, sem modificar catálogo. |

Projeto: tarifa R$/kWh é opcional e sem valor padrão; área/perímetro/pontos continuam cadastrais. Município/UF identificam o projeto e distribuidora continua candidata manual. Pavimentos/tipo de residência são metadados opcionais secundários. Tensão geral continua sem controle duplicado. Escopo “normativa” não é mais oferecido para novos estudos enquanto indisponível; um projeto legado nesse escopo pode sair dele e mantém seus dados. Apresentações simples/técnica exibem o mesmo resultado do backend.

### Achados corrigidos e organização

- Controles de placa sem operação útil foram retirados sem apagar dados; três controles básicos nos equipamentos comuns, com extras específicos condicionais.
- Substituída a descrição antiga que dizia que parâmetros de placa apareciam no PDF: exportação continua resumida, parâmetros históricos ficam na origem dos dados dentro do app.
- `EnergyFields` separa formulário opcional de consumo da edição de identidade/referência; `energy.py` concentra aritmética de energia, sem FastAPI/Pydantic/ORM. Tarifa integra a chave de recálculo e digest, impedindo exportar custo antigo para tarifa nova.
- Removidas atualizações de estado redundantes em efeitos: foco não dispara limpeza de estado; retry limpa seus erros na própria ação; seletor de sugestões remonta ao mudar tipo de ambiente; referência de entrada atual sincroniza no layout effect, preservando proteção de edições durante gravações.
- `Field` deriva controles/erros sem mutação capturada em callbacks. Sem desabilitar regras do lint para esconder erros encontrados.
- Links de referências salvas aceitam HTTP(S) sem credenciais; protocolos executáveis/dados não viram links. Frontend recebe cabeçalhos de proteção, foco/movimento reduzido e hover coerente com estado desabilitado.
- ESLint/TypeScript, Prettier e Ruff com configuração local explícita. Fonte Python/TS/TSX/CSS/config/testes formatada; `api.generated.ts` continua exclusivamente gerado por types:sync. Ruff não verifica estilo normativo nem substitui revisão matemática; exceção E402 somente no teste executável que ajusta sys.path.
- npm audit inicial: dois alertas críticos e um moderado no conjunto Vitest/tinypool/mocker. Vitest atualizado para 4.1.12. Configuração eslint-config-next trazia a dependência braces com alerta sem versão corrigida no conjunto consultado; removida em favor de ESLint 10, typescript-eslint e react-hooks, sem essa cadeia. Não foram adicionados overrides que mascarassem o relatório.

### Limites e evolução

Permanecem sem texto normativo autorizado completo: iluminação mínima, previsão TUG, demanda, condutores/proteção/queda de tensão. Não habilitados por estimativa. Não se infere potência elétrica de BTU, tela ou consumo mensal; nem corrente total da residência somando correntes de equipamentos em tensões/fases diferentes. Próximas proteções concretas e ordem de implantação em security.md e roadmap.md. Resultados efetivos de testes e preservação em CURRENT_STATE/SESSION_HISTORY.


## Revisão de uso real — Casa do Codex (22/10/2026, versão 0.10.1)

Solicitação: revisar o próprio preenchimento e confrontar formulário, cálculos, persistência e arquivos. Conferência real em Chromium no localhost:3000; PDF aberto/renderizado independentemente em MuPDF; JSON confrontado campo a campo com SQLite. Exemplo fictício, não residência medida. Não foi correto tratar a criação inicial como demonstração de todos os fluxos: variantes estavam inacessíveis e restaurar referência perdia o estudo de consumo; corrigidos nesta entrega. Falhas de seletor nos scripts temporários iniciais não significavam falha ao salvar da aplicação. O novo teste E2E passou a ler o arquivo baixado, pois a leitura direta da resposta de download no Playwright retornava corpo vazio.

### Preenchimento e utilidade dos campos

| Campo/grupo | Avaliação e tratamento |
| --- | --- |
| Nome, UF, município e distribuidora | Úteis para identificar o estudo; Enel SP foi seleção manual para o cenário, sem associação territorial automática. Demanda continua indisponível. |
| Área construída, pavimentos e tipo | Úteis para contexto; não multiplicam cargas. 110 m² construídos, 96 m² úteis de ambientes, um pavimento; diferença explicitada para paredes/elementos construtivos. Pavimentos/tipo estavam ausentes do relatório, agora preservados. |
| Tarifa | Opcional; R$1,00/kWh é hipótese expressa, não tarifa oficial ou conta real. Sem tarifa, custo continua ausente. |
| Observações | Úteis para hipóteses e limites; divididas em parágrafos e ampliadas para aparelhos com ciclos. Não substituem informações obrigatórias de equipamento. |
| Tensão de referência do projeto | Não preenche outras tensões nem calcula corrente de equipamentos; legado preservado, sem novo campo comum. |
| Nome/tipo de ambiente | Necessários para identificação e aplicação limitada de luz/TUG. Todos os nove ambientes internos classificados explicitamente. |
| Área e perímetro por ambiente | Úteis para previsão residencial; não exigidos para somar aparelhos em W. Geometrias retangulares coerentes; sem avaliação de planta/locação. |
| Pontos de luz e tomadas | Úteis para comparar quantidade cadastrada com mínimos; não contam como eletrodomésticos nem duplicam iluminação nominal. Quantidades acima dos mínimos são preservadas. |
| Equipamento, quantidade e W | Úteis para instalada e energia por uso. Referências documentadas/genéricas não foram chamadas de medição de placa. 24 cadastros correspondem a 28 unidades; relatório agora distingue. |
| Tensão, FP e configuração | Úteis para VA/corrente; secundários quando só há W/energia. Tensão adotada explicitamente no cenário; FP desconhecido não inventado, total VA nulo. Não forçar FP=1 em motor/eletrônicos. |
| Capacidade BTU/h e características do AC | Úteis para identificar a referência; não dimensionam o ambiente nem equivalem a potência elétrica. Referência nominal de 1.130 W preservada. |
| Variantes documentadas | Úteis: 127/220 V e potências do chuveiro estavam no catálogo mas inacessíveis diretamente. Seletor somente no painel avançado e somente quando há variantes do mesmo equipamento. Não acrescentar seletor redundante onde não há opções. |
| Horas/dia e dias/mês | Necessários se a energia for estimada pela potência. São horas efetivas equivalentes, não duração de ciclo ou tempo na tomada. Não presumir ciclo, standby ou média física de inverter. |
| kWh mensal unitário | Útil e prioritário se houver etiqueta/medição; não preencher com dado inventado. Neste exemplo não há etiqueta/medição real, portanto mantido vazio; cenários por horários explícitos. |
| Fonte/origem/identificação/categoria | Úteis para rastreabilidade/organização, mantidos no avançado. Marca/modelo são da referência e não prova do aparelho existente. Exportações sem URLs e memória extensa. |
| Potência mecânica, rendimento, partida e demais dados legados | Não necessários aos equipamentos deste cenário: mantidos condicionais a motores/avançado ou apenas na origem quando informativos. Não preencher por obrigação, não inventar rendimento/corrente de partida. |
| Demanda/classificação da concessionária | Não habilitar por haver consumo calculado. Falta procedimento validado para o atendimento; sem coeficientes ou padrão de entrada inventados. |

### Inventário conferido individualmente

Potências adotadas do catálogo; tempos são hipóteses explícitas. A energia abaixo foi recalculada independentemente com Decimal a partir das entradas, sem modificar fórmulas do produto.

| Ambiente | Equipamento | Qtd. | W/un. | V | h/dia × dias/mês | kWh/mês da quantidade |
| --- | --- | --- | --- | --- | --- | --- |
| Sala de estar | Lâmpada LED | 2 | 9 | 127 | 5 × 30 | 2.7 |
| Sala de estar | Televisor | 1 | 130 | 127 | 4 × 30 | 15.6 |
| Sala de estar | Ventilador | 1 | 140 | 127 | 4 × 20 | 11.2 |
| Cozinha | Lâmpada LED | 2 | 9 | 127 | 4 × 30 | 2.16 |
| Cozinha | Geladeira | 1 | 130 | 127 | 8 × 30 | 31.2 |
| Cozinha | Micro-ondas | 1 | 1050 | 220 | 0.25 × 30 | 7.875 |
| Cozinha | Air fryer | 1 | 1500 | 127 | 0.4 × 20 | 12.0 |
| Cozinha | Liquidificador | 1 | 550 | 127 | 0.1 × 15 | 0.825 |
| Cozinha | Cafeteira | 1 | 550 | 127 | 0.25 × 30 | 4.125 |
| Cozinha | Lava-louças | 1 | 1400 | 220 | 1 × 12 | 16.8 |
| Quarto principal | Lâmpada LED | 1 | 9 | 127 | 3 × 30 | 0.81 |
| Quarto principal | Ar-condicionado | 1 | 1130 | 220 | 4 × 20 | 90.4 |
| Quarto de solteiro | Lâmpada LED | 1 | 9 | 127 | 3 × 30 | 0.81 |
| Quarto de solteiro | Ventilador | 1 | 140 | 127 | 6 × 20 | 16.8 |
| Escritório | Lâmpada LED | 1 | 9 | 127 | 6 × 22 | 1.188 |
| Escritório | Computador | 1 | 300 | 127 | 6 × 22 | 39.6 |
| Banheiro | Lâmpada LED | 1 | 9 | 127 | 1 × 30 | 0.27 |
| Banheiro | Chuveiro elétrico | 1 | 7500 | 220 | 0.5 × 30 | 112.5 |
| Banheiro | Secador de cabelos pequeno | 1 | 600 | 127 | 0.1 × 15 | 0.9 |
| Lavanderia | Lâmpada LED | 1 | 9 | 127 | 1 × 30 | 0.27 |
| Lavanderia | Máquina de lavar | 1 | 600 | 127 | 1 × 12 | 7.2 |
| Circulação | Lâmpada LED | 2 | 9 | 127 | 2 × 30 | 1.08 |
| Garagem | Lâmpada LED | 2 | 9 | 127 | 1 × 30 | 0.54 |
| Garagem | Motor de portão | 1 | 370 | 127 | 0.05 × 30 | 0.555 |

Totais independentes: 16.207 W instalados, iluminação nominal 117 W incluída, 377,408 kWh/mês; custo ilustrativo R$377,41 com a tarifa declarada. Luz prevista 1.500 VA e TUG 6.700 VA em bases separadas da instalada, sem soma W/VA. Os nove ambientes têm quantidades cadastradas suficientes no escopo quantitativo, sem certificação de localização/circuitos/segurança da instalação. Não faltar entrada para o cálculo escolhido não significa ter informações para todas as finalidades.

### Defeitos corrigidos e verificações

- Restaurar sugestão preserva energia e horários; troca de variante preserva potência manual válida. Seleção de outro equipamento continua explícita. Regressões unitárias e E2E para referência 127 V/5.500 W ↔ 220 V/7.500 W, manual 5.000 W, restauração e energia 112,5 kWh.
- JSON não confunde manual_override por tensão/uso com edição de potência. Acrescenta características, IDs para ambientes homônimos, natureza da potência e limites do consumo. Unidades continuam explícitas mesmo quando o resultado é nulo. Sem dump de referências/fórmulas.
- PDF arredonda somente moeda exibida para centavos, preserva precisão no JSON; títulos/tabelas com maior reserva de espaço, características da casa, 24 cadastros/28 unidades, identificação da potência máxima da TV e genéricas onde necessário. Texto repetido de referência nominal removido. Arquivo final do caso tem cinco páginas, conferidas por extração e imagens de páginas representativas em MuPDF.
- Casa do Codex continua salva com o mesmo ID. Nesta revisão só as observações foram alteradas; entradas numéricas, equipamentos, snapshots, cadastro global e demais sete projetos preservados. Históricos anteriores mantidos.
- 252 pytest +11 subtestes, 85 frontend, 10 E2E e cinco continuidade aprovados; TypeScript/build webpack, lint/formatação, contratos, Alembic check e pip check aprovados. E2E usa banco isolado. Navegação real com nove ambientes/24 cargas em 320/390/768/1024/1440 sem overflow horizontal e sem pageerror; PDF/JSON baixados com nome Casa do Codex.

### O que permanece necessário

Para estimativa física mais representativa: substituir hipóteses por hábitos observados/etiqueta/medição, especialmente TV em potência máxima, refrigeração, AC, lavadora e lava-louças; cadastrar outros aparelhos e standby quando relevantes. Não existe certeza sobre consumo real desta casa fictícia. Não foi necessário acrescentar eletrodomésticos, consumo medido fictício, FP ou rendimentos para preencher campos opcionais.

Pendências estruturais conhecidas não resolvidas por este preenchimento: recuperação de rascunhos não enviados, autenticação/autorização para uso remoto, associação territorial oficial completa e demanda validada por distribuidora. Impressão física, leitores de tela reais, Windows/PostgreSQL e pentest não executados. A revisão não garante ausência de todo bug ou conformidade integral.


## Residência do CODEX — segundo projeto pela interface (22/10/2026)

Novo projeto independente da Casa do Codex, ID `b18c0f1f-3a6c-4c39-ad50-840fbe7bf9dc`. Apartamento fictício de 70 m² para duas pessoas, 60,5 m² úteis nos oito ambientes; um pavimento da unidade, sem consumo das áreas comuns. Dimensões retangulares plausíveis registradas nas observações, sem alegar levantamento físico, planta executiva ou dimensionamento de condutores/proteções. Preenchimento por Chromium/Playwright em localhost3000: Criar novo projeto → metadados → ambientes → catálogo/cargas personalizadas → variantes → previsão luz/TUG → Salvar projeto HTTP201 → PDF/JSON → recarregar e reabrir biblioteca. Não criado por SQL ou POST direto. 21 cadastros/27 unidades; tarifa ausente, FP desconhecido preservado; hipótese resistiva explícita apenas no chuveiro.

Referências reais e premissas: LG S3-Q09AA33A (9.000 BTU/h/800 W/220 V), Lorenzetti Advanced 6.400 W/220 V e LEDs/documentação do catálogo; geladeira RE31 127 V/72 W e 13,1 kWh/mês conforme página atual do fabricante, sem confundir com ficha antiga de consumo diferente. Lavadora LAC09 127 V/495 W conforme ficha 2017; guia oficial2019 documenta 0,26 kWh/ciclo Pesado Sujo, com hipótese de oito ciclos/mês →2,08 kWh/mês, sem converter duração do ciclo em funcionamento contínuo. Entradas mensais obtidas usando os helpers puros existentes de calculations/energy.py para o cenário, sem novas fórmulas na aplicação. Monitor Dell P2422H com 48 W máximos na carga e referência de12 W em uso ativo durante6 h×22 dias→1,584 kWh/mês; desligado da rede fora desse uso no cenário. Mac mini M2/2023/24GB/2TB com referência CPU máxima de50 W; Deco S7 US com15,7 W máximos incluindo adaptador, não a potência DC do adaptador. Parcelas por horários em potência máxima são cenários conservadores, não médias medidas. Cocção principal a gás, sem fogão/forno elétricos ou motor de portão na unidade. AC e cargas com ciclos usam horas equivalentes explicitamente hipotéticas. Todas as fontes foram consultadas; não inventar FP/rendimento ou tarifa para completar opcionais.

Fontes primárias consultadas (mantidas também em Fonte técnica de cada nova carga; sem adicionar catálogo global):

- Electrolux RE31, especificações atuais: https://loja.electrolux.com.br/geladeira-refrigerador-degelo-pratico-240l-cycle-defrost-branco-re31-electrolux/p . Abertura integral excedeu limite do navegador de pesquisa; especificações da página foram recuperadas pela busca oficial direcionada (72/70 W,13,1 kWh/mês). Valor mensal tratado como referência informada pelo fabricante, não leitura física de etiqueta nem medição.
- Electrolux LAC09, ficha2017, p.2/código21081JBA106: https://www.electrolux-ui.com/DocumentDownLoad.aspx?DocURL=2017%5CA05%5C771501LAC09isPT.pdf . Guia rápido Out19 revC/rev005, p.2: https://api.electrolux-medialibrary.com/asset/396da2fc-4c34-484b-aadb-6d9b5bcefba4/E4RM3Q/f6fb5e5e-8ac5-455a-87f6-d2eb01bd8a3a/ORIGINAL/f6fb5e5e-8ac5-455a-87f6-d2eb01bd8a3a.pdf . Tabela Inmetro indexada corroborava0,26, mas link integral retornou404: não utilizada como única evidência.
- LG S3-Q09AA33A: https://www.lg.com/br/ar-condicionado-residencial/dual-inverter-split/s3-q09aa33a/ . Lorenzetti Advanced tabela de variantes: https://www.lorenzetti.com.br/produto/advanced-multitemperaturas/ . Sem declarar adequação térmica, circuito ou padrão de entrada por esses dados.
- Apple Mac mini M2: https://support.apple.com/pt-br/103253 . Dell P2422H: https://www.dell.com/en-gb/shop/dell-24-monitor-p2422h/apd/210-azyx/computer-monitors . TP-Link Deco S7 US, ficha2023,p.4: https://static.tp-link.com/upload/product-overview/2023/202308/20230807/Deco%20S7%28EU_US%291.20_1.0_Datasheet_PT.pdf . Versões e condições não universalizadas.

Inventário exportado e conferido com os campos salvos:

| Ambiente | Área m² | Perímetro m | Luz/TUG cadastrados | Potência W | kWh/mês |
| --- | --- | --- | --- | --- | --- |
| Sala de estar e jantar | 18 | 18 | 2/5 | 181.7 | 25.374 |
| Cozinha | 8 | 11.4 | 1/5 | 3740 | 27.3875 |
| Quarto do casal | 12 | 14 | 1/4 | 818 | 49.08 |
| Quarto de hóspedes e trabalho | 9 | 12 | 1/4 | 247 | 15.474 |
| Banheiro social | 4.5 | 9 | 1/1 | 6409 | 57.87 |
| Área de serviço | 4 | 8 | 1/3 | 504 | 2.215 |
| Circulação íntima | 3 | 8 | 2/1 | 18 | 0.54 |
| Hall de entrada | 2 | 6 | 1/1 | 9 | 0.135 |

Totais: 11.926,7 W, iluminação nominal126 W incluída;178,0755 kWh/mês (apresentação arredondada178,076). Luz prevista1.040 VA/TUG5.900 VA, sem soma com W; nenhum ponto faltante no escopo quantitativo dos oito ambientes. Ausência de tarifa→custo nulo; FP não publicado→VA total nulo. Demanda regional permanece nula; hipótese resistiva gera alerta técnico explícito, não erro de cadastro. Não esconder o aviso apenas para obter tela sem alertas.

Conferências: criação201/reabertura, oito ambientes/21 cargas, ausência de inputs inválidos e erros JavaScript, sem overflow390px. PDF/JSON baixados como Residência do CODEX; JSON confrontado com todas as quantidades/W/energia/vínculos; PDF aberto/extraído/renderizado em MuPDF independente, seis páginas, nome/acentos/valores/tarifa ausente conferidos. Sem impressão física. Oito projetos anteriores integralmente idênticos ao backup /tmp/eletroprojeto-before-residencia-codex.db;27 históricos anteriores preservados, novo total28, sete revisões; banco íntegro/FK ok/migração0003. Sem alteração de código, fórmulas, regras, catálogo ou migrações; suíte geral não repetida porque a tarefa foi cadastro, validado pelo fluxo real e conferência dos arquivos. Versão0.10.1/motor0.6.0/JSON1.2 mantidos. Evidências/arquivos temporários em /tmp/residencia-codex-* e /tmp/Residência do CODEX.pdf/json.


## Organização e limpeza — 23/10/2026

Pedido: revisar raiz/pastas, organizar e excluir o necessário. Inventário dos 156 arquivos próprios com hashes, leitura automatizada integral e validação sintática Python/JSON; revisão de documentação/configurações e identificação das saídas locais. Dependências instaladas não receberam auditoria linha a linha e foram preservadas pelos locks/uso real. Inventário privado: `.checkpoints/cleanup-inventory-before-20261023.json`.

- PDFs NDU7.0 e6.3 movidos para references/energisa (6.3 em historico), hashes preservados; metadados da API mantêm nomes originais como proveniência. Dois Zone.Identifier removidos; bytes recuperáveis no manifesto privado. PDFs excluídos do Git/ZIP de código.
- Cinco reviews movidos para docs/history; índice docs/README e references/README. Antigo CURRENT_STATE integralmente preservado como history/state-before-organization.md, ajustando apenas links relativos; novo CURRENT_STATE apresenta o resumo vigente. README/KNOWN_ISSUES corrigidos onde ainda tratavam lint, autenticação, catálogo, PostgreSQL e Windows como não implementados. SESSION_HISTORY anterior não foi reescrito.
- Removidas 15 entradas regeneráveis/dispensáveis, 1.984.089 bytes de conteúdo: caches Python/pytest/Ruff/TypeScript, resultados temporários e marcadores de download. Manifesto `.checkpoints/cleanup-20261023.json`; espaço alocado em disco pode diferir. Instalações .venv/.venv-windows/node_modules/egg-info, Next em uso/build, banco/backups, Git, checkpoints, migrações e integrações privadas preservados. Nenhum arquivo de execução/contrato alterado (hashes comparados).
- Recuperação anterior `.checkpoints/20261023T181839782078Z`: ZIP/hashes/SQLite/bundle Git e restauração/clonagem isoladas verificados. Banco real íntegro/FK sem violações, 9 projetos/29 históricos/7 revisões, conteúdo integral das três tabelas igual ao checkpoint. Alembic check sem operações novas.
- Verificações desta limpeza: backend320 testes+85 subtestes; frontend90; tipos/lint; continuidade/backup8; links Markdown locais sem destinos ausentes; hashes dos dois PDFs iguais; git diff --check. Teste backend no sandbox não progrediu e foi interrompido, repetição fora dele aprovada. Primeira chamada aos testes de scripts usou diretório inexistente, corrigida para os dois arquivos reais. Comparação SQLite inicialmente usou cwd incorreto; repetida corretamente e aprovada.
- Não repetidos build, E2E, PostgreSQL nem Windows: código/contratos/configurações de execução permaneceram byte a byte iguais; evidências anteriores continuam históricas. API8000 health0.12.0/motor0.7.0 e frontend3000 HTTP200 confirmados nesta limpeza; nenhum serviço reiniciado. Sem push/publicação/cópia externa. Retenção dos checkpoints sinalizada para revisão; nenhum backup removido.

## Revisão geral — 0.17.0, 24/10/2026

Revisados contratos e fluxos de cálculo, cadastro, persistência/concorrência, exportação, revalidação, autenticação, biblioteca, formulários, requisições, scripts e configuração de qualidade. Não houve recriação do produto, descarte de funcionalidades úteis, mudança de tabelas normativas ou promessa de ausência universal de bugs. Esta é uma revisão de engenharia com verificações funcionais, não certificação normativa/pentest/teste de carga.

| Área | Decisão e resultado |
| --- | --- |
| Motor elétrico | Manter funções puras, Decimal e separação de W/VA/energia. Corrigido digest que omitia circuitos e entrada; motor0.9.1. Acrescentados exemplos independentes de soma vetorial com FP misto e igualdade/ultrapassagem do limite de corrente. Nenhum coeficiente alterado. |
| API e histórico | Manter rotas compatíveis e versionamento. Tipar sessão/login, prévia e projeto recalculado. Centralizar último histórico e ordenar por versão, pois timestamps iguais podiam recuperar resultado antigo. Snapshots históricos continuam com formato original. |
| Projetos e recuperação | Manter autosave, rascunhos, idempotência, conflitos, biblioteca/lixeira e exclusão definitiva explícita. Remover uma carga limpa somente suas associações na edição; dados anteriores/catálogo não são regravados. |
| Circuitos/entrada | Manter estudos opcionais condicionados ao escopo. Mostrar capacidade de interrupção, base/faixa e fontes já presentes na API. Informar cargas não associadas, impedir novas duplicações e permitir reparo explícito de vínculos ausentes. Campo de nominais acompanha valores carregados, mantém vírgula decimal durante edição e recusa hexadecimal. Troca de projeto renova o estado local do estudo. |
| Revalidação | Integrar a prévia existente à interface e permitir registrar nova versão conscientemente. Bloquear comparação com edição não salva, verificar versão devolvida e ocultar prévia após mudar entradas. Registrar não troca valores manuais nem apaga histórico. |
| Cliente HTTP e acesso | Centralizar erros de formulários/relatórios e normalizar HeadersInit, preservando chave idempotente e CSRF. Nova tentativa de consulta de sessão sem recarregar a página. Sessão usa contrato gerado. |
| Estrutura frontend | Extrair inicialização independente/cancelável para hook próprio; manter edição na página e apresentações em componentes. Preservar foco, debounce, cancelamento, snapshots vinculados às entradas e aparência aprovada. |
| Biblioteca e ferramentas | Preservar consulta, leitores, fontes, originais, OCR e auditorias. Não refazer OCR/importação/descarte sem nova necessidade. CLI próprias incluídas no Ruff do CI; Vitest inclui testes .ts além de .tsx. Busca textual especializada e desempenho sob tráfego permanecem pontos futuros de medição. |
| Documentação | Consolidar architecture.md em estado atual; corrigir afirmações antigas sobre ausência de autenticação/PostgreSQL/resumos e atualizar roadmap. Histórico de decisões continua em SESSION_HISTORY/CHANGELOG. |

Verificações efetivas:394backend+85subtestes em SQLite e394+85 em PostgreSQLQA,16scripts,103frontend,19E2E e1HTTPS. Último ajuste de nominais/escopo validado por103frontend e2E2E dirigidos;tipos/lint/formatação/buildwebpack aprovados. Ruff61arquivos,migraçõesSQLite/PG,contratos gerados,pipcheck echecagemTS sem locais/parâmetros não utilizados aprovados. Npm audit e pip-audit do lock sem vulnerabilidades conhecidas. Teste E2E de revalidação força somente a flag histórica para exercitar o botão;prévia,registro,histórico e preservação do valor123,456789W×3=370,370367W usam API/bancoQA reais. Smoke local de consulta real sem gravação,sem pageerrors/overflow390px;capturas inspecionadas.

Dados reais comparados integralmente nas12tabelas com checkpoint20261024T042034311554Z,sem divergência:9projetos/30históricos/8revisões e acervo preservados. Dependências de execução não mudaram;sem nova migração,sem exclusão de dados,sem push/publicação. Não executados Windows/leitor de tela real/inspeção elétrica física,pentest ou teste de carga nesta revisão. Pendências técnicas e normativas permanecem no roadmap/KNOWN_ISSUES.
