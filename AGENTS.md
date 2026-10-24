# Regras permanentes

- Stack: Next.js App Router, TypeScript, Tailwind; Python, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic e SQLite. Preservar portabilidade para PostgreSQL.
- Toda matemática elétrica fica em `backend/app/calculations`. Funções puras não importam FastAPI, Pydantic ou ORM.
- Frontend formata e valida formulários; não replica fórmulas.
- Não inventar coeficientes, potências nominais, mapeamentos de concessionárias ou regras normativas.
- Habilitar regras somente após conferir fonte oficial, edição, condições, cláusulas, limites e exemplos independentes. Registrar referência, testes e estado de validação.
- Regras não conferidas retornam `null` e estado pendente, nunca zero como substituto.
- Separar W de VA, estimativa de placa, iluminação nominal de previsão normativa e carga cadastrada de catálogo.
- Usar Decimal, unidades explícitas e evitar arredondamentos intermediários.
- Alterações de cálculos exigem testes de resultados e limites. Executar pytest, testes frontend e E2E quando dependências estiverem disponíveis; relatar o que não foi executado.
- Gerar contratos com `npm run types:sync`. Nunca editar `api.generated.ts` manualmente.
- Preservar migrações e histórico dos projetos. Não modificar catálogo ao editar instância.
- Não exibir resultado antigo para entradas novas. Preservar debounce e cancelamento de requisições.
- Priorizar Etapa 1. Não declarar conformidade ou dimensionamento final enquanto houver pendências normativas.

## Produto e execução

- Prioridade: leigos primeiro, profissionais depois; estimativa de consumo de moradia pronta ou planejada. Preservar início/sidebar e fluxo 01 Projeto → 02 Ambientes → 03 Conferência. Estudos técnicos permanecem opcionais e recolhidos.
- O agente executa as rotinas de terminal. Autorização permanente revisada em24/10/2026: testes proporcionais, contratos, migrações sem reset, serviços, limpeza de gerados permitidos, compactação de backups idênticos e sincronização normal de commits revisados com o repositório PRIVADO `thegodKoDDa/eletroprojeto`. Não pedir confirmação novamente para essas rotinas.
- A autorização não inclui apagar dados/referências/pontos únicos de recuperação, force-push, reescrever histórico, mudar destino/visibilidade, publicar o site ou alterar políticas globais de segurança. Restrições obrigatórias do ambiente permanecem válidas.
- Usar instalações e serviços existentes. Não reinstalar, atualizar versões ou repetir baterias aprovadas sem mudança relevante/falha. Atualizações usam manifests/locks e revisão; nunca `audit fix --force` ou reset do banco.
- Permissões privadas POSIX0700/0600; não alterar fontes/.git/ACL/política Windows indiscriminadamente. Não fechar programas à força ou desligar o computador.

## RETOMAR ELETROPROJETO

1. Ler AGENTS, `docs/CURRENT_STATE.md` e `docs/PROJECT_MEMORY.md`. Consultar roadmap/KNOWN_ISSUES e a cauda dos registros somente conforme o trabalho atual; versões e limitações históricas não são o estado atual.
2. Executar `python3 scripts/continuity.py retomar`: Git/banco/dependências, consulta do origin, serviços e último checkpoint. Fetch não mescla ou sobrescreve a edição. Sem rede, continuar localmente e informar a pendência; `--offline` evita a consulta.
3. Seguir o próximo passo registrado/pedido atual. Antes de iniciar serviços, conferir os existentes; entregar localhost somente após HTTP confirmado. Doctor apenas para diagnóstico quando necessário.

## Durante o trabalho

- Preservar produto, dados, funcionalidades corretas, migrações e história dos projetos. Editar instância não altera catálogo; valores manuais válidos prevalecem sobre sugestões.
- Atualizar o documento responsável e CURRENT_STATE após mudanças relevantes; SESSION_HISTORY é cumulativo, CHANGELOG registra entregas. Não duplicar arquitetura/cálculos/normas em novos arquivos.
- Registrar causa/correção de bugs, verificações efetivas e limites. Regras elétricas exigem fonte/edição/condições/testes/projetos afetados. Checkpoint antes de mudanças estruturais e em marcos relevantes.
- Código/docs ficam no GitHub; SQLite, `.env`, checkpoints e acervo técnico permanecem locais e ignorados. Nunca versionar banco, backup, token ou credencial. GitHub não contém projetos salvos nem originais do acervo.

## ENCERRAR SESSÃO DO ELETROPROJETO

1. Conferir disco/Git/arquivos novos e executar somente verificações proporcionais. Atualizar CURRENT_STATE com o que foi feito, limites e próximo passo; acrescentar SESSION_HISTORY e atualizar documentos responsáveis.
2. Quando houver gerados dispensáveis, `python3 scripts/maintenance.py clean` simula; `--apply --qa-builds` remove somente a lista permitida e com portas QA livres. Não fazer limpeza/doctor completo em todo encerramento por hábito. Dependências úteis, dados, fontes e pontos únicos ficam preservados.
3. Revisar nomes/conteúdo/segredos e criar um único commit revisado de código/docs, se houver alterações. Não adicionar arquivos privados ou incluir alterações alheias sem revisão.
4. Executar `python3 scripts/continuity.py encerrar --sync`. Confirma destino privado, envia apenas commits na main sem divergência remota e confere o hash. Em seguida cria/revalida checkpoint local com restauração SQLite/Git isolada. Falha de rede ainda preserva checkpoint local e retorna pendência; não anunciar sincronização concluída se falhou.
5. Conferir resultado/status e relatar brevemente alterações, preservações/exclusões, verificações e pendências. `.checkpoints/latest.json` é a referência do ponto final; não criar commit extra só para copiar seu caminho. Buffers externos e rascunhos não enviados do navegador não são verificáveis pelo checkpoint.

Detalhes de manutenção e recuperação em `docs/continuity.md`. `verificar` restaura o último checkpoint isoladamente; marker/hash do manifest não substitui essa verificação. Checkpoints antigos são preservados e bancos idênticos compartilham armazenamento por hardlink quando suportado, sem apagar versões. Publicação do site, CI hospedado, impressão física e cópia externa de dados seguem fora do escopo. Os scripts só executam durante a sessão; não há trabalho em segundo plano prometido.
