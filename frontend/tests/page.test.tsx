import { StrictMode } from 'react';
import { Blob as NodeBlob } from 'node:buffer';
import type { ProjectInput } from '../src/lib/api';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import Home from '../src/app/page';
import requirements from './fixtures/requirements.json';
import fixture from './fixtures/result.json';
import catalog from './fixtures/catalog.json';

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function renderProject(element = <Home />) {
  const view = render(element);
  fireEvent.click(screen.getByRole('button', { name: /^Criar novo projeto/ }));
  return view;
}

test('memory DOM and input focus survive recalculation; previous values are labelled and cannot be exported', async () => {
  vi.useFakeTimers();
  let latestInput: ProjectInput | undefined;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      let data: unknown = [];
      if (url.endsWith('/validation/requirements')) data = requirements;
      if (url.endsWith('/equipment')) data = catalog;
      if (url.endsWith('/calculations/full')) {
        const payload = JSON.parse(String(options?.body));
        latestInput = payload;
        const load = payload.environments[0]?.loads[0];
        const result = structuredClone(fixture);
        result.memory = load ? [{ ...result.memory[0], load_id: load.id, name: load.name }] : [];
        result.load_results = [];
        result.technical_context = { registry_version: 'a'.repeat(64) };
        data = result;
      }
      return { ok: true, status: 200, json: async () => data };
    }),
  );
  const { container } = renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.click(screen.getByText('Adicionar primeiro ambiente'));
  fireEvent.change(screen.getByLabelText('Pesquisar catálogo'), { target: { value: 'lampada' } });
  expect(screen.getByLabelText('Adicionar equipamento em Novo ambiente')).toHaveTextContent(
    'Lâmpada LED',
  );
  fireEvent.change(screen.getByLabelText('Adicionar equipamento em Novo ambiente'), {
    target: { value: catalog[0].id },
  });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  const memory = container.querySelector('#results .divide-y > div');
  expect(memory).not.toBeNull();
  const details = container.querySelector('#results > details')!;
  details.setAttribute('open', '');
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  fireEvent.change(screen.getByLabelText('Fator de potência'), { target: { value: '0.9' } });
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  expect(screen.getByLabelText('Fator de potência')).toHaveValue(0.9);
  const power = screen.getByLabelText('Potência unitária (W)');
  power.focus();
  fireEvent.change(power, { target: { value: '12' } });
  expect(power).toHaveFocus();
  expect(container.querySelector('#results .divide-y > div')).toBe(memory);
  expect(details).toHaveAttribute('open');
  expect(screen.getByTestId('calculation-status')).toHaveTextContent('desatualizados');
  expect(screen.getByRole('button', { name: 'Exportar JSON' })).toBeDisabled();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(container.querySelector('#results .divide-y > div')).toBe(memory);
  expect(power).toHaveFocus();
  expect(screen.getByTestId('calculation-status')).toHaveTextContent('Resultados atualizados');
  expect(screen.getByRole('button', { name: 'Exportar JSON' })).toBeEnabled();
  expect(latestInput?.environments?.[0].loads?.[0].power_factor).toBe('0.9');
  expect(latestInput?.environments?.[0].loads?.[0].unit_power_w).toBe('12');
});

test('saving an earlier snapshot preserves edits made while the request is in flight', async () => {
  vi.useFakeTimers();
  let finishSave!: (response: unknown) => void;
  let savedPayload: Record<string, unknown> = {};
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      if (url.endsWith('/projects') && options?.method === 'POST') {
        savedPayload = JSON.parse(String(options.body));
        return new Promise((resolve) => {
          finishSave = resolve;
        });
      }
      return {
        ok: true,
        status: 200,
        json: async () =>
          url.endsWith('/validation/requirements')
            ? requirements
            : url.endsWith('/calculations/full')
              ? fixture
              : [],
      };
    }),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.change(screen.getByLabelText('Município'), { target: { value: 'Cidade' } });
  fireEvent.click(screen.getByRole('button', { name: 'Salvar projeto' }));
  fireEvent.click(screen.getByText('Outros dados do projeto'));
  fireEvent.change(screen.getByLabelText('Observações'), {
    target: { value: 'Anotação feita durante o salvamento' },
  });
  await act(async () => {
    finishSave({
      ok: true,
      status: 201,
      json: async () => ({
        ...savedPayload,
        id: '11111111-1111-4111-8111-111111111111',
        version: 1,
        created_at: '2026-10-21T12:00:00Z',
        updated_at: '2026-10-21T12:00:00Z',
        standards_version: 'pending',
      }),
    });
  });
  expect(screen.getByLabelText('Observações')).toHaveValue('Anotação feita durante o salvamento');
  expect(screen.getByText('Alterações não salvas')).toBeInTheDocument();
});

