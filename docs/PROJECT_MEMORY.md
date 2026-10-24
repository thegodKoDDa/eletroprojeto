# Memória permanente — EletroProjeto

## Produto e escopo

Estimativa de consumo elétrico residencial para **leigos primeiro, profissionais depois**, em moradia pronta ou planejada. Preservar produto, dados e identidade visual. Percurso principal: **01 Projeto → 02 Ambientes → 03 Conferência**. Início mantém sidebar/marca e três cartões. Circuitos, entrada e demanda ficam recolhidos depois dos resultados em Estudos técnicos; não voltar a promovê-los a etapas obrigatórias sem pedido.

Consumo/custo recebem destaque, tarifa fica visível e uso dos aparelhos é explícito. Medidas/pontos, dados extras, potência, memória e previsões ficam em detalhes. Catálogo sugere referências, não potências universais; valores manuais válidos prevalecem. A biblioteca técnica serve para melhorar utilidades verificadas, não para exigir novos formulários ou presumir dados.

Uso local. GitHub privado protege a fonte/histórico; implantação do site, CI hospedado, impressão física e cópia externa de dados privados continuam fora do escopo. O agente executa rotinas de terminal, sem delegá-las ao usuário. Autorização de manutenção/sincronização revisada em24/10/2026 está no AGENTS; não repetir perguntas para essas rotinas.

## Invariantes

- Um motor Python em `backend/app/calculations`, funções puras, Decimal, unidades explícitas e sem arredondamento intermediário. Frontend valida/formata; não replica fórmulas.
- W, VA, kWh, BTU/h e potência mecânica são distintos. Desconhecido/regra não validada é null com motivo, nunca zero fictício. Corrente por aparelho não dimensiona circuito. Não declarar conformidade final/aprovação da distribuidora.
- Regras novas exigem fonte oficial, edição, condições, cláusulas, limites, exemplos independentes e testes; registrar em standards/calculations. OCR/importação não habilita regra automaticamente.
- Preservar SQLite, migrações0001–0007, histórico e snapshots. Editar instância não muda catálogo global. Não resetar banco nem atualizar projetos antigos silenciosamente.
- Resultados antigos ficam ocultos para entradas novas, com debounce400ms, cancelamento/rejeição de respostas antigas e exportações vinculadas ao snapshot atual. Metadados não devem refazer matemática sem necessidade.

## Projetos e recuperação

Início, edição, biblioteca e lixeira são independentes; navegar mantém a edição na aba. GET summaries traz metadados; abrir busca payload completo. PUT idêntico na mesma revisão não gera versão/histórico. POST inicial com Idempotency-Key UUID permite repetir após resposta perdida sem duplicar; payload diferente retorna409. Preservar edições feitas durante o envio.

Autosave somente após primeiro salvamento manual, debounce1,5s; renomeação/conflito pausam. Falha não aparece como Salvo nem cria repetição infinita. Conflito409 permite copiar edição local ou carregar servidor preservando rascunho.

Rascunhos por conta/aba/slot em localStorage, escrita agrupada250ms e flush ao ocultar/sair/desmontar. Recuperar não envia automaticamente. Limpeza do navegador, outra máquina e término abrupto sem eventos limitam recuperação; SQLite/checkpoints não capturam dados ainda não enviados ao servidor.

Remover cargas/ambientes limpa associações atuais; histórico/catálogo permanecem intactos. Referências ausentes em projetos antigos têm reparo explícito. Revalidação compara edição salva e registra nova versão conscientemente, preservando entradas manuais. Histórico ordenado por versão resolve timestamps iguais.

PDF principal/JSON secundário incluem consumo, hipóteses, cobertura e pendências; JSON de relatório não é backup completo. Assinatura inclui circuitos/proteções/entrada. Horários públicos America/Sao_Paulo; armazenamento/checkpoints UTC.

## Motor e acervo

Versões e contagens atuais em CURRENT_STATE; fontes/condições em standards/calculations. NDU-0017.0 d1–d5 exige inventário/classificação/escopo e revisão vinculada por digest; somente residência individual Energisa Sul-Sudeste/SP até75kW. d6/d7/centrais presentes bloqueiam; reservas saem da demanda, mas entram na instalada do limite. Não inferir grupo, distribuidora municipal, FP ou converter VA/BTU/energia em W.

Estudos condicionais de circuitos Cu/PVC70/B1/B2/dois condutores, proteção e entrada ESS220/127V/tabela16 permanecem limitados às condições documentadas; não equivalem a dimensionamento final universal. Sem inferir DPS, seletividade, geometria, ensaios ou parâmetros do produto.

Acervo local:2.196objetos técnicos,2.082documentos/51.324unidades/3.788fontes. OCR recuperou963páginas,97vazias; nenhuma falha. Método/confiança separados de validação normativa.199objetos sem utilidade foram descartados com autorização/auditoria anterior; não reimportar inventário histórico nem tratar `library/objects` como cache. Originais Energisa7.0/6.3 e quatro JSONs de auditoria permanecem locais. Revisão humana integral do acervo não concluída.

## Estrutura e continuidade

Backend: REST/main, schemas/contratos, projects/histórico, database/ORM, reports, calculations. Frontend: page orquestra; componentes projects/equipment/calculations/layout e hooks em lib. `use-workspace-resources` carrega recursos independentemente; cliente centraliza erros/cabeçalhos/CSRF. Modo local loopback e autenticação remota/HTTPS/isolamento já implementados são preservados.

Fonte de dependências são manifests/locks. Reutilizar `.venv`, `.venv-windows` e node_modules; não reinstalar por hábito. Contratos somente por `npm run types:sync`. Não rodar build e E2E simultaneamente; QA usa bancos/portas e diretórios próprios.

GitHub: `https://github.com/thegodKoDDa/eletroprojeto`, origin/main, privado, Actions desativado. Encerramento autorizado envia commits revisados apenas para esse destino após conferir privacidade; sem force-push ou merge automático. Credencial existente via Git Credential Manager do Windows, sem token em URL/arquivo/log. Código/docs no GitHub; banco, checkpoints, `.env` e originais do acervo continuam locais.

Rotina em AGENTS e detalhes em continuity.md. Retomar lê AGENTS/CURRENT_STATE/esta memória e executa continuity retomar; documentos históricos são consultados conforme necessidade. Encerrar atualiza docs uma vez, testa proporcionalmente, faz commit revisado e executa encerrar --sync. Sem rede, checkpoint local é preservado e sincronização fica pendente. Não criar commit extra pelo caminho do ponto; consultar `.checkpoints/latest.json`.

Checkpoints mantêm fonte/SQLite/bundle, hashes e restauração completa isolada. Bancos idênticos compartilham armazenamento por hardlinks, sem apagar pontos; ausência de suporte mantém cópias independentes. Não editar snapshots; restaurar para arquivo novo. Marker não substitui verificar. Clean/doctor/compact só quando necessário, preservando dados, referências, instalações úteis e recuperação. Exportador GPG fora de uso retirado; versões antigas estão no Git. POSIX0700/0600 nos privados; não mudar política global/ACL Windows indiscriminadamente.
