import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { ProjectActions } from '@/components/layout/ProjectActions';
afterEach(cleanup);
it('keeps save and PDF visible, with independent actions in a secondary disclosure', () => {
  const actions = {
    onSave: vi.fn(),
    onSaveAs: vi.fn(),
    onNew: vi.fn(),
    onPdf: vi.fn(),
    onJson: vi.fn(),
    onDelete: vi.fn(),
    onCheck: vi.fn(),
  };
  render(
    <ProjectActions
      saved
      busy={false}
      saving={false}
      exporting={false}
      canExport
      canExportPdf
      {...actions}
    />,
  );
  expect(screen.getByRole('button', { name: 'Salvar projeto' })).toBeVisible();
  expect(screen.getByRole('button', { name: 'Exportar PDF' })).toBeVisible();
  const menu = screen.getByLabelText('Mais ações do projeto');
  fireEvent.click(menu);
  fireEvent.click(screen.getByText('Salvar como novo'));
  expect(actions.onSaveAs).toHaveBeenCalledTimes(1);
  expect(actions.onSave).not.toHaveBeenCalled();
  fireEvent.click(menu);
  fireEvent.click(screen.getByText('Exportar JSON'));
  expect(actions.onJson).toHaveBeenCalledTimes(1);
});
it('disables exports until their own calculation dependencies exist', () => {
  const noop = vi.fn();
  render(
    <ProjectActions
      saved={false}
      busy
      saving
      exporting={false}
      canExport
      canExportPdf={false}
      onNew={noop}
      onSave={noop}
      onSaveAs={noop}
      onPdf={noop}
      onJson={noop}
      onDelete={noop}
      onCheck={noop}
    />,
  );
  expect(screen.getByRole('button', { name: 'Salvando…' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Exportar PDF' })).toBeDisabled();
});

it('locks all project actions and prevents opening the menu during export', () => {
  const noop = vi.fn();
  render(
    <ProjectActions
      saved
      busy={false}
      saving={false}
      exporting
      canExport
      canExportPdf
      onNew={noop}
      onSave={noop}
      onSaveAs={noop}
      onPdf={noop}
      onJson={noop}
      onDelete={noop}
      onCheck={noop}
    />,
  );
  expect(screen.getByRole('button', { name: 'Salvar projeto' })).toBeDisabled();
  const summary = screen.getByLabelText('Mais ações do projeto');
  fireEvent.click(summary);
  expect(summary).toHaveAttribute('aria-disabled', 'true');
  expect(summary.closest('details')).not.toHaveAttribute('open');
  expect(screen.getByRole('button', { name: 'Exportar JSON', hidden: true })).toBeDisabled();
});
