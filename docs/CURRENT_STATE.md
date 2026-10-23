# Estado atual — EletroProjeto 0.13.1 / motor 0.8.0

## Escopo vigente

Uso LOCAL por decisão explícita do usuário. Publicação/infraestrutura remota, CI hospedado, impressão física e backup externo fora do trabalho atual. Preservar checkpoints locais, recursos existentes, dados e produto; não cobrar esses itens descartados.

## Entrega — polimento geral da interface, 23/10/2026

Etapas01/02/03 padronizadas com SectionHeading (marcador, título e descrição); revisão Energisa segue a mesma hierarquia. Campos, selects, checkboxes, disclosures, botões, bordas, raios, espaçamentos, hover/foco, ativo/aberto/desativado e opções do catálogo revisados. Tema escuro e organização principal preservados.

Checkboxes não herdam mais padding de campos de texto:18px, padding zero, rótulo clicável/alinhado e foco visível. Salvamento automático está sempre visível em cartão próprio, com estado Após salvar/Ativado/Desativado/Pausado/Salvando e explicação. Mantidos debounce1,5s, primeiro salvamento manual, pausa em renomeação/conflito e proteção contra repetição de falhas. Preferência continua da sessão, sem novo armazenamento.

Observações em área própria sempre visível, cinco linhas redimensionáveis, limite10.000, contador e descrição acessível. Outros dados mantém apenas campos complementares. Mais ações tem ícones alinhados, seta/estado aberto, lixeira separada, títulos explicativos e fechamento por Escape/foco/clique fora; bloqueio inclui salvamento/exportação. Avisos ganharam role group compatível com aria-label. Indicador Next de desenvolvimento desativado por sobrepor controles no celular; erros continuam visíveis.

## Funcionalidades preservadas

Projetos/biblioteca/lixeira/histórico, rascunhos/conflitos, catálogo persistente, valores manuais, consumo/custo, previsão residencial luz/TUG e demandaNDU7.0 d1–d5 com inventário/classificação/revisão explícitos. Revisão de demanda vinculada ao digest: alteração relevante invalida confirmação; resultado antigo oculto durante recálculo e exportação exige snapshot atual. Escopo residencial individual Energisa Sul-Sudeste/SP até75kW, sem d6/d7/centrais presentes/agrupamentos. Sem dimensionamento final ou aprovação da concessionária. Fontes/regras em standards/calculations; UI em forms-and-pdf.

API/frontend0.13.1, motor0.8.0 e JSON1.3; schema0005, sem migração. Nenhuma fórmula/norma/catálogo ou dependência runtime alterada; locks comparados estruturalmente ao Git, somente versão própria mudou. Contratos gerados por types:sync; instalação editável Python atualizada.

## Dados e verificações desta entrega

Banco inicial desta tarefa:9projetos (8ativos/1lixeira),30históricos,8revisões técnicas. Todas as colunas das três tabelas comparadas ao checkpoint inicial e idênticas; SQLite íntegro/FK sem violações. Testes de gravação usaram banco QA isolado, não os projetos reais.

- Backend345+85subtestes e continuidade8 (353+85 conjuntos),92frontend aprovados.
- 14E2E locais aprovados; repetição final de interface.spec após ocultar indicadorNext também aprovada.
- Teste novo verifica autosave desligado semPUT/ligado com persistência real QA, observações multilinha, tipografia dos três cabeçalhos, menu por teclado/Escape/clique fora, axe e telas320/390/768/1024/1440, sem overflow horizontal. Checkbox18px/textarea>130px conferidos.
- Capturas desktop/celular inspecionadas em/tmp/eletroprojeto-{project,actions}-polish-{390,1440}.png; não representam banco real nem backup.
- Tipos/lint/formatação/buildwebpack/Ruff/contratos/Alembiccheck/pipcheck/npm ls aprovados. Sem alterações em cálculos; PostgreSQL/Windows/E2EHTTPS não repetidos nesta entrega visual local.

API reiniciada PID573356/sessão24451 para carregar versão0.13.1; frontend existente preservado e reiniciado automaticamente pelo Next ao mudar configuração. Smoke final no navegador real: versão0.13.1, checkbox18×18px, sem overflow em390px ou pageerrors; health API0.13.1/motor0.8.0 confirmado. Conferir PIDs/portas em cada retomada, sem iniciar duplicados.

## Continuidade e próximo passo

Checkpoint inicial `.checkpoints/20261023T191637169089Z`:163arquivos e restaurações SQLite/Git verificadas. Caminho do checkpoint final a registrar após geração. PDFs locais em references/energisa, fora do Git/ZIP de código. Sem push/publicação.

Próximas prioridades locais no roadmap: ampliar exceções normativas somente após fontes/testes próprios; dimensionamento e geometria completos; associação territorial oficial. Leitor de tela real ainda não conferido. Retomar por AGENTS e `python3 scripts/continuity.py retomar`; preservar este polimento e o motor único existente.
