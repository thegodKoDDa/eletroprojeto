# Formulários e relatórios

Referência de comportamento da versão 0.19.0. O [guia de uso](usage.md) explica o percurso pela interface; [cálculos](calculations.md) e [fontes](standards.md) concentram fórmulas e condições técnicas.

## Entradas e pendências

O editor segue **Projeto → Ambientes → Conferência**. Dados de identificação, aparelhos e uso são separados dos estudos técnicos opcionais. A finalidade de cada campo e seus diagnósticos vêm de `backend/app/validation.py`; o frontend formata e valida formulários sem repetir a matemática.

Potência elétrica, consumo mensal, potência aparente e capacidade térmica são grandezas distintas. Potência/FP/tensão desconhecidos não recebem valores presumidos. Contagens e tarifa podem ser zero quando isso é válido; falta de informação continua nula.

Os resultados identificam os aparelhos e ambientes com consumo pendente e oferecem atalhos para completar os campos. Nenhum horário ou tarifa é preenchido para produzir uma estimativa aparentemente completa. Referências do catálogo são sugestões; editar uma instância não modifica o catálogo.

## Cálculo atual e edição

Uma alteração relevante oculta os resultados antigos imediatamente. O cliente aguarda o debounce, cancela requisições anteriores e rejeita respostas que não correspondem à edição atual. As mesmas condições impedem exportar um resultado antigo com entradas novas.

Circuitos, proteções, demanda revisada e geometria participam da assinatura das entradas. Mudanças em parâmetros e fontes da demanda invalidam a confirmação do inventário. Nenhum cálculo novo é aplicado silenciosamente ao histórico salvo.

## Salvamento e recuperação

O primeiro salvamento é manual. Depois dele, autosave pode registrar alterações, com controle de versão e preservação de edições feitas durante o envio. Falhas não aparecem como sucesso nem provocam repetição infinita.

Rascunhos do navegador são separados por conta, aba e slot. Recuperar um rascunho não envia o conteúdo automaticamente. Conflitos de versão pausam o salvamento e oferecem recuperação sem fusão ou sobrescrita silenciosa.

Banco, histórico, rascunhos do navegador e relatórios têm finalidades diferentes. Os limites de recuperação estão em [continuidade](continuity.md).

## Conteúdo dos relatórios

PDF é a exportação principal; JSON é uma alternativa estruturada. Ambos usam o resultado atual e incluem os dados pertinentes ao estudo:

- Identificação, ambientes, aparelhos e potências cadastradas.
- Consumo, custo quando há tarifa, base de uso e cobertura dos dados.
- Pendências, hipóteses e distinção entre valores conhecidos e estimados.
- Estudos opcionais presentes: previsão residencial, demanda revisada, circuitos, entrada e localização de componentes.
- Referências e condições necessárias para interpretar os resultados técnicos.

JSON de relatório usa `formato_versao: "1.4"`, preserva valores nulos e não é uma cópia completa do projeto para restauração. O campo aditivo `localizacao_banheiros` reúne o estudo de envelopes. A consulta territorial por coordenadas é uma busca de referência separada e não é gravada no projeto ou no relatório.

Os números são apresentados com formatação brasileira; a saída estruturada conserva a precisão do motor. Datas de apresentação usam America/Sao_Paulo. Nomes de arquivo são derivados do projeto, com caracteres incompatíveis neutralizados.

## Integridade da exportação

`POST /api/v1/reports/pdf` e `POST /api/v1/reports/json` validam entradas, assinatura, versões do motor/registro e, quando aplicável, o snapshot salvo. O backend calcula e renderiza o relatório; não aceita um resultado técnico fabricado pelo navegador. Divergências de versão ou conteúdo retornam HTTP 409.

Exportar não salva nem modifica o projeto ou o catálogo. Edições posteriores ao início da exportação não são misturadas ao documento solicitado.

