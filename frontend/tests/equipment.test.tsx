import catalogFixture from './fixtures/catalog.json';
import requirements from './fixtures/requirements.json';
import { RequirementsContext, CalculationScopeContext } from '../src/components/ui/Field';
import { useState } from 'react';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { EquipmentEditor } from '../src/components/equipment/EquipmentEditor';
import { applyReference, newLoad, technicalDefaults, selectionCatalog } from '../src/lib/equipment';
import type { CatalogItem, Load } from '../src/lib/api';

afterEach(cleanup);
const reference: CatalogItem = {
  id: 'reference',
  name: 'Ar-condicionado',
  selection_name: 'Ar-condicionado',
  selection_default: true,
  category: 'Climatização',
  kind: 'specific_use',
  equipment_type: 'air_conditioner',
  technology: 'Inverter',
  unit: 'W',
  brand: 'LG',
  model: 'S3-W12JA33B',
  reference_power_w: '1130',
  voltage_v: '220',
  power_factor: null,
  power_rating: 'nominal',
  status: 'verified',
  source: 'LG',
  source_url: 'https://www.lg.com/br/ar-condicionado-residencial/dual-inverter-split/s3-w12ja33b/',
  document: 'Especificações gerais',
  verified_on: '2026-10-21',
  note: 'Modelo específico',
  parameters: {
    ...technicalDefaults(),
    cooling_capacity_btu_h: '12000',
    compressor: 'inverter',
    ac_type: 'split',
  },
};
function Editor({
  initial = newLoad(reference),
  operation = 'installed',
}: {
  initial?: Load;
  operation?: string;
}) {
  const [load, setLoad] = useState(initial);
  return (
    <RequirementsContext.Provider value={requirements}>
      <CalculationScopeContext.Provider value={operation}>
        <EquipmentEditor
          load={load}
          catalog={[reference]}
          onChange={(patch) => setLoad((old) => ({ ...old, ...patch }))}
          onRemove={vi.fn()}
          onDuplicate={vi.fn()}
        />
      </CalculationScopeContext.Provider>
    </RequirementsContext.Provider>
  );
}

