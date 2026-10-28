# Continuidade e manutenção

## Uso diário

O usuário continua pedindo **RETOMAR ELETROPROJETO** ou **ENCERRAR SESSÃO DO ELETROPROJETO**. O agente executa as rotinas de terminal; não é necessário repetir permissões para testes, serviços, manutenção de gerados e sincronização normal com o GitHub público já autorizado.

| Operação | Comando na raiz | Resultado |
| --- | --- | --- |
| Retomar | `python3 scripts/continuity.py retomar` | Git, integridade/contagens SQLite, instalações presentes, fetch do origin, HTTP e último checkpoint. |
| Encerrar | `python3 scripts/continuity.py encerrar --sync` | Sincroniza commits revisados e cria/revalida checkpoint local. |
| Verificar recuperação | `python3 scripts/continuity.py verificar` | Restaura o último checkpoint em diretório temporário e confere fonte, SQLite e Git. |

Antes de encerrar, o agente atualiza estado/histórico, executa verificações proporcionais, revisa segredos e cria um único commit se houver mudanças. O script não adiciona arquivos nem faz commit automaticamente. Não há reinstalação, limpeza completa ou bateria inteira de testes em toda sessão. Confirmação final usa o resultado real e `.checkpoints/latest.json`, sem commit adicional para copiar o caminho.

Retomar consulta o remoto, mas não faz merge/reset/pull automático. Se houver commits remotos, revisar diferenças e atualizar a cópia de trabalho sem perder edições antes de prosseguir. `retomar --offline` funciona sem GitHub. Se a sincronização falhar ao encerrar, o checkpoint local ainda é produzido e o comando retorna falha de sincronização; resolver/repetir quando possível e relatar a pendência. `encerrar` sem `--sync` cria somente o ponto local.

## O que fica salvo

| Local | Conteúdo | Exclusões relevantes |
| --- | --- | --- |
| GitHub público e Git local | Código, docs, testes, contratos, locks, migrações e histórico de commits. | SQLite, credenciais, `.env` privado, checkpoints, dependências/builds e acervo técnico. |
| `.checkpoints/<identificador>` | `source.zip`, `data.sqlite3`, `manifest.json`, `VERIFIED.json` e `repository.bundle` quando há Git. | Buffers não salvos, rascunhos do navegador, dependências e binários do acervo. |
| `references/library` e `references/energisa` | Originais locais, auditoria e fontes técnicas. | Não são cache nem conteúdo para push. |

O ZIP também preserva os quatro JSONs de auditoria da biblioteca; SQLite inclui seus documentos/páginas/fontes. Os originais em `library/objects` são necessários para abrir o acervo e ficam fora do ZIP/Git. Não reimportar o inventário histórico nem limpar o acervo como cache. A lixeira e as versões dos projetos fazem parte do banco. Dados ainda não enviados pelo navegador não ficam no backup SQLite.

O checkpoint é publicado atomicamente apenas após hashes, extração segura da fonte, backup/restauração SQLite com integrity/FK e leitura de todas as linhas, além de clone isolado do bundle Git. Falha mantém o ponteiro anterior. Sem mudança de fonte/banco/Git, reutiliza o ponto após verificação completa. `encerrar --force-new` força outro identificador; `verificar --checkpoint CAMINHO` seleciona um ponto anterior.

Backups SQLite byte a byte idênticos compartilham armazenamento por hardlinks quando o volume suporta. Cada ponto mantém nome, manifest, hash e capacidade de restauração; não depende de outro nome de diretório e nenhum histórico é apagado. Novo backup captura pelo SQLite API antes de compartilhar, nunca se liga ao banco ativo. Não editar os arquivos dos checkpoints: restaurar sempre para um arquivo novo. Sem suporte a hardlinks, a cópia independente permanece válida.

## GitHub e permissões

O único destino de sincronização automática é `thegodKoDDa/eletroprojeto`, confirmado como público pela API antes do envio. Exige main, árvore limpa e commit revisado. Fetch e comparação recusam divergência/commits remotos; nunca há force-push ou reescrita de história. O hash remoto é conferido depois do envio. A confirmação pública usa a API sem credencial. O envio usa a credencial Git existente, sem copiar tokens para URL, arquivos ou logs. O workflow Pages foi habilitado por autorização explícita em 27/10/2026; quality.yml permanece desativado.

