import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { TerritoryStudy } from '@/components/projects/TerritoryStudy';
import { request } from '@/lib/api';
vi.mock('@/lib/api', () => ({ request: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const answer = {
  status: 'awaiting_technical_validation',
  automatic_assignment: false,
  candidates: [],
  source: 'https://sigel.aneel.gov.br/',
  consulted_on: '2026-10-26T00:00:00Z',
  reason: 'Nenhuma feição encontrada para este ponto.',
  notice: 'Confirme atendimento manualmente.',
};
function fill() {
  fireEvent.change(screen.getByLabelText('Latitude SIRGAS2000 (graus)'), {
    target: { value: '-23' },
  });
  fireEvent.change(screen.getByLabelText('Longitude SIRGAS2000 (graus)'), {
    target: { value: '-46' },
  });
  fireEvent.submit(
    screen.getByRole('button', { name: 'Consultar distribuidoras no ponto' }).closest('form')!,
  );
}

test('coordinates changes abort the previous query and late answers stay hidden', async () => {
  let resolve!: (value: typeof answer) => void;
  vi.mocked(request).mockReturnValue(
    new Promise((done) => {
      resolve = done;
    }),
  );
  render(<TerritoryStudy />);
  fill();
  const call = vi.mocked(request).mock.calls[0];
  expect(call[0]).toContain('latitude=-23&longitude=-46');
  fireEvent.change(screen.getByLabelText('Longitude SIRGAS2000 (graus)'), {
    target: { value: '-47' },
  });
  expect(call[1]?.signal?.aborted).toBe(true);
  await act(async () => resolve(answer));
  expect(screen.queryByText(answer.reason)).toBeNull();
});

test('query has no automatic assignment and published results disappear on new input', async () => {
  vi.mocked(request).mockResolvedValue(answer);
  render(<TerritoryStudy />);
  fill();
  expect(await screen.findByText(answer.reason)).toBeTruthy();
  fireEvent.change(screen.getByLabelText('Latitude SIRGAS2000 (graus)'), {
    target: { value: '-24' },
  });
  expect(screen.queryByText(answer.reason)).toBeNull();
  expect(screen.getByText(/não seleciona distribuidora/)).toBeTruthy();
});
