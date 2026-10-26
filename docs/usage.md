# Guia de uso

O EletroProjeto estima o consumo elétrico de uma residência pronta ou planejada. Você informa os aparelhos e como são usados; a aplicação organiza os resultados por ambiente e equipamento.

## Escolha como quer usar

Na abertura, escolha uma apresentação:

- **USUÁRIO LEIGO:** preenchimento essencial em destaque, consumo mensal dos aparelhos aberto e orientação para chegar à estimativa. Os campos necessários seguem os requisitos da operação atual; a tarifa é opcional para estimar o consumo e necessária para estimar o custo.
- **USUÁRIO PROFISSIONAL:** dados elétricos, medidas, memória de cálculo e atalhos de demanda, circuitos/proteções, localização, território e biblioteca técnica em destaque. Todos os limites e condições dos estudos permanecem.
- **ESTOU APENAS DANDO UMA OLHADA:** organização original, com consumo primeiro e estudos técnicos recolhidos.

No celular e tablet, leigo e profissional têm um botão **Navegação** para abrir os acessos a início, projetos, lixeira e biblioteca. Selecionar um destino recolhe esse menu; salvar e exportar continuam visíveis durante a edição. No computador a navegação permanece aberta.

Todos os recursos estão disponíveis em qualquer perfil. Use **Alterar perfil** na navegação para trocar a apresentação sem perder o projeto ou a edição. O diálogo também pode ser fechado por Escape ou **Voltar sem alterar**. A escolha é lembrada nesta aba, inclusive ao recarregar; uma aba nova começa com a tela de escolha. A preferência é separada por conta quando há autenticação e não é gravada no projeto ou relatório.

Nos perfis leigo e profissional, a biblioteca técnica ocupa o terceiro atalho da tela inicial; a lixeira continua disponível na navegação. Na exploração, o terceiro atalho continua sendo a lixeira. Em detalhes dos resultados, **Mostrar verificações e memória detalhadas** permite aprofundar a consulta em qualquer um dos novos perfis; a exploração conserva o seletor original.

## 1. Projeto

Na tela inicial, escolha **Criar novo projeto**. Informe um nome e o município. A tarifa é opcional: sem ela, o consumo ainda pode ser estimado; com ela, aparece também o custo calculado para a energia informada.

Use a tarifa da sua conta ou contrato. O custo apresentado não inclui automaticamente bandeiras, tributos, iluminação pública ou outras parcelas da fatura.

## 2. Ambientes

Adicione os cômodos e escolha os aparelhos no catálogo, ou cadastre uma carga personalizada. Confira a quantidade e a potência elétrica. Uma referência de catálogo representa um modelo identificado; valores da placa ou do fabricante têm prioridade.

Para estimar o consumo de cada unidade, informe uma das bases:

- **Consumo mensal em kWh:** da etiqueta, de uma medição ou de outra referência identificada.
- **Horários de uso:** potência elétrica, horas por dia e dias por mês, considerando as condições de funcionamento do aparelho.

A aplicação não presume horários, tarifas ou potência elétrica a partir de BTU/h. Se um dado não é conhecido, mantenha-o ausente; um campo pendente não significa consumo zero. Equipamentos cíclicos podem exigir medição ou uma referência de consumo mais adequada que a potência nominal.

## 3. Conferência

Consulte o consumo e o custo estimados, o detalhamento por aparelho e as pendências. Os atalhos levam ao ambiente e ao campo que precisa de informação. Ao editar uma entrada, o resultado anterior fica oculto até o novo cálculo.

![Conferência com dados fictícios: quatro lâmpadas de 10 W, cinco horas por dia, trinta dias e tarifa de R$ 0,80/kWh](assets/consumption.png)

A imagem é um exemplo fictício de funcionamento, não uma recomendação de potência, tarifa ou horário.

## Salvar e recuperar

**Salvar projeto** registra a edição e seu histórico. O salvamento automático pode ser ativado depois do primeiro salvamento manual. Rascunhos locais ajudam a recuperar edições ainda não enviadas; não substituem o banco e podem se perder ao limpar o navegador ou trocar de dispositivo.

