# Formulários e relatórios — consumo residencial0.25.1

Comportamento de uso em [usage](usage.md), contratos/fluxos em [architecture](architecture.md), fórmulas em [calculations](calculations.md). Histórico anterior preservado em [history](history/README.md).

property_stage opcional: planned/construction/ready/renovation; residence_type conserva nomes livres antigos e oferece sugestões. utility_name é nome contextual opcional para distribuidoras fora dos candidatos existentes. municipality agora pode ficar vazio. Todos preservam manuais e snapshots, sem migração SQL destrutiva.

Energia unitária mensal/anual declarada ou horários efetivos são alternativas, não exigências cumulativas. Potência nominal de referência não é valor obrigatório. Campos elétricos opcionais podem fornecer indicadores adicionais, mas não bloqueiam kWh. Requisitos de fornecimento e configurações de instalação foram retirados da interface ativa.

JSON2.0 e PDF representam estimativas residenciais: identificação, imóvel e estágio, UF/distribuidora, ambientes/aparelhos, potência instalada, média diária anualizada, energia mensal/anual, custos, distribuições, parâmetros/fórmulas/fontes e premissas. Ausência de tarifa afeta custo; ausência parcial de energia identifica subtotal, nunca zera desconhecidos. Memória secundária na tela, incluída no relatório. Campos de fornecimento e cobertura normativa não aparecem.

Exportação recalcula no Python e exige digest, motor e revisão própria de estimativas correspondentes. Mudança enquanto exporta gera409, inclusive identidade do snapshot salvo. Nome legado expected_registry_version é token de revisão do motor, sem consulta a normas. PDF tem fonte incorporada, Unicode, quebra por largura/paginação e não executa HTML/rede.

Autosave, rascunhos, histórico, idempotência inicial, conflito409 e lixeira preservados. Dados anteriores não são regravados ao abrir. Resultado antigo continua montado para estabilidade de geometria mas oculto/aria-hidden/inert; debounce e abort impedem resposta antiga de virar atual. Troca de perfil mantém edição. Acervo carrega só por consulta explícita independente.

## Comparação opcional de cenários

O painel opcional compara edição e versão salva sem gravar. Suas diferenças são exibidas na tela; PDF/JSON exportam o cenário atual, sem tabela comparativa entre snapshots.

Vistoria 0.25.1: kWh mensais/anuais declarados tornam os campos de potência opcionais na apresentação; falta de potência é informação para completar W, não erro de consumo. Subtotais aparecem nos indicadores e tarifa já preenchida não é solicitada novamente quando faltam dados energéticos. Metadados legados continuam opacos, exigindo apenas números JSON finitos. Referência do comparador permanece no autosave e é trocada por ação explícita.
