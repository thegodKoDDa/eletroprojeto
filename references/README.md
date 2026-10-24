# Referências locais

## Biblioteca integrada — 0.15.0

As pastas de entrada `elétrica` e `normas` foram excluídas por solicitação expressa do usuário, somente após importação, testes e duas verificações integrais dos hashes. Os conteúdos únicos permanecem na biblioteca da aplicação; não são arquivos descartáveis.

- `library/objects/<sha256>`: 2.395 objetos únicos, 8.546.299.070 bytes. Mantém bytes originais de PDFs, guias, modelos, SVGs e registros auxiliares. Contêineres ZIP redundantes foram substituídos pela preservação de todos os seus membros; o inventário registra hashes dos ZIPs e de cada membro. Não extrair caminhos de ZIP diretamente em diretórios executáveis.
- `library/inventory.json`: 6.231 entradas de arquivo/membro, nomes de origem, tamanhos e hashes; nomes antigos são proveniência, não caminhos ativos.
- `library/import-result.json` e `verification.json`: conclusão da ingestão e exclusão verificada.
- SQLite da API: documentos, texto normalizado por página e fontes, em tabelas próprias da migração0006. Não altera projetos, histórico, catálogo ou regras validadas.

Biblioteca técnica na navegação do programa: 2.281 documentos (2.244 PDFs,27 guias,6 modelos/checklists,4 diagramas),83.424 páginas PDF e37 unidades textuais/didáticas, total83.461.80.995 unidades têm texto extraído;2.466 páginas não têm texto extraível e precisam de consulta visual ao original. Não houve OCR nem revisão técnica humana integral de83mil páginas.

API: `/api/v1/knowledge/stats`, `/documents`, `/documents/{id}`, `/documents/{id}/pages`, `/documents/{id}/file` e `/sources`, sob a mesma autenticação da aplicação. Busca literal por conteúdo/metadados, sem distinção de acentos; filtros/paginação, leitura e originais. URLs são referências, não baixadas automaticamente. UF/grupo catalogados não comprovam cobertura municipal.

### Administração e recuperação

Executar a partir da raiz, com Python do backend:

```sh
backend/.venv/bin/python backend/knowledge_admin.py collect
backend/.venv/bin/python backend/knowledge_admin.py import
backend/.venv/bin/python backend/knowledge_admin.py verify
```

`collect` exige as duas pastas de entrada; não é necessário repeti-lo para usar a biblioteca já integrada. `import` é idempotente para o inventário atual. `verify --remove-inputs` foi a operação autorizada de exclusão; recusa importação incompleta, objeto divergente, banco divergente e entrada nova/alterada. Não usar para limpar outros diretórios. A dependência opcional `ingest` é PyMuPDF1.28.2 no lock; a API de consulta não importa o extrator.

Objetos/inventários locais ficam fora do Git. O checkpoint inclui o SQLite e os três inventários de auditoria; exclui `library/objects` do ZIP de código. Para recuperar os arquivos originais é necessário preservar também essa pasta de objetos. O motor de cálculo não lê PDFs; somente o leitor dos originais depende desses objetos. Não apagar `library` como cache.

## Exemplar de trabalho Energisa preservado

| Arquivo | Uso |
| --- | --- |
| `energisa/ndu-001-v7.0.pdf` | NDU-0017.0/novembro2024,162páginas; escopo/revisões explícitas já implementados. |
| `energisa/historico/ndu-001-v6.3.pdf` |189páginas; consulta histórica. |

Esses exemplares anteriores foram preservados. A biblioteca não modifica a validação limitada do motor; fontes e condições em [normas](../docs/standards.md).
