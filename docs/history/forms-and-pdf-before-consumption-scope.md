# Formulários e relatórios

Referência de comportamento atualizada na versão 0.24.1. O [guia de uso](../usage.md) explica o percurso pela interface; [cálculos](../calculations.md) e [fontes](../standards.md) concentram fórmulas e condições técnicas.

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

Banco, histórico, rascunhos do navegador e relatórios têm finalidades diferentes. Os limites de recuperação estão em [continuidade](../continuity.md).

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

Testes de exportação e snapshot estão em `backend/tests/test_api.py`, `test_pdf.py`, `test_report_summary.py`, `test_project_demand.py`, `test_bathroom_geometry.py` e nos E2E. Resultados efetivos da última entrega estão em [verificações](../audit.md).

O [registro de revisões até 0.14.1](../history/forms-and-pdf-through-0.14.1.md) foi preservado para rastrear a evolução dos formulários e dos formatos; seus requisitos e posições antigas não descrevem necessariamente a interface atual.


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

## Refinamento dos perfis — 0.22.1

Revisados os grupos de identificação, ambientes, catálogo/instâncias, consumo, estudos, biblioteca, salvamento/recuperação e relatórios. Cada grupo tem uso concreto nos dois perfis e continua acessível: profissional também precisa de consumo e recuperação; leigo pode consultar referências e estudos opcionais. Nenhuma função ou dado foi excluído por baixa frequência de uso. Foram retirados peso visual dos blocos destacados, estilos sem efeito em details com display:contents e o rótulo genérico Restaurar nos novos perfis. Exploração mantém organização e nomes anteriores, com melhorias comuns dos controles.

O menu móvel dos dois perfis é recolhível, preservando ações de salvar/exportar e abrindo todos os destinos. Cancelar a criação de outro projeto mantém menu, foco e edição. Desktop mantém navegação aberta. Campos têm rótulo separado do controle, destaques laterais sem preenchimento que desalinhava linhas, bordas/hover/foco consistentes e áreas de toque maiores em telas pequenas. Ações destrutivas usam cor própria, botões de aparelhos têm área e estados visíveis e selects preservam o controle nativo e o teclado.

Consumo agrupado em duas alternativas por fieldsets/legends: etiqueta/medição e horários. Prioridade de kWh, zero válido, horários latentes preservados e correção de valores inválidos permanecem iguais. Restaurar referência recebe explicação e não limpa o uso. Atalho profissional de concessionária nomeia seu destino real; parâmetros do primeiro aparelho ficam acessíveis por atalho. Resultados e memória passa a focar o summary interno, reabrindo os detalhes após fechamento manual. Fórmulas longas na memória quebram em telas estreitas: o teste de 320px revelou overflow que ficava oculto com os detalhes fechados.

Não há alteração de fórmulas, requisitos da API, permissões, payloads de projetos, catálogo ou relatórios. Perfil continua sendo apenas apresentação. Verificações e limites desta entrega estão no CURRENT_STATE e no registro cumulativo da sessão.

## Padrão visual e ajuda progressiva — 0.23.0

Paleta compartilhada de superfícies neutras, texto/contraste, tipografia do sistema, espaçamentos, bordas, raios e controles. Início, entrada/perfis, editor, biblioteca técnica, projetos salvos, lixeira e acesso autenticado usam o mesmo CSS e componentes de títulos, seções e feedback. Ações principais usam verde; informação azul; pendências âmbar; erros/remoção vermelho. Estados também têm texto/símbolos, nunca dependem apenas da cor. Lista de projetos passa a cartões, cabeçalhos têm separação comum e avisos usam ícone/estrutura iguais. Nenhuma fonte remota ou dependência nova.

Leigo recebe cinco tarefas: identificar projeto, cadastrar ambientes/aparelhos, informar uso, conferir estimativa e salvar. Estado deriva das entradas atuais, dos limites de texto fornecidos pela API, do resultado atual e da igualdade da edição salva. Campos obrigatórios válidos mostram Preenchido. Uma tarefa preenchida ganha Concluída e o próximo item é destacado automaticamente. O botão contextual leva ao campo correto e abre detalhes quando necessário; não há salto automático de foco enquanto a pessoa digita, preenchimento presumido ou salvamento implícito.

