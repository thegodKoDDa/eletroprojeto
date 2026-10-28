'use client';
import { useStableHeight } from '@/lib/use-stable-height';
import { EnergyBreakdown } from './EnergyBreakdown';
import { SectionHeading } from '@/components/ui/SectionHeading';
import type { CalculationResult, ProjectInput } from '@/lib/api';
import { format, formatCurrency } from '@/lib/format';
import { CalculationNotices, focusField } from '@/components/calculations-notices';
import { energyCompletionTarget } from '@/lib/journey';

export function ResultsPanel({
  result,
  reviewed = false,
  onReview,
  loading,
  stale,
  environments,
}: {
  result?: CalculationResult;
  reviewed?: boolean;
  onReview?: () => void;
  loading: boolean;
  stale: boolean;
  scope?: ProjectInput['analysis_scope'];
  environments?: ProjectInput['environments'];
  tariff?: ProjectInput['energy_tariff_brl_per_kwh'];
  onScopeChange?: (scope: ProjectInput['analysis_scope']) => void;
}) {
  const heightRef = useStableHeight('estimates', loading);
  return (
    <section
      ref={heightRef}
      id="results"
      tabIndex={-1}
      aria-labelledby="results-heading"
      className="panel min-h-64 results-panel"
      aria-busy={loading}
      data-stale={stale}
    >
      <header className="section-header">
        <SectionHeading
          id="results-heading"
          eyebrow="03 / ESTIMATIVAS"
          title="Resultados e Estimativas"
          description="Energia e custo dos equipamentos e hábitos informados, para sua residência atual ou planejada."
        />
      </header>
      <p className="result-state mt-3 text-xs muted" role="status">
        {loading
          ? 'Recalculando as entradas atuais…'
          : stale
            ? 'Cálculo indisponível. Confira os dados ou a conexão.'
            : result
              ? 'Resultados correspondem às entradas atuais.'
              : 'Sem resultados atuais.'}
      </p>
      {result && (
        <div
          className="results-content"
          aria-label="Consumo e custo mensais"
          hidden={stale && !loading}
          aria-hidden={stale || undefined}
          inert={stale || undefined}
          style={{ visibility: stale ? 'hidden' : undefined }}
        >
          <div
            className="consumption-summary mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-3"
            aria-label="Resumo de resultados"
          >
            {[
              [
                'Potência instalada',
                `${format(result.installed_power_kw.value)} kW · ${format(result.installed_power.value)} W${result.unknown_load_ids?.length ? ' · subtotal' : ''}`,
              ],
              [
                'Consumo diário estimado · média anualizada',
                result.daily_energy
                  ? `${format(result.daily_energy.value)} kWh/dia`
                  : 'Informe os hábitos ou o consumo da etiqueta',
              ],
              [
                'Consumo mensal estimado',
                result.monthly_energy
                  ? `${format(result.monthly_energy.value)} kWh/mês`
                  : 'Consumo ainda não estimado',
              ],
              [
                'Consumo anual estimado',
                result.annual_energy
                  ? `${format(result.annual_energy.value)} kWh/ano`
                  : 'Consumo ainda não estimado',
              ],
              [
                'Custo mensal estimado',
                result.monthly_cost
                  ? formatCurrency(result.monthly_cost.value)
                  : 'Informe a tarifa em R$/kWh',
              ],
              [
                'Custo anual estimado',
                result.annual_cost
                  ? formatCurrency(result.annual_cost.value)
                  : 'Informe a tarifa em R$/kWh',
              ],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-xs muted">{label}</p>
                <p className="mt-2 text-xl font-semibold">{value}</p>
              </div>
            ))}
          </div>
          <p className="field-hint mt-4">
            Estimativas, não medições reais. A média diária divide a projeção anual por 365 dias;
            não descreve um dia específico. Clima, ciclos e hábitos alteram o consumo. O custo usa a
            tarifa informada e não representa a fatura completa.
          </p>
          {!!result.energy_unknown_load_ids?.length && (
            <div className="mt-4">
              <p>
                {result.energy_unknown_load_ids.length} aparelho(s) sem consumo informado. O
                subtotal não representa a residência completa.
              </p>
              <button
                className="btn mt-2"
                onClick={() => focusField(energyCompletionTarget({ environments }, result))}
              >
                Completar consumo dos aparelhos
              </button>
            </div>
          )}
          {!!result.energy_unknown_load_ids?.length && (
            <details className="mt-3">
              <summary>Aparelhos com consumo pendente</summary>
              <ul>
                {result.energy_unknown_load_ids.map((id) => {
                  const room = environments?.find((room) =>
                    room.loads?.some((load) => load.id === id),
                  );
                  const load = room?.loads?.find((load) => load.id === id);
                  return (
                    <li key={id}>
                      <button
                        className="text-action mt-2"
                        onClick={() =>
                          focusField(energyCompletionTarget({ environments }, result, id))
                        }
                      >
                        Informar consumo: {room?.name ?? 'Ambiente'} → {load?.name ?? 'Aparelho'}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </details>
          )}
          {result.monthly_energy && !result.monthly_cost && (
            <button
              className="btn mt-3"
              onClick={() => focusField('project.energy_tariff_brl_per_kwh')}
            >
              Informar tarifa para estimar o custo
            </button>
          )}
          <EnergyBreakdown result={result} environments={environments} />
          <CalculationNotices notices={result.notifications ?? []} stale={false} />
          <details className="result-details mt-5 min-w-0 [overflow-wrap:anywhere]">
            <summary id="results-memory">Memória de cálculo e premissas</summary>
            <p className="field-hint mt-3">
              Valores de referência são sugestões. Potências e consumos adotados manualmente
              prevalecem. Potência instalada não equivale a consumo energético.
            </p>
            <div className="divide-y">
              {environments?.map((room) => (
                <div key={room.id} className="mt-4">
                  <h3 className="font-semibold">
                    {room.name} · {format(result.by_environment_w[room.id!])} W
                  </h3>
                  {room.loads?.map((load) => {
                    const resolved = result.load_results?.find((item) => item.load_id === load.id);
                    return (
                      <article className="mt-3" key={load.id}>
                        <h4>
                          {load.name} · {load.quantity} unidade(s)
                        </h4>
                        <p className="text-xs muted">
                          Fonte: {load.source || 'Informação do usuário'} · Potência adotada:{' '}
                          {format(resolved?.electrical_input_w)} W por unidade
                        </p>
                        {resolved?.steps.map((step, index) => (
                          <div key={index} className="mt-2 text-sm">
                            <p>
                              {step.formula} · {step.substituted}
                            </p>
                            <p className="text-xs muted">{step.assumptions}</p>
                          </div>
                        ))}
                      </article>
                    );
                  })}
                </div>
              ))}
            </div>
            <details className="mt-4">
              <summary>Agregações e conversões</summary>
              {result.aggregate_steps?.map((step, index) => (
                <p className="mt-2 text-sm" key={index}>
                  {step.calculation}: {step.substituted}
                </p>
              ))}
            </details>
          </details>
          {onReview && (
            <button id="estimate-confirm" className="btn mt-4" onClick={onReview}>
              {reviewed ? 'Conferência concluída' : 'Já conferi a estimativa'}
            </button>
          )}
        </div>
      )}
    </section>
  );
}
