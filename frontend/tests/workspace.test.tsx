import { render, screen, fireEvent, cleanup, act } from '@testing-library/react';
import { it, expect, vi, afterEach, beforeEach } from 'vitest';
import { ProjectWorkspace } from '@/components/projects/ProjectWorkspace';
import type { Project } from '@/lib/api';

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
const project = {
  id: 'project-a',
  name: 'Casa A',
  municipality: 'Cidade',
  version: 3,
  updated_at: '2026-10-21T12:00:00Z',
} as Project;
const actions = () => ({
  onOpen: vi.fn(),
  onDelete: vi.fn(),
  onDuplicate: vi.fn(),
  onRestore: vi.fn(),
  onPurge: vi.fn(),
  onNew: vi.fn(),
});
const tick = async () => {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(250);
  });
};
function list(rows: Project[]) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, status: 200, json: async () => rows })),
  );
}

it('targets the exact project and blocks actions while an operation is pending', async () => {
  list([project]);
  const callbacks = actions();
  const view = render(
    <ProjectWorkspace archived={false} busy={false} revision={0} {...callbacks} />,
  );
  await tick();
  fireEvent.click(screen.getByRole('button', { name: 'Excluir Casa A' }));
  fireEvent.click(screen.getByRole('button', { name: 'Duplicar Casa A' }));
  expect(callbacks.onDelete).toHaveBeenCalledWith(project);
  expect(callbacks.onDuplicate).toHaveBeenCalledWith(project);
  view.rerender(<ProjectWorkspace archived={false} busy revision={0} {...callbacks} />);
  expect(screen.getByRole('button', { name: 'Excluir Casa A' })).toBeDisabled();
});

it('shows the library as a page and searches the full collection', async () => {
  const rows = Array.from({ length: 5 }, (_, i) => ({
    ...project,
    id: `project-${i}`,
    name: `Casa ${i}`,
  }));
  list(rows);
  render(<ProjectWorkspace archived={false} busy={false} revision={0} {...actions()} />);
  await tick();
  expect(screen.queryByRole('dialog')).toBeNull();
  expect(screen.getByRole('region', { name: 'Projetos salvos' })).toBeInTheDocument();
  expect(screen.getAllByRole('article')).toHaveLength(5);
  expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain('limit=21');
  fireEvent.change(screen.getByLabelText('Pesquisar projetos'), { target: { value: 'Casa 4' } });
  expect(screen.queryAllByRole('article')).toHaveLength(0);
  await tick();
  expect(String(vi.mocked(fetch).mock.calls.at(-1)?.[0])).toContain('q=Casa+4');
});

it('offers restore and confirmed purge only in trash, with deletion dates', async () => {
  const removed = { ...project, deleted_at: '2026-10-22T14:30:00Z' };
  list([removed]);
  const callbacks = actions();
  render(<ProjectWorkspace archived busy={false} revision={0} {...callbacks} />);
  await tick();
  expect(screen.getByText(/Excluído em/)).toHaveTextContent('22/10/2026');
  expect(screen.queryByRole('button', { name: 'Duplicar Casa A' })).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Restaurar Casa A' }));
  fireEvent.click(screen.getByRole('button', { name: 'Excluir definitivamente Casa A' }));
  expect(callbacks.onRestore).toHaveBeenCalledWith(removed);
  expect(callbacks.onPurge).toHaveBeenCalledWith(removed);
});

it('does not show active cached projects as deleted during a filter transition', async () => {
  list([project]);
  const callbacks = actions();
  const view = render(
    <ProjectWorkspace archived={false} busy={false} revision={0} {...callbacks} />,
  );
  await tick();
  view.rerender(<ProjectWorkspace archived busy={false} revision={0} {...callbacks} />);
  expect(screen.queryByText('Casa A')).toBeNull();
  expect(screen.getByText('Carregando projetos…')).toBeInTheDocument();
});

it('does not confuse an empty collection with an empty search or a loading request', async () => {
  list([]);
  const callbacks = actions();
  render(<ProjectWorkspace archived={false} busy={false} revision={0} {...callbacks} />);
  expect(screen.queryByText('Você ainda não tem projetos salvos')).toBeNull();
  await tick();
  fireEvent.click(screen.getByRole('button', { name: 'Criar novo projeto' }));
  expect(callbacks.onNew).toHaveBeenCalledOnce();
  fireEvent.change(screen.getByLabelText('Pesquisar projetos'), { target: { value: 'ausente' } });
  await tick();
  expect(screen.getByText('Nenhum projeto encontrado')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Limpar pesquisa' }));
  expect(screen.getByLabelText('Pesquisar projetos')).toHaveValue('');
});

it('recovers a failed list without dropping the current search', async () => {
  let online = false;
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => {
      if (!online) throw new TypeError('network');
      return { ok: true, status: 200, json: async () => [project] };
    }),
  );
  render(<ProjectWorkspace archived={false} busy={false} revision={0} {...actions()} />);
  fireEvent.change(screen.getByLabelText('Pesquisar projetos'), { target: { value: 'Casa' } });
  await tick();
  expect(screen.getByRole('alert')).toBeInTheDocument();
  online = true;
  fireEvent.click(screen.getByRole('button', { name: 'Tentar carregar novamente' }));
  await tick();
  expect(screen.getByLabelText('Pesquisar projetos')).toHaveValue('Casa');
  expect(screen.getByRole('button', { name: 'Casa A' })).toBeInTheDocument();
});

it('returns to the previous page when the last item on the current page is removed', async () => {
  const first = Array.from({ length: 21 }, (_, i) => ({
    ...project,
    id: `${i}`,
    name: `Casa ${i}`,
  }));
  let removed = false;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => ({
      ok: true,
      status: 200,
      json: async () => (url.includes('offset=20') ? (removed ? [] : [project]) : first),
    })),
  );
  const callbacks = actions();
  const view = render(
    <ProjectWorkspace archived={false} busy={false} revision={0} {...callbacks} />,
  );
  await tick();
  fireEvent.click(screen.getByRole('button', { name: 'Próxima' }));
  await tick();
  expect(screen.getByText('Página 2')).toBeInTheDocument();
  removed = true;
  view.rerender(<ProjectWorkspace archived={false} busy={false} revision={1} {...callbacks} />);
  await tick();
  await tick();
  expect(screen.getByText('Página 1')).toBeInTheDocument();
  expect(screen.getAllByRole('article')).toHaveLength(20);
});