test('JSON exports general results using the project name', async () => {
  vi.useFakeTimers();
  vi.stubGlobal('Blob', NodeBlob);
  const createUrl = vi.fn<(blob: Blob) => string>().mockReturnValue('blob:exported-project');
  const revokeUrl = vi.fn();
  vi.stubGlobal(
    'URL',
    class extends URL {
      static createObjectURL = createUrl;
      static revokeObjectURL = revokeUrl;
    },
  );
  let download = '';
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
    this: HTMLAnchorElement,
  ) {
    download = this.download;
  });
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url.endsWith('/reports/json'))
        return {
          ok: true,
          status: 200,
          headers: new Headers({ 'Content-Type': 'application/json' }),
          blob: async () =>
            new NodeBlob(
              [
                JSON.stringify({
                  projeto: { nome: 'Novo projeto residencial' },
                  resultados: { potencia_instalada: { valor: fixture.installed_power.value } },
                  previsoes_normativas: { demand: { valor: null } },
                }),
              ],
              { type: 'application/json' },
            ),
        };
      return {
        ok: true,
        status: 200,
        json: async () =>
          url.endsWith('/equipment')
            ? catalog
            : url.endsWith('/calculations/full')
              ? { ...fixture, technical_context: { registry_version: 'a'.repeat(64) } }
              : [],
      };
    }),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.click(screen.getByText('Adicionar primeiro ambiente'));
  fireEvent.change(screen.getByLabelText('Adicionar equipamento em Novo ambiente'), {
    target: { value: catalog[0].id },
  });
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  fireEvent.change(screen.getByLabelText('Fator de potência'), { target: { value: '0.9' } });
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Exportar JSON' }));
  });
  expect(download).toBe('Novo projeto residencial.json');
  expect(revokeUrl).toHaveBeenCalledWith('blob:exported-project');
  const exported = JSON.parse(await (createUrl.mock.calls[0][0] as NodeBlob).text());
  expect(exported.projeto.nome).toBe('Novo projeto residencial');
  expect(exported.resultados.potencia_instalada.valor).toBe(fixture.installed_power.value);
  expect(exported.previsoes_normativas.demand.valor).toBeNull();
  expect(exported.project).toBeUndefined();
  expect(exported.calculation).toBeUndefined();
  expect(JSON.stringify(exported)).not.toContain('source_url');
  expect(JSON.stringify(exported)).not.toContain('aggregate_steps');
});

test('state changes reset utility and send location to Python without assuming municipality coverage', async () => {
  vi.useFakeTimers();
  let payload: ProjectInput | undefined;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      let data: unknown = [];
      if (url.endsWith('/validation/requirements')) data = requirements;
      if (url.endsWith('/locations/states')) data = ['SP', 'MG'];
      if (url.endsWith('/utilities'))
        data = [{ id: 'cpfl_paulista', name: 'CPFL Paulista', states: ['SP'] }];
      if (url.endsWith('/calculations/full')) {
        payload = JSON.parse(String(options?.body));
        data = fixture;
      }
      return { ok: true, status: 200, json: async () => data };
    }),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.change(screen.getByLabelText('Concessionária'), { target: { value: 'cpfl_paulista' } });
  fireEvent.change(screen.getByLabelText('Município'), { target: { value: 'Campinas' } });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(payload?.utility).toBe('cpfl_paulista');
  expect(payload?.municipality).toBe('Campinas');
  fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'MG' } });
  expect(screen.getByLabelText('Concessionária')).toHaveValue('unconfirmed');
  expect(screen.queryByRole('option', { name: /CPFL Paulista/ })).toBeNull();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  expect(payload?.state).toBe('MG');
  expect(payload?.utility).toBe('unconfirmed');
});

