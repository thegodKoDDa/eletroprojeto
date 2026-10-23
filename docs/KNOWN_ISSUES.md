# Pendências conhecidas

Atualizado em 23/10/2026. Bugs corrigidos constam em CHANGELOG/revisões, não como pendências aqui.

| ID / gravidade | Local e reprodução | Esperado / estado / causa conhecida |
| --- | --- | --- |
| NORM-01 / alta | Demanda da distribuidora; ampliação normativa | NDU7.0 enviada pelo usuário permitiu método parametrizado d1–d5 em0.12.0. Demanda automática do cadastro segue null sem classificação revisada; d6/d7/centrais presentes e dimensionamento final não implementados. Servidor oficial segue403, mas exemplar local/hash/condições estão registrados em standards.md. Não transferir fatores a outras distribuidoras ou presumir W a partir da previsãoVA. |
| ENV-01 / alta para verificação | Iniciar API/Next ou Playwright neste sandbox | Sandbox bloqueia sockets com EPERM. Na retomada de 22/10, serviços iniciados fora dele e HTTP confirmado nas portas 8000/3000. E2E aprovados fora do sandbox; 0.6.0 isola testes em 3010/8010. |
| BUILD-01 / média | `npm run build:webpack` | Build webpack aprovado fora do sandbox na retomada de 22/10; sandbox reproduz falha ao analisar `tsc --showConfig`. Importação de version corrigida em 0.6.0; build fora do sandbox aprovado sem esse aviso. |
| QA-01 / média | Qualidade contínua/CI | Workflow ampliado Ubuntu/Windows/PostgreSQL, lint/formatação/contratos/testes/E2E/build sequenciais. Verificações locais registradas em CURRENT_STATE; falta configurar remote e observar execução hospedada, sem push autorizado nesta tarefa. |
| SEC-01 / alta antes de publicar | Implantação remota | Autenticação/sessões HTTPS/CSRF e isolamento por proprietário implementados/testados em0.11.0. Ainda faltam implantação TLS/ingresso reais, quotas/monitoramento e revisão de operação; testes locais não constituem pentest. Modo local não deve ser exposto por proxy público. |
| GEO-01 / média | Município/distribuidora | Associação territorial oficial incompleta; seleção manual/candidatas por UF. Não presumir cobertura nacional ou regras regionais completas. |
| CONT-02 / alta | Perda de disco/computador | .checkpoints no mesmo disco não protege contra perda física. Cópia externa protegida ainda necessária; não realizada nesta sessão. |
| PDF-01 / média | Conferência documental | Extração/renderização independentes em MuPDF e inspeção visual realizadas nas entregas 0.10.0/0.10.1; impressão física e conferência em outros visualizadores ainda pendentes. |

Backend e frontend foram executados em Windows real; PostgreSQL e catálogo persistente também foram validados. Os testes de continuidade no Windows tiveram duas limitações explícitas: GPG ausente e privilégio de symlink indisponível. Impressão física e leitor de tela real permanecem pendentes; axe automático não os substitui.

Resolvidas em0.11.0: DATA-01 (rascunhos recuperáveis por conta/aba, erros de armazenamento explícitos) e fluxo guiado de conflitos409; CONT-01 (Git init autorizado, status/commit utilizáveis; baseline local revisado `d5d8212`, sem push). Limites da recuperação: dados gravados neste perfil de navegador, não após limpar o armazenamento ou em outro computador. Banco/checkpoint não capturam rascunhos do navegador.

VSP-40-W: divergência do catálogo antigo (60 W) corrigida para 140 W conforme página Mondial em 22/10. Não é pendência de implementação; instâncias antigas preservam os valores adotados e requerem conferência da placa/revalidação explícita. Não alterar potência manual apenas por divergir da sugestão.
