# Roadmap — uso local, 0.17.0

Decisão do usuário em 23/10/2026: operar localmente. Publicação/infraestrutura remota, execução hospedada de CI, impressão física e backup externo foram retirados do escopo atual; não tratá-los como bloqueios ou cobrar recursos para essas tarefas. Código funcional de autenticação, CI e backup já existente fica preservado para evitar regressões.

0.14.0: biblioteca leve, salvamento idempotente/sem gravação redundante, rascunhos com flush, checkpoints atômicos/reutilizáveis e auditoria/limpeza local. Procedimento em continuity.md; testes atuais em CURRENT_STATE.

0.15.0: biblioteca técnica pesquisável,guias/modelos/diagramas/PDFs e fontes locais persistidas. Revisão técnica específica ainda exigida para habilitar regras; importar não conclui dimensionamento nem cobertura territorial.

0.16.0:OCR/triagem,estudo limitado de circuitos Cu/PVC/B1/B2 e verificações de proteção com dados explícitos;enquadramentoESS220/127Vtabela16. Métodos e campos novos não concluem dimensionamento final universal; ampliar somente com fontes/condições/testes.

0.17.0: revisão de integração, assinatura completa de exportações, contratos de acesso/revalidação, prévia e registro explícito de revalidação na interface, limpeza de associações removidas e inicialização extraída para hook próprio. Sem ampliar regras normativas.

## Disponível

- Projetos, histórico, biblioteca/lixeira, duplicação, autosave, rascunhos recuperáveis e resolução guiada de conflitos.
- Motor Python Decimal, potências W/VA, correntes com dados suficientes, consumo/custo opcionais e catálogo persistente com preservação de valores manuais.
- Previsão residencial quantitativa de iluminação/TUG em escopo explícito; resultados simples/técnicos e PDF/JSON.
- NDU-001 7.0 d1–d5 integrada ao inventário do projeto: classificação explícita de cada carga, reservas, ausências, escopo e revisão vinculada por hash. Mudanças invalidam a confirmação; sem classificação ou fora do escopo, demanda nula. Não constitui dimensionamento final.
- Git e checkpoints locais com verificação de hashes, restauração SQLite e recuperação de histórico. PostgreSQL e Windows já possuem validações anteriores.

## Prioridades locais seguintes

1. Manter regressões de cálculos, cadastro, relatórios, acessibilidade automática, contratos, tipos, lint e build conforme as mudanças.
2. Ampliar a cobertura de demanda somente com revisão específica de grupos especiais, centrais de ar-condicionado e demais exceções. Não aplicar fatores de outra distribuidora.
3. Ampliar os estudos de circuitos, condutores/proteções e entrada além do subconjunto entregue em0.16.0, somente após conferir fontes, condições, limites e exemplos.
4. Implementar análise física de localização/distribuição de pontos e restrições da instalação; quantidades previstas não validam posição em planta.
5. Ampliar associação territorial oficial sem inferir concessionária por município ou endereço incompleto.
6. Melhorar revalidação seletiva de projetos afetados por mudanças normativas e desempenho em grandes acervos quando necessário.

Fontes, condições e testes normativos em [standards](standards.md) e [calculations](calculations.md). Estado das verificações em [CURRENT_STATE](CURRENT_STATE.md). A ausência de impressão física foi aceita pelo usuário; testes automáticos de acessibilidade não equivalem a uso com leitor de tela real, ainda não conferido.
