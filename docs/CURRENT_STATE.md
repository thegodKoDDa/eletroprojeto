# Estado atual — EletroProjeto0.17.0 / motor0.9.1

## Revisão geral — 24/10/2026

Pedido: revisar frontend/backend/API, corrigir integrações, organizar código e concluir a sessão preservando o produto. Corrigidos digest de relatórios sem circuitos/entrada, desempate de histórico, cabeçalhos HeadersInit, mensagens de validação das exportações, consulta de sessão sem nova tentativa, associações de cargas removidas e estado local das correntes de disjuntores ao carregar outra edição. Inicialização extraída para use-workspace-resources; leitura de último histórico e interpretação de erros centralizadas. Vitest inclui .test.ts e .test.tsx; CI verifica todas as CLI Python próprias.

Novidade integrada: prévia tipada de revalidação na interface e registro explícito em nova versão pela API existente. Exige edição salva, verifica versão e preserva alterações durante a requisição. Circuitos mostram cargas não associadas, bloqueiam novas associações duplicadas, permitem reparar referências ausentes e apresentam capacidade de interrupção, limites e dados de enquadramento de entrada que já vinham da API. Não foram removidas funcionalidades úteis nem ampliadas regras normativas. Coeficientes/fontes mantidos; motor0.9.1 identifica a correção de rastreabilidade. Arquitetura consolidada e documentação de segurança/roadmap atualizada.

## Base funcional e escopo preservados

Ordem24/10/2026: concluir pendências da integração e descartar materiais sem utilidade. Concluídos OCR/triagem e métodos específicos de circuitos/proteções/entrada,com testes. NÃO equivale à revisão técnica humana integral de2mil documentos nem a dimensionamento final universal. Uso local; publicação/impressão física/backup externo seguem fora do escopo. JSON de relatório1.4,schema0007. Sem nova potência de catálogo ou regra presumida.

## Acervo e descarte

199PDFs descartados com autorização:2livros sem conteúdo elétrico e197relatórios de interrupção/expurgo,4.949.265.589bytes. Fontes/metadados preservam motivo e hash; binários desses199 foram excluídos. Livro/relatório precisa de justificativa específica; classificação genérica não autoriza apagar manual técnico. Os demais2.196objetos (3.597.033.481bytes) e referências Energisa anteriores foram mantidos.

Acervo atual:2.082documentos (2.045PDFs,27guias,6modelos,4diagramas),51.324unidades de leitura (51.287páginasPDF+37unidades didáticas),3.788fontes. OCR nas1.060páginas nativas sem texto:963com texto,78vazias detectadas e19vazias com ruído conferidas visualmente. Nenhuma falha de OCR; nenhuma página nativa sem texto por processar. Total51.227com texto e97vazias. Texto OCR marcado não revisado/confiança,sem habilitar cálculos pelo reconhecimento. Tesseract5.5/por+eng instalado por extração de pacotes oficiais somente em/tmp/eletroprojeto-ocr-tools,sem instalação global.

Migração0007 registra método/nota/confiança. Auditoria `references/library/maintenance.json` mantém descartes e hashes de textoOCR; inventário original imutável. verify conhece descartes autorizados e verifica conteúdoOCR; import do histórico bloqueado para não ressuscitar descartes. Banco e4arquivos de auditoria entram no checkpoint; objetos seguem fora do Git/ZIP de código,não são cache.

## Cálculos integrados

