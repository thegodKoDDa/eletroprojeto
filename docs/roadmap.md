# Roadmap — estado 0.12.0

0.12.0: NDU0017.0 enviada pelo usuário permitiu método residencial parametrizado d1–d5 na API, com classificação e ausências explícitas. Integração ao cadastro, grupos especiais, dimensionamento e território completos continuam pendentes. Fontes/escopo/testes em standards.md; não confundir endpoint disponível com demanda automática ou conformidade final.

## Atualização 0.11.0 — 23/10/2026

Rascunhos/conflitos guiados, autenticação de proprietário com sessões HTTPS/CSRF, catálogo persistente versionado, testes PostgreSQL reais e backend Windows implementados/verificados. Workflow CI ampliado e Git inicializado; falta execução hospedada/remote, cópia externa real e validações físicas. Preparar frontend Windows. Detecção seletiva de impacto normativo, colaboração com permissões de equipe e implantação remota operacional continuam futuras. Prioridades normativas abaixo continuam válidas, sem demanda/dimensionamento final habilitados por suposição.

## Disponível

- Previsão residencial de iluminação/TUG por ambiente interno, por seleção explícita; API/interface/relatórios integrados. Escopo, fontes e exceções em standards.md.

- Motor Python Decimal, somas e memória por carga, ambiente e categoria; W/kW, VA/kVA e correntes com dados suficientes; conversões térmicas/mecânicas separadas.
- Catálogo rastreável, referências editáveis, proteção de valores manuais, requisitos e avisos por operação. Pesquisa/cobertura normativa integrada à API em 0.8.0, separada de erros de cadastro.
- Projetos com histórico/versionamento, duplicação, exclusão reversível, recuperação e salvamento automático após primeiro salvamento.
- Ação de ambientes persistente durante a rolagem, foco no novo cadastro; apresentações simples e técnica dos mesmos resultados.
- PDF preliminar e JSON consistentes com snapshot; registro técnico versionado e revalidação conservadora.
- Proteção inicial de tamanho HTTP/CORS, backup e workflow de qualidade. Estado dos testes em `review-0.5.0.md`.

## Pendências prioritárias

1. Manter testes de navegador/build/lint/contratos/formatação e auditorias online em atualizações. ESLint/Prettier/Ruff configurados em 0.7.0; consumo mensal/custo opcionais disponíveis. Implantar essas verificações em CI quando houver Git/repositório utilizável.
2. Completar acesso/revisão da demanda da distribuidora (NDU integral/tabelas/notas), mantendo nulos até validação. Previsão residencial quantitativa de iluminação/TUG disponível em escopo limitado na 0.9.0; ampliar apenas com condições/casos/testes próprios. Não há dimensionamento final.
3. Autenticação e autorização por projeto antes de exposição multiusuário; ingress/TLS, rate limiting, observabilidade e backup durável.
4. Recuperação de rascunhos não enviados, gerenciamento de conflitos mais guiado e otimização de consultas para grandes acervos.
5. Conferir áreas de concessão e ampliar regras regionais sem presumir distribuidora por município.
6. Catálogo global persistente e validação PostgreSQL. Preservar a revisão contínua dos componentes e contratos, sem prometer ausência universal de erros.

## Etapas posteriores

Circuitos, condutores, proteções, queda de tensão e padrão de entrada dependem de regras e testes próprios. Corrente por equipamento não representa dimensionamento de circuito. O relatório PDF existente continua sendo estudo parcial de cargas.

## Continuidade estabelecida

Memória, estado, sessões e checkpoint local verificável: [continuity.md](continuity.md). Manter atualizados em cada sessão. Pendências: Git utilizável nesta instalação, cópia externa protegida e validação dos wrappers no Windows. Não são substitutos para a validação normativa ou os testes reais de navegador.