test('autofills real reference and preserves manual override and restoration', () => {
  const original = structuredClone(reference);
  render(<Editor />);
  const power = screen.getByLabelText('Potência unitária (W)');
  expect(power).toHaveValue(1130);
  expect(screen.getByLabelText('Tensão nominal (V)')).toHaveValue(220);
  expect(screen.getByLabelText('Fator de potência')).toHaveValue(null);
  fireEvent.change(power, { target: { value: '850' } });
  expect(power).toHaveValue(850);
  expect(screen.getByText(/Valor de referência.*editado/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Restaurar sugestão' }));
  expect(power).toHaveValue(1130);
  expect(reference).toEqual(original);
});

test('changing thermal capacity invalidates a model suggestion instead of converting to electrical watts', () => {
  render(<Editor />);
  fireEvent.change(screen.getByLabelText('Capacidade térmica (BTU/h)'), {
    target: { value: '24000' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(null);
  expect(screen.queryByLabelText('Modelo', { exact: true })).not.toBeInTheDocument();
  expect(screen.getByLabelText('Capacidade térmica (BTU/h)')).toHaveValue(24000);
});

test('refrigeration energy does not replace the electrical input', () => {
  const load = { ...newLoad(), equipment_type: 'refrigeration' as const, unit_power_w: '130' };
  render(<Editor initial={load} />);
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  fireEvent.change(screen.getByLabelText('Consumo de energia (kWh/mês)'), {
    target: { value: '40' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(130);
  expect(screen.queryByLabelText('Capacidade térmica (BTU/h)')).not.toBeInTheDocument();
});

test('motor displays mechanical input only when selected', () => {
  render(<Editor initial={{ ...newLoad(), equipment_type: 'motor' }} />);
  expect(screen.queryByLabelText('Potência mecânica de saída')).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Unidade da potência'), { target: { value: 'cv' } });
  expect(screen.getByLabelText('Potência mecânica de saída')).toBeInTheDocument();
  expect(screen.getByLabelText('Rendimento do motor (0 a 1)')).toHaveValue(null);
  expect(screen.queryByLabelText('Potência unitária (W)')).not.toBeInTheDocument();
});

test('clearing quantity retains focus and does not replace the draft with zero', () => {
  render(<Editor />);
  const quantity = screen.getByLabelText('Quantidade');
  quantity.focus();
  fireEvent.change(quantity, { target: { value: '' } });
  expect(quantity).toHaveValue(null);
  expect(quantity).toHaveFocus();
});

test('catalog replacement preserves instance identity and quantity', () => {
  const load = newLoad();
  load.quantity = 3;
  const result = applyReference(load, reference);
  expect(result.id).toBe(load.id);
  expect(result.quantity).toBe(3);
  expect(result.unit_power_w).toBe('1130');
  expect(load.unit_power_w).toBeNull();
});

test('new equipment does not inherit another device voltage', () => {
  const load = newLoad();
  expect(load.voltage_v).toBeNull();
  expect(load.unit_power_w).toBeNull();
});

test('quantity edits keep the same source rating and switching to lighting selects its nature', () => {
  render(<Editor />);
  fireEvent.change(screen.getByLabelText('Quantidade'), { target: { value: '2' } });
  expect(screen.getByTestId('equipment-reference').querySelector('summary')).not.toHaveTextContent(
    'editado',
  );
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  fireEvent.change(screen.getByLabelText('Tipo de equipamento'), { target: { value: 'lighting' } });
  expect(screen.getByLabelText('Natureza')).toHaveValue('lighting');
  expect(screen.getByLabelText('Natureza')).toBeDisabled();
});

test('normal equipment shows three essential controls; advanced fields and commercial metadata stay secondary', () => {
  render(
    <Editor
      initial={{
        ...newLoad(),
        name: 'Televisor',
        equipment_type: 'television',
        brand: 'Dados antigos',
        model: 'ABC123',
        unit_power_w: '130',
      }}
    />,
  );
  const essential = screen.getByTestId('equipment-essential');
  expect(essential.querySelectorAll('input, select')).toHaveLength(3);
  expect(within(essential).getByLabelText('Quantidade')).toBeVisible();
  expect(screen.getByLabelText('Fator de potência')).not.toBeVisible();
  expect(screen.queryByLabelText('Marca')).not.toBeInTheDocument();
  expect(screen.queryByLabelText('Modelo', { exact: true })).not.toBeInTheDocument();
  expect(screen.getByTestId('equipment-advanced').querySelector('summary')).not.toHaveTextContent(
    'FP necessário',
  );
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  expect(screen.getByLabelText('Fator de potência')).toBeVisible();
  fireEvent.change(screen.getByLabelText('Fator de potência'), { target: { value: '0.8' } });
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  expect(screen.getByLabelText('Fator de potência')).not.toBeVisible();
  expect(screen.getByLabelText('Fator de potência')).toHaveValue(0.8);
  fireEvent.click(screen.getByText(/Origem dos dados/));
  expect(screen.getByText('Dados salvos: Dados antigos · ABC123')).toBeVisible();
});

test('generic selection is estimated and does not duplicate commercial variants', () => {
  const variant = {
    ...reference,
    id: 'variant',
    name: 'Marca e modelo comerciais',
    selection_default: false,
  };
  expect(selectionCatalog([reference, variant])).toEqual([reference]);
  expect(selectionCatalog([variant, reference])).toEqual([reference]);
  const load = newLoad(reference);
  expect(load.name).toBe('Ar-condicionado');
  expect(load.power_origin).toBe('user_estimate');
  expect(load.catalog_reference?.power_rating).toBe('nominal');
  expect(load.unit_power_w).toBe('1130');
  render(<Editor initial={load} />);
  expect(screen.getByRole('combobox', { name: 'Equipamento' })).toHaveTextContent(
    'Ar-condicionado',
  );
  expect(
    screen.queryByRole('combobox', { name: 'Trocar por referência do catálogo' }),
  ).not.toBeInTheDocument();
  expect(screen.getByTestId('equipment-reference')).not.toHaveAttribute('open');
  fireEvent.click(screen.getByText(/Valor de referência/));
  expect(screen.getByRole('link', { name: /LG/ })).toHaveAttribute('href', reference.source_url);
});

test('AC capacity restores electrical watts only when an actual documented match exists', () => {
  render(<Editor />);
  fireEvent.change(screen.getByLabelText('Capacidade térmica (BTU/h)'), {
    target: { value: '24000' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(null);
  expect(screen.getByText(/Potência unitária \(W\): preenchimento necessário/)).toBeVisible();
  fireEvent.change(screen.getByLabelText('Capacidade térmica (BTU/h)'), {
    target: { value: '12000' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(1130);
});

test('motor efficiency remains visible and marked as required in mechanical mode', () => {
  render(<Editor initial={{ ...newLoad(), equipment_type: 'motor' }} />);
  fireEvent.change(screen.getByLabelText('Unidade da potência'), { target: { value: 'hp' } });
  expect(screen.getByLabelText('Potência mecânica de saída')).toBeVisible();
  expect(screen.getByLabelText('Rendimento do motor (0 a 1)')).toBeVisible();
  expect(screen.getByText(/Rendimento do motor \(0 a 1\): preenchimento necessário/)).toBeVisible();
  expect(screen.getByTestId('equipment-advanced')).not.toHaveAttribute('open');
});

test('capacity matches a documented non-default variant without adding commercial selectors', () => {
  const ref9000: CatalogItem = {
    ...reference,
    id: 'lg-ac-9000-s3q09aa33a',
    selection_default: false,
    reference_power_w: '800',
    model: 'S3-Q09AA33A',
    parameters: { ...technicalDefaults(), ...reference.parameters, cooling_capacity_btu_h: '9000' },
  };
  function MultiReferenceEditor() {
    const [load, setLoad] = useState(newLoad(reference));
    return (
      <RequirementsContext.Provider value={requirements}>
        <EquipmentEditor
          load={load}
          catalog={[reference, ref9000]}
          onChange={(patch) => setLoad((old) => ({ ...old, ...patch }))}
          onRemove={vi.fn()}
          onDuplicate={vi.fn()}
        />
      </RequirementsContext.Provider>
    );
  }
  render(<MultiReferenceEditor />);
  fireEvent.change(screen.getByLabelText('Capacidade térmica (BTU/h)'), {
    target: { value: '9000' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(800);
  expect(screen.getByLabelText('Capacidade térmica (BTU/h)')).toHaveValue(9000);
  expect(screen.getByLabelText('Fator de potência')).toHaveValue(null);
  expect(screen.queryByLabelText('Modelo', { exact: true })).toBeNull();
});

test('required marker and warning track validity in both directions without losing focus', () => {
  render(<Editor initial={{ ...newLoad(), equipment_type: 'shower' }} />);
  const power = screen.getByLabelText('Potência unitária (W)');
  expect(power).toHaveAttribute('aria-required', 'true');
  expect(power.closest('label')?.querySelector('.required-mark')).toHaveTextContent('*');
  expect(power).toHaveAttribute('aria-invalid', 'true');
  power.focus();
  fireEvent.change(power, { target: { value: '-1' } });
  expect(power).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByText('Potência unitária (W): valor inválido.')).toBeVisible();
  fireEvent.change(power, { target: { value: '0' } });
  expect(power).toHaveAttribute('aria-invalid', 'true');
  fireEvent.change(power, { target: { value: '7500' } });
  expect(power).toHaveAttribute('aria-invalid', 'false');
  expect(screen.queryByText(/Potência unitária.*preenchimento necessário/)).toBeNull();
  expect(power).toHaveFocus();
  fireEvent.change(power, { target: { value: '' } });
  expect(power).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByText(/Potência unitária.*preenchimento necessário/)).toBeVisible();
});

test('optional thermal capacity is unmarked and mechanical efficiency becomes required only in mechanical mode', () => {
  render(<Editor />);
  expect(
    screen
      .getByLabelText('Capacidade térmica (BTU/h)')
      .closest('label')
      ?.querySelector('.required-mark'),
  ).toBeNull();
  expect(screen.getByLabelText('Tensão nominal (V)')).toHaveAttribute('aria-required', 'false');
});

test('explicit resistive hypothesis makes FP entry optional while retaining current requirements', () => {
  render(<Editor operation="current" initial={{ ...newLoad(), equipment_type: 'shower' }} />);
  fireEvent.click(screen.getByText(/Configurações avançadas/));
  const fp = screen.getByLabelText('Fator de potência');
  expect(fp).toHaveAttribute('aria-required', 'true');
  fireEvent.click(screen.getByLabelText('Adotar hipótese de carga resistiva (FP=1)'));
  expect(fp).toHaveAttribute('aria-required', 'false');
  expect(fp.closest('label')?.querySelector('.required-mark')).toBeNull();
  expect(screen.getByLabelText('Configuração para corrente')).toHaveAttribute(
    'aria-required',
    'true',
  );
});

test('a manually edited estimate survives capacity changes without requiring nameplate origin', () => {
  render(<Editor />);
  const power = screen.getByLabelText('Potência unitária (W)');
  fireEvent.change(power, { target: { value: '850' } });
  fireEvent.change(screen.getByLabelText('Capacidade térmica (BTU/h)'), {
    target: { value: '9000' },
  });
  expect(power).toHaveValue(850);
  fireEvent.click(screen.getByRole('button', { name: 'Restaurar sugestão' }));
  expect(power).toHaveValue(1130);
  expect(screen.getByLabelText('Capacidade térmica (BTU/h)')).toHaveValue(12000);
});

test('requesting current marks only its extra dependencies while W remains editable', () => {
  const load = newLoad(reference);
  const view = render(<Editor initial={load} operation="installed" />);
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveAttribute('aria-required', 'true');
  expect(screen.getByLabelText('Fator de potência')).toHaveAttribute('aria-required', 'false');
  view.rerender(<Editor initial={load} operation="current" />);
  expect(screen.getByLabelText('Fator de potência')).toHaveAttribute('aria-required', 'true');
  expect(screen.getByLabelText('Tensão nominal (V)')).toHaveAttribute('aria-required', 'true');
  expect(screen.getByLabelText('Capacidade térmica (BTU/h)')).toHaveAttribute(
    'aria-required',
    'false',
  );
});

test('documented 18000/24000/30000 capacities update watts; custom and manual values remain safe', () => {
  const refs = catalogFixture.filter(
    (item) => item.equipment_type === 'air_conditioner',
  ) as CatalogItem[];
  function FullCatalogEditor() {
    const [load, setLoad] = useState(
      newLoad(refs.find((item) => item.id === 'lg-ac-12000-s3w12ja33b')!),
    );
    return (
      <EquipmentEditor
        load={load}
        catalog={refs}
        onChange={(patch) => setLoad((old) => ({ ...old, ...patch }))}
        onRemove={vi.fn()}
        onDuplicate={vi.fn()}
      />
    );
  }
  render(<FullCatalogEditor />);
  const capacity = screen.getByLabelText('Capacidade térmica (BTU/h)');
  const power = screen.getByLabelText('Potência unitária (W)');
  for (const [btu, watts] of [
    ['9000', 800],
    ['12000', 1130],
    ['18000', 1583],
    ['24000', 2170],
    ['30000', 2430],
  ] as const) {
    fireEvent.change(capacity, { target: { value: btu } });
    expect(power).toHaveValue(watts);
    expect(screen.getByLabelText('Fator de potência')).toHaveValue(null);
  }
  fireEvent.change(capacity, { target: { value: '15000' } });
  expect(power).toHaveValue(null);
  expect(capacity).toHaveValue(15000);
  fireEvent.change(power, { target: { value: '1777' } });
  fireEvent.change(capacity, { target: { value: '24000' } });
  expect(power).toHaveValue(1777);
  expect(screen.getByLabelText('Tensão nominal (V)')).toHaveValue(220);
});

test('AC identity change rechecks suggestions without losing custom name, voltage or FP', () => {
  const refs = catalogFixture.filter(
    (item) => item.equipment_type === 'air_conditioner',
  ) as CatalogItem[];
  function CustomAC() {
    const original = newLoad(refs.find((item) => item.id === 'lg-ac-12000-s3w12ja33b')!);
    const [load, setLoad] = useState<Load>({
      ...original,
      name: 'AC da suíte',
      voltage_v: '230',
      power_factor: '0.9',
      parameters: { ...technicalDefaults(), ...original.parameters, nameplate_current_a: '7' },
    });
    return (
      <EquipmentEditor
        load={load}
        catalog={refs}
        onChange={(patch) => setLoad((old) => ({ ...old, ...patch }))}
        onRemove={vi.fn()}
        onDuplicate={vi.fn()}
      />
    );
  }
  render(<CustomAC />);
  fireEvent.change(screen.getByLabelText('Capacidade térmica (BTU/h)'), {
    target: { value: '24000' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(2170);
  expect(screen.getByLabelText('Identificação da carga')).toHaveValue('AC da suíte');
  expect(screen.getByLabelText('Tensão nominal (V)')).toHaveValue(230);
  expect(screen.getByLabelText('Fator de potência')).toHaveValue(0.9);
  expect(screen.getByText(/Corrente nominal de placa \(A\): 7/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Compressor'), { target: { value: 'conventional' } });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(null);
});

test('computer reference never caps a manually adopted 600 W load', () => {
  const computer = catalogFixture.find((item) => item.id === 'enel-computer') as CatalogItem;
  render(<Editor initial={newLoad(computer)} />);
  const power = screen.getByLabelText('Potência unitária (W)');
  expect(power).toHaveValue(300);
  fireEvent.change(power, { target: { value: '600' } });
  expect(power).toHaveValue(600);
  expect(power).not.toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByText(/capacidade da fonte do computador/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Quantidade'), { target: { value: '2' } });
  expect(power).toHaveValue(600);
});

test('automatic capacity matching preserves manual quantity and category', () => {
  const refs = catalogFixture.filter(
    (item) => item.equipment_type === 'air_conditioner',
  ) as CatalogItem[];
  function AC() {
    const [load, setLoad] = useState<Load>({
      ...newLoad(refs.find((item) => item.id === 'lg-ac-12000-s3w12ja33b')!),
      quantity: 3,
      category: 'Climatização da suíte',
    });
    return (
      <EquipmentEditor
        load={load}
        catalog={refs}
        onChange={(patch) => setLoad((old) => ({ ...old, ...patch }))}
        onRemove={vi.fn()}
        onDuplicate={vi.fn()}
      />
    );
  }
  render(<AC />);
  fireEvent.change(screen.getByLabelText('Capacidade térmica (BTU/h)'), {
    target: { value: '24000' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(2170);
  expect(screen.getByLabelText('Quantidade')).toHaveValue(3);
  expect(screen.getByLabelText('Categoria')).toHaveValue('Climatização da suíte');
});

test('voltage becomes essential only for current without losing its value', () => {
  const view = render(<Editor />);
  expect(screen.getByLabelText('Tensão nominal (V)')).not.toBeVisible();
  view.rerender(<Editor operation="current" />);
  expect(screen.getByLabelText('Tensão nominal (V)')).toBeVisible();
  expect(screen.getByLabelText('Tensão nominal (V)')).toHaveValue(220);
  expect(screen.getAllByLabelText('Tensão nominal (V)')).toHaveLength(1);
});

test('energy fields are optional and monthly measurement takes priority without deleting hours', () => {
  render(<Editor />);
  fireEvent.click(screen.getByText('Consumo mensal (opcional)'));
  const hours = screen.getByLabelText('Horas de uso por dia');
  const days = screen.getByLabelText('Dias de uso por mês');
  fireEvent.change(hours, { target: { value: '5' } });
  fireEvent.change(days, { target: { value: '30' } });
  const monthly = screen.getByLabelText('Consumo de energia (kWh/mês)');
  fireEvent.change(monthly, { target: { value: '40' } });
  expect(hours).toBeDisabled();
  expect(days).toBeDisabled();
  expect(hours).toHaveValue(5);
  fireEvent.change(monthly, { target: { value: '' } });
  expect(hours).toBeEnabled();
  expect(days).toHaveValue(30);
  fireEvent.change(hours, { target: { value: '25' } });
  expect(hours).toHaveAttribute('aria-invalid', 'true');
  fireEvent.change(monthly, { target: { value: '40' } });
  expect(hours).toBeEnabled();
  expect(days).toBeEnabled();
  fireEvent.change(hours, { target: { value: '0' } });
  expect(hours).toHaveAttribute('aria-invalid', 'false');
});

test('removed informational controls preserve old plate data in references', () => {
  render(
    <Editor
      initial={{
        ...newLoad(),
        equipment_type: 'television',
        parameters: {
          ...technicalDefaults(),
          screen_inches: '55',
          microwave_output_w: '800',
          starting_current_a: '10',
        },
      }}
    />,
  );
  expect(screen.queryByLabelText('Tamanho da tela (polegadas)')).toBeNull();
  expect(screen.queryByLabelText('Tecnologia / tipo')).toBeNull();
  fireEvent.click(screen.getByText(/Origem dos dados/));
  expect(screen.getByText(/Tela \(polegadas\): 55/)).toBeVisible();
  expect(screen.getByText(/Corrente de partida \(A\): 10/)).toBeVisible();
});

test('saved reference URLs do not expose executable links', () => {
  render(<Editor initial={newLoad({ ...reference, source_url: 'javascript:alert(1)' })} />);
  fireEvent.click(screen.getByText(/Valor de referência/));
  expect(screen.queryByRole('link')).toBeNull();
});

test('restoring technical data preserves monthly energy and usage schedules', () => {
  const load = newLoad(reference);
  load.parameters = {
    ...technicalDefaults(),
    ...load.parameters,
    monthly_energy_kwh: '42',
    usage_hours_per_day: '4',
    usage_days_per_month: 20,
  };
  render(<Editor initial={load} />);
  fireEvent.change(screen.getByLabelText('Potência unitária (W)'), { target: { value: '850' } });
  fireEvent.click(screen.getByRole('button', { name: 'Restaurar sugestão' }));
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(1130);
  expect(screen.getByLabelText('Consumo de energia (kWh/mês)')).toHaveValue(42);
  expect(screen.getByLabelText('Horas de uso por dia')).toHaveValue(4);
  expect(screen.getByLabelText('Dias de uso por mês')).toHaveValue(20);
});

test('documented shower variants are selectable without losing usage or manual power', () => {
  const catalog = catalogFixture as CatalogItem[];
  const shower = catalog.find((item) => item.id === 'lorenzetti-advanced-220-7500')!;
  function VariantEditor() {
    const [load, setLoad] = useState(newLoad(shower));
    return (
      <EquipmentEditor
        load={load}
        catalog={catalog}
        onChange={(patch) => setLoad((old) => ({ ...old, ...patch }))}
        onRemove={vi.fn()}
        onDuplicate={vi.fn()}
      />
    );
  }
  render(<VariantEditor />);
  fireEvent.change(screen.getByLabelText('Horas de uso por dia'), { target: { value: '0.5' } });
  fireEvent.change(screen.getByLabelText('Dias de uso por mês'), { target: { value: '30' } });
  fireEvent.change(screen.getByLabelText('Variante de referência'), {
    target: { value: 'lorenzetti-advanced-127-5500' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(5500);
  expect(screen.getByLabelText('Tensão nominal (V)')).toHaveValue(127);
  expect(screen.getByLabelText('Horas de uso por dia')).toHaveValue(0.5);
  fireEvent.change(screen.getByLabelText('Potência unitária (W)'), { target: { value: '5000' } });
  fireEvent.change(screen.getByLabelText('Variante de referência'), {
    target: { value: 'lorenzetti-advanced-220-7500' },
  });
  expect(screen.getByLabelText('Potência unitária (W)')).toHaveValue(5000);
  expect(screen.getByLabelText('Tensão nominal (V)')).toHaveValue(220);
  expect(screen.getByLabelText('Dias de uso por mês')).toHaveValue(30);
  expect(shower.reference_power_w).toBe('7500');
});

test.each([{ monthly_energy_kwh: '35' }, { annual_energy_kwh: '0' }])(
  'declared energy makes missing power optional without inventing it: %j',
  (parameters) => {
    render(
      <Editor
        initial={{
          ...newLoad(reference),
          unit_power_w: null,
          parameters: { ...technicalDefaults(), ...parameters },
        }}
      />,
    );
    const power = screen.getByLabelText('Potência unitária (W)');
    expect(power).toHaveValue(null);
    expect(power).toHaveAttribute('aria-required', 'false');
    expect(power).toHaveAttribute('aria-invalid', 'false');
  },
);