test('PDF is primary, exports the current snapshot and is blocked while recalculating', async () => {
  vi.useFakeTimers();
  let exported: Record<string, unknown> | undefined;
  const pdfBlob = new Blob(['%PDF-1.4\n%%EOF'], { type: 'application/pdf' });
  const createUrl = vi.fn(() => 'blob:pdf');
  vi.stubGlobal('URL', { createObjectURL: createUrl, revokeObjectURL: vi.fn() });
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      if (url.endsWith('/reports/pdf')) {
        exported = JSON.parse(String(options?.body));
        return {
          ok: true,
          status: 200,
          headers: new Headers({ 'Content-Type': 'application/pdf' }),
          blob: async () => pdfBlob,
        };
      }
      const data = url.endsWith('/validation/requirements')
        ? requirements
        : url.endsWith('/calculations/full')
          ? { ...fixture, technical_context: { registry_version: 'a'.repeat(64) } }
          : [];
      return { ok: true, status: 200, json: async () => data };
    }),
  );
  renderProject();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(400);
  });
  const pdf = screen.getByRole('button', { name: 'Exportar PDF' });
  expect(screen.getByRole('button', { name: 'Salvar projeto' })).toHaveClass('primary');
  expect(pdf.closest('details')).toBeNull();
  expect(screen.getByRole('button', { name: 'Exportar JSON' }).closest('details')).not.toBeNull();
  expect(screen.getByRole('button', { name: 'Exportar JSON' })).not.toHaveClass('primary');
  expect(pdf).toBeEnabled();
  await act(async () => {
    fireEvent.click(pdf);
  });
  expect(exported?.expected_input_digest).toBe(fixture.input_digest);
  expect((exported?.project as ProjectInput).name).toBe('Novo projeto residencial');
  expect(createUrl).toHaveBeenCalledWith(pdfBlob);
  fireEvent.change(screen.getByLabelText('Município'), { target: { value: 'Novo município' } });
  expect(pdf).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Exportar JSON' })).toBeDisabled();
});

test('Strict Mode cancellation does not leave false metadata warnings on the mounted page', async () => {
  vi.useFakeTimers();
  const counts = new Map<string, number>();
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      const count = (counts.get(url) ?? 0) + 1;
      counts.set(url, count);
      if ((url.endsWith('/validation/requirements') || url.endsWith('/utilities')) && count === 1) {
        return new Promise((_, reject) => {
          options?.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError')),
          );
        });
      }
      return {
        ok: true,
        status: 200,
        json: async () => (url.endsWith('/validation/requirements') ? requirements : []),
      };
    }),
  );
  renderProject(
    <StrictMode>
      <Home />
    </StrictMode>,
  );
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
  expect(screen.getByLabelText('Nome do projeto')).toHaveAttribute('aria-required', 'true');
  expect(screen.queryByTestId('project-message')).toBeNull();
});

test('adding another environment focuses its name without remounting existing inputs', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => ({
      ok: true,
      status: 200,
      json: async () => (url.endsWith('/validation/requirements') ? requirements : []),
    })),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.click(screen.getByRole('button', { name: 'Adicionar primeiro ambiente' }));
  const first = screen.getByLabelText('Nome');
  expect(first).toHaveFocus();
  fireEvent.change(first, { target: { value: 'Quarto preservado' } });
  fireEvent.click(screen.getByRole('button', { name: 'Adicionar ambiente' }));
  const names = screen.getAllByLabelText('Nome');
  expect(names[0]).toBe(first);
  expect(first).toHaveValue('Quarto preservado');
  expect(names[1]).toHaveFocus();
});

