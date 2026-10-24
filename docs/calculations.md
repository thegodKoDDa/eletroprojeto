# Cálculos disponíveis

## Demanda Energisa parametrizada — motor0.7.0

Implementação pura `calculations/energisa.py`, fonte/escopo/condições em [standards.md](standards.md). Endpoint tipado `/api/v1/calculations/energisa-demand`, inventário explícito e ausência dos grupos confirmada; sem inferir classificação do catálogo ou converter bases VA em W. d1 soma cada faixa da Tabela5; d2–d5 aplicam fator por quantidade total às potênciasW declaradas. Reservas não entram na demanda; todos os aparelhos declarados entram na conferência conservadora do limite instalado. Soma d[kW]/0,92 resulta em D[kVA]; divisor não altera FP cadastrado ou potência instalada dos projetos. Memória mostra faixas, base/fator/demanda por grupo, sem arredondamento intermediário.

Dados insuficientes →null/pending; grupos especiais ou escopo incompatível →null/out_of_scope, sem resultado final parcial disfarçado. Zero exige ausência explícita. Testes independentes/limites em test_energisa.py e API; fonte6.3 histórica não executada. Método não está automaticamente ligado ao inventário de projetos nem ao dimensionamento final. Potência manual e relatórios existentes preservados; motor/registro novos requerem revalidação quando solicitada, sem regravar históricos.

Operações em Python Decimal, contexto do motor com 40 algarismos significativos. Entradas de potência, área, perímetro e tensão têm até 18 dígitos e seis casas decimais. No procedimento residencial, blocos inteiros de área e frações de perímetro usam os critérios específicos documentados abaixo. A UI apresenta até três casas, preservando valores completos no JSON.

- Potência nominal de cada carga: `P [W] = quantidade × potência unitária [W]`.
- Instalada cadastrada: soma de cada instância exatamente uma vez, por ambiente e categoria.
- Iluminação nominal: subconjunto das cargas marcadas `lighting`; não é adicionada outra vez ao total.
- Conversão: `P [kW] = P [W] / 1000`.
- Aparente cadastrada: soma de `P [W] / FP` em VA, apenas se todas as cargas tiverem FP informado. É agregação escalar de cargas; não é demanda ou análise vetorial do sistema.
- Corrente monofásica: `I [A] = P [W] / (V [V] × FP)`.
- Corrente trifásica equilibrada: `I [A] = P [W] / (√3 × V_linha [V] × FP)`.

As funções de corrente são integradas à API e à memória por equipamento quando houver dados suficientes. Não representam dimensionamento de circuito.

Exemplos aritméticos: 2 × 7.500 W = 15.000 W; 4 × 9 W = 36 W; total 15.036 W = 15,036 kW. Com FP 1 nos chuveiros e 0,9 nas lâmpadas: 15.000 VA + 40 VA = 15.040 VA. Exemplos não são recomendações de potência nem fatores normativos.

Dados negativos, não finitos, quantidades fracionárias, FP fora de (0,1], tensões nulas e IDs duplicados são rejeitados. Potência zero recebida no cálculo fica pendente e não equivale à potência real do equipamento; salvar uma carga com zero é rejeitado. Use null para potência desconhecida. Todas as potências são editáveis. Origem `user_estimate` propaga estado estimado; `nameplate` e `manufacturer` identificam a declaração do usuário, sem alegar verificação independente do produto.

Memória inclui IDs da carga/ambiente, entradas, fórmula, resultado/unidade, estado e origem. SHA-256 identifica o payload normalizado; versão do motor identifica o procedimento. Demanda e previsões sem dados/escopo suficiente retornam `null`, nunca zero ou aproximação para preencher lacunas. Nenhuma soma entre W e VA é realizada.

Política de contagem: somar cargas cadastradas uma vez; iluminação é subconjunto; previsão TUG/iluminação e demanda são bases separadas. A previsão residencial usa base separada; agrupamento/substituição para demanda depende da futura validação do método da distribuidora.

## Ampliação do motor 0.2.0

