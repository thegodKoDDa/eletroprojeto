# Segurança e recuperação

## Acesso implementado — revisão 24/10/2026

Implementação nova em `app/auth.py` e migração0004: modo local restrito a loopback e projetos sem proprietário; modo remoto exige HTTPS, contas provisionadas localmente (sem inscrição pública), Argon2 via pwdlib e sessões opacas com hash SHA256 no banco, validade de oito horas e revogação no logout/troca de senha/desativação. Cookie Secure/HttpOnly/SameSite Strict; operações mutáveis exigem Origin permitido e token CSRF em memória. CORS explícito aceita credenciais somente nas origens configuradas. Não usar o modo local atrás de proxy público.

Consultas ORM dos projetos são filtradas pelo proprietário no escopo da requisição, inclusive restauração/purga; novos projetos recebem o proprietário autenticado. Usuários não acessam IDs/históricos/relatórios de terceiros (404). Projetos legados permanecem sem proprietário, com dados/histórico preservados, e não ficam acessíveis remotamente até atribuição administrativa explícita. Permissão atual é de proprietário exclusivo; compartilhamento por equipe não implementado.

`backend/accounts.py` cria contas, redefine senhas, desativa e atribui projetos locais. Senhas entram por getpass, nunca por argumentos/logs. Redefinição/desativação revoga sessões; recuperação operacional é administrativa, sem e-mail automático. Há bloqueio persistido após cinco falhas por conta em quinze minutos. Isso não substitui rate limiting no ingresso, TLS real, configuração de proxy confiável, quotas e monitoramento. Testes de duas contas/CSRF/revogação/HTTPS/isolamento aprovados em SQLite e PostgreSQL; não é pentest ou aprovação de publicação remota.

Frontend remoto exige `NEXT_PUBLIC_AUTH_MODE=remote` e URL HTTPS da API; backend exige `AUTH_MODE=remote` e CORS_ORIGINS HTTPS explícito. Login/sair e escopo de rascunhos por conta implementados; tokens de sessão não são persistidos em localStorage. Rascunhos contêm dados pessoais em armazenamento local do perfil do navegador, sem criptografia própria; recuperação é oferecida antes de carregar, sem envio automático. O usuário autorizou recuperação neste pedido; em dispositivo compartilhado, apagar rascunhos locais e usar perfis separados. Slots independentes evitam sobrescrita entre abas; armazenamento bloqueado/cheio é informado.

Código/histórico são sincronizados com o repositório GitHub público autorizado; dados e originais permanecem locais. Sincronização exige destino fixo, main limpa, visibilidade pública conferida e ausência de commits remotos a revisar. Não usa force-push, não armazena token e não publica o site. O antigo exportador GPG opcional foi retirado; recuperação atual e limites em [continuity](continuity.md).

## Proteções implementadas

- Validação Pydantic e consultas SQLAlchemy; valores inválidos não são gravados como dados técnicos válidos.
- Corpo HTTP limitado a 4 MiB antes da validação JSON, contando os bytes de todos os chunks. Configuração `MAX_REQUEST_BYTES` (mínimo 1024).
- CORS aceita somente origens HTTP/HTTPS explícitas de `CORS_ORIGINS`, sem curingas, credenciais ou caminhos. CORS não é controle de acesso à API.
- Respostas sem cache e `X-Content-Type-Options: nosniff`.
- Exclusão lógica com versão otimista. Projetos excluídos não aparecem na listagem ativa nem podem ser editados/exportados pelos endpoints de projeto. Restauração exige versão atual. Cargas e histórico ficam preservados.
- Importação de referências continua sendo operação local de candidatos; não publica regras automaticamente.

## Recuperação e migração

A migração 0003 apenas acrescenta `deleted_at` e seu índice, sem apagar payloads ou histórico. Antes da aplicação local foi criado backup SQLite íntegro em `/tmp/eletroprojeto-before-0003.db`. Esse registro é histórico; a operação atual mantém checkpoints privados datados.

O utilitário `backend/technical_admin.py backup` usa a API de backup SQLite e verifica integridade, recusando sobrescrever o destino. A restauração de projetos é feita pela interface de projetos excluídos ou `POST /api/v1/projects/{id}/restore?expected_version=N`.

## Limites reais

Operação atual local; autenticação remota e isolamento por proprietário já existem. A publicação futura exige configuração de TLS/proxy confiável, rate limiting no ingresso, política de backup durável e monitoramento operacional. Cadastro público, recuperação de senha por e-mail e compartilhamento por equipe não estão implementados. Não publicar o modo local atrás de proxy.

O limite de bytes reduz risco de grandes corpos; não substitui limites de concorrência, timeout e recursos do servidor. A interface usa a listagem paginada de resumos; a rota legada completa permanece disponível. A busca literal da biblioteca ainda não possui índice especializado de texto. Exclusão lógica não constitui apagamento definitivo de dados.

Em24/10/2026, npm audit online e pip-audit sobre requirements.lock não apontaram vulnerabilidades conhecidas. Isso não é pentest nem garantia de ausência de vulnerabilidades futuras; verificações efetivas da entrega em CURRENT_STATE.

## Continuidade e manutenção

Procedimento responsável em [continuity.md](continuity.md). Checkpoints preservam fonte, SQLite, Git e auditoria; hashes e restauração isolada são conferidos antes de publicar latest.json. Cópias SQLite idênticas podem compartilhar armazenamento, mantendo cada ponto e sua restauração. Originais do acervo, buffers externos e rascunhos ainda não enviados não ficam no arquivo de fonte.

GitHub protege a fonte/histórico fora deste computador, mas não recebe banco/credenciais/checkpoints/objetos do acervo. Não há implantação ou cópia externa automática dos dados privados. Esse limite não é tratado como tarefa pendente do usuário. GitHub Actions permanece desativado e o workflow é preservado.

Doctor inspeciona dependências/permissões/serviços sem reinstalar ou revelar credenciais. fix-permissions atua apenas nos privados conhecidos, sem symlinks, chmod de fontes/.git ou alteração global de políticas. POSIX0600/0700 não equivalem a auditoria de ACL Windows. Limpeza limita-se a gerados permitidos e pastas vazias conhecidas; compactação restaura todos os pontos antes de compartilhar arquivos idênticos.

## Evolução somente quando aplicável

Uso remoto futuro exige TLS/proxy confiável, rate limiting, limites de concorrência/tempo, monitoramento e backup adequado ao banco. Modo local não deve ser publicado por proxy. Autenticação/isolamento já implementados não substituem preparação operacional. Não solicitar esses recursos para bloquear a operação local atual.

Atualizações de dependências são controladas pelos manifests/locks e verificações pertinentes; não executar `audit fix --force` nem tratar auditoria sem alertas como pentest. Histórico de auditorias e entregas está em SESSION_HISTORY/audit; resultados da sessão atual em CURRENT_STATE.
