# Estado atual — EletroProjeto 0.17.0 / motor 0.9.1

Atualizado em24/10/2026. JSON de relatório1.4; SQLite/schema0007. Registros anteriores permanecem em SESSION_HISTORY, CHANGELOG e Git; este arquivo descreve apenas o estado vigente.

## Produto

Estimativa de consumo residencial para leigos primeiro, profissionais depois. Fluxo **01 Projeto → 02 Ambientes → 03 Conferência**, início com três cartões/sidebar preservados. Consumo/custo em destaque, tarifa visível, ação para completar horários e consumo por aparelho. Medidas/pontos, potência/memória/VA/corrente/previsões são secundários; demanda/circuitos/entrada ficam em Estudos técnicos recolhidos.

Projetos, autosave após primeiro salvamento, rascunhos/conflitos, biblioteca/lixeira, catálogo referenciado e PDF/JSON preservados. Regras/fontes/escopos em standards/calculations; não há dimensionamento final universal. Nenhuma alteração de cálculo, formulário, API, dependência ou migração nesta manutenção.

## Rotina simplificada e GitHub

- **Retomar:** ler AGENTS/este estado/PROJECT_MEMORY e executar `python3 scripts/continuity.py retomar`. Consulta GitHub, confere Git/banco/instalações/HTTP e último checkpoint; não mescla alterações. Outros documentos e cauda do histórico são lidos conforme o trabalho.
- **Encerrar:** atualizar documentos responsáveis/este estado/histórico, verificar proporcionalmente e fazer um único commit revisado; executar `python3 scripts/continuity.py encerrar --sync`. Sincroniza somente com o origin privado conhecido e cria/revalida checkpoint local. Sem rede, preserva checkpoint e informa pendência.
- **Recuperação:** `python3 scripts/continuity.py verificar` restaura o último ponto isoladamente. `.checkpoints/latest.json` é a referência; não criar outro commit pelo caminho do checkpoint.
- Autorização permanente para essas rotinas e manutenção segura está no AGENTS; sem perguntas repetidas, force-push, reset de dados ou alteração global de permissões. Doctor/limpeza/compactação são sob demanda, não baterias obrigatórias a cada sessão.

[GitHub privado](https://github.com/thegodKoDDa/eletroprojeto), origin/main; Actions desativado, workflow preservado. Fonte/histórico estão no GitHub; SQLite, configurações privadas, checkpoints e originais do acervo ficam locais. Credencial existente via Git Credential Manager do Windows; nenhum token persistido em URL/arquivo/log. Não há implantação ativa ou cópia externa automática dos dados privados.

## Organização e limpeza desta sessão

Conferidos árvore/arquivos versionados e locais, dependências, serviços, backups e referências. Organização backend/frontend/docs/references mantida por responsabilidade. README, memória, segurança e continuidade perderam instruções históricas repetidas/contraditórias; históricos continuam preservados. Exportador GPG opcional fora de uso e seu teste retirados, recuperáveis pelo Git. Wrappers Windows e ferramentas de QA úteis permanecem.

**39 checkpoints históricos restaurados antes da compactação**;24cópias SQLite passaram a compartilhar armazenamento por hardlink, mantendo15bancos distintos e todos os pontos/manifests/hashes. Recuperados1.354.702.848bytes sem apagar nenhum ponto. Novos checkpoints já compartilham bancos idênticos automaticamente; sem suporte, mantêm cópia independente. Nunca há hardlink com o banco ativo.

Limpeza simulada/aplicada retirou155.320.686bytes de caches/relatórios/saídas QA inativas e as pastas vazias `.agents`, `.aws`, `.codex`. Preservados fontes/migrações, dois backups antigos, `.venv`Linux192MiB, `.venv-windows`122MiB, node_modules551MiB, Next ativo/cache e todo o acervo. Auditorias privadas de compactação/limpeza em `.checkpoints`; cerca1,51GB recuperados no total.

## Dados e verificações

SQLite íntegro/FKok;12tabelas integralmente iguais ao checkpoint20261024T180851680616Z. **10projetos/33históricos/9revisões**,9ativos/1na lixeira. Vila Ipê permanece na versão3, com8ambientes/25cadastros/10circuitos; números/exportações da criação histórica eram da versão1.

Acervo preservado:2.196objetos/3.597.033.481bytes,2.082documentos/51.324unidades/3.788fontes.199descartes anteriores continuam auditados; OCR963páginas recuperadas/97vazias. Não reimportar o inventário histórico ou limpar originais como cache.

Verificações desta manutenção: **27 testes de scripts aprovados**, incluindo envio Git local, recusa de arquivos não revisados/destino público/divergência, comportamento offline com checkpoint, compartilhamento/fallback e bloqueio de compactação corrompida. Ruff de63arquivos Python e formatação aprovados; retomada online e39restaurações reais conferidas. Doctor inicial e final aprovaram instalações/permissões/HTTP. Verificador integral do acervo aprovou hashes dos2.196objetos,199descartes auditados,OCR e contagens do banco. Resultados finais de sincronização/checkpoint devem ser confirmados pela execução e latest.json, sem presumir sucesso futuro.

Suítes da aplicação permanecem como evidência da entrega anterior:394backend+85subtestes,103frontend,20E2E e1HTTPS,contratos/tipos/lint/formatação/build aprovados. Não repetidas nesta manutenção de scripts/documentação sem mudança funcional; sem reinstalação. Windows/ACL/hardlink em Windows e leitor de tela real não revalidados. Serviços8000/3000 preservados; confirmar HTTP ao entregar/retomar.

## Próximo passo

Continuar os ajustes de simplicidade/consumo conforme uso e retorno do usuário. Não reabrir etapas técnicas no percurso principal ou ampliar regras sem fontes/condições/exemplos/testes. Pendências técnicas vigentes em KNOWN_ISSUES/roadmap. Publicação do site, CI hospedado, impressão física e cópia externa dos dados privados permanecem fora do escopo; não cobrá-los como bloqueios.
