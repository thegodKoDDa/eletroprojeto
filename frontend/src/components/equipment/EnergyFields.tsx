'use client';
import { useExperience } from '@/lib/experience';
import { Field } from '@/components/ui/Field';
import type { Load, TechnicalParameters } from '@/lib/api';

/** Optional energy study. Clearing a field keeps it unknown, never silently zero. */
export function EnergyFields({
  load,
  onChange,
}: {
  load: Load;
  onChange: (patch: Partial<TechnicalParameters>) => void;
}) {
  const { profile } = useExperience();
  const params: Partial<TechnicalParameters> = load.parameters ?? {};
  const descriptionId = `load.${load.id}.energy-description`;
  const priorityId = `load.${load.id}.energy-priority`;
  const stated = params.monthly_energy_kwh != null || params.annual_energy_kwh != null;
  const minutes = params.usage_time_unit === 'minutes';
  const minutesValid =
    params.usage_minutes_per_day == null ||
    (Number.isFinite(Number(params.usage_minutes_per_day)) &&
      Number(params.usage_minutes_per_day) >= 0 &&
      Number(params.usage_minutes_per_day) <= 1440);
  // Invalid dormant values must remain correctable even when stated energy takes priority.
  const hoursValid =
    params.usage_hours_per_day == null ||
    (Number.isFinite(Number(params.usage_hours_per_day)) &&
      Number(params.usage_hours_per_day) >= 0 &&
      Number(params.usage_hours_per_day) <= 24);
  const daysValid =
    params.usage_days_per_month == null ||
    (Number.isInteger(params.usage_days_per_month) &&
      params.usage_days_per_month >= 0 &&
      params.usage_days_per_month <= 31);
  return (
    <details
      open={profile !== 'explore' || undefined}
      data-testid="equipment-energy"
      data-emphasis={profile === 'beginner' ? 'recommended' : undefined}
    >
      <summary className="cursor-pointer text-xs muted">
        {profile === 'beginner' ? 'Consumo mensal · informe como usa' : 'Consumo mensal (opcional)'}
      </summary>
      <p id={descriptionId} className="mt-2 text-xs muted">
        Informe o consumo mensal por unidade da etiqueta ou medição. Se não souber, informe as horas
        efetivas de funcionamento e os dias de uso para estimar pela potência. Nenhum horário é
        presumido.
      </p>
      {load.catalog_reference?.power_rating === 'maximum' && !load.power_user_edited && (
        <p className="mt-2 text-xs muted">
          A referência deste aparelho informa potência máxima. Estimar por horas nessa potência pode
          superar o consumo típico; prefira etiqueta ou medição quando disponível.
        </p>
      )}
      <div className="energy-alternatives">
        <fieldset className="energy-method">
          <legend>Etiqueta ou medição</legend>
          <Field
            field="load.parameters.monthly_energy_kwh"
            label="Consumo de energia (kWh/mês)"
            path={`load.${load.id}.parameters.monthly_energy_kwh`}
          >
            <input
              type="number"
              min="0"
              step="any"
              aria-describedby={`${descriptionId} ${priorityId}`}
              placeholder="Desconhecido"
              value={params.monthly_energy_kwh ?? ''}
              onChange={(e) => onChange({ monthly_energy_kwh: e.target.value || null })}
            />
          </Field>
          <details className="mt-3">
            <summary className="text-xs">Minha etiqueta informa kWh/ano</summary>
            <Field
              field="load.parameters.annual_energy_kwh"
              label="Consumo de energia (kWh/ano)"
              path={`load.${load.id}.parameters.annual_energy_kwh`}
            >
              <input
                type="number"
                min="0"
                step="any"
                placeholder="Valor anual por unidade"
                value={params.annual_energy_kwh ?? ''}
                onChange={(event) => onChange({ annual_energy_kwh: event.target.value || null })}
                aria-describedby={priorityId}
              />
            </Field>
            <p className="field-hint mt-2">
              O programa divide o valor anual por 12 para obter a média mensal. As condições da
              etiqueta podem diferir do uso real.
            </p>
          </details>
        </fieldset>
        <fieldset className="energy-method">
          <legend>Estimativa por horários</legend>
          <div className="grid grid-cols-2 gap-3">
            <label className="col-span-2">
              Unidade do tempo de uso
              <select
                aria-label="Unidade do tempo de uso"
                value={minutes ? 'minutes' : 'hours'}
                onChange={(event) =>
                  onChange({ usage_time_unit: event.target.value as 'hours' | 'minutes' })
                }
              >
                <option value="hours">Horas por dia</option>
                <option value="minutes">Minutos por dia</option>
              </select>
            </label>
            <Field
              field={
                minutes
                  ? 'load.parameters.usage_minutes_per_day'
                  : 'load.parameters.usage_hours_per_day'
              }
              label={minutes ? 'Minutos de uso por dia' : 'Horas de uso por dia'}
              path={`load.${load.id}.parameters.${minutes ? 'usage_minutes_per_day' : 'usage_hours_per_day'}`}
            >
              <input
                type="number"
                min="0"
                max={minutes ? '1440' : '24'}
                step="any"
                aria-describedby={`${descriptionId} ${priorityId}`}
                disabled={stated && hoursValid && minutesValid && daysValid}
                placeholder={minutes ? 'Ex.: 15' : 'Ex.: 0,5'}
                value={(minutes ? params.usage_minutes_per_day : params.usage_hours_per_day) ?? ''}
                onChange={(event) =>
                  onChange(
                    minutes
                      ? { usage_minutes_per_day: event.target.value || null }
                      : { usage_hours_per_day: event.target.value || null },
                  )
                }
              />
            </Field>
            <Field
              field="load.parameters.usage_days_per_month"
              label="Dias de uso por mês"
              path={`load.${load.id}.parameters.usage_days_per_month`}
            >
              <input
                type="number"
                min="0"
                max="31"
                step="1"
                aria-describedby={`${descriptionId} ${priorityId}`}
                disabled={stated && hoursValid && minutesValid && daysValid}
                placeholder="Não informado"
                value={params.usage_days_per_month ?? ''}
                onChange={(e) =>
                  onChange({
                    usage_days_per_month: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
              />
            </Field>
          </div>
          {((minutes && !hoursValid) || (!minutes && !minutesValid)) && (
            <div className="mt-3">
              <p className="field-hint">
                Existe um valor anterior inválido na outra unidade. Corrija ou limpe esse valor; a
                unidade selecionada acima continua sendo usada no cálculo.
              </p>
              <Field
                field={
                  minutes
                    ? 'load.parameters.usage_hours_per_day'
                    : 'load.parameters.usage_minutes_per_day'
                }
                label={minutes ? 'Horas de uso por dia' : 'Minutos de uso por dia'}
                path={`load.${load.id}.parameters.${minutes ? 'usage_hours_per_day' : 'usage_minutes_per_day'}`}
              >
                <input
                  type="number"
                  min="0"
                  max={minutes ? '24' : '1440'}
                  step="any"
                  value={
                    (minutes ? params.usage_hours_per_day : params.usage_minutes_per_day) ?? ''
                  }
                  onChange={(event) =>
                    onChange(
                      minutes
                        ? { usage_hours_per_day: event.target.value || null }
                        : { usage_minutes_per_day: event.target.value || null },
                    )
                  }
                />
              </Field>
            </div>
          )}
        </fieldset>
      </div>
      <p className="mt-2 text-xs muted">
        Os kWh informados são de uma unidade. O resultado considera a quantidade cadastrada (
        {load.quantity}). Para aparelhos com rotinas diferentes, cadastre cada um separadamente.
      </p>
      <p id={priorityId} className="mt-2 text-xs muted">
        {stated
          ? 'O consumo mensal informado prevalece sobre o anual; o anual prevalece sobre os horários. Limpe os valores de consumo informado para estimar pelo tempo de uso.'
          : 'A estimativa considera potência constante nas horas informadas. Para geladeira e aparelhos com ciclos, prefira a etiqueta ou medição; tempo ligado na tomada não é tempo efetivo de funcionamento.'}
      </p>
    </details>
  );
}
