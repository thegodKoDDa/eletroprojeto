# Revisão PDF, avisos e dependências — versão 0.2.0

## Diagnóstico e correções

O PDF anterior usava tabelas compostas por caracteres, repetia explicações/fontes extensas e apresentava identificadores internos em pendências. O novo layout mantém o gerador e a fonte incorporada, mas usa células posicionadas, cabeçalhos e faixas discretas, quebras por altura real e referências numeradas. Não foi alterado o design do site.

Seções: identificação, resumo, ambientes, quadro de cargas, demanda/previsão normativa, memória, pendências e referências. O quadro separa W/quantidades de V/VA/A para preservar legibilidade. Natureza elétrica é distinguida da categoria cadastral. Cabeçalhos e ambiente reaparecem em continuações. Fórmulas idênticas são registradas uma vez e identificadas por C1/C2 no quadro, mantendo todas as instâncias.

A revisão encontrou também uma divergência exclusivamente documental: resultados derivados arredondados apareciam em igualdades exatas. Agora usa-se ≈ quando necessário; somas repetidas são condensadas e entradas com seis casas permanecem exatas na memória. Nenhuma fórmula elétrica foi transferida ao frontend ou substituída por aproximação.

## Avisos e direcionamento

`notifications` diferencia erro de entrada, alerta técnico, pendência normativa, estimativa e informação. Cada aviso possui identificação estável, nomes do ambiente/equipamento, problema, solução, resultados afetados e alvo quando existe campo editável. O frontend agrupa os avisos e remove duplicações por identificação. Pendências normativas não viram uma mensagem vermelha por equipamento.

Corrigir informação usa o ID do controle, abre todos os detalhes ancestrais, posiciona a visualização, aplica destaque e dá foco. Campo corrigido é revalidado no próximo cálculo; avisos antigos não são mostrados como atuais durante o debounce. HTTP 422 conserva `detail` e acrescenta avisos localizados, com limites de preenchimento quando conhecidos. Casos estruturais sem campo editável recebem diagnóstico sem ação enganosa.

## Obrigatoriedade e preservação manual

A seleção discreta Requisitos para determina qual conjunto de ausências deve ser solicitado:

- W: quantidade e entrada elétrica; potência mecânica/rendimento quando esse modo é usado.
- VA: requisitos de potência e FP documentado ou hipótese resistiva explícita.
- Corrente: requisitos de VA, tensão e configuração.
- Normativo: dimensões, pontos e distribuidora pertinentes, sem habilitar regras ainda não verificadas.

Identificação exigida para salvar permanece separada da matemática. Área construída, pavimentos, tipo e tensão global podem ficar desconhecidos, em vez de exigir números para satisfazer o cadastro. Campos opcionais ainda respeitam unidade, faixa e formato quando informados. Projetos/cálculos independentes não são bloqueados por ausências sem relação com a operação escolhida.

A potência manual do ar-condicionado é protegida por `power_user_edited`, inclusive quando é estimativa; projetos antigos também têm diferenças contra a referência reconhecidas. Restaurar limpa essa proteção e reaplica a sugestão. Capacidade térmica não é convertida em consumo elétrico. Sugestões por capacidade dependem de referência real; tensão/FP personalizados são preservados nas trocas automáticas compatíveis. Alertas apontam divergências entre tensão/faixa documentada e valor utilizado, mantendo W fixo.

O motor continua reavaliando atomicamente o snapshot residencial. Debounce, cancelamento e rejeição de respostas obsoletas foram mantidos; não foi introduzido um grafo/cache cuja complexidade não se justificava. Histórico e parâmetros de projeto não são sobrescritos por uma atualização de referência.

## API e versão

Aplicação/API/pacote Python/frontend: **0.1.0 → 0.2.0**, atualização MINOR com campos adicionais e rotas existentes. Motor: **0.3.1 → 0.4.0**. Health retorna versões; OpenAPI identifica 0.2.0 e organiza módulos por tags. O rodapé mostra versão e comunicação sem expor configuração de infraestrutura. Erro de preenchimento é distinguido de falta de comunicação. Tipos TypeScript foram regenerados.

