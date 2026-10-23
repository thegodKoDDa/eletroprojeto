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