POSIX: diretórios privados0700, arquivos0600. Doctor verifica e `--fix-permissions` corrige somente privados conhecidos, sem symlinks ou mudanças globais. No Windows, chmod não audita ACL; os wrappers usam o Python já instalado (`.venv-windows`, depois `.venv`) e não mudam ExecutionPolicy. `retomar.ps1 -Offline` e `encerrar.ps1 -Sync` equivalem às opções Python.

## Manutenção sob demanda

```sh
python3 scripts/maintenance.py doctor
python3 scripts/maintenance.py clean
python3 scripts/maintenance.py clean --apply --qa-builds
python3 scripts/maintenance.py compact
python3 scripts/maintenance.py compact --apply
```

Doctor diagnostica dependências/permissões/serviços, sem reinstalar pacotes nem exibir segredos. Clean simula primeiro e só remove caches, relatórios QA e saídas nomeadas de QA quando suas portas estão livres; mantém Next ativo/cache útil, ambientes Python Linux/Windows e node_modules. Pastas administrativas conhecidas só são removidas se vazias. Não varrer instalações globais ou diretórios externos.

Compact simula e restaura todos os checkpoints antes de compartilhar backups idênticos; não exclui pontos históricos. Clean/compact aplicados registram auditoria privada em `.checkpoints`. Não é necessário rodar compact em todo encerramento: os novos checkpoints já compartilham cópias idênticas automaticamente. O exportador GPG opcional fora de uso foi retirado; versões anteriores continuam recuperáveis pelo Git. Não há implantação nem cópia externa automática de dados privados.

## Recuperar

1. Executar `verificar`, ou escolher explicitamente um checkpoint anterior. Não usar `.pending-*` como ponto concluído.
2. Recuperar código pelo GitHub/Git ou extrair source.zip para diretório novo; instalar pelos locks somente quando necessário.
3. Copiar `data.sqlite3` pela API SQLite para **arquivo de destino novo**, conferir integridade/FK/schema/contagens e selecionar esse caminho absoluto em DATABASE_URL. Não substituir o banco ativo ou apagar migrações para ajustar versões.
4. Preservar/restaurar também os originais do acervo e a configuração privada pelos seus meios locais. Abrir biblioteca/projetos/lixeira e conferir o funcionamento.

GitHub protege a fonte fora deste computador; SQLite e originais continuam locais. Checkpoint no mesmo disco não protege esses dados contra perda física. Isso é um limite conhecido, não uma tarefa externa pendente imposta ao usuário. DATABASE_URL simples e absoluto SQLite é respeitado; PostgreSQL requer ferramenta de backup própria. Não fechar processos à força nem interromper gravações para recuperar.

## Instalações distribuídas

O ZIP não contém dados do desenvolvedor. Nativamente, uma instalação nova usa `data/eletroprojeto.db`; um banco legado em `backend/eletroprojeto.db` continua sendo usado. `--data-dir` seleciona explicitamente outra instalação. Docker usa seu volume `projects`, separado do banco nativo.

Atualize o código mantendo a pasta/banco de dados ou volume. `docker compose down` preserva o volume; sua remoção não faz parte da atualização. Antes de transferir dados, pare a instância correspondente e faça cópia consistente. Migrações necessárias pelo iniciador geram cópia anterior em `backups/`, sem apagar versões existentes. Essa cópia não substitui armazenamento externo.

A publicação do repositório e da release de fontes foi autorizada em 26/10/2026. Ela não publica o site, não habilita CI e não envia bancos, credenciais, acervo ou checkpoints. Os mecanismos internos de checkpoint continuam disponíveis para manutenção; o uso normal do iniciador não sincroniza projetos com o GitHub.

## Retenção e limites de preservação

Preservar pontos históricos, sem expurgo automático nem sobrescrita. Revisar crescimento após 14 pontos; reutilizar snapshots sem mudanças e compartilhar bancos idênticos por hardlink verificado. Exclusão de pontos únicos exige autorização específica. Isso reduz duplicação, mas não impõe teto ao crescimento histórico. Monitorar espaço em cada encerramento.

Os scripts não salvam buffers de editores nem capturam rascunhos de navegador. O modo Pages armazena projetos em localStorage, separado do SQLite local: suas duas chaves não constituem cópia externa nem são incluídas neste checkpoint. Originais do acervo e .env permanecem privados nos caminhos existentes; não fazem parte do source.zip. O sistema depende de execução na sessão, sem automação após desligamento.

A autorização posterior de 27/10/2026 permitiu a publicação Pages; as antigas exclusões de publicação nesta página descrevem a distribuição local e não revogam essa entrega. CI geral, impressão física e cópia externa continuam fora do escopo.
