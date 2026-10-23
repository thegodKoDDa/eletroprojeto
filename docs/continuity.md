# Continuidade, checkpoint e recuperação

## Uso permanente

Ao pedir **ENCERRAR SESSÃO DO ELETROPROJETO**, o agente segue AGENTS, atualiza estado/histórico, testa o necessário, revisa segredos e executa o checkpoint. Ao pedir **RETOMAR ELETROPROJETO**, lê a documentação e confere o estado real antes de continuar. Isso funciona pela leitura local, não por memória garantida da conversa nem por processo em segundo plano.

Linux/macOS, a partir da raiz (Python 3.11+ padrão ou backend/.venv/bin/python):

```bash
python3 scripts/continuity.py encerrar
python3 scripts/continuity.py retomar
python3 scripts/continuity.py verificar --checkpoint .checkpoints/IDENTIFICADOR
```

Windows/PowerShell:

```powershell
./scripts/encerrar.ps1
./scripts/retomar.ps1
```

Wrappers procuram backend/.venv/Scripts/python.exe, depois python no PATH. Não alterar ExecutionPolicy global para executá-los. Python não depende de pacotes externos para continuidade; ambiente Windows/PowerShell não está disponível para teste nesta sessão. Instalação/execução da aplicação em README; `types:sync` atual usa sintaxe POSIX e precisará adaptação no Windows nativo ou WSL. Scripts não instalam pacotes, migram banco, abrem portas, encerram processos, fazem commits ou push.

## Conteúdo e limites

`.checkpoints/<UTC-com-microssegundos>/` contém source.zip, data.sqlite3, manifest.json (hashes SHA-256, estado Git e contagens sem dados pessoais) e VERIFIED.json. Só considerar íntegro após saída verificada. Diretório 0700 e arquivos 0600 em POSIX; no Windows usar conta/diretório protegidos por ACL. Sem criptografia embutida.

ZIP captura arquivos regulares do projeto, incluindo código, referências, fontes licenciadas, lockfiles, migrações, testes e documentos. Exclui .git, dependências, builds/cache/logs, symlinks, .checkpoints, .env privados, bancos, chaves e credenciais por nome. Essa exclusão não detecta todos os segredos possíveis: o agente deve revisar conteúdo antes de versionar/compartilhar. Bancos contêm projetos e devem ficar privados. `.env.example` é incluído; configurações privadas devem ter recuperação segura separada, nunca publicadas. Arquivos em buffers do editor e rascunhos ainda no navegador não são capturados. Salvar no editor e aguardar Salvo na aplicação antes de fechar.

SQLite é aberto mode=ro; Connection.backup cria snapshot consistente, incluindo transações confirmadas em WAL. Verifica integrity_check e foreign_key_check; restaura em arquivo temporário isolado e lê dump completo. Não toca no banco original. Usa DATABASE_URL absoluto SQLite, se definido no ambiente, ou backend/eletroprojeto.db; URL relativa/outro banco é recusada. Variáveis configuradas apenas num processo servidor externo não são detectáveis: conferir seu DATABASE_URL antes do encerramento. O script não carrega .env automaticamente.

Fonte não é snapshot atômico do filesystem: evitar editar durante a captura; script confere hashes novamente e falha se detectar alteração. Banco representa um instante transacional, não inclui edições futuras. Arquivos/código e banco são preservados separadamente, sem promessa de transação entre eles.

## Retenção

Manter os 14 checkpoints verificados mais recentes e pelo menos um por semana durante oito semanas. O script sinaliza revisão quando há mais de 14, mas não apaga automaticamente. Antes de remover cópias antigas, verificar as mantidas e copiar para disco/local externo protegido. Revisar mensalmente espaço e retenção com o agente. Não há agendamento automático nem cópia externa configurada. Mesmo disco não é proteção contra roubo/falha física; desligamento não apaga cópia local, mas não garante durabilidade externa.

## Recuperação segura

1. Não substituir arquivos em uso. Confirmar ausência de gravações e preservar a versão atual primeiro; não fechar processos à força.
2. Executar verificar no checkpoint escolhido. ZIP inclui paths relativos sem .git; não apaga arquivos novos da instalação atual.
3. Extrair source.zip para diretório novo, revisar manifest/hashes e arquivos, nunca por cima da única cópia. Instalar dependências dos locks conforme README. Não copiar node_modules ou venv entre máquinas.
4. Restaurar data.sqlite3 com a API SQLite `backup` para um **arquivo de destino novo**, conferindo integrity_check e foreign_key_check. Exemplo (trocar caminhos, não usar o banco ativo como destino):

