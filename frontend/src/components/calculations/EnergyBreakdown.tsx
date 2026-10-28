'use client';
import type { CalculationResult, ProjectInput } from '@/lib/api';
import { format, formatCurrency } from '@/lib/format';
import { focusField } from '@/components/calculations-notices';

export function EnergyBreakdown({
  result,
  environments,
}: {
  result: CalculationResult;
  environments?: ProjectInput['environments'];
}) {
  if (!result.monthly_energy) return null;
  const partial = !!result.energy_unknown_load_ids?.length;
  return (
    <details open className="energy-breakdown mt-4">
      <summary>Contas automáticas: ambientes, maiores consumos e 12 meses</summary>
      <p className="field-hint mt-2">
        {partial
          ? 'Subtotal dos aparelhos com consumo conhecido; não representa a casa completa.'
          : 'Estimativa dos aparelhos cadastrados.'}{' '}
        Os percentuais usam o subtotal conhecido; em consumo zero não há participação percentual
        definida.
      </p>
      <div className="consumption-summary grid gap-3 sm:grid-cols-2 mt-3">
        <div>
          <p className="text-xs muted">Projeção de consumo em 12 meses</p>
          <p className="mt-2 text-lg font-semibold">
            {result.annual_energy ? `${format(result.annual_energy.value)} kWh` : 'Pendente'}
          </p>
        </div>
        <div>
          <p className="text-xs muted">Projeção de custo em 12 meses</p>
          <p className="mt-2 text-lg font-semibold">
            {result.annual_cost ? formatCurrency(result.annual_cost.value) : 'Informe a tarifa'}
          </p>
        </div>
      </div>
      <p className="field-hint mt-2">
        Repete a rotina mensal por 12 meses ou usa o consumo anual da etiqueta. Não presume
        sazonalidade, reajustes ou encargos da fatura.
      </p>
      <h3 className="result-section-title mt-4">Consumo e custo por ambiente</h3>
      <ul className="energy-breakdown-list">
        {environments?.map((room) => (
          <li key={room.id}>
            <span>{room.name}</span>
            <span>
              {result.energy_by_environment_kwh?.[room.id!] == null
                ? room.loads?.length
                  ? 'Consumo pendente'
                  : 'Sem aparelhos'
                : `${format(result.energy_by_environment_kwh[room.id!])} kWh/mês`}
            </span>
            <span>
              {result.energy_cost_by_environment_brl?.[room.id!] == null
                ? !room.loads?.length
                  ? '—'
                  : result.monthly_cost
                    ? 'Consumo pendente'
                    : 'Tarifa não informada'
                : formatCurrency(result.energy_cost_by_environment_brl[room.id!])}
            </span>
          </li>
        ))}
      </ul>
      <details className="mt-3">
        <summary>Consumo e custo por categoria</summary>
        {partial && (
          <p className="field-hint mt-2">
            Valores por ambiente e categoria representam apenas os aparelhos com consumo informado.
          </p>
        )}
        <ul className="energy-breakdown-list">
          {Object.entries(result.energy_by_category_kwh ?? {}).map(([category, amount]) => (
            <li key={category}>
              <span>{category}</span>
              <span>{format(amount)} kWh/mês</span>
              <span>
                {result.energy_cost_by_category_brl?.[category] == null
                  ? 'Tarifa não informada'
                  : formatCurrency(result.energy_cost_by_category_brl[category])}
              </span>
            </li>
          ))}
        </ul>
      </details>
      <h3 className="result-section-title mt-4">Até 5 maiores consumos cadastrados</h3>
      <ol className="energy-breakdown-list">
        {result.energy_ranked_load_ids?.slice(0, 5).map((id) => {
          const load = result.load_results?.find((item) => item.load_id === id);
          const room = environments?.find((item) =>
            item.loads?.some((candidate) => candidate.id === id),
          );
          const share = result.energy_share_by_load_pct?.[id];
          return load ? (
            <li key={id}>
              <button
                type="button"
                className="text-action"
                onClick={() =>
                  focusField(
                    `load.${id}.parameters.${load.energy_basis === 'annual_stated' ? 'annual_energy_kwh' : load.energy_basis === 'schedule' ? (room?.loads?.find((candidate) => candidate.id === id)?.parameters?.usage_time_unit === 'minutes' ? 'usage_minutes_per_day' : 'usage_hours_per_day') : 'monthly_energy_kwh'}`,
                  )
                }
              >
                {room?.name} → {load.name}
              </button>
              <span>{format(load.monthly_energy_kwh)} kWh/mês</span>
              <span>
                {share == null ? (
                  'Participação não definida'
                ) : (
                  <>
                    <meter
                      min={0}
                      max={100}
                      value={Number(share)}
                      aria-label={`Participação de ${load.name} no subtotal`}
                    />{' '}
                    {format(share)}% do subtotal
                  </>
                )}
              </span>
            </li>
          ) : null;
        })}
      </ol>
    </details>
  );
}
