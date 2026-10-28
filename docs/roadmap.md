# Roadmap — uso local, 0.21.0

Atualização de escopo em 28/10/2026: Pages foi autorizado e publicado em 27/10; restrições históricas abaixo à publicação não descrevem mais esse modo. CI geral, impressão física e cópia externa continuam fora do escopo. Estado operacional em [CURRENT_STATE](CURRENT_STATE.md).

Decisão do usuário em 23/10/2026: operar localmente. Publicação/infraestrutura remota, execução hospedada de CI, impressão física e backup externo foram retirados do escopo atual; não tratá-los como bloqueios ou cobrar recursos para essas tarefas. Autenticação e workflow continuam preservados; GitHub público agora recebe a fonte e o encerramento autorizado. Checkpoints locais continuam protegendo SQLite/fonte/Git, com armazenamento compartilhado de cópias idênticas.

0.14.0: biblioteca leve, salvamento idempotente/sem gravação redundante, rascunhos com flush, checkpoints atômicos/reutilizáveis e auditoria/limpeza local. Procedimento em continuity.md; testes atuais em CURRENT_STATE.

0.15.0: biblioteca técnica pesquisável,guias/modelos/diagramas/PDFs e fontes locais persistidas. Revisão técnica específica ainda exigida para habilitar regras; importar não conclui dimensionamento nem cobertura territorial.

0.16.0:OCR/triagem,estudo limitado de circuitos Cu/PVC/B1/B2 e verificações de proteção com dados explícitos;enquadramentoESS220/127Vtabela16. Métodos e campos novos não concluem dimensionamento final universal; ampliar somente com fontes/condições/testes.

0.17.0: revisão de integração, assinatura completa de exportações, contratos de acesso/revalidação, prévia e registro explícito de revalidação na interface, limpeza de associações removidas e inicialização extraída para hook próprio. Sem ampliar regras normativas.

0.18.0: pesquisa explícita não exclui equipamentos pelas sugestões do ambiente; pendências de consumo por aparelho/ambiente, atalhos e descrições acessíveis. Estudo B1/B2 ampliado até95mm², com PE e testes de fronteira; demais ampliações técnicas continuam pendentes. Validação com leitor de tela real foi descartada pelo usuário em25/10/2026; melhorias de acessibilidade existentes permanecem.

0.21.0: revisão das pendências, ampliação condicionada de circuitos para XLPE/EPR90 e D/E/F/G, comparações documentais DPS/seletividade e relações oficiais INDGER/IBGE por município/CNPJ/mês. Casos não cobertos e dependências externas permanecem em KNOWN_ISSUES, sem simular conclusão universal.

## Disponível

- Projetos, histórico, biblioteca/lixeira, duplicação, autosave, rascunhos recuperáveis e resolução guiada de conflitos.
- Motor Python Decimal, potências W/VA, correntes com dados suficientes, consumo/custo opcionais e catálogo persistente com preservação de valores manuais.
- Previsão residencial quantitativa de iluminação/TUG em escopo explícito; resultados simples/técnicos e PDF/JSON.
- NDU-001 7.0 d1–d7 e centrais integrada ao inventário do projeto: classificação explícita de cada carga, reservas, ausências, escopo e revisão vinculada por hash. Mudanças invalidam a confirmação; sem classificação ou fora do escopo, demanda nula. Não constitui dimensionamento final.
- Git e checkpoints locais com verificação de hashes, restauração SQLite e recuperação de histórico. PostgreSQL e Windows já possuem validações anteriores.

## Prioridades locais seguintes

Direção de produto reafirmada em 24/10/2026: simplicidade para leigos antes da ampliação de estudos profissionais. O percurso principal permanece 01 Projeto → 02 Ambientes → 03 Conferência, com consumo/custo em destaque; circuitos/entrada/demanda são opcionais e recolhidos. Melhorias futuras devem reduzir esforço de cadastro e explicar estimativas usando os dados/fontes realmente disponíveis, sem inventar horários, tarifas ou fatores. Os itens normativos abaixo são evolução técnica posterior, não exigências para o uso básico.

1. Manter regressões de cálculos, cadastro, relatórios, acessibilidade automática, contratos, tipos, lint e build conforme as mudanças.
2. Preservar d6/d7/centrais habilitados em0.19.0; esclarecer oficialmente a ordenação quando W/VA divergirem e revisar demais exceções/distribuidoras antes de ampliar.
3. Preservar métodos A1–G e isolação PVC70/XLPE90/EPR90 condicionados da0.21.0. Próximos modelos: neutro, desequilíbrio/harmônicas, paralelos e outros arranjos de solo/agrupamento; completar proteção/entrada somente com fontes e exemplos próprios. DPS exige revisão da NBR5419:2026 e requisitos do estudo; comparações documentais já disponíveis não resolvem isso.
4. Ampliar o modelo de localização além do chuveiro sem delimitação/divisórias dafigura18, entregue em0.19.0; banheiras, divisórias, cabines, percursos e demais restrições exigem modelagem e revisão próprias.
5. Relações municipais oficiais INDGER/IBGE implementadas em0.21.0, com períodos próprios por CNPJ. Restam vigência jurídica/topologia integral e atendimento do endereço; não transformar declarações mensais ou polígonos em exclusividade/sucessão automática.
6. Melhorar revalidação seletiva de projetos afetados por mudanças normativas e desempenho em grandes acervos quando necessário.

Fontes, condições e testes normativos em [standards](standards.md) e [calculations](calculations.md). Estado das verificações em [CURRENT_STATE](CURRENT_STATE.md). Impressão física e validação com leitor de tela real foram retiradas do escopo pelo usuário. Manter acessibilidade implementada e testes automáticos/teclado; não reabrir essa validação como pendência sem novo pedido.
