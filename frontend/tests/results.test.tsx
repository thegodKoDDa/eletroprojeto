import { DemandSummary } from '@/components/calculations/DemandSummary';
import { render, screen, fireEvent, cleanup, within } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { ResultsPanel } from '@/components/calculations/ResultsPanel';
import type { CalculationResult } from '@/lib/api';
import fixture from './fixtures/result.json';
afterEach(cleanup);
it('presentation changes expand the same backend memory without changing the calculation scope', () => {
  const onScopeChange = vi.fn();
  const { container } = render(
    <ResultsPanel
      result={fixture as CalculationResult}
      loading={false}
      stale={false}
      scope="installed"
      onScopeChange={onScopeChange}
    />,
  );
  const memory = screen.getByText('Memória por equipamento').closest('details')!;
  const before = container.textContent;
  expect(memory.open).toBe(false);
  fireEvent.change(screen.getByLabelText('Apresentação'), { target: { value: 'technical' } });
  expect(memory.open).toBe(true);
  expect(container.textContent).toBe(before);
  expect(onScopeChange).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText('Apresentação'), { target: { value: 'simple' } });
  expect(memory.open).toBe(false);
});

it('demand presentation follows the API status rather than a permanent validation label', () => {
  const { rerender } = render(
    <DemandSummary demand={{ value: '12.5', unit: 'kVA', status: 'calculated' }} stale={false} />,
  );
  expect(screen.getByText('12,5 kVA')).toBeInTheDocument();
  expect(screen.queryByText('Cálculo ainda indisponível')).toBeNull();
  rerender(
    <DemandSummary
      demand={{
        value: null,
        unit: 'kVA',
        status: 'pending',
        reason: 'Informe a classificação da carga.',
      }}
      stale={false}
    />,
  );
  expect(screen.getByText('Dados de entrada pendentes')).toBeInTheDocument();
  expect(screen.getByText('Informe a classificação da carga.')).toBeInTheDocument();
  rerender(
    <DemandSummary
      demand={{
        value: null,
        status: 'awaiting_technical_validation',
        reason: 'Tabela oficial não conferida.',
      }}
      stale={false}
    />,
  );
  expect(screen.getByText('Cálculo ainda indisponível')).toBeInTheDocument();
});

it('shows incomplete monthly consumption and estimated cost from the API', () => {
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
      scope="installed"
      onScopeChange={vi.fn()}
    />,
  );
  expect(screen.getByText('85,4 kWh/mês')).toBeVisible();
  expect(screen.getByText('R$ 68,32')).toBeVisible();
  expect(screen.getByText(/1 carga\(s\) sem consumo calculável/)).toBeVisible();
});

it('separates unavailable features from correctable inputs without repeating warning cards', () => {
  render(
    <ResultsPanel
      result={fixture as CalculationResult}
      loading={false}
      stale={false}
      scope="installed"
      onScopeChange={vi.fn()}
    />,
  );
  expect(screen.getByText('C · Dados do projeto a revisar')).toBeVisible();
  expect(screen.getByText('Nenhum dado pendente para o cálculo selecionado.')).toBeVisible();
  expect(screen.queryByText('Procedimento não validado')).toBeNull();
  expect(screen.queryByText('Demanda normativa')).toBeNull();
  const coverage = screen.getByLabelText('Cobertura normativa');
  expect(coverage.querySelector('details')?.open).toBe(false);
  fireEvent.click(screen.getByText('Recursos normativos ainda indisponíveis (3)'));
  expect(screen.getByText(/Não indicam erros na sua instalação/)).toBeVisible();
  expect(screen.getByRole('heading', { name: 'Previsão mínima de iluminação' })).toBeVisible();
  fireEvent.click(screen.getByText('Pesquisa e fontes de previsão mínima de iluminação'));
  expect(
    within(
      screen.getByRole('heading', { name: 'Previsão mínima de iluminação' }).closest('section')!,
    ).getByRole('link', { name: 'Catálogo oficial ABNT' }),
  ).toHaveAttribute('href', 'https://www.abntcatalogo.com.br/');
  expect(screen.queryByRole('button', { name: /Corrigir informação/ })).toBeNull();
});

it('keeps real missing inputs actionable while hiding stale coverage details', () => {
  const result = {
    ...fixture,
    notifications: [
      {
        id: 'missing.power',
        category: 'error',
        location: ['Sala', 'Carga'],
        problem: 'Potência ausente',
        solution: 'Informe a placa',
        affected_results: ['W'],
        target_id: 'load.a.unit_power_w',
      },
    ],
  } as CalculationResult;
  const view = render(
    <ResultsPanel
      result={result}
      loading={false}
      stale={false}
      scope="installed"
      onScopeChange={vi.fn()}
    />,
  );
  expect(screen.getByRole('button', { name: /Corrigir informação/ })).toBeVisible();
  expect(screen.queryByText('Nenhum dado pendente para o cálculo selecionado.')).toBeNull();
  view.rerender(
    <ResultsPanel
      result={result}
      loading={true}
      stale={true}
      scope="installed"
      onScopeChange={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByText('Recursos normativos ainda indisponíveis (3)'));
  expect(screen.getByText('Atualizando a cobertura para as entradas atuais…')).toBeVisible();
  expect(screen.queryByRole('link', { name: 'Catálogo oficial ABNT' })).toBeNull();
});