Use **Abrir projetos salvos** para continuar um projeto. A lixeira permite restaurar projetos removidos. Em caso de conflito entre versões, escolha a recuperação indicada pela interface; não há sobrescrita silenciosa.

## Exportar

PDF e JSON apresentam o resultado atual, as hipóteses de uso, a cobertura e as pendências. Um cálculo desatualizado precisa terminar antes da exportação. JSON de relatório não é um backup completo para restaurar projetos.

Detalhes do formato e da rastreabilidade estão em [formulários e relatórios](forms-and-pdf.md); cópias completas e recuperação, em [continuidade](continuity.md).

## Estudos técnicos opcionais

Na conferência, abra **Estudos técnicos** apenas quando precisar de uma análise adicional. Demanda, circuitos, localização de componentes e consulta territorial exigem dados e condições específicos. Nenhum desses estudos é obrigatório para estimar o consumo.

Os procedimentos têm cobertura limitada e fontes identificadas. Uma posição, seção ou demanda estimada não declara conformidade final da instalação. Consulte [cálculos](calculations.md), [referências](standards.md) e [limitações conhecidas](KNOWN_ISSUES.md).


Nos circuitos, escolha isolação/método/arranjo reais; terminais para90°C, condições enterradas e afastamentos precisam ser conferidos. D exige temperatura do solo e referência limitada; G exige circuito único trifásico equilibrado sem neutro. Dados de impedância próprios são necessários para queda em XLPE/EPR e D/E/F/G. Os painéis DPS/seletividade comparam documentação de produtos e estudo informado, sem selecionar proteção final.

Em **Referência territorial · ANEEL**, a consulta municipal opcional usa código IBGE de sete dígitos, mostra todas as empresas com relação positiva no último mês declarado por cada uma e preserva datas/atrasos. Confirme a empresa que atende o endereço pela fatura/contrato; a consulta não troca a distribuidora do projeto.

Na edição do aparelho, **Etiqueta ou medição** reúne os kWh mensais; **Estimativa por horários** reúne horas e dias. São alternativas: kWh informados, inclusive zero, prevalecem. Limpar os kWh reabilita os horários preservados. **Restaurar referência** recupera os dados técnicos sugeridos sem apagar consumo/horários; duplicar cria outra instância, sem modificar o catálogo. No perfil profissional, **Parâmetros dos aparelhos** leva aos dados do primeiro aparelho e **Resultados e memória** reabre os detalhes quando necessário.

## Acompanhe o próximo passo

No perfil leigo, o quadro Passo a passo mostra o que já está concluído e a próxima ação. Preencha os dados no seu ritmo: o destaque avança sem tirar o cursor do campo. No celular, Ver todas as etapas expande a lista completa; a próxima ação continua visível quando a lista está recolhida. Use Ir para identificação/cadastro/dados de uso/conferência/salvamento para chegar ao destino e abrir os detalhes necessários. Não precisa seguir a ordem para usar os recursos.

A sequência é identificar o projeto → cadastrar ambientes e aparelhos → informar o uso → conferir a estimativa → salvar. Consumo pendente pode ficar em aberto quando você não conhece o dado. Zero informado é válido e diferente de vazio. A tarifa é opcional; os estudos técnicos também.

Quando houver consumo para todos os aparelhos cadastrados, leia os resultados e os avisos e clique Já conferi a estimativa. O quadro destaca o salvamento se ele estiver pendente. Alterar os dados pede nova conferência; reabrir ou recarregar também não presume que você leu a nova estimativa. Conferência do usuário não é aprovação técnica da instalação.

No profissional, Acompanhar as etapas da estimativa oferece o mesmo percurso de forma opcional, abaixo dos atalhos explicados. Em qualquer perfil, Precisa de ajuda? explica as alternativas de preenchimento e o significado dos estados. Verde com confirmação indica tarefa concluída; âmbar indica pendência; vermelho indica correção; azul indica informação. Texto e símbolos acompanham as cores.
