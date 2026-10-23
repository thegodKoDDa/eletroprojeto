import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { SectionNavigation } from '@/components/projects/SectionNavigation';
afterEach(cleanup);

test('workspace navigation keeps calculation memory inside the project', () => {
  const actions = {
    onHome: vi.fn(),
    onNew: vi.fn(),
    onProject: vi.fn(),
    onLibrary: vi.fn(),
    onTrash: vi.fn(),
  };
  const { rerender } = render(
    <SectionNavigation active="home" busy={false} hasProject={false} {...actions} />,
  );
  expect(screen.getByRole('button', { name: 'Início' })).toHaveAttribute('aria-current', 'page');
  expect(screen.queryByRole('button', { name: /Memória/ })).toBeNull();
  expect(screen.queryByRole('button', { name: 'Projeto em edição' })).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Projetos salvos' }));
  expect(actions.onLibrary).toHaveBeenCalledOnce();
  rerender(<SectionNavigation active="project" busy={false} hasProject {...actions} />);
  expect(screen.getByRole('button', { name: 'Projeto em edição' })).toHaveAttribute(
    'aria-current',
    'page',
  );
  expect(document.querySelectorAll('[aria-current]')).toHaveLength(1);
  rerender(<SectionNavigation active="project" busy hasProject {...actions} />);
  expect(screen.getByRole('button', { name: 'Novo projeto' })).toBeDisabled();
});
