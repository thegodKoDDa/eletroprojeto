# Estado atual — EletroProjeto 0.14.1 / motor 0.8.0

## Escopo e dados

Uso LOCAL. Publicação, CI hospedado, impressão física e backup externo fora do trabalho atual. Recursos existentes preservados; sem push. API/frontend0.14.1, motor0.8.0, JSON1.3 e schema0005, sem nova migração ou fórmula/regra/catálogo alterados.

9 projetos (8 ativos/1 na lixeira),30 históricos e8 revisões técnicas. Todas as colunas dessas três tabelas comparadas ao checkpoint inicial `.checkpoints/20261023T194010017686Z` e idênticas após a tarefa. SQLite íntegro/FK sem violações. Testes de gravação usaram bancos QA isolados; nada foi regravado nos projetos reais.

## Interface compacta — 0.14.1

Início sem aside: marca/logo e saída de conta no cabeçalho, informações e rodapé preservados. Criar projeto, projetos salvos e lixeira abrem o espaço com navegação lateral; voltar ao início a oculta novamente. Estado da edição permanece ao continuar. Cartões iniciais e espaçamentos gerais de controles/painéis reduzidos, sem retirar campos.

Equipamentos agrupam Configurações avançadas, Consumo mensal e Valores de referência em disclosures nativos compactos, alinhados no desktop e com quebra no celular. Resumos de30px no desktop/ mínimo34px no celular, ações separadas por borda e espaçamento menor. Conteúdo aberto sem altura fixa; foco, hover, desabilitados e teclado preservados.

Validação desta entrega:348 testes backend+85 subtestes,92 frontend,16E2E e1E2EHTTPS de duas contas aprovados. Contratos/tipos/lint/formatação/buildwebpack/Alembiccheck aprovados. Novo E2E confere Home sem aside, rodapé dentro da janela1440×900, navegação, edição preservada, três disclosures funcionais, axe e ausência de overflow320/390/768/1440. Capturas QA desktop/celular inspecionadas. Smoke localhost confirmou API0.14.1/motor0.8.0, comportamento da barra e nenhum pageerror. API reiniciada PID594371; frontend3000 existente preservado. Conferir processos ao retomar.

Banco real comparado integralmente ao checkpoint `.checkpoints/20261023T214013315521Z`:9projetos/30históricos/8revisões idênticos, nenhuma gravação pela tarefa. Nenhuma dependência, fórmula, migração ou catálogo alterados; locks comparados estruturalmente, somente versão própria mudou. PostgreSQL, Windows e testes unitários dos scripts não repetidos nesta entrega visual; evidências abaixo são da0.14.0. Encerramento final verifica novamente fonte, hashes e restauração isolada.

## Otimização entregue

- Biblioteca usa GET projects/summaries, projeção SQL sem equipamentos/notas; abrir busca payload completo/fresco. Consulta única para lista completa e resumos, filtros nome/município escapados, paginação/ordenação e isolamento por proprietário. Transferência real dos mesmos8 projetos:328.785→2.827bytes (-99,14%). Endpoint completo preservado por compatibilidade.
- PUT sem mudanças na mesma revisão mantém versão/data/histórico e evita cálculo/gravação redundantes. expected_version continua obrigatório e conflito409 precede comparação. Mudanças reais mantêm transação/histórico e valores manuais.
- Primeiro POST com Idempotency-Key UUID evita duplicação após perda de resposta. Chave persistida no rascunho antes do envio; reenvio diferente409 recupera versão já criada, mantendo edições locais. Salvar como novo conserva nome da cópia também após resposta perdida. Sem sobrescrita silenciosa de outra conta/lixeira.
- Serialização de input/base por snapshot memoizada. Rascunhos schema1 compatíveis com createId opcional, escrita agrupada250ms e flush em saída/ocultação/desmontagem/troca de contexto. Recuperar não envia ao servidor. Limite real: término abrupto sem eventos pode perder o intervalo anterior ao flush; navegador limpo/outro perfil não recupera esses dados.
- Encerrar captura em .pending privado, valida hashes, restaura SQLite/Git, sincroniza e publica atomicamente. Lock evita concorrência no ponteiro; latest.json só avança após sucesso. Dados grandes lidos em blocos/dump percorrido sem reter tudo em RAM. Ponto idêntico é reutilizado somente após nova verificação completa; --force-new força distinto. Pontos incompletos/corrompidos não são anunciados como seguros.
- Regras AGENTS/continuidade simplificadas: ler docs atuais + cauda de registros, retomar compacto, um commit revisado final e só então checkpoint. latest.json elimina commit/checkpoint extra só para registrar caminho. Memória/guia consolidados; SESSION_HISTORY preservado.
- maintenance.py doctor/clean auditam instalações/permissões/serviços e limpam apenas gerados por allowlist, com simulação/manifest. Cerca50MB de caches/saídas QA removidos. Preservados venvs Linux/Windows, node_modules, Next ativo/cache/build, dados, backups, normas e Git.28 checkpoints anteriores integralmente verificados e distintos, nenhum apagado. Três arquivos privados corrigidos para0600; fontes sem escrita global. Não alterar ACL/política global por suposição.

