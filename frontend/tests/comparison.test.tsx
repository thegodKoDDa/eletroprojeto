import { cleanup, fireEvent, render, screen, act } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { ScenarioComparison } from '@/components/calculations/ScenarioComparison';
import type { ProjectInput, Project } from '@/lib/api';
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
test('comparison hides outdated differences and aborts in-flight work after an edit', async () => {
  const input = {
    name: 'Casa',
    municipality: '',
    state: 'SP',
    utility: 'unconfirmed',
    analysis_scope: 'installed',
    residence_type: 'Casa',
    floors: 1,
    reference_voltage_v: null,
    notes: '',
    environments: [],
  } as ProjectInput;
  const saved = { ...input, id: 'saved', version: 1 } as Project;
  let resolve: ((response: unknown) => void) | undefined;
  let signal: AbortSignal | undefined;
  vi.stubGlobal(
    'fetch',
    vi.fn((_url: string, init: RequestInit) => {
      signal = init.signal as AbortSignal;
      return new Promise((done) => {
        resolve = done;
      });
    }),
  );
  const view = render(<ScenarioComparison input={input} saved={saved} ready />);
  fireEvent.click(screen.getByText('Comparar cenários de consumo'));
  fireEvent.click(screen.getByRole('button', { name: 'Comparar com versão salva' }));
  await act(async () => {
    resolve!({
      ok: true,
      status: 200,
      json: async () => ({
        differences: { monthly_energy: { value: '5', unit: 'kWh', status: 'estimated' } },
      }),
    });
  });
  expect(screen.getByText('5 kWh')).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Comparar com versão salva' }));
  view.rerender(
    <ScenarioComparison
      input={{ ...input, energy_tariff_brl_per_kwh: '0.8' }}
      saved={saved}
      ready
    />,
  );
  expect(signal?.aborted).toBe(true);
  expect(screen.queryByText('5 kWh')).toBeNull();
  await act(async () => {
    resolve!({
      ok: true,
      status: 200,
      json: async () => ({
        differences: { monthly_energy: { value: '99', unit: 'kWh', status: 'estimated' } },
      }),
    });
  });
  expect(screen.queryByText('99 kWh')).toBeNull();
});
