import { StrictMode, useState } from 'react';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { ExperienceBoundary, ExperienceSwitcher } from '@/components/projects/ExperienceBoundary';
import { experienceStorageKey, fieldEmphasis, useExperience } from '@/lib/experience';
import { EnergyFields } from '@/components/equipment/EnergyFields';
import type { Load } from '@/lib/api';

beforeEach(() => {
  sessionStorage.clear();
  Object.defineProperties(HTMLDialogElement.prototype, {
    showModal: {
      configurable: true,
      value: function () {
        this.setAttribute('open', '');
      },
    },
    close: {
      configurable: true,
      value: function () {
        this.removeAttribute('open');
      },
    },
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function Editor() {
  const { profile } = useExperience();
  const [value, setValue] = useState('');
  return (
    <main>
      <h1 data-workspace-heading tabIndex={-1}>
        Editor {profile}
      </h1>
      <ExperienceSwitcher />
      <label>
        Minha edição
        <input value={value} onChange={(e) => setValue(e.target.value)} />
      </label>
    </main>
  );
}

test.each([
  ['beginner', 'USUÁRIO LEIGO'],
  ['professional', 'USUÁRIO PROFISSIONAL'],
  ['explore', 'ESTOU APENAS DANDO UMA OLHADA'],
] as const)(
  'fresh opening offers all choices and selecting %s starts a session',
  (profile, label) => {
    render(
      <StrictMode>
        <ExperienceBoundary owner="local">
          <Editor />
        </ExperienceBoundary>
      </StrictMode>,
    );
    expect(screen.queryByLabelText('Minha edição')).toBeNull();
    expect(screen.getAllByRole('button')).toHaveLength(3);
    fireEvent.click(screen.getByRole('button', { name: new RegExp(label) }));
    expect(screen.getByRole('heading', { name: `Editor ${profile}` })).toBeTruthy();
    expect(sessionStorage.getItem(experienceStorageKey('local'))).toBe(profile);
  },
);

test('switching presentation preserves mounted input, draft and focusable controls', () => {
  sessionStorage.setItem(experienceStorageKey('local'), 'beginner');
  render(
    <ExperienceBoundary owner="local">
      <Editor />
    </ExperienceBoundary>,
  );
  const input = screen.getByLabelText('Minha edição');
  fireEvent.change(input, { target: { value: 'Uma edição em andamento' } });
  fireEvent.click(screen.getByRole('button', { name: 'Alterar perfil' }));
  const dialog = screen.getByRole('dialog');
  fireEvent.click(within(dialog).getByRole('button', { name: /USUÁRIO PROFISSIONAL/ }));
  expect(screen.queryByRole('dialog')).toBeNull();
  expect(screen.getByLabelText('Minha edição')).toBe(input);
  expect(input).toHaveValue('Uma edição em andamento');
  expect(screen.getByRole('heading', { name: 'Editor professional' })).toBeTruthy();
});

test('cancel does not change the preference, persisted scope is isolated and invalid preferences reopen the chooser', () => {
  sessionStorage.setItem(experienceStorageKey('user:alice'), 'professional');
  const { unmount } = render(
    <ExperienceBoundary owner="user:alice">
      <Editor />
    </ExperienceBoundary>,
  );
  fireEvent.click(screen.getByRole('button', { name: 'Alterar perfil' }));
  fireEvent.click(screen.getByRole('button', { name: 'Voltar sem alterar' }));
  expect(screen.getByRole('heading', { name: 'Editor professional' })).toBeTruthy();
  unmount();
  sessionStorage.setItem(experienceStorageKey('user:bob'), 'invalid');
  render(
    <ExperienceBoundary owner="user:bob">
      <Editor />
    </ExperienceBoundary>,
  );
  expect(screen.queryByLabelText('Minha edição')).toBeNull();
});

test('storage unavailable never blocks choosing or switching a presentation', () => {
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
    throw new Error('blocked');
  });
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
    throw new Error('blocked');
  });
  render(
    <ExperienceBoundary owner="local">
      <Editor />
    </ExperienceBoundary>,
  );
  fireEvent.click(screen.getByRole('button', { name: /USUÁRIO LEIGO/ }));
  expect(screen.getByRole('heading', { name: 'Editor beginner' })).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Alterar perfil' }));
  fireEvent.click(
    within(screen.getByRole('dialog')).getByRole('button', { name: /DANDO UMA OLHADA/ }),
  );
  expect(screen.getByRole('heading', { name: 'Editor explore' })).toBeTruthy();
});

test('emphasis never invents mandatory fields or changes the original exploration presentation', () => {
  expect(fieldEmphasis('load.power_factor', 'explore', true)).toBeUndefined();
  expect(fieldEmphasis('project.name', 'beginner', true)).toBe('essential');
  expect(fieldEmphasis('project.notes', 'beginner', false)).toBeUndefined();
  expect(fieldEmphasis('load.parameters.usage_hours_per_day', 'beginner', false)).toBe(
    'recommended',
  );
  expect(fieldEmphasis('load.power_factor', 'professional', false)).toBe('technical');
});

test('energy fields open for the guided presentation and preserve valid zero usage', () => {
  sessionStorage.setItem(experienceStorageKey('local'), 'beginner');
  const onChange = vi.fn();
  const load = { id: 'a', quantity: 1, parameters: { monthly_energy_kwh: '0' } } as Load;
  render(
    <ExperienceBoundary owner="local">
      <EnergyFields load={load} onChange={onChange} />
    </ExperienceBoundary>,
  );
  expect(screen.getByTestId('equipment-energy')).toHaveAttribute('open');
  expect(screen.getByLabelText('Consumo de energia (kWh/mês)')).toHaveValue(0);
  expect(screen.getByLabelText('Horas de uso por dia')).toBeDisabled();
  expect(onChange).not.toHaveBeenCalled();
});

test('invalid dormant minutes remain visible and correctable when hours or stated energy takes priority', () => {
  render(
    <EnergyFields
      load={
        {
          id: 'dormant',
          quantity: 1,
          parameters: {
            monthly_energy_kwh: '0',
            usage_time_unit: 'hours',
            usage_minutes_per_day: '1441',
          },
        } as Load
      }
      onChange={() => {}}
    />,
  );
  expect(screen.getByLabelText('Minutos de uso por dia')).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByLabelText('Minutos de uso por dia')).not.toBeDisabled();
});
