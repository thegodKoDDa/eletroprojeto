# Segurança e recuperação — 0.3.0

## Revisão em andamento — 23/10/2026

Implementação nova em `app/auth.py` e migração0004: modo local restrito a loopback e projetos sem proprietário; modo remoto exige HTTPS, contas provisionadas localmente (sem inscrição pública), Argon2 via pwdlib e sessões opacas com hash SHA256 no banco, validade de oito horas e revogação no logout/troca de senha/desativação. Cookie Secure/HttpOnly/SameSite Strict; operações mutáveis exigem Origin permitido e token CSRF em memória. CORS explícito aceita credenciais somente nas origens configuradas. Não usar o modo local atrás de proxy público.

Consultas ORM dos projetos são filtradas pelo proprietário no escopo da requisição, inclusive restauração/purga; novos projetos recebem o proprietário autenticado. Usuários não acessam IDs/históricos/relatórios de terceiros (404). Projetos legados permanecem sem proprietário, com dados/histórico preservados, e não ficam acessíveis remotamente até atribuição administrativa explícita. Permissão atual é de proprietário exclusivo; compartilhamento por equipe não implementado.

`backend/accounts.py` cria contas, redefine senhas, desativa e atribui projetos locais. Senhas entram por getpass, nunca por argumentos/logs. Redefinição/desativação revoga sessões; recuperação operacional é administrativa, sem e-mail automático. Há bloqueio persistido após cinco falhas por conta em quinze minutos. Isso não substitui rate limiting no ingresso, TLS real, configuração de proxy confiável, quotas e monitoramento. Testes de duas contas/CSRF/revogação/HTTPS/isolamento aprovados em SQLite e PostgreSQL; não é pentest ou aprovação de publicação remota.

Frontend remoto exige `NEXT_PUBLIC_AUTH_MODE=remote` e URL HTTPS da API; backend exige `AUTH_MODE=remote` e CORS_ORIGINS HTTPS explícito. Login/sair e escopo de rascunhos por conta implementados; tokens de sessão não são persistidos em localStorage. Rascunhos contêm dados pessoais em armazenamento local do perfil do navegador, sem criptografia própria; recuperação é oferecida antes de carregar, sem envio automático. O usuário autorizou recuperação neste pedido; em dispositivo compartilhado, apagar rascunhos locais e usar perfis separados. Slots independentes evitam sobrescrita entre abas; armazenamento bloqueado/cheio é informado.

`scripts/external_backup.py` prepara cópia GPG para fingerprint completo e destino escolhido, verifica o checkpoint antes de criptografar e o hash após transferência, recusa sobrescrita. Teste com chave temporária fez ida/volta, decriptação e restauração SQLite isolada com sucesso. A cópia real externa ainda depende de destino/chave do usuário; teste em /tmp não é cópia externa nem restauração da chave real. Fontes de implementação: [FastAPI/pwdlib e Argon2](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/). A aplicação usa sessões revogáveis, não o JWT do exemplo.

## Proteções implementadas

- Validação Pydantic e consultas SQLAlchemy; valores inválidos não são gravados como dados técnicos válidos.
- Corpo HTTP limitado a 4 MiB antes da validação JSON, contando os bytes de todos os chunks. Configuração `MAX_REQUEST_BYTES` (mínimo 1024).
- CORS aceita somente origens HTTP/HTTPS explícitas de `CORS_ORIGINS`, sem curingas, credenciais ou caminhos. CORS não é controle de acesso à API.
- Respostas sem cache e `X-Content-Type-Options: nosniff`.
- Exclusão lógica com versão otimista. Projetos excluídos não aparecem na listagem ativa nem podem ser editados/exportados pelos endpoints de projeto. Restauração exige versão atual. Cargas e histórico ficam preservados.
- Importação de referências continua sendo operação local de candidatos; não publica regras automaticamente.

## Recuperação e migração

A migração 0003 apenas acrescenta `deleted_at` e seu índice, sem apagar payloads ou histórico. Antes da aplicação local foi criado backup SQLite íntegro em `/tmp/eletroprojeto-before-0003.db`. `/tmp` é temporário: retenção permanente e cópias externas ainda devem ser configuradas no ambiente de implantação.

O utilitário `backend/technical_admin.py backup` usa a API de backup SQLite e verifica integridade, recusando sobrescrever o destino. A restauração de projetos é feita pela interface de projetos excluídos ou `POST /api/v1/projects/{id}/restore?expected_version=N`.

## Limites reais

Uso local, sem contas ou autorização por proprietário. Não publicar a API abertamente como aplicação multiusuário. Faltam autenticação, autorização, TLS/ingress, rate limiting compartilhado, política de backup durável e monitoramento operacional. Não foi introduzida uma chave fixa ou mecanismo improvisado para simular autenticação.

O limite de bytes reduz risco de grandes corpos; não substitui limites de concorrência, timeout e recursos do servidor. A listagem atual ainda retorna payloads completos e precisa de paginação/resumos para grandes acervos. Exclusão lógica não constitui apagamento definitivo de dados.

Auditoria npm offline executada com resultado zero no relatório local; isso não confirma ausência de vulnerabilidades atuais sem consulta atualizada à base de avisos. Auditoria online e Python devem ser registradas separadamente, conforme disponibilidade das fontes.

## Checkpoints privados — 22/10/2026