test('autosave coalesces edits after first save and does not retry a failed snapshot indefinitely', async () => {
  vi.useFakeTimers();
  const writes: { method: string; input: ProjectInput }[] = [];
  let failUpdate = false;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      if ((options?.method === 'POST' && url.endsWith('/projects')) || options?.method === 'PUT') {
        const input = JSON.parse(String(options?.body));
        writes.push({ method: options!.method!, input });
        if (failUpdate) throw new Error('Conexão interrompida');
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ...input,
            id: '11111111-1111-4111-8111-111111111111',
            version: writes.length,
            created_at: '2026-10-21T12:00:00Z',
            updated_at: '2026-10-21T12:00:00Z',
            standards_version: 'pending',
          }),
        };
      }
      return {
        ok: true,
        status: 200,
        json: async () =>
          url.endsWith('/validation/requirements')
            ? requirements
            : url.endsWith('/calculations/full')
              ? fixture
              : [],
      };
    }),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.change(screen.getByLabelText('Município'), { target: { value: 'Cidade' } });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
  });
  expect(writes).toHaveLength(0); // no unsolicited project creation
  fireEvent.click(screen.getByRole('button', { name: 'Salvar projeto' }));
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.change(screen.getByLabelText('Observações'), { target: { value: 'Casa em edição' } });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  fireEvent.change(screen.getByLabelText('Observações'), { target: { value: 'Casa final' } });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1499);
  });
  expect(writes).toHaveLength(1);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1);
  });
  expect(writes).toHaveLength(2);
  expect(writes[1].input.notes).toBe('Casa final');
  expect(screen.getByTestId('project-message')).toHaveTextContent('salvas automaticamente');
  failUpdate = true;
  fireEvent.change(screen.getByLabelText('Observações'), { target: { value: 'Casa offline' } });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10000);
  });
  expect(writes).toHaveLength(3);
  expect(screen.getByLabelText('Observações')).toHaveValue('Casa offline');
  expect(screen.getByTestId('project-message')).toHaveTextContent(
    'Não foi possível conectar ao serviço',
  );
});

test('save as new creates another ID without turning rename into an overwrite of the original', async () => {
  vi.useFakeTimers();
  const writes: { url: string; method: string; input: ProjectInput }[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      if ((options?.method === 'POST' && url.endsWith('/projects')) || options?.method === 'PUT') {
        const input = JSON.parse(String(options?.body));
        writes.push({ url, method: options!.method!, input });
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ...input,
            id: writes.length === 1 ? 'first' : 'second',
            version: 1,
            created_at: '2026-10-22T12:00:00Z',
            updated_at: '2026-10-22T12:00:00Z',
            standards_version: 'pending',
          }),
        };
      }
      return {
        ok: true,
        status: 200,
        json: async () =>
          url.endsWith('/validation/requirements')
            ? requirements
            : url.endsWith('/calculations/full')
              ? fixture
              : [],
      };
    }),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.change(screen.getByLabelText('Município'), { target: { value: 'Cidade' } });
  fireEvent.click(screen.getByRole('button', { name: 'Salvar projeto' }));
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.change(screen.getByLabelText('Nome do projeto'), { target: { value: 'Outra casa' } });
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2500);
  });
  expect(writes).toHaveLength(1); // rename must not autosave over the source before choosing new
  fireEvent.click(screen.getByRole('button', { name: 'Salvar como novo' }));
  await act(async () => {
    await Promise.resolve();
  });
  expect(writes).toHaveLength(2);
  expect(writes.map((item) => item.method)).toEqual(['POST', 'POST']);
  expect(writes[0].input.name).toBe('Novo projeto residencial');
  expect(writes[1].input.name).toBe('Outra casa');
  expect(screen.getByText(/Editando projeto salvo: Outra casa/)).toBeInTheDocument();
});

