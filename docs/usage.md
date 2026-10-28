# Usar o EletroProjeto — estimativas residenciais

Escolha Leigo, Profissional ou Exploração. Todos usam os mesmos cálculos; Alterar perfil conserva a edição. Funciona com casa pronta, planejada, em construção ou reforma, apartamento, kitnet, studio, sobrado ou outro imóvel residencial.

## Projeto e imóvel

Clique Criar novo projeto. Informe nome, UF e, se quiser, município e tarifa emR$/kWh. Em Outros dados do projeto registre tipo/estágio, área/pavimentos e distribuidora selecionada ou nome informado. Distribuidora/área/geometria/instalação definitiva não são exigências para kWh; sem tarifa, apenas o custo fica indisponível.

## Ambientes e equipamentos

Adicione ambientes, escolha tipo e nome personalizados. Catálogo oferece sugestões por ambiente; busca encontra também equipamentos incomuns. Marca/modelo não são obrigatórios. Potência da referência é ponto de partida: altere para o valor adotado da estimativa sem modificar o catálogo ou outra instância. Duplicar ambiente/aparelho cria IDs independentes. Restaurar sugestão recupera referência sem apagar consumo/horários.

Em Consumo mensal informe kWh mensais/anuais unitários da etiqueta/medição ou potência elétrica e tempo efetivo (horas/minutos, dias/mês). Mensal declarado prevalece sobre anual e horários; anual é dividido por12 só para média mensal. Não use automaticamente potência nominal×24h de uma geladeira; use consumo declarado ou uma premissa explícita de tempo efetivo. Não sabe? Deixe vazio: conhecidos continuam em subtotal identificado.

## Resultados e Estimativas

Potência instalada, média diária anualizada, energia mensal/anual e custo quando há tarifa. Consulte ambientes/categorias e maiores consumos; detalhes mostram fórmulas, parâmetros, fonte e premissas. Média diária é anual/365; hábitos e clima reais variam. Alterar potência, quantidade, horários, kWh ou tarifa recalcula automaticamente, ocultando números antigos durante a atualização. Avisos tratam entradas ou cobertura, sem pendências de fornecimento.

## Salvar, copiar, excluir e restaurar

Salvar projeto cria registro com histórico. Salvar como novo projeto (menu Mais ações) conserva o original e registra outra cópia; duplicar na biblioteca faz cópia independente. Use nomes para comparar cenários e modificar apenas uma cópia. Autosave inicia após primeiro salvamento manual, com pausa em renomeação/conflito. Conflito409 oferece preservar a edição local como cópia ou carregar a versão salva; não sobrescreve silenciosamente.

Projetos salvos abre a biblioteca; remover envia à lixeira, restaurar recupera com histórico. Exclusão definitiva continua explícita/versionada, sem apagar outras instâncias. Projetos antigos abrem com ambientes, equipamentos, valores manuais e localização; estudos normativos antigos continuam no snapshot histórico, sem execução/exibição ou atualização em massa.

Rascunhos por conta/aba ajudam a recuperar edição local ainda não salva; limpar navegador ou usar outro dispositivo limita recuperação. Pages guarda projetos em localStorage, separado do SQLite local. Não confundir exportar relatório com salvar/backup.

## Relatório

Exportar PDF ou JSON usa cálculo atual conferido pelo servidor: identificação/imóvel/localização, equipamentos, potências, energia/custos/distribuições, memória e premissas. JSON2.0 não é backup completo. Não inclui demanda, circuitos, fornecimento ou aprovação técnica. [Continuidade](continuity.md) descreve salvamento completo, checkpoints e recuperação.

## Comparação opcional de cenários

Abra Comparar cenários de consumo, salve uma configuração e altere aparelhos ou hábitos. Comparar com versão salva mostra diferenças sem sobrescrever o original. A referência permanece durante o autosave; Usar versão salva mais recente como referência troca essa base explicitamente. Reabrir/recarregar inicia outra referência. Para manter as duas configurações, use Salvar como novo projeto. Valores negativos indicam redução; dados insuficientes ficam explícitos. Trocar entradas invalida a comparação anterior.