O renderizador PDF é local, em texto e tabelas, sem executar HTML ou buscar recursos pela rede. A fonte incorporada tem licença própria preservada junto do arquivo. Estudos condicionais não recebem declaração de dimensionamento final.

## Evidências e histórico

Testes de exportação e snapshot estão em `backend/tests/test_api.py`, `test_pdf.py`, `test_report_summary.py`, `test_project_demand.py`, `test_bathroom_geometry.py` e nos E2E. Resultados efetivos da última entrega estão em [verificações](audit.md).

O [registro de revisões até 0.14.1](history/forms-and-pdf-through-0.14.1.md) foi preservado para rastrear a evolução dos formulários e dos formatos; seus requisitos e posições antigas não descrevem necessariamente a interface atual.


Na0.21.0, estudos recolhidos recebem isolação/arranjo/solo e dados documentais DPS/seletividade. Campo sem fonte ou condição não ganha aprovação. CircuitResult.study_conditions e motivos de proteção preservam parâmetros/fontes no PDF/JSON, inclusive o requisito comparado; relatório continua formato1.4 aditivo. A consulta municipal INDGER/IBGE também é independente, cancela/esconde resultados antigos e não entra no projeto/relatório ou na seleção automática.


## Revisão de opções e perfis — 0.22.0

A escolha inicial altera apresentação, destaque e abertura dos detalhes; não altera o inventário, os requisitos recebidos da API, os cálculos ou as condições normativas. Todas as funções foram mantidas acessíveis nos três perfis. Recursos de recuperação e dados salvos não foram considerados descartáveis.

| Grupo de opções | Leigo | Profissional | Exploração / decisão |
| --- | --- | --- | --- |
| Nome, localização, tarifa e salvamento | Requisitos atuais destacados; tarifa recomendada, sem torná-la obrigatória | Cadastro básico preservado e dados complementares abertos | Organização original preservada |
| Ambientes, catálogo, valores manuais e consumo | Consumo aberto; caminho orientado e dados essenciais destacados | Consumo disponível e parâmetros elétricos destacados | Recolhimentos originais; todas as alternativas de entrada mantidas |
| Medidas, concessionária, circuitos, demanda e localização | Estudos opcionais acessíveis após resultados | Medidas/dados extras e grupo técnico abertos, com atalhos diretos | Grupo técnico original recolhido; sem promover estudos a exigência de consumo |
| Memória, unidades W/VA/A e previsão residencial | Detalhamento acessível por controle explícito | Memória/verificações destacadas e detalhamento inicial ativo | Seletor Apresentação original mantido; requisitos da operação são independentes do perfil |
| Biblioteca, lixeira e recuperação | Biblioteca no terceiro cartão; lixeira na navegação | Biblioteca destacada; lixeira na navegação | Três cartões originais, incluindo lixeira; nada removido do armazenamento |
| PDF/JSON, histórico, autosave, conflitos e revalidação | Disponíveis com os mesmos bloqueios de entradas/snapshot | Disponíveis com os mesmos bloqueios | Disponíveis; perfil não é gravado no projeto/relatório e não dispara cálculo |

Descartes de interface nos dois novos perfis: atalho principal duplicado para lixeira, substituído por referências úteis ao estudo; seletor Simples/Técnica redundante com a preferência, substituído por um controle explícito de detalhamento. A opção de exploração conserva esses controles originais. Não foi identificada função sem utilidade que justificasse apagar código de cálculos, recuperação, dados, catálogo, documentação ou estudos. Textos de escolha no celular são compactos, mantendo as três decisões visíveis sem repetir listas de benefícios.

A troca de perfil mantém Workspace e campos montados, preserva edições durante operações e não dispara novas requisições de cálculo. O diálogo usa elemento nativo, foco contido por Tab/Shift+Tab, Escape e retorno ao botão de origem. Preferência inválida reabre a escolha; sessionStorage indisponível permite uso na sessão atual. Auth continua anterior ao espaço de trabalho e a preferência é isolada por conta/aba.