```python
import sqlite3
from pathlib import Path
source = Path('.checkpoints/IDENTIFICADOR/data.sqlite3').resolve()
target = Path('/caminho/novo/recuperado.db')
if target.exists():
    raise ValueError('Não sobrescrever destino existente')
with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as old:
    with sqlite3.connect(target) as restored:
        old.backup(restored)
        assert restored.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        assert restored.execute('PRAGMA foreign_key_check').fetchall() == []
```

5. Apontar DATABASE_URL para o arquivo restaurado (caminho absoluto); conferir Alembic current/heads antes de qualquer upgrade. Nunca downgrade/reset para resolver diferenças.
6. Conferir projetos ativos, lixeira e histórico; iniciar serviços apenas após conferência. Restauração isolada dos backups é testada a cada checkpoint, sem alterar produção.

## Git

Quando disponível, revisar status/diff/novos arquivos e exclusões de segredos antes de criar commit local seletivo. Nenhum `git add .` indiscriminado. Snapshot não inventa branch/commit e não cria repositório dentro de .git bloqueada. Nesta instalação não há histórico Git recuperável: a relação completa preservada está no manifest do checkpoint. Git não contém o banco; backup não substitui versionamento. Sem push remoto autorizado.

Na revisão 0.7.0, novos arquivos de fonte dos checkpoints passaram a excluir também `.ruff_cache` e diretórios terminados em `.egg-info`/`.dist-info`, metadados gerados ao instalar pacotes. A fonte canônica de dependências permanece em pyproject/package/lock, não nesses artefatos. Checkpoints anteriores não foram alterados ou apagados. Teste de exclusão cobre essas entradas.
# Atualização de portabilidade e cópia protegida — 0.11.0

As conexões SQLite das rotinas de checkpoint/restauração e do backup administrativo são fechadas explicitamente com contextlib.closing. O gerenciador de contexto da conexão SQLite sozinho gerencia transação, mas não fecha o arquivo: o Windows revelou bloqueio de exclusão do arquivo restaurado. Corrigido e verificado em Linux e Windows; nunca ocultar a falha ignorando erros de limpeza/restauração.

Fonte de checkpoint exclui também `.venv-windows` e arquivos criptografados/arquivos de backup, além das exclusões anteriores. O banco continua preservado separadamente; contas e hashes/sessões também fazem parte dos dados privados e devem ser protegidos. Git inicializado em23/10 por solicitação explícita; primeiro commit revisado não substitui os checkpoints nem uma cópia fora do computador.

`scripts/external_backup.py` recebe checkpoint verificado, diretório externo escolhido e fingerprint completo de chave pública GPG já importada. Criptografa código/banco/manifest/VERIFIED, recusa sobrescrever e compara hash do arquivo transferido. A recuperação real exige decriptação com a chave do responsável e nova verificação de arquivo/hashes/restauração; o comando não marca essa etapa como concluída. Teste QA com chave temporária efetuou o ciclo completo. A cópia real depende de destino/chave e não foi feita nesta revisão.

`scripts/windows_qa.ps1` prepara cópia nativa temporária a partir do ZIP de fonte verificado, baixa Node oficial com SHA256 comparado e executa contratos/tipos/frontend/Chromium/build. Python Windows separado deve existir; ELETROPROJETO_PYTHON aponta para ele. Nenhum npm ci Windows é executado sobre node_modules Linux. Artefatos ficam em diretório temporário identificado, sem exclusão de projetos ou checkpoints. Validação física e leitor de tela real continuam distintos desses testes.
Histórico Git agora também é preservado quando há commit: `repository.bundle`, hash SHA256 e clonagem bare isolada com comparação de HEAD durante a verificação. O pacote criptografado inclui o bundle quando presente. Testes rejeitam corrupção e comprovam restauração do histórico; Git é necessário para verificar essa parte. A fonte continua capturando arquivos do disco, inclusive alterações não commitadas; o bundle preserva apenas commits/refs existentes, não os buffers de editor ou segredos de configuração de `.git`.


Decisão de escopo em23/10/2026: usuário manterá operação local e retirou publicação remota/CI hospedado, impressão física e backup externo do trabalho atual. Não solicitar destino/chave nem bloquear entregas por esses itens. Mecanismos existentes permanecem preservados; checkpoints locais continuam verificados. Limitações físicas de armazenamento local permanecem verdadeiras, sem constituir tarefa ativa de cópia externa.