`unit_power_w` e tensão podem ser nulos; ausência de potência ou potência zero deixa o total com estado `pending`. O número em W é então um subtotal conhecido, não a potência completa. `unknown_load_ids` identifica as pendências. O estado de iluminação é independente do estado de outras categorias.

O catálogo inclui potência nominal, máxima ou estimativa, explicitamente identificadas. Referências de fabricante não são médias de categoria; o usuário pode substituir valores e restaurar o snapshot da referência. Nenhum FP foi inferido: o LED Philips documenta 0,7; para outros modelos sem informação ele continua desconhecido. Hipótese resistiva FP=1, quando usada, é explicitamente declarada e registrada.

Conversões em units.py: BTU International Table/h × 1055,05585262/3600 para W térmicos; cv métrico × 735,49875 e HP mecânico × 745,69987158227022 para W mecânicos. Entrada elétrica de motor = saída mecânica/rendimento do motor. Rendimento hidráulico não substitui rendimento do motor. Sem rendimento, a entrada permanece desconhecida; uma potência elétrica direta permite dispensar essa conversão.

Capacidade térmica, consumo mensal em kWh e saída de aquecimento de micro-ondas nunca entram como potência elétrica. Para AC, alterar capacidade de uma referência específica invalida seu preenchimento automático em W. Só se estima consumo a partir de eficiência quando houver metodologia e dados documentados; tal estimativa não foi habilitada nesta entrega.

A resposta inclui load_results, steps e aggregate_steps com fórmula, substituição, resultado, unidade, hipóteses e fonte quando aplicável. Corrente é por unidade de equipamento, não corrente geral da residência. VA continua sendo soma escalar, sem alegação de análise vetorial. O digest identifica as entradas técnicas normalizadas (utility/environments), incluindo suas fontes, e ignora nome/observações administrativos.

## Revisão de cálculos — 22/10/2026, motor 0.4.3

Auditoria dos módulos power/current/units/equipment/engine, schemas, referências e fluxo de recálculo. Potências e somas continuam Decimal com 40 algarismos; nenhuma regra normativa foi ativada. Corrente agora divide diretamente P pelo produto V×FP (ou √3×V×FP), evitando arredondar P/FP antes de calcular I. Exemplo independente por fração racional: 1 W, 127 V, FP 0,9 → 0,008748906386701662292213473315835520559930 A em 40 algarismos. A diferença anterior estava na última casa, sem efeito visível usual; histórico não regravado.

Cobertura acrescentada: todas as 37 referências (31 seleções padrão), multiplicação por quantidade, valor manual acima da sugestão, watts desconhecidos, digest e preservação do catálogo; limites de quantidade/precisão, finitude, tensão e FP via API; mudanças independentes de tensão/FP e potência mecânica/rendimento. Watts não mudam ao editar tensão/FP; corrente por unidade não é multiplicada pela quantidade; VA total considera quantidade. Campos opcionais térmicos/energia/saída útil permanecem separados da entrada elétrica.

Categoria personalizada passa a sobreviver à troca automática de referência de AC. Potência manual continua protegida, mesmo estimada; somente seleção/restauração explícita reaplica uma sugestão. Referência atual do ventilador VSP-40-W corrigida de 60 para 140 W após leitura da página oficial; instâncias antigas e valores manuais não são atualizados silenciosamente. Revalidação técnica identifica mudança do registro/motor; snapshots e históricos persistidos permanecem íntegros.

## Energia e custo — motor 0.5.0

