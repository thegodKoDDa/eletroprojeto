# Pendências conhecidas

Escopo local definido pelo usuário em 23/10/2026: publicação remota/CI hospedado, impressão física e backup externo foram descartados do trabalho atual. Recursos já implementados foram preservados. Checkpoints locais continuam em uso.

Atualizado em 23/10/2026. Bugs corrigidos constam em CHANGELOG/revisões, não como pendências aqui.

| ID / gravidade | Local e reprodução | Esperado / estado / causa conhecida |
| --- | --- | --- |
| NORM-01 / alta | Ampliação normativa | NDU7.0 d1–d5 integrada ao cadastro/PDF/JSON com classificação e revisão explícitas em0.13.0. d6/d7/centrais presentes e dimensionamento/geometria integrais ainda pendentes;0.16.0inclui estudo limitado de circuitos e referência de entradaESS; sem inventário revisado o resultado permanece nulo. Não transferir regras a outras distribuidoras. |
| ENV-01 / alta para verificação | Iniciar API/Next ou Playwright neste sandbox | Sandbox bloqueia sockets com EPERM. Na retomada de 22/10, serviços iniciados fora dele e HTTP confirmado nas portas 8000/3000. E2E aprovados fora do sandbox; 0.6.0 isola testes em 3010/8010. |
| BUILD-01 / média | `npm run build:webpack` | Build webpack aprovado fora do sandbox na retomada de 22/10; sandbox reproduz falha ao analisar `tsc --showConfig`. Importação de version corrigida em 0.6.0; build fora do sandbox aprovado sem esse aviso. |
| REF-01 / limite de consulta | Biblioteca técnica0.15.0 |OCRconcluído sobre1.060páginas relevantes:963recuperadas e97vazias identificadas;199documentos sem utilidade descartados com auditoria. TextoOCRnão revisado,não habilita regra. Revisão humana integral do acervo e dimensionamento/geometria universais continuam pendentes. |
| GEO-01 / média | Município/distribuidora | Associação territorial oficial incompleta; seleção manual/candidatas por UF. Não presumir cobertura nacional ou regras regionais completas. |

Backend e frontend foram executados em Windows real; PostgreSQL e catálogo persistente também foram validados. Os testes de continuidade no Windows tiveram duas limitações explícitas: GPG ausente e privilégio de symlink indisponível. Leitor de tela real ainda não conferido; axe automático não o substitui. Impressão física retirada do escopo pelo usuário.

Resolvidas em0.11.0: DATA-01 (rascunhos recuperáveis por conta/aba, erros de armazenamento explícitos) e fluxo guiado de conflitos409; CONT-01 (Git init autorizado, status/commit utilizáveis; baseline local revisado `d5d8212`, sem push). Limites da recuperação: dados gravados neste perfil de navegador, não após limpar o armazenamento ou em outro computador. Banco/checkpoint não capturam rascunhos do navegador.

VSP-40-W: divergência do catálogo antigo (60 W) corrigida para 140 W conforme página Mondial em 22/10. Não é pendência de implementação; instâncias antigas preservam os valores adotados e requerem conferência da placa/revalidação explícita. Não alterar potência manual apenas por divergir da sugestão.