test('removes recent projects and loads the library only when requested', async () => {
  vi.useFakeTimers();
  const fetch = vi.fn(async (url: string) => ({
    ok: true,
    status: 200,
    json: async () => (url.endsWith('/validation/requirements') ? requirements : []),
  }));
  vi.stubGlobal('fetch', fetch);
  render(<Home />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  expect(screen.queryByText('Recentes')).toBeNull();
  expect(fetch.mock.calls.some(([url]) => url.includes('/projects/summaries?'))).toBe(false);
  fireEvent.click(screen.getByRole('button', { name: 'Projetos salvos' }));
  await act(async () => {
    await vi.advanceTimersByTimeAsync(250);
  });
  expect(screen.getByRole('region', { name: 'Projetos salvos' })).toBeInTheDocument();
  expect(fetch.mock.calls.some(([url]) => url.includes('/projects/summaries?'))).toBe(true);
});

test('failed saving exposes a correction action for the exact project field', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      if (url.endsWith('/projects') && options?.method === 'POST')
        return {
          ok: false,
          status: 422,
          json: async () => ({
            detail: [{ loc: ['body', 'municipality'], msg: 'Município obrigatório' }],
            notifications: [
              {
                id: 'invalid.municipality',
                category: 'error',
                location: ['Projeto'],
                problem: 'Município não informado.',
                solution: 'Informe o município.',
                affected_results: ['Salvar projeto'],
                target_id: 'project.municipality',
              },
            ],
          }),
        };
      return {
        ok: true,
        status: 200,
        json: async () =>
          url.endsWith('/validation/requirements')
            ? requirements
            : url.endsWith('/calculations/full')
              ? fixture
              : [],
      };
    }),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.click(screen.getByRole('button', { name: 'Salvar projeto' }));
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.click(
    screen.getByRole('button', { name: /Corrigir informação: Projeto · Município não informado/ }),
  );
  expect(screen.getByLabelText('Município')).toHaveFocus();
  expect(screen.getByTestId('project-message')).toHaveTextContent('Corrija os campos indicados');
});

test('save as without renaming creates an identifiable copy and adopts its returned inputs', async () => {
  const writes: ProjectInput[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, options?: RequestInit) => {
      if (options?.method === 'POST' && url.endsWith('/projects')) {
        const data = JSON.parse(String(options.body));
        writes.push(data);
        return {
          ok: true,
          status: 201,
          json: async () => ({
            ...data,
            id: `copy-${writes.length}`,
            version: 1,
            created_at: '2026-10-22T12:00:00Z',
            updated_at: '2026-10-22T12:00:00Z',
            standards_version: 'pending',
          }),
        };
      }
      return {
        ok: true,
        status: 200,
        json: async () => (url.endsWith('/validation/requirements') ? requirements : []),
      };
    }),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.change(screen.getByLabelText('Município'), { target: { value: 'Cidade' } });
  fireEvent.click(screen.getByRole('button', { name: 'Salvar projeto' }));
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.click(screen.getByLabelText('Mais ações do projeto'));
  fireEvent.click(screen.getByRole('button', { name: 'Salvar como novo' }));
  await act(async () => {
    await Promise.resolve();
  });
  expect(writes).toHaveLength(2);
  expect(writes[1].name).toBe('Novo projeto residencial · cópia');
  expect(screen.getByLabelText('Nome do projeto')).toHaveValue('Novo projeto residencial · cópia');
});

test('new project does not prompt for an untouched draft and cancellation preserves actual edits', async () => {
  const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => ({
      ok: true,
      status: 200,
      json: async () => (url.endsWith('/validation/requirements') ? requirements : []),
    })),
  );
  renderProject();
  await act(async () => {
    await Promise.resolve();
  });
  fireEvent.click(screen.getByLabelText('Mais ações do projeto'));
  fireEvent.click(screen.getByRole('button', { name: /^Novo projeto$/ }));
  expect(confirm).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText('Nome do projeto'), {
    target: { value: 'Rascunho importante' },
  });
  fireEvent.click(screen.getByLabelText('Mais ações do projeto'));
  fireEvent.click(screen.getByRole('button', { name: /^Novo projeto$/ }));
  expect(confirm).toHaveBeenCalledTimes(1);
  expect(screen.getByLabelText('Nome do projeto')).toHaveValue('Rascunho importante');
});

