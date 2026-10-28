import { render, screen, cleanup, fireEvent } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';
import { ResultsPanel } from '@/components/calculations/ResultsPanel';
import type { CalculationResult } from '@/lib/api';
import fixture from './fixtures/result.json';
afterEach(cleanup);
it('prioritizes energy estimates and keeps calculation memory secondary', () => {
  render(<ResultsPanel result={fixture as CalculationResult} loading={false} stale={false} />);
  expect(screen.getByRole('heading', { name: 'Resultados e Estimativas' })).toBeVisible();
  const memory = screen.getByText('Memória de cálculo e premissas').closest('details')!;
  expect(memory.open).toBe(false);
  fireEvent.click(screen.getByText('Memória de cálculo e premissas'));
  expect(memory.open).toBe(true);
  expect(screen.queryByText('Requisitos para')).toBeNull();
  expect(screen.queryByLabelText('Cobertura normativa')).toBeNull();
  expect(screen.queryByText('Demanda normativa')).toBeNull();
});
it('shows partial monthly consumption and cost supplied by Python', () => {
  render(
    <ResultsPanel
      result={
        {
          ...fixture,
          monthly_energy: { value: '85.4', unit: 'kWh', status: 'pending' },
          monthly_cost: { value: '68.32', unit: 'BRL', status: 'pending' },
          energy_unknown_load_ids: ['a'],
        } as CalculationResult
      }
      loading={false}
      stale={false}
    />,
  );
  expect(screen.getByText('85,4 kWh/mês')).toBeVisible();
  expect(screen.getByText('R$ 68,32')).toBeVisible();
  expect(screen.getByText(/1 aparelho\(s\) sem consumo informado/)).toBeVisible();
});
it('keeps input issues actionable and hides old results during recalculation', () => {
  const result = {
    ...fixture,
    notifications: [
      {
        id: 'missing.power',
        category: 'error',
        location: ['Sala', 'Carga'],
        problem: 'Potência ausente',
        solution: 'Informe a potência adotada',
        affected_results: ['W'],
        target_id: 'load.a.unit_power_w',
      },
    ],
  } as CalculationResult;
  const view = render(<ResultsPanel result={result} loading={false} stale={false} />);
  expect(screen.getByRole('button', { name: /Corrigir informação/ })).toBeVisible();
  view.rerender(<ResultsPanel result={result} loading stale />);
  expect(screen.getByText('Recalculando as entradas atuais…')).toBeVisible();
  expect(screen.queryByRole('button', { name: /Corrigir informação/ })).toBeNull();
});
it('shows daily and annual estimates without calculating in the frontend', () => {
  render(
    <ResultsPanel
      result={
        {
          ...fixture,
          daily_energy: { value: '3.15', unit: 'kWh', status: 'estimated' },
          annual_energy: { value: '1152', unit: 'kWh', status: 'estimated' },
        } as CalculationResult
      }
      loading={false}
      stale={false}
    />,
  );
  expect(screen.getByText('3,15 kWh/dia')).toBeVisible();
  expect(screen.getByText('1.152 kWh/ano')).toBeVisible();
});
