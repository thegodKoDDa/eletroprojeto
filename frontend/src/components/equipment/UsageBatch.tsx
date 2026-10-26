'use client';
import { useId, useState } from 'react';
import type { Load } from '@/lib/api';
import { acceptsUsageRoutine, applyUsageRoutine } from '@/lib/usage';

export function UsageBatch({
  loads,
  onApply,
}: {
  loads: Load[];
  onApply: (loads: Load[]) => void;
}) {
  const id = useId();
  const [unit, setUnit] = useState<'hours' | 'minutes'>('hours');
  const [duration, setDuration] = useState('');
  const [days, setDays] = useState('');
  const [message, setMessage] = useState('');
  const eligible = loads.filter(acceptsUsageRoutine).length;
  const valid =
    duration !== '' &&
    days !== '' &&
    Number.isFinite(Number(duration)) &&
    Number(duration) >= 0 &&
    Number(duration) <= (unit === 'minutes' ? 1440 : 24) &&
    Number.isInteger(Number(days)) &&
    Number(days) >= 0 &&
    Number(days) <= 31;
  if (!loads.length) return null;
  return (
    <details className="usage-batch mt-3">
      <summary>Preencher uma rotina para vários aparelhos</summary>
      <p className="field-hint mt-2" id={id}>
        Informe uma rotina comum para os aparelhos deste ambiente que ainda não têm consumo nem
        horários. Nenhum valor preenchido será substituído. Para aparelhos com ciclos, prefira a
        etiqueta.
      </p>
      <div className="grid gap-3 sm:grid-cols-3 mt-3">
        <label>
          Unidade do tempo
          <select
            aria-label="Unidade da rotina comum"
            value={unit}
            onChange={(event) => setUnit(event.target.value as 'hours' | 'minutes')}
          >
            <option value="hours">Horas por dia</option>
            <option value="minutes">Minutos por dia</option>
          </select>
        </label>
        <label>
          {unit === 'hours' ? 'Horas por dia' : 'Minutos por dia'}
          <input
            aria-label="Tempo de uso da rotina comum"
            type="number"
            min="0"
            max={unit === 'hours' ? 24 : 1440}
            step="any"
            aria-describedby={id}
            value={duration}
            onChange={(event) => setDuration(event.target.value)}
          />
        </label>
        <label>
          Dias no mês
          <input
            aria-label="Dias por mês da rotina comum"
            type="number"
            min="0"
            max="31"
            step="1"
            value={days}
            onChange={(event) => setDays(event.target.value)}
          />
        </label>
      </div>
      <div className="field-caption mt-3">
        <p className="field-hint">
          {eligible} aparelho(s) sem rotina; os demais serão preservados.
        </p>
        <button
          type="button"
          className="btn"
          disabled={!eligible || !valid}
          onClick={() => {
            onApply(
              applyUsageRoutine(loads, {
                usage_time_unit: unit,
                usage_hours_per_day: unit === 'hours' ? duration : null,
                usage_minutes_per_day: unit === 'minutes' ? duration : null,
                usage_days_per_month: Number(days),
              }),
            );
            setMessage(
              `Rotina aplicada a ${eligible} aparelho(s). Consumo e custo serão recalculados.`,
            );
          }}
        >
          Aplicar aos aparelhos sem rotina
        </button>
      </div>
      <p role="status" className="field-hint mt-2">
        {message}
      </p>
    </details>
  );
}