test('starts at home without calculating, and preserves the draft when returning home', async () => {
  vi.useFakeTimers();
  const fetch = vi.fn(async (url: string) => ({
    ok: true,
    status: 200,
    json: async () =>
      url.endsWith('/calculations/full') ? fixture : url.endsWith('/equipment') ? catalog : [],
  }));
  vi.stubGlobal('fetch', fetch);
  render(<Home />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
  expect(
    screen.getByRole('heading', { name: 'Seu próximo projeto começa aqui.' }),
  ).toBeInTheDocument();
  expect(screen.queryByLabelText('Nome do projeto')).toBeNull();
  expect(fetch.mock.calls.some(([url]) => url.endsWith('/calculations/full'))).toBe(false);
  fireEvent.click(screen.getByRole('button', { name: /^Criar novo projeto/ }));
  fireEvent.change(screen.getByLabelText('Nome do projeto'), {
    target: { value: 'Rascunho preservado' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Início' }));
  expect(screen.queryByLabelText('Nome do projeto')).toBeNull();
  expect(screen.getByText('Rascunho preservado')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Continuar edição' }));
  expect(screen.getByLabelText('Nome do projeto')).toHaveValue('Rascunho preservado');
});

test('connection retry recovers the startup services without replacing the draft', async () => {
  let online = false;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (!online) throw new TypeError('Failed to fetch');
      return {
        ok: true,
        status: 200,
        json: async () =>
          url.endsWith('/health')
            ? { status: 'ok' }
            : url.endsWith('/validation/requirements')
              ? requirements
              : [],
      };
    }),
  );
  renderProject();
  fireEvent.change(screen.getByLabelText('Nome do projeto'), {
    target: { value: 'Casa sem conexão' },
  });
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
  expect(screen.getByRole('button', { name: 'Tentar conexão novamente' })).toBeInTheDocument();
  online = true;
  fireEvent.click(screen.getByRole('button', { name: 'Tentar conexão novamente' }));
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
  expect(screen.queryByRole('button', { name: 'Tentar conexão novamente' })).toBeNull();
  expect(screen.getByLabelText('Nome do projeto')).toHaveValue('Casa sem conexão');
});

test('an equipment-only startup failure offers retry and restores the catalog', async () => {
  let failed = true;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url.endsWith('/equipment') && failed) throw new TypeError('Network error');
      return {
        ok: true,
        status: 200,
        json: async () => (url.endsWith('/equipment') ? catalog : []),
      };
    }),
  );
  render(<Home />);
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
  expect(screen.getByRole('alert')).toHaveTextContent('Catálogo de equipamentos indisponível');
  failed = false;
  fireEvent.click(screen.getByRole('button', { name: 'Tentar conexão novamente' }));
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
  expect(screen.queryByRole('alert')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: /^Criar novo projeto/ }));
  fireEvent.click(screen.getByRole('button', { name: 'Adicionar primeiro ambiente' }));
  expect(screen.getByLabelText('Adicionar equipamento em Novo ambiente')).toHaveTextContent(
    'Lâmpada LED',
  );
});

test('sidebar changes sections directly, resets library filters for trash and preserves the draft', async () => {
  vi.useFakeTimers();
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, status: 200, json: async () => [] })),
  );
  renderProject();
  fireEvent.change(screen.getByLabelText('Nome do projeto'), {
    target: { value: 'Edição mantida' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Projetos salvos' }));
  fireEvent.change(screen.getByLabelText('Pesquisar projetos'), {
    target: { value: 'Filtro da biblioteca' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Lixeira' }));
  expect(screen.getByRole('region', { name: 'Lixeira' })).toBeInTheDocument();
  expect(screen.getByLabelText('Pesquisar projetos')).toHaveValue('');
  expect(screen.queryByRole('dialog')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Projeto em edição' }));
  expect(screen.getByLabelText('Nome do projeto')).toHaveValue('Edição mantida');
});
