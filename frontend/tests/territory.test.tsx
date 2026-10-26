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

test('municipal query keeps multiple agents and cancels late results on a new code', async () => {
  let resolve!: (value: unknown) => void;
  vi.mocked(request).mockReturnValue(
    new Promise((done) => {
      resolve = done;
    }),
  );
  render(<TerritoryStudy />);
  fireEvent.click(screen.getByText('Distribuidoras por município — declarações oficiais ANEEL'));
  const field = screen.getByLabelText('Código IBGE do município (7 dígitos)');
  fireEvent.change(field, { target: { value: '3550308' } });
  fireEvent.submit(
    screen.getByRole('button', { name: 'Consultar distribuidoras no município' }).closest('form')!,
  );
  const call = vi.mocked(request).mock.calls[0];
  expect(call[0]).toContain('code=3550308');
  fireEvent.change(field, { target: { value: '3509502' } });
  expect(call[1]?.signal?.aborted).toBe(true);
  await act(async () => resolve({ ...answer, reason: 'Município anterior' }));
  expect(screen.queryByText('Município anterior')).toBeNull();
});

test('municipal declarations show the reference month and all matching CNPJs', async () => {
  vi.mocked(request).mockResolvedValue({
    ...answer,
    source: 'https://dadosabertos.aneel.gov.br/',
    reason: 'Relações declaradas',
    municipality: { code: '3550308', name: 'São Paulo', state: 'SP' },
    reference_month: '2026-09-01',
    candidates: [
      {
        cnpj: '00000000000001',
        acronym: 'Empresa A',
        name: 'Empresa A fictícia',
        grant_type: 'Concessão',
        reference_month: '2026-08-01',
        active_units: 100,
      },
      {
        cnpj: '00000000000002',
        acronym: 'Empresa B',
        name: 'Empresa B fictícia',
        grant_type: 'Permissão',
        reference_month: '2026-09-01',
        active_units: 20,
      },
    ],
  });
  render(<TerritoryStudy />);
  fireEvent.click(screen.getByText('Distribuidoras por município — declarações oficiais ANEEL'));
  fireEvent.change(screen.getByLabelText('Código IBGE do município (7 dígitos)'), {
    target: { value: '3550308' },
  });
  fireEvent.submit(
    screen.getByRole('button', { name: 'Consultar distribuidoras no município' }).closest('form')!,
  );
  expect(await screen.findByText(/Empresa A fictícia/)).toBeTruthy();
  expect(screen.getByText(/Empresa B fictícia/)).toBeTruthy();
  expect(screen.getByText(/declaradas em 2026-08/)).toBeTruthy();
  expect(screen.getByText(/declaradas em 2026-09/)).toBeTruthy();
  expect(screen.getByText(/Mês mais recente no município: 2026-09/)).toBeTruthy();
});
