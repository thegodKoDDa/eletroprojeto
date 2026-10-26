# Pendências conhecidas

Escopo local definido pelo usuário em 23/10/2026: publicação remota/CI hospedado, impressão física e backup externo foram descartados do trabalho atual. Recursos já implementados foram preservados. Checkpoints locais continuam em uso.

Atualizado em 26/10/2026. Bugs corrigidos constam em CHANGELOG/revisões, não como pendências aqui.

| ID / gravidade | Local e reprodução | Esperado / estado / causa conhecida |
| --- | --- | --- |
| NORM-01 / alta | Casos além dos modelos conferidos | 0.19.0 habilita d6/d7/centrais com parâmetros/fontes/revisão, circuitos Cu/PVC70 A1/A2/B1/B2/C mono e tri equilibrado sem neutro, e envelopes no arranjo restrito da figura18. Permanecem ambiguidade de ordenação W/VA emd7, outras distribuidoras, XLPE/outros métodos/neutro/desequilíbrio/harmônicas, proteções/entrada integrais e banheiras/divisórias/cabines. Sem dimensionamento/conformidade final universal. |
| REF-01 / limite de consulta | Biblioteca técnica0.15.0 |OCRconcluído sobre1.060páginas relevantes:963recuperadas e97vazias identificadas;199documentos sem utilidade descartados com auditoria. TextoOCRnão revisado,não habilita regra. Revisão humana integral do acervo e dimensionamento/geometria universais continuam pendentes. |
| GEO-01 / média | Vigência e associação municipal | Obtidas121feições oficiais da camadaHosted/AREA_ATUACAO/5, conferidas contagem/hash/referencial e implementada consulta local pontual. A base inclui registros encerrados/sucessores sobrepostos; sem certificar atualidade jurídica, município inteiro ou atendimento de imóvel. Seleção manual preservada, sem inventar sucessão ou mapeamento deIDs. Fonte/datas/limites emstandards; originais locais ignorados. |

Backend e frontend foram executados em Windows real; PostgreSQL e catálogo persistente também foram validados. O teste histórico no Windows registrou ausência de GPG e privilégio de symlink. O exportador GPG foi retirado nesta organização; symlink/ACL/compactação Windows não foram revalidados nesta revisão. Validação com leitor de tela real retirada do escopo por solicitação explícita do usuário em25/10/2026; não é pendência. Melhorias de acessibilidade e verificações automáticas/teclado permanecem. Impressão física também está fora do escopo.

Resolvidas em0.11.0: DATA-01 (rascunhos recuperáveis por conta/aba, erros de armazenamento explícitos) e fluxo guiado de conflitos409; CONT-01 (Git init autorizado, status/commit utilizáveis; baseline local revisado `d5d8212`, sem push). Limites da recuperação: dados gravados neste perfil de navegador, não após limpar o armazenamento ou em outro computador. Banco/checkpoint não capturam rascunhos do navegador.

VSP-40-W: divergência do catálogo antigo (60 W) corrigida para 140 W conforme página Mondial em 22/10. Não é pendência de implementação; instâncias antigas preservam os valores adotados e requerem conferência da placa/revalidação explícita. Não alterar potência manual apenas por divergir da sugestão.

ENV-01/BUILD-01 eram restrições históricas do sandbox: nesta revisão0.17.0,serviçosHTTP,E2E/HTTPS ebuildwebpack executaram com sucesso no ambiente disponível. Não representam falha atual do produto;conferir novamente se o ambiente mudar. Busca textual da biblioteca segue literal e sem índice especializado;capacidade sob carga não foi medida.