Procedimento atual em [continuity.md](continuity.md): backups nomeados em .checkpoints, SQLite API, integrity/FK e restauração isolada, hashes de fonte e banco, permissões POSIX e exclusão de segredos/dependências por nome. Não há criptografia nem cópia externa automática; revisar segredos no conteúdo antes de compartilhar. Informações acima sobre retenção permanente ausente são históricas: cópias locais datadas agora existem, proteção externa continua pendente. Listagem de projetos já possui paginação; purga definitiva está disponível e não deve ser confundida com exclusão lógica reversível.

## Revisão 0.7.0 — proteções atuais e ordem dos próximos passos

1. **Proteção dos dados e do código:** manter o serviço restrito a loopback; obter Git utilizável sem substituir histórico recuperável e cópia externa protegida/criptografada do checkpoint. Testar restauração periodicamente. `.checkpoints` continua no mesmo disco; não há cópia externa configurada nesta instalação. Cache Ruff e metadados `.egg-info/.dist-info` agora são excluídos dos novos arquivos de fonte dos checkpoints, além das exclusões privadas já existentes. Não se apagam checkpoints antigos.
2. **Antes de uso remoto/multiusuário:** autenticação com mecanismo de sessão estabelecido, autorização de proprietário em TODOS os endpoints de projetos, históricos, relatórios, cópias, lixeira e purga; migração não destrutiva de proprietário e testes de acesso entre dois usuários. Definir política de contas/recuperação antes de implantar; não improvisar chave fixa no frontend. Se usar cookies, HttpOnly/Secure/SameSite e proteção CSRF nas operações mutáveis. CORS não substitui essas medidas.
3. **Implantação:** reverse proxy/TLS, hosts/origens permitidos, quotas por usuário, limites de concorrência/tempo em cálculos/PDF, rate limiting no ingresso e paginação/resumos obrigatórios em coleções grandes. Limite de corpo já existe, mas não limita sozinho trabalho computacional ou tamanho de respostas. Não expor servidores dev de Next/Vitest.
4. **Prevenção de regressões:** CI com pytest, lint/formatação, typecheck, types:sync sem divergência, Alembic, E2E isolado e auditorias periódicas. `package-lock.json` já fixa o frontend; preparar lock Python reproduzível com hashes para implantação, atualização controlada e inventário de dependências. Ruff/pip-audit usados nesta sessão em venv separado em /tmp; provisionar essas ferramentas de forma reproduzível no CI.
5. **Continuidade do usuário:** recuperação de rascunhos com consentimento/escopo local, tratamento de conflitos e política de retenção/limpeza em dispositivos compartilhados. Não registrar payloads pessoais/credenciais em logs de operação. Observabilidade de erros/latência e testes reais de backup/PDF/PostgreSQL completam a operação.
6. **Cabeçalhos de produção:** CSP com política testada para os scripts Next e API configurada; avaliar nonce e impacto na renderização/cache. HSTS apenas após TLS efetivo. Não adicionar política permissiva só para dizer que há CSP.

Entregue agora: links de referência salvos são filtrados para HTTP(S) sem credenciais; protocolos `javascript:`, `data:` e `file:` não viram links. Frontend com nosniff, X-Frame-Options DENY, Referrer-Policy no-referrer e Permissions-Policy sem câmera/microfone/geolocalização. Headers conferidos no E2E. Backend conserva no-store/nosniff, fronteira de corpo, validação estrita, SQLAlchemy e versionamento otimista.

Auditoria npm inicial encontrou dois alertas críticos e um moderado em ferramentas de teste. Vitest atualizado para 4.1.12, com correções publicadas pelo [mantenedor](https://github.com/vitest-dev/vitest/security/advisories/GHSA-qxg6-89mg-rqv8). Dependência transitiva braces com alerta foi evitada removendo eslint-config-next; ESLint 10 + typescript-eslint/react-hooks mantêm lint sem essa cadeia. Sem overrides ou `audit fix --force` para mascarar compatibilidade. Auditoria npm após instalações e pip-audit do inventário instalado sem alertas conhecidos na consulta desta sessão; isso não é teste de invasão, SAST completo ou garantia futura. Pacote local editável é código próprio e não é validado por bancos de vulnerabilidades de terceiros.


Decisão de escopo em23/10/2026: usuário manterá operação local e retirou publicação remota/CI hospedado, impressão física e backup externo do trabalho atual. Não solicitar destino/chave nem bloquear entregas por esses itens. Mecanismos existentes permanecem preservados; checkpoints locais continuam verificados. Limitações físicas de armazenamento local permanecem verdadeiras, sem constituir tarefa ativa de cópia externa.


## Manutenção local — 0.14.0

Doctor inspeciona toolchain/instalações, SQLite/Git, HTTP local e modos privados, sem imprimir conteúdo de .env/credenciais. fix-permissions restringe apenas arquivos conhecidos ao dono (POSIX0600/0700), não segue symlinks nem altera código/.git/política global. Três arquivos privados nesta instalação foram ajustados; fontes sem escrita global. ACL Windows não é validada por chmod. QA Windows usou permissão de execução somente no processo temporário, sem mudar ExecutionPolicy global.

Summaries mantém isolamento por proprietário inclusive filtros; tentativa de reutilizar chave de criação de outra conta responde409 sem retornar payload. Idempotency-Key não autentica nem substitui CSRF. Fluxos de sessão/HTTPS existentes preservados, sem implantação remota ativa. Limpeza estritamente por allowlist, nunca dados/backups/venvs/node_modules; detalhes em continuity.md.
