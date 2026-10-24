# Memória permanente — EletroProjeto

## Estado e escopo vigentes

Aplicação local de estudo/cálculo elétrico residencial, para leigos, estudantes e profissionais. Preservar produto, dados, funcionalidades e identidade visual; não recriar. API/frontend0.16.0, motor0.9.0, JSON de relatório1.4, banco/schema0007. Versões e testes atuais em CURRENT_STATE; roadmap/KNOWN_ISSUES descrevem o que realmente falta. Registros anteriores foram preservados em SESSION_HISTORY, CHANGELOG, Git e checkpoints; não tratar limitações históricas como atuais.

Usuário autorizou otimizar armazenamento, salvamento, continuidade, estrutura e limpeza, mantendo funcionalidade. Publicação/infraestrutura remota/CI hospedado, impressão física e backup externo foram retirados do escopo atual; não voltar a cobrá-los. Manter mecanismos existentes e checkpoints locais. Rotinas de terminal/testes/contratos/migrações/serviços são executadas pelo agente, sem delegar ao usuário. Restrições obrigatórias do ambiente continuam válidas; nunca push sem autorização.

Correção da0.14.1: usuário pediu restaurar APENAS a aparência antiga do início. Sidebar sempre presente, marca/logo no aside, cartões verticais maiores e rodapé abaixo do conteúdo. Não voltar a ocultar aside no início. Compactação das outras telas/equipamentos preservada.

## Invariantes de produto

- Um único motor Python em backend/app/calculations atende apresentações simples/técnica e relatórios. Frontend só valida/formata; Decimal e unidades explícitas, sem fatores inventados nem arredondamento intermediário.
- W/VA/kWh/BTU/h e potência mecânica são distintos; dados desconhecidos/regras não verificadas ficam null com motivo. Corrente por equipamento não dimensiona circuito. Não afirmar conformidade final ou aprovação da concessionária.
- Referências do catálogo são sugestões documentadas, não potências universais. Preservar valores manuais válidos e snapshots; editar instância nunca altera catálogo global. Fonte/cálculos/normas/arquitetura nos documentos responsáveis, sem duplicá-los.
- Dados reais em backend/eletroprojeto.db por padrão ou DATABASE_URL absoluto. Alembic0001–0007 e histórico preservados; não resetar banco ou regravar projetos antigos para atualizar regra/referência. PostgreSQL portátil e já validado em entregas anteriores.

## Fluxo funcional

Início, projeto em edição, biblioteca e lixeira são telas independentes. Criar/salvar/duplicar/renomear/restaurar mantêm IDs/versionamento e histórico. Autosave só após primeiro salvamento manual, debounce1,5s; renomeação/conflito pausam. Erro não é Salvo, falha não gera repetição infinita e edições feitas durante envio são mantidas. GET projects/summaries traz só metadados para a biblioteca; abrir busca payload completo. PUT idêntico na mesma revisão não incrementa versão/histórico. Primeiro POST pode usar Idempotency-Key UUID: repetir não duplica, payload diferente retorna409 e editor recupera a versão já gravada mantendo alterações locais.

Rascunhos locais por conta/aba/slot, sem envio automático ao recuperá-los. Escrita agrupada250ms e flush em ocultação, pagehide/beforeunload e desmontagem; criação preserva UUID antes do POST. Não prometer recuperação após limpar navegador, outra máquina ou término abrupto sem eventos. Dados ainda não enviados ao servidor não ficam no backup SQLite. Conflitos409 preservam local e permitem nova cópia ou carregamento do servidor conservando rascunho.

Cálculo tem debounce400ms, cancelamento e rejeição de respostas antigas. Exportações exigem snapshot atual. Alteração de metadados não deve refazer matemática sem necessidade. PDF principal/JSON secundário usam nome do projeto, resumo/consumo/custo/equipamentos, pendências e demanda; JSON não é backup completo. Horários públicos usam America/Sao_Paulo; armazenamento/checkpoints UTC.

NDU-0017.0 fornecida pelo usuário e rastreada por hash permite demanda d1–d5 com classificação/inventário/escopo explícitos e revisão vinculada por digest. Só residência individual Energisa Sul-Sudeste/SP até75kW; d6/d7/centrais presentes e outros escopos ficam bloqueados. Reservas excluídas da demanda, incluídas na instalada do limite. Não inferir grupo por catálogo nem converter previsãoVA/BTU/energia emW. PDFs em references/energisa;6.3 só histórica; ambos fora de Git/ZIP de código. Fontes/condições em standards.md e cálculos em calculations.md.

Biblioteca revisada0.16.0:2.082documentos/51.324unidades/3.788fontes.199objetos sem utilidade excluídos com auditoria;2.196objetos técnicos preservados. OCR963páginas recuperadas e97vazias,zero falhas. Método/nota/confiança separados de validação normativa. Inventário histórico+maintenance.json e banco entram no checkpoint; objetos não. Não reimportar inventário histórico nem limpar library como cache. Critério de descarte restrito,não apagar manuais técnicos por classificação genérica.

Motor0.9.0 integra circuitos B1/B2/Cu/PVC70/2condutores,Iz/temp/agrupamento,sobrecarga,seção/PE,queda estimada e verificações explícitas curto térmico/TN/TT/DR; entradaESS/SP220/127 por tabela16NDU7.0. Tudo condicionado a dados e escopo confirmados,sem dimensionamento final universal/DPS/seletividade/geometria. Circuitos/service_entry entram na assinatura do hook e nos projetos,drafts,autosave eJSON1.4/PDF. Fonte e testes em standards/calculations; método fora de escopo fica pendente. Nenhuma regra inferida doOCR.

## Estrutura e continuidade

Frontend: page.tsx orquestra; components/projects, equipment, calculations e layout dividem responsabilidades; lib guarda cliente/contratos/hooks/rascunhos. SectionHeading padroniza etapas; checkbox não recebe padding de texto. Observações/autosave visíveis, Mais ações com foco/Escape/clique fora. Tema escuro e polimento0.13.1 preservados.

Backend: main REST /api/v1 e health, schemas contratos, projects snapshots/histórico, database ORM/escopo por proprietário, reports documentos, calculations motor. Modo local é loopback; autenticação/HTTPS/CSRF/isolamento já implementados permanecem, sem implantação remota ativa. Catálogo global persistente em revisões próprias.

Scripts: continuity.py (retomar/encerrar/verificar), maintenance.py (doctor/clean), external_backup.py preservado fora do escopo atual, check_migrations.py e wrappers/QA Windows. Fonte de dependências são manifests/locks; não editar contrato api.generated.ts manualmente, usar npm run types:sync. Não rodar build e E2E ao mesmo tempo, porque .next/e2e fica sob o diretório do build.

Início/encerramento seguem AGENTS. Ler documentos atuais e cauda dos registros; retomar imprime resumo compacto. Último checkpoint em .checkpoints/latest.json: restauração completa via verificar; não confundir marker com nova verificação. Atualizar docs uma vez, commit local revisado, encerrar e conferir resultado; não criar commit extra só pelo caminho. Reutilização só para fonte/banco/refs Git idênticos e após nova restauração. Ponto incompleto não substitui o anterior. Backup local não cobre perda física. Cleanup só em gerados permitidos, nunca dependências ativas/venvs/node_modules, .git, referências, dados ou checkpoints únicos. Permissões privadas POSIX0700/0600, sem chmod indiscriminado ou mudanças globais de política Windows.
