# Cálculos — estimativas residenciais / motor0.13.0

Funções puras em backend/app/calculations. Decimal com contexto40dígitos, sem arredondamentos intermediários; frontend apenas formata. Nenhuma norma de fornecimento, demanda normativa, circuito, proteção ou dimensão de instalação é executada.

## Potência

Potência elétrica unitária adotada em W × quantidade = potência do cadastro. Soma por ambiente/categoria e residência, contando cada instância uma vez. Iluminação nominal é subconjunto do total, não mínimo normativo. Potência ausente produz cobertura incompleta, nunca potência inventada. Catálogo é referência e manuais válidos prevalecem. Conversão W/1000=kW. VA e corrente unitária continuam indicadores secundários quando há FP/tensão/configuração informados, sem bloquear kWh nem dimensionar instalações. Conversões mecânicas/térmicas existentes permanecem explícitas; BTU/h nunca é somado como potência elétrica.

## Energia e custo

energy.resolve_energy preservado, nesta prioridade:

1. Consumo mensal unitário declarado × quantidade.
2. Consumo anual unitário declarado × quantidade /12 para média mensal; anual conserva a base original.
3. Quantidade × potência elétrica W × horas efetivas/dia × dias de uso/mês /1000. Minutos/dia são convertidos exatamente por60, conforme unidade escolhida.

Projeção anual=mensal×12 quando a base não é anual declarada. Média diária anualizada=projeção anual/365; é indicador de planejamento, não medição ou perfil de um dia de uso. Nenhum mês padrão de uso ou sazonalidade é inferido. Geladeira/aparelhos cíclicos podem usar kWh da etiqueta; não presumir potência nominal×24h. Ausência de energia declarada/horários suficientes deixa o consumo daquela carga pendente, mantendo o subtotal dos conhecidos.

Custo=energia×tarifa manual em BRL/kWh. Sem tarifa, custo=null; tarifa0 é válida. Não acrescenta automaticamente tributos, encargos fixos ou reajustes. Totais por ambiente/categoria, ranking e participação no subtotal são calculados em Python; totalzero gera percentualnull. Consumo declarado não permite deduzir potência elétrica.

## Exemplos independentes

Dois computadores com600W,4h/dia em20dias/mês: potência1200W; energia96kWh/mês,1152kWh/ano; média1152/365kWh/dia. Tarifa fictícia0,80 resulta76,80BRL/mês e921,60BRL/ano. Alterar potência para300W resulta48kWh/mês; depois uso2h resulta24kWh/mês. Referência original300W não obriga adotar esse valor.

Geladeira declarada35kWh/mês, uma unidade:35kWh/mês e420kWh/ano, mesmo sem potência conhecida; custo28BRL/mês na tarifa fictícia0,80. Os exemplos são fixtures verificáveis, não sugestões universais de potência/tarifa/hábitos.

## Validação e rastreabilidade

Quantidade inteira positiva; potência negativa/infinita/inválida rejeitada; horas0–24, minutos0–1440 e dias inteiros0–31. Zero de energia/tempo é distinto de ausência. Unidade/entradas contraditórias continuam corrigíveis. Falta de tensão/FP, geometria, distribuidora ou norma não bloqueia consumo. Nome do projeto é necessário para salvar; município é opcional.

Cada carga expõe steps com fórmula, substituição, resultado/unidade, premissas e fonte. Agregações e referência do catálogo permanecem rastreáveis. Calculated significa aritmética disponível; estimated explicita estimativa, pending cobertura insuficiente. Nenhum estado atesta medição real ou conformidade. Projetos antigos não são regravados automaticamente. Fonte de métodos energéticos já conferida (EIA/NIST) e referências anteriores em [arquivo de cálculos](history/calculations-before-consumption-scope.md) e [fontes](standards.md).

Testes independentes em test_estimates_scope, energy, energy_automation, equipment, math, API, relatórios e navegador. Pesquisas de normas conservam testes das funções puras isoladas; integrações do antigo produto foram retiradas com seus endpoints, preservadas no Git.

## Comparação opcional de cenários

O motor executa os dois snapshots e subtrai cenário atual menos base salva para potência, energia mensal/anual e custos, com Decimal/contexto40. Valores negativos indicam redução. Diferenças de consumo/custo são nulas se qualquer cobertura energética estiver incompleta; potência depende da própria cobertura. Sem tarifa, diferença de custo é nula. Exemplo independente:96−48=48kWh/mês e76,80−38,40=38,40BRL/mês.