## Verificações da otimização 0.14.0 (histórico)

- Linux:348 testes backend+85 subtestes e15 scripts de continuidade/manutenção (363+85 conjuntos).
- Frontend92;15E2E locais; repetição final do fluxo de resposta perdida/recarga/cópia;1E2EHTTPS de duas contas aprovado. Tipos/lint/formatação/contratos/buildwebpack/Ruff/Alembiccheck/pipcheck/npm ls aprovados.
- PostgreSQL QA18.6 já ativo:93 testes API/autenticação aprovados, com schemas temporários. Banco real continua SQLite0005.
- Windows real/Python3.13:11 scripts aprovados,4 pulados por recursos/permissões/plataforma indisponíveis. Wrappers retomar/encerrar/reutilizar/ForceNew aprovados em projeto fictício isolado. Política inicial bloqueou .ps1; QA usou autorização somente do processo, sem mudança global. ACL Windows e backend/frontend Windows completos não revalidados nesta tarefa.
- Instalações Python/pip, Node/npm/pacotes e Git auditadas, sem dependência nova. Git fsck sem corrupção; blobs órfãos recuperáveis preservados, sem prune. Banco real idêntico e28 backups antigos restaurados/verificados, sem falhas.
- Smoke navegador real: biblioteca leve, abertura/recalculo de projeto existente, versão0.14.0 e nenhum pageerror. API PID586275/sessão55305 e frontend3000 HTTP200; revalidar processos ao retomar. Doctor final sem modos privados pendentes ou lock/.pending, serviços saudáveis.

Benchmark sintético de checkpoint16MiB antes/depois sem ganho relevante de tempo observado (0,1227/0,1212s, medição intermediária); RSS observado46.972/43.008KiB. Não extrapolar promessa universal. Ganhos principais comprovados: transferência da biblioteca, eliminação de gravações/cópias redundantes, contexto menor e segurança da recuperação. Fonte/banco/refs alterados continuam exigindo ponto novo completo.

## Continuidade e próximo trabalho

Referência persistente do encerramento final: `.checkpoints/latest.json`, preenchida/confirmada somente pelo comando encerrar após o commit revisado. Não alterar estes docs novamente apenas para colar o caminho. O retorno da execução e VERIFIED.json comprovam o resultado; verificar refaz restauração completa. FonteZIP exclui dados privados/PDFs; referências locais intactas em references/energisa.

Retomar por AGENTS + continuity.py retomar. Próximas prioridades locais no roadmap: exceções normativas, dimensionamento e geometria completos, associação territorial oficial. Polimento0.13.1, motor único, revisões explícitas de demanda NDU7.0 d1–d5 e limites permanecem. Sem implantação ou tarefas de impressão física/cópia externa.
