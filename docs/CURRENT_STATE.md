# Estado atual — EletroProjeto0.16.0 / motor0.9.0

## Entrega e escopo

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

Testes finais:383backend+85subtestes;103API/auth/bibliotecaPGQA;92frontend,18E2E,1HTTPS,tipos/contratos/lint/formatação/build eRuff aprovados. Migração0007/checkSQLite/PG aprovados. Bibliotecas/objetos/hashesOCR verificados. 13testes de continuidade/backup também aprovados. Windows/leitor de tela/inspeção de instalação real não executados nesta entrega.

Dados:9projetos,30históricos,8revisões técnicas; todas as colunas das três tabelas idênticas ao checkpoint20261024T005824389645Z,com conferência integral após os testes. Nenhum projeto real editado. API0.16.0/motor0.9.0 confirmada por health, PID852766/porta8000;frontend existente PID572313/porta3000 responde HTTP. Estatísticas reais confirmadas:2.082documentos/51.324unidades. Confirmar serviços ao retomar. Checkpoint final por latest.json após commit e restauração real; sem push.

## Limites que permanecem

Outros métodos/materiais/fases,grupos especiais de demanda,geometria/localização de tomadas,dimensionamento integralDPS/seletividade/ensaio e associação municipal oficial ainda não implementados/validados integralmente. Arquivos elétricos válidos não foram apagados por estarem fora de um método habilitado. Regras fora do escopo retornam pendência. A leitura automática do acervo não comprova revisão semântica humana total. Roadmap e standards descrevem condições; não declarar toda a lista original concluída.
