# Continuidade, armazenamento e recuperação — 0.14.0

## Rotina curta e verificável

RETOMAR: ler AGENTS, memória/estado/roadmap/pendências atuais e cauda dos registros; `python3 scripts/continuity.py retomar` retorna Git, banco, dependências e último checkpoint. A saída compacta evita imprimir documentos já lidos; `--documents` os inclui quando necessário. O agente confere serviços existentes e segue o próximo passo registrado. Scripts não iniciam serviços nem substituem leitura/análise.

ENCERRAR: conferir disco/Git, atualizar docs responsáveis e testes efetivos, revisar segredos e fazer um único commit local quando autorizado. Depois executar `python3 scripts/continuity.py encerrar`: inclui o HEAD final no bundle, verifica fonte/banco e restaura SQLite/Git isoladamente. O retorno informa o caminho; `.checkpoints/latest.json` é o ponteiro persistente. Não criar novo commit/checkpoint só para copiar esse caminho aos docs. Nenhum push, desligamento ou encerramento forçado de programas.

```bash
python3 scripts/continuity.py retomar
python3 scripts/continuity.py encerrar
python3 scripts/continuity.py encerrar --force-new
python3 scripts/continuity.py verificar --checkpoint .checkpoints/IDENTIFICADOR
python3 scripts/maintenance.py doctor
python3 scripts/maintenance.py clean
python3 scripts/maintenance.py clean --apply --qa-builds
```

Continuidade usa só stdlib Python3.11+. Wrappers retomar.ps1/encerrar.ps1 preferem backend/.venv-windows/Scripts/python.exe, depois .venv/Scripts/python.exe ou python no PATH; aceitam -Documents e -ForceNew respectivamente. Não alterar ExecutionPolicy global. Políticas de sessão podem bloquear .ps1; QA Windows usou autorização temporária somente do processo. Os comandos Python equivalentes continuam disponíveis; limitações reais são relatadas.

## O que fica protegido

Cada diretório publicado contém source.zip, data.sqlite3, manifest.json, VERIFIED.json e repository.bundle quando há Git com commit. Fonte inclui código/locks/testes/migrações/docs e arquivos normais não privados, inclusive alterações no disco ainda sem commit. Exclui .git, checkpoints, ambientes/dependências, builds/caches/logs, symlinks, bancos/arquivos de backup, .env privado/chaves/credenciais conhecidas, PDFs normativos e metadados de download. .env.example é incluído. Revisar segredos também no conteúdo/histórico antes de versionar. Não capturar buffers de editor nem rascunhos do navegador é um limite explícito.

Banco privado SQLite é copiado pela API backup, incluindo transações confirmadas em WAL, sem alterar o original. integrity_check e foreign_key_check no snapshot; restauração isolada confere contagens/migração e percorre todas as linhas do dump sem guardar o SQL inteiro em RAM. Hashes de arquivos grandes são lidos em blocos. Não há garantia de transação única entre fonte e banco: hashes da fonte são reconferidos e alterações de refs Git durante captura causam falha.

DATABASE_URL absoluto SQLite do ambiente é respeitado; relativo/memória/outro banco é recusado para não copiar dados errados. Default backend/eletroprojeto.db. O script não carrega .env nem descobre variáveis privadas de outro processo; o agente confere configuração ao operar serviços. PostgreSQL requer backup apropriado ao banco, não cópia de arquivo SQLite.

## Publicação e reutilização

Capturas concorrentes são bloqueadas por lock privado, sem disputar latest.json. Lock POSIX de processo encerrado na mesma máquina pode ser recuperado; em outros casos é preciso conferir o processo antes de removê-lo. Doctor informa lock/pontos pendentes.

Captura em .checkpoints/.pending-*, privado e sem anúncio como ponto concluído. Componentes são gravados/fechados/sincronizados; manifest/marker escritos com troca atômica. Só após verify bem-sucedido o diretório ganha o nome final e latest.json é atualizado atomicamente com hash do manifest. POSIX sincroniza também os diretórios. Falha mantém o ponteiro anterior; .pending não é backup concluído nem deve ser apagado sem análise.

