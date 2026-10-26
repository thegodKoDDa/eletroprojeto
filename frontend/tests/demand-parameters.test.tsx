import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { DemandLoadParameters } from '@/components/calculations/DemandLoadParameters';
import { BathroomStudy } from '@/components/projects/BathroomStudy';
import type { ProjectInput } from '@/lib/api';
afterEach(cleanup);

test('motor data stays explicit and editing preserves other motor fields', () => {
  const onChange = vi.fn();
  render(
    <DemandLoadParameters
      name="Bomba"
      value={{
        reserve: false,
        air_conditioning_type: 'unconfirmed',
        group: 'd6',
        motor: { configuration: 'single_phase', shaft_power_cv: '1', source: 'Placa' },
      }}
      onChange={onChange}
    />,
  );
  fireEvent.change(screen.getByLabelText('Potência de eixo em cv de Bomba'), {
    target: { value: '1.5' },
  });
  expect(onChange).toHaveBeenCalledWith({
    motor: { configuration: 'single_phase', shaft_power_cv: '1.5', source: 'Placa' },
  });
});

test('central current and special VA remain separate and can be cleared', () => {
  const onChange = vi.fn();
  const { rerender } = render(
    <DemandLoadParameters
      name="Central"
      value={{
        reserve: false,
        group: 'd5',
        air_conditioning_type: 'central_unit',
        central: { maximum_total_current_a: '10', source: 'Fabricante' },
      }}
      onChange={onChange}
    />,
  );
  fireEvent.change(screen.getByLabelText('Corrente máxima total de Central (A por unidade)'), {
    target: { value: '' },
  });
  expect(onChange).toHaveBeenLastCalledWith({
    central: { maximum_total_current_a: null, source: 'Fabricante' },
  });
  rerender(
    <DemandLoadParameters
      name="Solda"
      value={{
        reserve: false,
        air_conditioning_type: 'unconfirmed',
        group: 'd7',
        special: { connection: 'standard' },
      }}
      onChange={onChange}
    />,
  );
  fireEvent.change(
    screen.getByLabelText('Potência elétrica aparente absorvida de Solda (VA por unidade)'),
    { target: { value: '2500' } },
  );
  expect(onChange).toHaveBeenLastCalledWith({
    special: { connection: 'standard', input_apparent_power_va: '2500' },
  });
});

test('bathroom envelope zero preserves other coordinates and opt-out is explicit', () => {
  const onChange = vi.fn();
  const input = {
    analysis_scope: 'installed',
    state: 'SP',
    utility: 'unconfirmed',
    residence_type: 'Casa',
    floors: 1,
    reference_voltage_v: null,
    notes: '',
    name: 'Casa',
    municipality: 'Cidade',
    environments: [
      {
        id: 'room',
        name: 'Banheiro',
        type: 'bathroom',
        lighting_points: 0,
        outlets: 0,
        loads: [],
        bathroom_geometry: {
          scope_confirmed: true,
          shower_x_m: '1',
          shower_y_m: '2',
          measurement_source: 'Planta',
          points: [{ id: 'one', name: 'Tomada', kind: 'socket', x_min_m: '1', x_max_m: '2' }],
        },
      },
    ],
  } as ProjectInput;
  const before = structuredClone(input);
  render(<BathroomStudy input={input} onChange={onChange} />);
  fireEvent.change(screen.getByLabelText('X mínimo de Tomada (m)'), { target: { value: '0' } });
  expect(onChange.mock.calls[0][0]).toBe('room');
  expect(onChange.mock.calls[0][1].bathroom_geometry.points[0]).toMatchObject({
    x_min_m: '0',
    x_max_m: '2',
  });
  expect(input).toEqual(before);
  fireEvent.click(screen.getByLabelText('Estudar localização em Banheiro'));
  expect(onChange).toHaveBeenLastCalledWith('room', { bathroom_geometry: null });
});