- Estudo de circuitos no projeto: associação exclusiva de cargas,quantidade contada uma vez,soma P/Q e corrente de circuito. Potência/FP/tensão/configuração desconhecidos ou incompatíveis impedem seleção,sem subtotal ou zero substituto.
- Subconjunto NBR5410:2004/VC2008:Cu/PVC70°C,B1/B2,2condutores carregados,seções1,5–35mm²,temperatura10–60°C em passos5,agrupamento homogêneo1–8. Seleção de seção e disjuntor entre nominais informados,Iz corrigida,Ib≤In≤Iz,I2≤1,45Iz somente com confirmação da condição de duração; caso contrário I2≤Iz. PE pela tabela58,no mesmo conduto. Fontes dos produtos/I2 não presumidas.
- Queda estimada em regime pelo modelo Prysmian2024 com aceitação explícita:ρCu0,0225Ωmm²/m,reatância0,08mΩ/m,cargas na extremidade. Limite terminal4%,total5/7% conforme origem e queda a montante explicitadas. Sem partida/harmônicas/modelagem de redes complexas.
- Verificações com dados adicionais explícitos:energia passante≤k²S² da fase,duração≤5s/k do cabo/fonte e mesmo disjuntor; essa restrição participa da seleção da seção. TN:Zs×Ia≤U0 e tempo tabela25,situações1/2,U0127/220V. TT:RA×IΔn≤UL,comDR compatível eULconferido. DR adicional até30mA quando exigência confirmada. Sem inferir tipo deDR,curva ou curto. Ensaios/PE/curto mínimo/DPS/seletividade e geometria não são certificados por essas verificações.
- Entrada:ESS/SP,rede220/127V,individual≤75kW,NDU0017.0tabela16/notas. Categoria por carga kW paraM/B ou demanda atual revisada kVA paraT,tensão das cargas respeitada,mínimos fase/neutro/aterramento conformePVC70 ouXLPE/HEPR/EPR90 e embutido/subterrâneo. PVCsubterrâneo/N.A./carga desconhecida/escopo não confirmado bloqueados. Disjuntor de faixa é apenas referência superior,não proteção escolhida.
- Formulários opcionais,debounce/cancelamento,resultado novo somente para entradas atuais; circuitos/entrada persistem em snapshots,drafts/autosave e conflitos. JSON1.4/PDF incluem resultados/fontes/pendências. Início/aside/compactação de equipamentos preservados. Relatórios não aprovam instalação ou ligação.

## Verificações

Validação desta revisão:394backend+85subtestes em SQLite e novamente394+85 em PostgreSQLQA;16testes de scripts;103frontend;19E2E completos e1HTTPS com duas contas. Após o último ajuste do estado das correntes,103frontend e2E2E dirigidos(circuitos/revalidação) repetidos e aprovados. Contratos gerados/tipos/lint/formatação/buildwebpack,Ruff de61arquivos Python,checagem adicional TS sem locais/parâmetros não utilizados,migraçõesSQLite/PG e pipcheck aprovados. Npm audit online e pip-audit do requirements.lock sem vulnerabilidades conhecidas. Sem nova dependência de execução ou migração.

Dados:12tabelas reais integralmente iguais ao checkpoint20261024T042034311554Z por hash de todas as linhas/colunas ordenadas:9projetos,30históricos,8revisões técnicas e todo o acervo preservados. QA usa bancos isolados; nenhum projeto real alterado. API0.17.0/motor0.9.1 reiniciada normalmente,PID863425/porta8000;frontend existente PID572313/porta3000 preservado e HTTP200 confirmado. Prévia real conferida sem gravação,sem pageerrors ou overflow390px;capturas em/tmp/eletroprojeto-review-real-{desktop,mobile}.png. Confirmar serviços na próxima retomada.

Não repetidos Windows,leitor de tela real,OCR ou inspeção elétrica física;sem teste de carga/implantação remota/pentest. Verificações anteriores do acervo continuam registradas acima. Commit/checkpoint final devem ser consultados em.checkpoints/latest.json,gerado depois do commit e restauração isolada. Sem push,publicação ou exclusão de dados. Próximo passo: manter regressões e ampliar somente os métodos/escopos documentados no roadmap,com fontes e exemplos independentes.

## Limites que permanecem

Outros métodos/materiais/fases,grupos especiais de demanda,geometria/localização de tomadas,dimensionamento integralDPS/seletividade/ensaio e associação municipal oficial ainda não implementados/validados integralmente. Arquivos elétricos válidos não foram apagados por estarem fora de um método habilitado. Regras fora do escopo retornam pendência. A leitura automática do acervo não comprova revisão semântica humana total. Roadmap e standards descrevem condições; não declarar toda a lista original concluída.
