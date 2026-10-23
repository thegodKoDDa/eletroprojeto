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

Ler este arquivo, `docs/PROJECT_MEMORY.md`, `docs/CURRENT_STATE.md`, `docs/roadmap.md`, `docs/KNOWN_ISSUES.md`, últimos registros de `CHANGELOG.md` e `docs/SESSION_HISTORY.md`. Conferir código, versões, Git real, banco/migrações e dependências; executar `python3 scripts/continuity.py retomar` (ou wrapper PowerShell). O script não inicia serviços nem valida testes: o agente verifica/inicia serviços conforme a tarefa e informa somente resultados observados. Continuar pelo próximo passo registrado, sem depender da conversa anterior.

### Durante o desenvolvimento

Depois de alterações relevantes, atualizar o documento responsável e CURRENT_STATE; registrar decisões, bugs/causas/regressões, testes efetivos e limitações. Registrar norma/edição/condições/testes/projetos afetados ao alterar regras. Antes de interromper, escrever o que foi feito, arquivos, o que falta e verificações pendentes. Checkpoints periódicos após marcos estáveis, especialmente antes de mudanças estruturais. Não duplicar arquitetura/cálculos/normas em arquivos novos: usar documentos existentes em minúsculas.

### ENCERRAR SESSÃO DO ELETROPROJETO

1. Conferir arquivos no disco e Git (inclusive novos arquivos); não é possível assegurar buffers não salvos de um editor externo.
2. Atualizar CURRENT_STATE, acrescentar SESSION_HISTORY sem apagar registros, atualizar CHANGELOG/documentos afetados; registrar testes realmente executados e tarefas interrompidas.
3. Executar verificações proporcionais, conferir banco/migrações. Não apagar dados nem alterações para obter estado limpo.
4. Revisar nomes/conteúdo de arquivos por segredos antes de versionar. Nunca adicionar `.env` privados, bancos, backups, tokens ou credenciais. Não fazer push sem autorização.
5. Executar `python3 scripts/continuity.py encerrar`. Exigir verificação do arquivo de código, hashes e restauração SQLite isolada; registrar caminho em CURRENT_STATE antes de criar o checkpoint final quando possível. Checkpoint falho não é seguro.
6. Criar commit Git local revisado quando disponível/autorizado pelo pedido de checkpoint; não inicializar/substituir histórico existente ou contornar restrições de `.git`. Se indisponível, registrar explicitamente ausência de commit e usar arquivo verificado como recuperação local.
7. Relatar o que foi preservado, exclusões, falhas, backup, Git e como retomar. Não desligar computador, fechar programas à força ou interromper gravações. Recomendar cópia externa protegida; backup no mesmo disco não protege contra perda do computador.

Scripts auxiliares não substituem análise/documentação do agente. Ver procedimento, restauração e retenção em `docs/continuity.md`. Nunca afirmar que o procedimento executa automaticamente fora de uma sessão ou que é possível recuperar contexto sem ler os arquivos.