Uso dos aparelhos só conclui com valor de consumo retornado pela API e nenhum aparelho pendente, incluindo zero válido. Não soma energia nem replica fórmulas no frontend. Durante recálculo, atalhos dessa tarefa aguardam o resultado atual; em erro, apontam para a entrada indicada pela API. A tarefa de cadastro cobre apenas os aparelhos que o usuário decidiu incluir, não prova inventário completo da casa. Tarifa continua opcional.

A conferência exige clicar Já conferi a estimativa nos resultados. A confirmação é local à edição/sessão do Workspace e vinculada ao digest e escopo do projeto; não integra o payload ou histórico técnico. Dados diferentes, novo projeto ou reabertura exigem nova conferência. Resultado anterior não conclui tarefas novas. Salvar segue as rotinas existentes, com autosave/conflitos e histórico preservados. O relatório continua disponível sem impor essa orientação como bloqueio.

Profissional tem cartões de atalhos com finalidade explícita e acompanhamento das mesmas tarefas recolhido. Nenhum estudo técnico opcional é marcado como validado pelo preenchimento. Exploração mantém organização/funcionalidades e recebe o padrão visual comum. Os três perfis têm ajuda recolhida explicando consumo, valores desconhecidos/zero, estados e limites dos estudos. Avisos de cálculo continuam localizados e oferecem correção no campo, com estado atualizado a cada resposta.

Conclusão do percurso significa apenas cadastro, estimativa conferida pelo próprio usuário e edição salva. Não significa conformidade normativa, fatura completa, medição ou aprovação profissional. A fonte das regras e das pendências continua no backend. Verificações efetivas e limites estão no CURRENT_STATE/SESSION_HISTORY.

## Automação de entradas e resultados — 0.24.0

Os três perfis recebem as mesmas capacidades: tempo em horas/minutos, consumo anual informado convertido em média mensal, rotina comum explícita para cargas sem uso no ambiente e painel recolhido de contas automáticas. Backend faz toda matemática; frontend só valida formatos/limites, copia entradas e apresenta valores. Campos de consumo anual têm destaque recomendado no leigo, sem se tornarem obrigatórios. Ajuda para consumo pendente leva à unidade selecionada.

Mensal > anual > horários, com zero válido e valores latentes preservados. Nenhum hábito é deduzido da categoria. A rotina comum não altera aparelhos com consumo conhecido ou rotina parcial, instâncias de outros ambientes, catálogo ou histórico. Restaurar referência conserva os novos parâmetros de uso e energia. Campo inválido latente de outra unidade aparece para correção, evitando erro sem destino visível.

JSON/PDF mostram base mensal/anual/horário, minutos ou horas efetivos, consumo/custo por ambiente e projeção de12meses com escopo. Resultado antigo continua oculto ao editar, inclusive o painel novo; salvar/exportar continuam usando o snapshot atual. Contrato de relatório1.4 ganha campos aditivos opcionais de projeção e participação, preservando leitores/históricos existentes. Motor0.12.0 identificado no registro; nenhuma migração/regravação automática de projetos.

## Recálculo, salvamento e menus sem saltos — 0.24.1

O aviso de cálculo permanece em área reservada e troca apenas o estado/texto. Mensagens de salvar/exportar/erro aparecem em aviso fixo com botão Fechar, sem empurrar o formulário. Conferências e erros detalhados continuam acionáveis após os resultados. O contexto do projeto não muda de altura ao salvar; renomear mantém o aviso de pausa no próprio bloco do autosave, sem inserir outra linha na grade dos campos.

Durante recálculo, a altura anterior dos resultados/guia é preservada, mas nenhum número antigo é visível, anunciado ou interativo. Detalhes/memória permanecem montados; campos mantêm foco e edição. Ao finalizar, disclosures voltam à altura natural. A resposta de salvamento não provoca outro cálculo por mera ordem de propriedades ou defaults: a identidade é normalizada pelo contrato, distinguindo null, zero, false e alterações reais.

A navegação lateral mantém espaçamentos e largura entre páginas. Mais ações abre em camada sobre a interface, acima ou abaixo conforme o espaço da janela, sem aumentar o aside/formulário; usa rolagem própria quando necessário. Autosave preserva menu/foco e consulta, enquanto ações que poderiam trocar o projeto em gravação continuam protegidas. Exportar requer resultado atual e preserva seu snapshot. Avisos não somem por cronômetro; podem ser dispensados ou substituídos pela próxima operação.
