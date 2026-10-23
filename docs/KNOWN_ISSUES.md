# Pendências conhecidas

Atualizado em 23/10/2026. Bugs corrigidos constam em CHANGELOG/revisões, não como pendências aqui.

| ID / gravidade | Local e reprodução | Esperado / estado / causa conhecida |
| --- | --- | --- |
| NORM-01 / alta | Demanda da distribuidora; ampliação normativa | Demanda segue null: íntegra NDU-001 v7.0/tabelas/notas ainda inacessíveis (403 inclusive novo caminho 2025-05). Iluminação/TUG residenciais quantitativas disponíveis em escopo limitado desde 0.9.0, fontes/condições em standards.md. Externo/outro, localização, circuitos e certificação não implementados. |
| ENV-01 / alta para verificação | Iniciar API/Next ou Playwright neste sandbox | Sandbox bloqueia sockets com EPERM. Na retomada de 22/10, serviços iniciados fora dele e HTTP confirmado nas portas 8000/3000. E2E aprovados fora do sandbox; 0.6.0 isola testes em 3010/8010. |
| BUILD-01 / média | `npm run build:webpack` | Build webpack aprovado fora do sandbox na retomada de 22/10; sandbox reproduz falha ao analisar `tsc --showConfig`. Importação de version corrigida em 0.6.0; build fora do sandbox aprovado sem esse aviso. |
| QA-01 / média | Qualidade contínua/CI | Workflow ampliado Ubuntu/Windows/PostgreSQL, lint/formatação/contratos/testes/E2E/build sequenciais. Verificações locais registradas em CURRENT_STATE; falta configurar remote e observar execução hospedada, sem push autorizado nesta tarefa. |
| SEC-01 / alta antes de publicar | Implantação remota | Autenticação/sessões HTTPS/CSRF e isolamento por proprietário implementados/testados em0.11.0. Ainda faltam implantação TLS/ingresso reais, quotas/monitoramento e revisão de operação; testes locais não constituem pentest. Modo local não deve ser exposto por proxy público. |
| GEO-01 / média | Município/distribuidora | Associação territorial oficial incompleta; seleção manual/candidatas por UF. Não presumir cobertura nacional ou regras regionais completas. |
| CONT-02 / alta | Perda de disco/computador | .checkpoints no mesmo disco não protege contra perda física. Cópia externa protegida ainda necessária; não realizada nesta sessão. |
| PDF-01 / média | Conferência documental | Extração/renderização independentes em MuPDF e inspeção visual realizadas nas entregas 0.10.0/0.10.1; impressão física e conferência em outros visualizadores ainda pendentes. |

Scripts PowerShell são wrappers opcionais; execução real em Windows/PowerShell depende de ambiente com Python 3.11+ e ainda precisa ser conferida lá. PostgreSQL, catálogo global persistido e detecção seletiva de impacto normativo continuam planejados, ver roadmap.

Atualização deste parágrafo histórico: PostgreSQL18.6 e backend Windows11/Python3.13 foram executados/testados; catálogo global persistido em0005. Continuidade Windows encontrou conexões SQLite não fechadas explicitamente; corrigidas com contextlib.closing, sete testes passaram com duas limitações explícitas (GPG ausente e privilégio de symlink indisponível). Frontend Windows em preparação. Impressão física/leitor de tela real permanecem pendentes; axe automático não os substitui.

Resolvidas em0.11.0: DATA-01 (rascunhos recuperáveis por conta/aba, erros de armazenamento explícitos) e fluxo guiado de conflitos409; CONT-01 (Git init autorizado, status/commit utilizáveis; baseline local revisado `d5d8212`, sem push). Limites da recuperação: dados gravados neste perfil de navegador, não após limpar o armazenamento ou em outro computador. Banco/checkpoint não capturam rascunhos do navegador.

VSP-40-W: divergência do catálogo antigo (60 W) corrigida para 140 W conforme página Mondial em 22/10. Não é pendência de implementação; instâncias antigas preservam os valores adotados e requerem conferência da placa/revalidação explícita. Não alterar potência manual apenas por divergir da sugestão.
