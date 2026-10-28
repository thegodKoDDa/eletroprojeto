# Pendências conhecidas

Atualização de escopo em 28/10/2026: Pages foi autorizado e publicado em 27/10; restrições históricas abaixo à publicação não descrevem mais esse modo. CI geral, impressão física e cópia externa continuam fora do escopo. Estado operacional em [CURRENT_STATE](CURRENT_STATE.md).

Escopo local definido pelo usuário em 23/10/2026: publicação remota/CI hospedado, impressão física e backup externo foram descartados do trabalho atual. Recursos já implementados foram preservados. Checkpoints locais continuam em uso.

Revisado integralmente em 26/10/2026, versão0.21.0. Pendências já resolvidas ou descartadas não foram reabertas. Bugs corrigidos constam em CHANGELOG/revisões, não como pendências aqui.

| ID / gravidade | Local e reprodução | Esperado / estado / causa conhecida |
| --- | --- | --- |
| NORM-01 / ampliação parcial | Circuitos e entrada além do modelo revisado | 0.21.0 cobre Cu/PVC70 ou XLPE/EPR90, A1/A2/B1/B2/C/D/E/F/G sob condições explícitas, mono ou tri equilibrado sem neutro,1,5–95mm². D exige referência de solo/profundidade e circuito único; G exige circuito único e arranjo espaçado. Neutro carregado, desequilíbrio, harmônicas, paralelos, outros solos/profundidades/agrupamentos e entrada integral continuam sem modelo validado. Alumínio residencial não foi liberado: §6.2.3.8 não autoriza uso indiscriminado nesse produto. |
| NORM-02 / evidência externa | Demanda d7 e outras distribuidoras | d6/d7/centrais já entregues; somente ordenação W/VA conflitante em d7 exige esclarecimento oficial. Pesquisa não encontrou instrução inequívoca; sem contato enviado à concessionária. Outros métodos de demanda/entrada exigem seus documentos/edições e revisão próprios, sem herdar NDU Energisa. |
| PROT-01 / ampliação parcial | DPS e seletividade integrais | 0.21.0 compara limite de seletividade documentado para o par exato e quatro requisitos documentais de DPS. Não seleciona classe/necessidade, não calcula risco atmosférico ou coordenação integral, não presume valores/curvas. Catálogo ABNT já lista NBR5419 partes1–4:2026/VC2026; conteúdo integral/condições aplicáveis ainda não revisados. Sobrecarga, terra, DR em série, todas as fontes e cascatas precisam de estudos próprios. |
| GEO-01 / relação municipal implementada; vigência ainda externa | INDGER/IBGE e polígonos ANEEL | 5.571 municípios relacionados a declarações mensais por CNPJ, com último mês de cada empresa; coexistência/atrasos/histórico preservados. 15 registros sem município e código1403205 não associado ao IBGE são segregados. Isso não certifica exclusividade, topologia de todas as feições, vigência jurídica atual ou atendimento do endereço. Consulta por coordenadas continua disponível; sem seleção automática. |
| GEO-02 / modelagem parcial e evidência presencial | Localização física | O arranjo restrito de chuveiro/figura18 já funciona. Banheiras, divisórias/cabines, percursos, mobiliário e acessibilidade integral não têm modelo validado. Inspeção e ensaios da instalação real não podem ser realizados pelo agente; exigem levantamento e responsável no local. Não confundir dados declarados com inspeção concluída. |
| REF-01 / revisão humana externa | Acervo técnico importado | OCR/importação e revisão específica de regras já executados. Não houve revisão humana integral dos2.082documentos; os estados preliminares permanecem. O agente não pode assinar ou simular essa revisão. |
| PERF-01 / avaliação sob demanda | Grandes acervos e revalidação | Busca literal e revalidação explícita funcionam. Desempenho sob carga e impacto seletivo de cada nova regra ainda não medidos/modelados; não há falha de desempenho reproduzida que justifique trocar o índice nesta revisão. |

Backend e frontend foram executados em Windows real; PostgreSQL e catálogo persistente também foram validados. O teste histórico no Windows registrou ausência de GPG e privilégio de symlink. O exportador GPG foi retirado nesta organização; symlink/ACL/compactação Windows não foram revalidados nesta revisão. Validação com leitor de tela real retirada do escopo por solicitação explícita do usuário em25/10/2026; não é pendência. Melhorias de acessibilidade e verificações automáticas/teclado permanecem. Impressão física também está fora do escopo.

Resolvidas em0.11.0: DATA-01 (rascunhos recuperáveis por conta/aba, erros de armazenamento explícitos) e fluxo guiado de conflitos409; CONT-01 (Git init autorizado, status/commit utilizáveis; baseline local revisado `d5d8212`, sem push). Limites da recuperação: dados gravados neste perfil de navegador, não após limpar o armazenamento ou em outro computador. Banco/checkpoint não capturam rascunhos do navegador.

VSP-40-W: divergência do catálogo antigo (60 W) corrigida para 140 W conforme página Mondial em 22/10. Não é pendência de implementação; instâncias antigas preservam os valores adotados e requerem conferência da placa/revalidação explícita. Não alterar potência manual apenas por divergir da sugestão.

ENV-01/BUILD-01 eram restrições históricas do sandbox: nesta revisão0.17.0,serviçosHTTP,E2E/HTTPS ebuildwebpack executaram com sucesso no ambiente disponível. Não representam falha atual do produto;conferir novamente se o ambiente mudar. Busca textual da biblioteca segue literal e sem índice especializado;capacidade sob carga não foi medida.

## Compatibilidade da distribuição 0.20.0

Iniciadores Windows e macOS preparados, mas sem execução nesses sistemas. Docker validado somente em Linux amd64; ARM não validado. ZIP contém código-fonte e exige Python/Node/npm, com internet na preparação inicial. Repositório público não fornece aplicação hospedada nem acervo técnico original.