Fonte primária para W/kW/kWh: [EIA — Measuring electricity](https://www.eia.gov/energyexplained/electricity/measuring-electricity.php), consultada em 22/10/2026. Grandeza física e estimativa de uso, sem coeficiente normativo ou tarifa brasileira presumida. Exemplo independente da fonte: lâmpada 40 W por 5 h = 0,2 kWh; em 30 dias informados = 6 kWh.

- Horários: E_mês [kWh] = quantidade × entrada elétrica [W] × horas efetivas/dia × dias de uso / 1000.
- Etiqueta/medição: E_mês [kWh] = quantidade × consumo mensal informado por unidade. Quando presente, prevalece sobre horários; não somar as duas bases.
- Custo: E_mês × tarifa informada [BRL/kWh]. Não representa a fatura completa e não inclui automaticamente encargos fixos, tributos ou bandeiras adicionais.
- Consumo agregado por equipamento, ambiente, categoria e projeto. As quantidades entram uma única vez. Identificadores sem dados de consumo acompanham os subtotais; sem nenhuma carga calculável, energia/custo são null. Zero só resulta de entrada explícita válida, como 0 h, 0 dias, 0 kWh ou tarifa zero.
- Sem horários padrão, sem divisão de kWh em potência, sem assumir que uma geladeira funciona com potência constante enquanto conectada à tomada. Etiqueta/medição pode ter condições diferentes do uso real; resultados são estimativas. Para motor, usa-se a entrada elétrica resolvida pelo mesmo motor matemático.
- Horas entre 0 e 24, dias inteiros entre 0 e 31, energia/tarifa finitas não negativas; Decimal/contexto 40, sem arredondamentos intermediários. Moeda na UI formatada em centavos; JSON guarda precisão do motor.

Exemplos independentes em test_energy.py: quatro lâmpadas 9 W × 5 h × 30 dias = 5,4 kWh; duas geladeiras com 40 kWh unitários = 80 kWh, independentemente de potência desconhecida; subtotal 85,4 kWh × R$0,80/kWh = R$68,32, sem considerar uma carga adicional sem consumo. Motor 1 cv/0,5 × 2 unidades × 2 h × 10 dias = 58,8399 kWh. Casos de fronteira, ausência/zero, prioridade mensal, quantidade, modo mecânico, alteração de potência/tarifa e persistência/API/PDF têm testes.

Mudança compatível sem migração: campos opcionais em payload JSON e resultados. Todos os projetos são potencialmente afetados na prévia/revalidação porque motor e registro técnico mudaram; históricos permanecem imutáveis, sem regravação automática em lote. Regras normativas permanecem null/pendentes.

## Previsão residencial — motor 0.6.0

Fonte, edição, cláusulas conferidas, escopo e restrições em [standards.md](standards.md). Implementação pura: `calculations/residential.py`; opt-in `analysis_scope=normative`. Nenhuma fórmula correspondente é executada no frontend.

- Iluminação por área A positiva: 100 VA para os primeiros 6 m² e 60 VA por bloco completo de 4 m² excedente, usando Decimal/ROUND_FLOOR. Exemplos: A=6; 6,000001; 9,999999 → 100 VA; A=10; 12 → 160 VA; A=14 → 220 VA. Quantidade mínima de luz separada da potência e da verificação de localização.
- Pontos TUG: sala/quarto usam perímetro/5 m, cozinha/lavanderia perímetro/3,5 m, sempre ROUND_CEILING; banheiro um ponto; demais cômodos internos um até 6 m² e, acima disso, perímetro/5 m com fração. A fronteira de 2,25 m² afeta localização permitida, não altera a quantidade mínima; localização não é calculada.
- Base de atribuição é max(pontos cadastrados, mínimo geométrico). Grupo banheiro/cozinha/lavanderia: 600 VA até três pontos por ambiente, 100 VA por excedente; demais internos 100 VA por ponto. Mantido o método básico, sem redução opcional entre ambientes molhados.
- Exemplo manual independente: quarto 3×4 m (A=12/P=14), cinco pontos cadastrados → mínimo três, base cinco/500 VA, iluminação 160 VA. Cozinha 3×3 m (A=9/P=12), um ponto cadastrado → mínimo/base quatro/1900 VA, iluminação 100 VA. Totais separados: iluminação 260 VA; TUG 2400 VA. Um LED de placa 9 W continua 9 W instalados; os VA não entram nessa soma.

API retorna `normative_environments` tipado com mínimos, cadastrados, base, VA, faltas e condições; `normative.lighting/outlets` só totalizam quando cada parcela é conhecida. Vazio/desconhecido/fora de escopo não vira zero. Notificações e requisitos condicionais são derivados no backend. Guardas de recálculo/contratos/exportação preservadas. Testes específicos de fronteira em `tests/test_residential.py`.


## Integração local NDU-001 — 0.13.0 / motor0.8.0, 23/10/2026

O projeto pode ativar `energisa_demand` e classificar explicitamente cada carga em `Load.energisa_demand` (grupo, reserva, enquadramento de AC). Não há inferência por nome, tipo, catálogo, VA normativo ou BTU/h. Adaptador puro `calculations/project_demand.py` encaminha o inventário ao mesmo método d1–d5 já conferido; fatores e fórmulas de energisa.py não mudaram. Potência elétrica adotada em W e quantidades manuais prevalecem; modo mecânico não é convertido implicitamente nesta integração.

Escopo precisa confirmar unidade residencial individual, Energisa Sul-Sudeste/SP, ausência de letreiros/vitrines, simultaneidade luz/TUG quando aplicável e ausência explícita dos grupos sem cargas em operação. Reservas são identificadas individualmente, excluídas da demanda mas incluídas na conferência de instalada/75kW. d6/d7 ou unidade central em operação continuam fora do escopo; sem potência positiva, classificação completa, escopo ou revisão, demanda nula. Inventário vazio não produz uma falsa demanda zero.

Revisão vinculada ao SHA256 canônico do inventário, IDs, nomes/ambientes, classificação, potências, quantidades, reservas e declarações de escopo/ausências. O backend emite o digest; confirmar no formulário grava esse digest no projeto. Qualquer mudança correspondente invalida a confirmação mesmo via API direta ou após salvar/reabrir; não depende apenas de reset de checkbox no frontend. Nenhum projeto antigo recebe classificação ou confirmação por migração.

`calculations/full` integra `energisa_demand` tipado e `normative.demand` coerentes. Capacidades técnicas distinguem método disponível de inventário ainda pendente. O digest geral inclui as configurações da demanda, preservando guards de exportação. Frontend envia essas configurações pelo hook existente, mantendo debounce/cancelamento; painel usa somente resultado atual e resumo de demanda oculta número anterior durante recálculo.

PDF/JSON1.3 trazem demanda, inventário por ID/ambiente, grupos, reservas, declarações, memória/fatores/faixas, pendências e referência NDU7.0. JSON mantém estrutura anterior com adições. Não determina circuito, cabos, proteção, categoria de fornecimento, território oficial nem aprovação. Referências/condições normativas continuam as da0.12, sem nova tabela habilitada. Testes próprios em test_project_demand.py e integração API/E2E; resultados finais em CURRENT_STATE/SESSION_HISTORY.

## Circuitos e verificações de proteção — motor0.9.0

Módulos puros circuits.py/protections.py/service_entry.py,sem FastAPI/Pydantic/ORM. Entradas persistidas opcionais `circuits` e `service_entry`; todos os números elétricos usam Decimal/contexto40,sem arredondamento intermediário. Projetos antigos são compatíveis por defaults vazios e não foram regravados. Revalidação identifica motor/registro novo; históricos anteriores permanecem íntegros.

### Circuito monofásico condicionado

Para cargas associadas exclusivamente:resolver potência elétrica unitária pelo motor existente e multiplicar quantidade uma vez. P=ΣP_i;q=Σ[P_i·√(1−FP_i²)/FP_i];S=√(P²+q²);Ib=S/U;FP_eq=P/S. Escopo de cargas indutivas/resistivas senoidais,sem presumir FP,tensão ou configuração. Carga removida/desconhecida,tensão incompatível ou associação em dois circuitos deixa seleção nula; não usar subtotal.

Tabela36Cu/PVC70/2condutores carregados,B1/B2,seções1,5–35mm²; tabela40(Tamb10–60°C,passos5) e42linha1(1–8circuitos homogêneos). Iz=Iz_ref×f_temp×f_grupo. Selecionar menor nominal disponível informado≥Ib e menor seção que atenda mínimos iluminação/força,térmica e queda. I2=In×relação de fabricante informada,nunca presumida. Critérios Ib≤In≤Iz e I2≤1,45Iz apenas com confirmação da condição de duração5.3.4.1;sem ela,aplicaI2≤Iz. PE por tabela58,mesmo material e conduto,fase≤16:PE=S;16<S≤35:PE16. Não verifica PE adiabático/continuidade só pela tabela.

Queda em regime:ΔU=2·L·Ib·[ρ/S·FP_eq+λ·√(1−FP_eq²)],Ldistância de ida,m;ρCu0,0225Ωmm²/m;λ0,00008Ω/m,modeloPrysmian2024§5 aceito explicitamente. Cargas concentradas no fim do percurso,conduto não magnético. Não é cálculo de partida/harmônicas. Queda%=100ΔU/U;limite terminal4%;quando informados origem/queda a montante,o limite útil é mínimo(4%,limite_total−queda_montante). Total5%na entrega BTcomum e7%nos outros três casos específicos de6.2.7.1;sem aplicar majoração opcional de percurso>100m. Sem dados,queda total nula e pendência explícita.

Verificações complementares,com fonte e dados explícitos:energia passante≤k²S² da fase para duração≤5s;k/energia não presumidos e dados precisam corresponder ao In selecionado. Restrição conhecida aumenta seção antes da escolha. TN:Zs×Ia≤U0 e tempo assegurado≤tabela25;U0127V:(0,8s/0,35s),220V:(0,4s/0,2s),situações1/2 doanexoC;semTN-C/exceção5s. TT:RA(incluindoPE)×IΔn[A]≤UL;DRcompatível eULconferidos. DRadicional:≤30mA somente como critério quando exigência/tipo compatível confirmados. Não escolhe tipo de DR,curva,DPS ou seletividade automaticamente.

Exemplos independentes/tests/test_circuits.py:4400W/220V/FP1⇒20A;série16/25/40A,In25A,I2/In1,45,B1/30°C/1grupo⇒4mm²,Iz32A,PE4mm²;30m⇒6,75V.40°C/3grupos:6mm²⇒24,969A(insuficiente para25A);10mm²⇒34,713A;sem confirmação da duração,I2=36,25A exige16mm². Queda a montante4%emBTexige16mm² no exemplo (1,6875V).I²t900000A²s/k115 exige10mm². Limites de igualdade,FP/tensão/potência ausentes,duplicação de associação,curto insuficiente e dados de outro produto têm testes.

### Entrada ESS220/127V

service_entry.py usaNDU0017.0§6.6/tabela16pp.73–75. Somente residência individualESS/SP,rede confirmada,carga instalada completa>0e≤75kW e avaliação declarada das restrições de motores/solda/cargas especiais. Modalidade por carga/tensão:M até8,8kWsemcarga220;B até17,7kWquando necessário;T por demanda atual revisada kVA. Solicitação explícita de fases é verificada,não é aprovação de fornecimento. Demanda ausente/zero/incompleta bloqueiaT.

M/B por intervalos de kW eT por kVA,limite superior inclusivo. Seções mínimas do ramal/aterramento respeitam isolação70/90°C e notas de subterrâneo,sem extrapolarN.A. PVCsubterrâneo bloqueado (notaIX). Valores de disjuntor da faixa são somente referências superiores da tabela,pois a notaVIIexige cálculo pela demanda real. Não substitui queda/curto/aterramento físico,caixa/poste,eletroduto ou aprovação. Testes cobrem fronteiras3,8/6,3/8,8/10,1/12,7/17,7kW,15,2kVA,isolação e distribuidora fora de escopo.

## Integridade do snapshot — motor 0.9.1

Correção de rastreabilidade, sem nova fórmula/tabela/coeficiente: `input_digest` passa a incluir `circuits` (inclusive proteções) e `service_entry`. Esses campos já influenciavam os resultados, mas eram omitidos do digest de exportação. PDF/JSON agora rejeitam com409 a alteração desses dados entre cálculo e relatório. Regressões parametrizadas para os dois formatos em test_api.py, mais hook de invalidação frontend/E2E. Históricos/projetos antigos não são regravados; a mudança de motor sinaliza revalidação conservadora. Exemplos independentes adicionais de FP misto (triângulo8–15–17) e corrente exatamente24A/um incremento acima em test_circuits.py;escopos normativos da0.9.0 permanecem inalterados.
