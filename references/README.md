# Referências locais

## Biblioteca integrada — 0.16.0

As pastas de entrada `elétrica` e `normas` foram excluídas por solicitação expressa do usuário, somente após importação, testes e duas verificações integrais dos hashes. Os conteúdos únicos permanecem na biblioteca da aplicação; não são arquivos descartáveis.

- `library/objects/<sha256>`:2.196objetos técnicos únicos,3.597.033.481bytes,fora do Git/ZIP. Os199objetos descartados (2livros/197relatórios,4.949.265.589bytes) têm motivo/hash em maintenance.json e fontes. Os outros binários não são cache.
- `library/inventory.json`:inventário histórico imutável de6.231entradas/2.395objetos,tamanhos/hashes originais. ZIPs redundantes foram substituídos por preservação dos membros. Entradas de origem antigas não são caminhos ativos.
- `library/maintenance.json`:descarte e resultados/hash deOCR. `import-result.json` é o registro histórico original; `verification.json` é a conferência corrente.
- SQLite0007:2.082documentos (2.045PDFs/27guias/6modelos/4diagramas),51.324unidades (51.287páginasPDF+37didáticas),3.788fontes.51.227com texto,97vazias identificadas. OCRrecuperou963páginas;78vazias detectadas e19vazias com ruído conferidas visualmente. Nenhuma falha de OCR ou página nativa sem texto por processar. Texto OCR é não revisado,com confiança;conferir números/símbolos no original.

Menu Biblioteca técnica e `/api/v1/knowledge/{stats,documents,sources}`:busca literal normalizada,filtros/paginação,páginas,originais,diagramas e auditoria de fontes. Importação/OCR não habilita regras automaticamente. UF/grupo não comprova concessão municipal. A revisão humana integral de todos os documentos não foi concluída; métodos específicos conferidos em [normas](../docs/standards.md).

Administração a partir da raiz:

```sh
backend/.venv/bin/python backend/knowledge_admin.py verify
```

O verificador considera manutenção autorizada,exige hashes dos objetos retidos e dos textosOCR,confere banco e recusa manutenção incompleta. `collect` exige novas pastas de entrada; `import` do inventário histórico é bloqueado depois da manutenção para não ressuscitar descartes/sobrescreverOCR. `knowledge_maintenance.py discard` exige justificativa específica;não elimina manuais técnicos por classificação genérica. `ocr --binary ... --data-root ... --workers 4` usa executável e idiomas explícitos. Nesta sessão:Tesseract5.5/idiomasapt extraídos somente em/tmp/eletroprojeto-ocr-tools;PyMuPDF1.28.2 opcional no venv. API de leitura não depende do executávelOCR.

Checkpoint inclui SQLite e4JSONs de auditoria;exclui `library/objects`. Preservar essa pasta para recuperar originais. Nenhum PDF original foi alterado peloOCR. As duas pastas de entrada solicitadas continuam ausentes; Energisa anterior preservada.

## Exemplar de trabalho Energisa preservado

| Arquivo | Uso |
| --- | --- |
| `energisa/ndu-001-v7.0.pdf` | NDU-0017.0/novembro2024,162páginas; escopo/revisões explícitas já implementados. |
| `energisa/historico/ndu-001-v6.3.pdf` |189páginas; consulta histórica. |

Esses exemplares anteriores foram preservados. A biblioteca não modifica a validação limitada do motor; fontes e condições em [normas](../docs/standards.md).

## Coleta territorial local — 26/10/2026

`territory/20261026T035935641118Z` preserva a primeira coleta integral bem-sucedida da camada oficial ANEELHosted/AREA_ATUACAO/5 (121feições), com atributos, geometrias, metadados, contagem, relatório e hashes. Caminho ignorado,0700/0600; originais não são gerados dispensáveis. Não apagar ou substituir como cache. `scripts/territory.py` cria diretório novo em cada coleta; nenhuma associação é liberada automaticamente. Condições/vigências/limites emdocs/standards, sem duplicar regras aqui.


## Relações municipais oficiais — 26/10/2026

`municipalities/20261026T174000622041Z` preserva metadados CKAN, CSV INDGER, identidades IBGE, índice e relatório/hash da coleta usada na0.21.0. Os diretórios anteriores de tentativa também ficam preservados. Código de coleta emscripts/municipalities.py; critérios/limites emdocs/standards. Ignorados no Git,0700/0600; não são cache dispensável nem acompanham a distribuição. O índice declara o mês de cada empresa e não constitui mapa jurídico ou confirmação de atendimento de um imóvel. Checkpoint local inclui esses arquivos pela rotina existente, separado da distribuição pública.
