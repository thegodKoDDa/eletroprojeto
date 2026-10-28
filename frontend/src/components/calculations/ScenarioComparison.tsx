'use client';
import { useEffect, useRef, useState } from 'react';
import type { components } from '@/lib/api.generated';
import { projectInputs, request, type Project, type ProjectInput } from '@/lib/api';
import { inputIdentity } from '@/lib/input-identity';
import { format, formatCurrency } from '@/lib/format';

type Comparison = components['schemas']['EstimateComparison'];
/** Explicit comparison with the saved snapshot; arithmetic stays in Python. */
export function ScenarioComparison({
  input,
  saved,
  ready,
}: {
  input: ProjectInput;
  saved?: Project;
  ready: boolean;
}) {
  const key = inputIdentity(input) + ':' + (saved?.id ?? '') + ':' + (saved?.version ?? '');
  const controller = useRef<AbortController | null>(null);
  const [state, setState] = useState<{
    key: string;
    pending?: boolean;
    result?: Comparison;
    error?: string;
  }>();
  useEffect(() => {
    return () => controller.current?.abort();
  }, [key]);
  const current = state?.key === key && ready ? state : undefined;
  async function compare() {
    if (!saved || !ready) return;
    controller.current?.abort();
    const abort = new AbortController();
    controller.current = abort;
    setState({ key, pending: true });
    try {
      const result = await request<Comparison>('/calculations/compare', {
        method: 'POST',
        body: JSON.stringify({ baseline: projectInputs(saved), scenario: input }),
        signal: abort.signal,
      });
      if (!abort.signal.aborted) setState({ key, result });
    } catch (error) {
      if (!abort.signal.aborted) setState({ key, error: (error as Error).message });
    }
  }
  return (
    <details className="panel mt-5">
      <summary>Comparar cenários de consumo</summary>
      <p className="field-hint mt-3">
        Salve uma configuração e ajuste os aparelhos ou hábitos. Compare a edição atual com a última
        versão salva, sem sobrescrevê-la. Para manter os dois cenários, use Salvar como novo
        projeto.
      </p>
      <button
        className="btn mt-3"
        disabled={!saved || !ready || current?.pending}
        onClick={compare}
      >
        {current?.pending ? 'Comparando…' : 'Comparar com versão salva'}
      </button>
      {!saved && (
        <p className="field-hint mt-2">Salve o primeiro cenário para habilitar a comparação.</p>
      )}
      {current?.error && <p role="alert">{current.error}</p>}
      {current?.result && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <caption>Diferença: edição atual menos versão salva {saved?.version}</caption>
            <thead>
              <tr>
                <th>Indicador</th>
                <th>Diferença estimada</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(current.result.differences).map(([name, value]) => (
                <tr key={name}>
                  <td>
                    {{
                      installed_power: 'Potência instalada',
                      monthly_energy: 'Consumo mensal',
                      annual_energy: 'Consumo anual',
                      monthly_cost: 'Custo mensal',
                      annual_cost: 'Custo anual',
                    }[name] ?? name}
                  </td>
                  <td>
                    {value
                      ? value.unit === 'BRL'
                        ? formatCurrency(value.value)
                        : `${format(value.value)} ${value.unit}`
                      : 'Dados insuficientes para comparar totais'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="field-hint mt-2">
            Valores negativos indicam redução. Não compara totais de consumo com cobertura
            incompleta; custos usam a tarifa de cada cenário.
          </p>
        </div>
      )}
    </details>
  );
}
