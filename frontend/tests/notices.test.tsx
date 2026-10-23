import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test } from 'vitest';
import { CalculationNotices } from '../src/components/calculations-notices';
import type { components } from '../src/lib/api.generated';
afterEach(cleanup);
const notice: components['schemas']['Notification'] = {
  id: 'missing.fp',
  category: 'error',
  location: ['Quarto 01', 'Televisor'],
  problem: 'Fator de potência não informado.',
  solution: 'Informe FP documentado.',
  affected_results: ['VA', 'Corrente'],
  target_id: 'load.test.power_factor',
};

test('correction opens advanced fields, scrolls and focuses the exact input; resolved notices disappear', () => {
  function View({ notices = [notice] }: { notices?: (typeof notice)[] }) {
    return (
      <>
        <details data-testid="advanced">
          <summary>Avançado</summary>
          <label>
            FP
            <input id="load.test.power_factor" />
          </label>
        </details>
        <CalculationNotices notices={notices} stale={false} />
      </>
    );
  }
  const view = render(<View />);
  expect(screen.getByLabelText('FP')).not.toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: /Corrigir informação/ }));
  expect(screen.getByTestId('advanced')).toHaveAttribute('open');
  expect(screen.getByLabelText('FP')).toHaveFocus();
  expect(screen.getByLabelText('FP')).toHaveAttribute('data-correction-target', 'true');
  expect(screen.getByText(/Quarto 01 → Televisor/, { selector: 'p' })).toBeVisible();
  view.rerender(<View notices={[]} />);
  expect(screen.queryByRole('button', { name: /Corrigir informação/ })).toBeNull();
  view.rerender(<View notices={[notice, notice]} />);
  expect(screen.getAllByRole('button', { name: /Corrigir informação/ })).toHaveLength(1);
});

test('stale notices are replaced with an explicit revalidation state', () => {
  render(<CalculationNotices notices={[notice]} stale={true} />);
  expect(screen.queryByRole('button')).toBeNull();
  expect(screen.getByText(/Revalidando avisos/)).toBeVisible();
});

test('internal normative limitations never create a fake correction button', () => {
  render(
    <CalculationNotices
      stale={false}
      notices={[
        {
          id: 'normative.lighting',
          category: 'normative',
          location: ['Sistema', 'Regra lighting'],
          problem: 'ABNT NBR 5410: edição e cláusula não conferidas.',
          solution: 'Depende da revisão técnica do sistema.',
          affected_results: ['Iluminação mínima'],
          target_id: null,
        },
      ]}
    />,
  );
  expect(screen.queryByRole('button', { name: /Corrigir/ })).toBeNull();
  expect(screen.getByText(/edição e cláusula não conferidas/)).toBeInTheDocument();
});
