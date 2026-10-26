import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { CircuitStudy } from '@/components/projects/CircuitStudy';
import type { ProjectInput } from '@/lib/api';

afterEach(cleanup);
const input: ProjectInput = {
  name: 'Casa',
  municipality: 'Cidade',
  analysis_scope: 'installed',
  state: 'SP',
  utility: 'unconfirmed',
  residence_type: 'Casa',
  floors: 1,
  reference_voltage_v: null,
  notes: '',
  environments: [
    {
      id: 'room',
      name: 'Sala',
      type: 'living',
      lighting_points: 1,
      outlets: 0,
      loads: [
        {
          id: 'load',
          name: 'Lâmpada',
          category: 'Iluminação',
          technology: '',
          kind: 'lighting',
          equipment_type: 'lighting',
          quantity: 2,
          source: 'Manual',
          power_origin: 'nameplate',
          brand: '',
          model: '',
          manual_override: false,
          power_user_edited: false,
          parameters: {
            power_mode: 'electrical',
            compressor: 'unknown',
            mechanical_unit: 'cv',
            configuration: 'unknown',
            assume_resistive: false,
          },
        },
      ],
    },
  ],
  circuits: [
    {
      id: 'one',
      insulation: 'PVC70',
      air_layout: 'unknown',
      buried_reference_confirmed: false,
      terminals_90c_confirmed: false,
      name: 'Iluminação',
      configuration: 'single_phase',
      purpose: 'lighting',
      method: 'unknown',
      scope_confirmed: false,
      voltage_drop_model_confirmed: false,
      overload_duration_confirmed: false,
      supply_origin: 'unknown',
      load_ids: ['load', 'missing'],
    },
  ],
};

test('missing associations can be repaired without changing existing loads', () => {
  const onChange = vi.fn();
  render(<CircuitStudy input={input} onChange={onChange} onEntryChange={vi.fn()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Remover associações de cargas ausentes' }));
  expect(onChange.mock.calls[0][0][0].load_ids).toEqual(['load']);
  expect(input.circuits?.[0].load_ids).toEqual(['load', 'missing']);
});

test('an assigned load is unavailable to a second circuit but can still be unchecked in its own', () => {
  const next = {
    ...input,
    circuits: [
      ...input.circuits!,
      { ...input.circuits![0], id: 'two', name: 'Outro circuito', load_ids: [] },
    ],
  };
  render(<CircuitStudy input={next} onChange={vi.fn()} onEntryChange={vi.fn()} />);
  const options = screen.getAllByRole('checkbox', { name: /Sala · Lâmpada/ });
  expect(options[0]).toBeEnabled();
  expect(options[0]).toBeChecked();
  expect(options[1]).toBeDisabled();
  expect(options[1]).not.toBeChecked();
});

test('breaker ratings accept decimal commas and reject hexadecimal input before the API', () => {
  const onChange = vi.fn();
  const props = { onChange, onEntryChange: vi.fn() };
  const { rerender } = render(<CircuitStudy input={input} {...props} />);
  const field = screen.getByLabelText('Correntes nominais disponíveis (A; separe por ;)');
  fireEvent.change(field, { target: { value: '16,5; 25' } });
  expect(onChange.mock.lastCall?.[0][0].breaker_ratings_a).toEqual(['16.5', '25']);
  rerender(<CircuitStudy input={{ ...input, circuits: onChange.mock.lastCall?.[0] }} {...props} />);
  expect(field).toHaveValue('16,5; 25');
  fireEvent.change(field, { target: { value: '0x10' } });
  rerender(<CircuitStudy input={{ ...input, circuits: onChange.mock.lastCall?.[0] }} {...props} />);
  expect(field).toHaveAttribute('aria-invalid', 'true');
  expect(onChange.mock.lastCall?.[0][0].breaker_ratings_a).toEqual([]);
  rerender(
    <CircuitStudy
      input={{ ...input, circuits: [{ ...input.circuits![0], breaker_ratings_a: ['32'] }] }}
      {...props}
    />,
  );
  expect(field).toHaveValue('32');
  expect(field).not.toHaveAttribute('aria-invalid');
});

test('90 degree cable inputs preserve manual data and expose documented coordination', () => {
  const onChange = vi.fn();
  const next: ProjectInput = {
    ...input,
    circuits: [{ ...input.circuits![0], insulation: 'XLPE90' }],
  };
  render(<CircuitStudy input={next} onChange={onChange} onEntryChange={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Resistividade do cobre a 90 °C (Ω·mm²/m)'), {
    target: { value: '0.025' },
  });
  expect(onChange.mock.lastCall?.[0][0].hot_resistivity_ohm_mm2_m).toBe('0.025');
  expect(input.circuits?.[0].insulation).toBe('PVC70');
  fireEvent.change(screen.getByLabelText('Limite de seletividade do par (kA)'), {
    target: { value: '6' },
  });
  expect(onChange.mock.lastCall?.[0][0].protections.selectivity).toMatchObject({
    limit_ka: '6',
    conditions_confirmed: false,
  });
  fireEvent.change(screen.getByLabelText('Onda exigida no estudo'), {
    target: { value: '10/350' },
  });
  expect(onChange.mock.lastCall?.[0][0].protections.surge.requirement_waveform).toBe('10/350');
});

test('changing physical cable conditions requires a new scope confirmation while preserving numeric data', () => {
  const onChange = vi.fn();
  const next: ProjectInput = {
    ...input,
    circuits: [
      {
        ...input.circuits![0],
        scope_confirmed: true,
        terminals_90c_confirmed: true,
        length_m: '25',
      },
    ],
  };
  render(<CircuitStudy input={next} onChange={onChange} onEntryChange={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Isolação do cabo de cobre'), {
    target: { value: 'EPR90' },
  });
  expect(onChange.mock.lastCall?.[0][0]).toMatchObject({
    insulation: 'EPR90',
    scope_confirmed: false,
    terminals_90c_confirmed: false,
    length_m: '25',
  });
});
