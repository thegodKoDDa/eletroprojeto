# Memória permanente — EletroProjeto

## Definição vigente em 28/10/2026

Plataforma de estimativa e análise de consumo energético residencial. Casas, apartamentos, kitnets, studios, sobrados e outros imóveis usam o mesmo motor, planejados, em construção, prontos ou em reforma. Não dimensiona instalações nem aprova fornecimento. Não reintroduzir dependências normativas sem decisão explícita de mudança de escopo.

## História recuperável e decisão

Os registros disponíveis em Git, CHANGELOG e SESSION_HISTORY documentam a evolução de cadastro de cargas, persistência/histórico, consumo/custos, acervo técnico, estudos normativos, perfis, automação e estabilidade. A motivação anterior aos registros não é recuperável integralmente e não foi inventada. A versão 0.24.1 implementava estudos condicionais de demanda Energisa, circuitos/proteções e geometria; em 28/10/2026 o usuário determinou retirar esse escopo do produto. A pesquisa permanece em disco, nos módulos puros independentes e no [arquivo histórico](history/README.md); não é dependência nem trabalho pendente do consumo.

## Fontes principais

- [Uso](usage.md): cadastro, salvar/salvar como, duplicar, lixeira/restaurar, referências e relatórios.
- [Arquitetura](architecture.md): API, frontend, SQLite/PostgreSQL, Pyodide, persistência e contratos.
- [Cálculos](calculations.md): matemática, bases de consumo, unidades, cobertura e exemplos.
- [Referências](standards.md): procedência do catálogo e acervo separado.
- [Estado atual](CURRENT_STATE.md), [sessões](SESSION_HISTORY.md), [roadmap](roadmap.md) e [limitações](KNOWN_ISSUES.md): entrega efetiva, verificações e próximo passo.

## Decisões permanentes

Um motor Python em backend/app/calculations, funções puras e Decimal. Frontend formata/valida, preserva debounce400ms, cancelamento e ocultação de resultados antigos. Distribuidora e estado são identificação; tarifa manual opcional, sem inferência. Catálogo é referência inicial, não obrigação: potência manual válida prevalece, não altera catálogo nem outras instâncias. kWh não são W, BTU/h é capacidade térmica e VA não é consumo. Consumo declarado pode existir sem potência conhecida.

Prioridade de energia unitária: mensal declarado > anual declarado > potência elétrica e horários efetivos. Não presumir uso24h, ciclos, hábitos, eficiência, tarifa ou sazonalidade. Subtotais parciais são identificados; vazio não vira zero. Média diária é projeção anual/365, não consumo de um dia típico medido. Custos não incluem automaticamente a fatura completa.

## Dados e apresentação

Três perfis mudam apresentação e orientação, mantendo cálculos/dados/permissões. Alterar perfil mantém Workspace montado. Identificação/imóvel → ambientes/aparelhos → estimativas → relatório. Memória é secundária e informa fórmulas, parâmetros/fontes e premissas. Acervo só carrega quando o usuário o consulta.

SQLite contém projetos, lixeira, históricos e revisões. Campos normativos legados continuam preservados nos payloads e cópias, sem serem executados pelo motor; nenhuma migração destrutiva. Estágio e nome livre da distribuidora são aditivos opcionais. Abrir não regrava projetos; salvar edição explícita registra nova versão com revisão do motor independente das normas. PUT idêntico não duplica histórico; conflitos409, idempotência inicial, autosave e rascunhos mantidos.

Pages executa os mesmos módulos Python via Pyodide e persiste em localStorage independente do SQLite. Limpeza do navegador pode apagar esses dados; PDF/JSON2.0 são relatórios, não backup completo. Publicação existente foi autorizada em27/10; nova implantação/release não é implicada por mudança local.

## Continuidade

AGENTS define as rotinas; [continuity](continuity.md) descreve backup SQLite API/WAL, ZIP, bundle Git, hashes e restauração isolada. Código/docs públicos no destino autorizado; banco/.env/checkpoints/originais privados ficam locais. Nunca restaurar banco antigo sobre uso posterior nem resetar migrações. Manter SESSION_HISTORY cumulativo, CURRENT_STATE conciso e documentos responsáveis atualizados durante mudanças. Checkpoint antes de estrutura e no encerramento. Não prometer preservação de buffers externos ou rascunhos não enviados, nem trabalho após desligamento.

## Comparação opcional de cenários

Comparação opcional entre edição e referência salva reutiliza o motor Python sem sobrescrever projetos. A referência é capturada na abertura/primeiro salvamento, permanece durante o autosave e é trocada explicitamente; reinicia ao reabrir. comportamento em [usage](usage.md) e matemática em [calculations](calculations.md).
