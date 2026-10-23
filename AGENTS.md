# Regras permanentes

- Stack: Next.js App Router, TypeScript, Tailwind; Python, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic e SQLite. Preservar portabilidade para PostgreSQL.
- Toda matemática elétrica fica em `backend/app/calculations`. Funções puras não importam FastAPI, Pydantic ou ORM.
- Frontend formata e valida formulários; não replica fórmulas.
- Não inventar coeficientes, potências nominais, mapeamentos de concessionárias ou regras normativas.
- Habilitar regras somente após conferir fonte oficial, edição, condições, cláusulas, limites e exemplos independentes. Registrar referência, testes e estado de validação.
- Regras não conferidas retornam `null` e estado pendente, nunca zero como substituto.
- Separar W de VA, estimativa de placa, iluminação nominal de previsão normativa e carga cadastrada de catálogo.
- Usar Decimal, unidades explícitas e evitar arredondamentos intermediários.
- Alterações de cálculos exigem testes de resultados e limites. Executar pytest, testes frontend e E2E quando dependências estiverem disponíveis; relatar o que não foi executado.
- Gerar contratos com `npm run types:sync`. Nunca editar `api.generated.ts` manualmente.
- Preservar migrações e histórico dos projetos. Não modificar catálogo ao editar instância.
- Não exibir resultado antigo para entradas novas. Preservar debounce e cancelamento de requisições.
- Priorizar Etapa 1. Não declarar conformidade ou dimensionamento final enquanto houver pendências normativas.

## Execução local — preferência do usuário

- Autorização permanente do usuário: executar autonomamente todos os testes e verificações necessários (backend, frontend, API, E2E, build, contratos e banco), sincronizações, migrações e inicialização/reinicialização dos serviços relacionados à tarefa. Não pedir confirmação novamente para essas rotinas. Agrupar verificações e usar permissões persistentes adequadamente delimitadas quando disponíveis. Respeitar restrições obrigatórias do ambiente; esta autorização não permite contorná-las nem autoriza apagar dados ou fazer push.

- O agente executa os comandos de atualização, sincronização de contratos, migração e inicialização/reinicialização dos serviços necessários à tarefa; não delegar rotinas de terminal ao usuário.
- Após alterações, verificar os serviços existentes antes de iniciar outros, preservar dados e entregar links localhost confirmados quando o ambiente permitir.
- Se o ambiente bloquear processos, rede ou portas, informar o impedimento de forma breve e honesta; não declarar que um localhost está ativo sem verificação.

## Identidade e continuidade permanente

EletroProjeto é uma ferramenta de estudo/cálculo elétrico residencial para leigos, estudantes e profissionais. Um único motor Python atende as apresentações simples e técnica. Preservar o produto, os dados e funcionalidades corretas; não recriar sem autorização explícita. Referências são sugestões, não potências universais: respeitar valores manuais válidos. Não esconder erros com remendos; preservar segurança e rastreabilidade.

### Início de toda sessão / RETOMAR ELETROPROJETO

Ler este arquivo, `docs/PROJECT_MEMORY.md`, `docs/CURRENT_STATE.md`, `docs/roadmap.md`, `docs/KNOWN_ISSUES.md` e os últimos registros de CHANGELOG/SESSION_HISTORY (começar por `tail -n 60`, ampliar somente se necessário). Executar `python3 scripts/continuity.py retomar`: saída compacta de Git, banco e dependências, sem repetir os documentos já lidos. `.checkpoints/latest.json` aponta para o último ponto publicado; marcador/hash do manifest não substituem restauração completa com verificar. Conferir serviços existentes antes de iniciar outros. Executar doctor quando dependências, permissões, ambiente ou falhas exigirem revisão; não reinstalar nem repetir baterias já aprovadas sem mudança relevante. Continuar pelo próximo passo registrado, sem depender da conversa anterior.


### Durante o desenvolvimento

Depois de alterações relevantes, atualizar o documento responsável e CURRENT_STATE; registrar decisões, bugs/causas/regressões, testes efetivos e limitações. Registrar norma/edição/condições/testes/projetos afetados ao alterar regras. Antes de interromper, escrever o que foi feito, arquivos, o que falta e verificações pendentes. Checkpoints periódicos após marcos estáveis, especialmente antes de mudanças estruturais. Não duplicar arquitetura/cálculos/normas em arquivos novos: usar documentos existentes em minúsculas.

### ENCERRAR SESSÃO DO ELETROPROJETO

1. Conferir disco, Git e arquivos novos; buffers não salvos de editor externo não são verificáveis.
2. Atualizar CURRENT_STATE e acrescentar SESSION_HISTORY sem apagar registros; atualizar documentos responsáveis. Registrar somente verificações efetivas, limitações e próximo passo. Usar `.checkpoints/latest.json` como referência persistente do checkpoint final, sem prometer sucesso antes da execução.
3. Executar verificações proporcionais às mudanças. Preservar dados e migrações; não repetir testes/instalações sem mudança, falha ou preocupação concreta. Limpeza com `python3 scripts/maintenance.py clean` primeiro simula; `--apply` remove apenas gerados permitidos e `--qa-builds` inclui saídas QA com portas livres. Nunca remover dependências úteis, dados, fontes, normas ou pontos únicos de recuperação para obter estado limpo.
4. Revisar segredos nos nomes/conteúdo antes de versionar. Nunca adicionar .env privado, banco, backup, token ou credencial. Revisar e criar um único commit local de código/docs quando Git estiver disponível e autorizado; nenhum push. Não modificar histórico nem contornar proteção de .git.
5. Depois do commit, executar `python3 scripts/continuity.py encerrar`. O checkpoint deve incluir o commit final, hashes, fonte e restaurações SQLite/Git isoladas; só então atualizará latest.json atomicamente. Sem mudanças, reutiliza o último ponto após revalidá-lo por completo; `--force-new` força cópia distinta. Falha não é sucesso: o ponteiro anterior permanece e o agente deve resolver/relatar o erro. Não fazer outro commit apenas para copiar o caminho do checkpoint para os docs; consultar o ponteiro evita ciclo de commits/checkpoints redundantes.
6. Conferir status final e relatar preservação, exclusões, verificações, checkpoint retornado e como retomar. Sem Git, registrar ausência de commit e usar arquivo de fonte verificado. Não fechar programas à força, interromper gravações ou desligar o computador.

Uso local definido pelo usuário em23/10/2026: publicação, impressão física e backup externo fora do trabalho atual; não cobrar esses itens. Checkpoint no mesmo disco não cobre perda física. Scripts não substituem análise/leitura dos documentos e não executam fora da sessão. Procedimento e recuperação em docs/continuity.md.
