export function ContextHelp() {
  return (
    <details className="context-help">
      <summary>Precisa de ajuda? Entenda os campos e os avisos</summary>
      <div className="help-topics">
        <div>
          <h3>Comece pelo consumo</h3>
          <p>
            Cadastre ambientes e aparelhos. Use os kWh da etiqueta ou potência e horários efetivos.
            A tarifa da conta de luz permite estimar o custo; ela é opcional.
          </p>
        </div>
        <div>
          <h3>Desconhecido pode ficar pendente</h3>
          <p>
            Não invente valores para concluir uma tarefa. Campo vazio significa falta de informação;
            zero é um valor e só deve ser usado quando for verdadeiro.
          </p>
        </div>
        <div>
          <h3>Entenda cada sinal</h3>
          <p>
            <span className="help-state" data-tone="success">
              ✓ Concluído
            </span>{' '}
            tarefa preenchida ou confirmada.{' '}
            <span className="help-state" data-tone="warning">
              ! Pendente
            </span>{' '}
            falta um dado ou uma verificação.{' '}
            <span className="help-state" data-tone="error">
              ! Corrigir
            </span>{' '}
            entrada inválida ou operação que não terminou.
          </p>
        </div>
        <div>
          <h3>Estudos técnicos são opcionais</h3>
          <p>
            Demanda, circuitos, proteções e localização têm condições próprias. Os avisos indicam os
            limites; concluir o cadastro não significa conformidade elétrica.
          </p>
        </div>
      </div>
    </details>
  );
}