Sem mudanças na fonte, hash do banco, HEAD/branch/refs Git, o último ponto pode ser reutilizado. Antes do retorno, executa a mesma verificação completa, restauração SQLite e clone Git. Não usar timestamp/marker como prova suficiente. --force-new força novo ponto físico. Corrupção impede reutilização; é criado novo ponto verificado e o corrompido fica para análise. Retomar confere somente pointer/hash do manifest, informando expressamente que não refez a restauração; verificar executa essa etapa.

Arquivos privados0600/diretórios0700 no POSIX. Em Windows, chmod não verifica ACL: considerar proteção da conta/local e inspeção nativa. A auditoria doctor mostra limites da plataforma; --fix-permissions só atua em privados conhecidos, sem seguir symlinks ou mudar código/.git/política global. Dados e snapshots não são criptografados automaticamente.

## Limpeza e retenção

clean primeiro simula; --apply remove somente allowlist de caches Python/pytest/Ruff/TypeScript e relatórios QA. --qa-builds também pode remover .next/e2e e e2e-auth se portas QA não estiverem ocupadas; estado de porta desconhecido impede essas exclusões. Preserva Next ativo/build/cache, venvs Linux/Windows, node_modules, metadados de instalação, fontes, normas, banco, backups, .git e checkpoints. Symlinks são recusados. A execução gera manifesto privado de remoções em .checkpoints/cleanup-*.json.

Não apagar pontos únicos automaticamente. O limite de14 sinaliza revisão, não autorização para descartar história nem exigência de backup externo (fora do escopo atual). Nesta revisão os pontos antigos eram distintos e foram preservados. Reutilização evita redundância futura. Cache de compilação útil é mantido; saídas QA opcionais podem ser regeneradas. Doctor verifica toolchain, pip/npm, Git, SQLite, serviços e permissões sem reinstalar tudo.

## Restauração

1. Preservar a instalação atual e confirmar ausência de gravações antes de substituir qualquer banco. Não fechar processos à força.
2. Selecionar o caminho de latest.json ou um ponto anterior e executar verificar. Não usar .pending ou arquivo sem verificação bem-sucedida.
3. Extrair source.zip para diretório novo e revisar arquivos/manifest. Instalar pelos locks; não copiar venv/node_modules entre sistemas. Extrair não remove arquivos extras nem restaura configuração privada excluída.
4. Restaurar data.sqlite3 via sqlite3.Connection.backup para **arquivo de destino novo**, validar integridade/FK e contagens. Não sobrescrever o banco ativo/única cópia. Fechar explicitamente todas as conexões, inclusive Windows.
5. Apontar DATABASE_URL absoluto ao restaurado, conferir Alembic current/heads; nunca downgrade/reset para eliminar diferenças. Conferir biblioteca/lixeira/histórico antes de continuar.
6. repository.bundle recupera commits/refs com clone isolado; source.zip cobre o disco no instante da captura. Git não contém banco e bundle não contém buffers ou .env. Verificação de hashes não prova ausência de segredos/normas corretas.

Fonte/PDFs locais enviados em references não integram ZIP; preservar os originais no projeto. Recursos já existentes external_backup.py/GPG e Windows QA ficam disponíveis, mas publicação, impressão física e cópia externa foram retiradas do trabalho atual pelo usuário. Mesmo disco não protege contra perda física; não há agendamento automático fora das sessões.


### Biblioteca técnica0.15.0

O banco0006 contém documentos,páginas e fontes; as contagens knowledge_* aparecem no relatório. O ZIP de fonte inclui inventory.json/import-result.json/verification.json como auditoria,mas exclui references/library/objects,mesmo com nomes sem extensão. Git ignora toda a library. Objetos originais são necessários para servir PDFs/SVG/modelos e não devem ser apagados como cache. As pastas de entrada elétrica/normas foram excluídas por pedido específico após transferência e verificação; essa autorização não se estende à library. Não repetir collect sem novas entradas. Verificar o acervo com knowledge_admin.py verify,além da restauração SQLite/Git do checkpoint.


## Manutenção do acervo — 0.16.0

Schema0007 acrescenta método, confiança e nota de extração. O checkpoint inclui também maintenance.json, além dos três registros anteriores. O inventário original permanece histórico; o verificador considera somente descartes justificados registrados e confere os hashes do texto OCR. Estado atual:2.196objetos retidos,2.082documentos,51.324unidades. Os objetos continuam necessários fora do ZIP; esta manutenção não autoriza apagar a biblioteca. Não reimportar o inventário anterior sobre o banco mantido.