## Fórmulas e referências

Testes independentes cobrem quantidade × W; somas por ambiente/categoria; W/kW; P/FP em VA; conversão VA/kVA; corrente mono e trifásica equilibrada; potência mecânica/rendimento; BTU_IT/h térmico; energia e limites. Exemplo de propagação: 2 × 1760 W = 3520 W, FP 0,8 → 4400 VA e 10 A por unidade em 220 V. Reduzir tensão a 110 V mantém W/VA e produz 20 A; mudar FP para 1 e quantidade para 3 produz 5280 W/VA e 16 A por unidade.

O [portal oficial Energisa](https://www.energisa.com.br/normas-tecnicas) foi consultado e continua apresentando NDU-001 7.0, em vigor desde 01/11/2024. Isso confirma metadados, não valida as tabelas. Iluminação/TUG normativas, fatores e parcelas de demanda continuam pendentes/nulos. Não há declaração de conformidade ou dimensionamento final. Normas sem execução não são listadas no PDF como fontes de resultados calculados.

## Verificações reais

- **pytest: 95 aprovados e 11 subtestes**, incluindo regressões anteriores, requisitos por operação, dados inválidos, propagação de potência/tensão/FP/quantidade/categoria, versionamento, persistência, compatibilidade de metadados e PDF.
- **Vitest/RTL: 34 aprovados**, incluindo navegação até campo avançado, foco, remoção/reaparecimento, deduplicação, proteção de potência manual, escopo de requisitos, debounce/concorrência e exportação.
- TypeScript/typegen, OpenAPI, compileall e Alembic check aprovados. Sem migração ou escrita nos projetos reais nesta revisão; testes usam bancos isolados.
- PDF: validação de estrutura/xref/Unicode, margens e intervalos horizontais, colunas, cabeçalhos, oito seções, fontes utilizadas, agrupamento documental e precisão de apresentação. Casos com 35 ambientes, 120 equipamentos, nomes/textos longos, valores estimados, campos completos e informações ausentes.
- Inspeção visual: geração de PNGs a partir dos streams de texto/vetores do PDF, via `tools/preview_pdf.py`/Cairo; páginas normais, relatório parcial, quadro extenso e mosaicos das páginas foram observados. Foram corrigidos contexto perdido na continuação, divisão título/fonte e repetição de explicações. A ferramenta interpreta somente o subconjunto que este gerador emite; **não é um leitor PDF independente**. PyMuPDF não estava disponível para instalação; libvips instalado não suporta entrada PDF; não havia leitor PDF/Chromium disponível. Conferência final em leitor externo permanece necessária.
- Playwright foi tentado; Uvicorn não conseguiu abrir `127.0.0.1:8000`, antes de iniciar o navegador. O cenário foi ampliado com correção por aviso e exportação PDF, mas não foi executado de ponta a ponta.
- Build Webpack tentado: falha ao interpretar a saída de TypeScript `--showConfig`. Typecheck direto passou. `npm run lint` foi tentado e não há script/ferramenta configurado disponível. Não foram considerados aprovados.

## Como testar

No projeto existente, abra Resultados e memória e selecione Requisitos para. Com Corrente, apague tensão/FP de uma carga: o aviso deve mostrar o ambiente, equipamento, finalidade e ação. Use Corrigir informação, preencha valor válido, aguarde recálculo e apague novamente. Volte para W e confira que FP/tensão não são exigidos para a soma. Edite potência/quantidade e confira ambiente, total e memória.

No ar-condicionado, edite W manualmente e mude BTU/h: W deve permanecer. Restaurar reaplica a referência. Exporte PDF: confira oito seções, identificação de preliminar, fontes numeradas e estados. JSON conserva dados/precisão originais. Nenhum localhost ativo foi confirmado nesta sessão.
