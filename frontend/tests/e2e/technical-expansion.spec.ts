import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFile } from 'node:fs/promises';

test('special demand, three-phase circuits and bathroom envelopes persist and export', async ({
  page,
  request,
}) => {
  const name = `Ampliação técnica QA ${Date.now()}`;
  const phaseLoad = '22222222-2222-4222-8222-222222222224';
  const response = await request.post('http://127.0.0.1:8010/api/v1/projects', {
    data: {
      name,
      municipality: 'Local QA',
      state: 'SP',
      utility: 'energisa_sul_sudeste',
      energisa_demand: {
        enabled: true,
        unit_type: 'individual_residential',
        has_signage_or_display_lighting: false,
        simultaneous_lighting_outlets: true,
        confirmed_absent_groups: ['d2', 'd3', 'd4'],
      },
      environments: [
        {
          name: 'Banheiro QA',
          type: 'bathroom',
          bathroom_geometry: {
            scope_confirmed: true,
            shower_x_m: '0',
            shower_y_m: '0',
            measurement_source: 'Planta de teste',
            points: [
              {
                id: 'point',
                name: 'Tomada QA',
                kind: 'socket',
                x_min_m: '1',
                x_max_m: '1.1',
                y_min_m: '0',
                y_max_m: '0.1',
                z_min_m: '1',
                z_max_m: '1.1',
              },
            ],
          },
          loads: [
            {
              name: 'Motor QA',
              unit_power_w: '1100',
              energisa_demand: {
                group: 'd6',
                motor: {
                  configuration: 'single_phase',
                  shaft_power_cv: '1',
                  source: 'Placa de teste',
                },
              },
            },
            {
              name: 'Central QA',
              unit_power_w: '2000',
              energisa_demand: {
                group: 'd5',
                air_conditioning_type: 'central_unit',
                central: {
                  configuration: 'single_phase',
                  voltage_v: '220',
                  maximum_total_current_a: '10',
                  power_factor: '.9',
                  source: 'Fabricante de teste',
                },
              },
            },
            {
              name: 'Solda QA',
              unit_power_w: '800',
              energisa_demand: {
                group: 'd7',
                special: {
                  equipment_type: 'arc_welder',
                  connection: 'standard',
                  input_apparent_power_va: '1000',
                  power_factor: '.8',
                  source: 'Ficha de teste',
                },
              },
            },
            {
              id: phaseLoad,
              name: 'Trifásica QA',
              unit_power_w: '6600',
              voltage_v: '220',
              power_factor: '1',
              parameters: { configuration: 'balanced_three_phase' },
              energisa_demand: { group: 'd1' },
            },
          ],
        },
      ],
      circuits: [
        {
          id: 'three',
          name: 'Trifásico QA',
          configuration: 'balanced_three_phase_without_neutral',
          purpose: 'dedicated',
          load_ids: [phaseLoad],
          method: 'C',
          voltage_v: '220',
          length_m: '30',
          ambient_temperature_c: 30,
          grouped_circuits: 1,
          scope_confirmed: true,
          voltage_drop_model_confirmed: true,
          overload_duration_confirmed: true,
          breaker_ratings_a: ['25'],
          breaker_i2_factor: '1.45',
          breaker_source: 'Fabricante de teste',
          prospective_short_circuit_ka: '3',
          breaking_capacity_ka: '6',
          supply_origin: 'public_lv_delivery',
          upstream_drop_percent: '0',
        },
      ],
    },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  const saved = await response.json();
  await page.goto('/');
  await page.getByRole('button', { name: /^Abrir projetos salvos/ }).click();
  await page.getByRole('button', { name, exact: true }).click();
  await page.getByText('Estudos técnicos (opcional)', { exact: true }).click();
  await page.getByText('Demanda da residência · Energisa', { exact: true }).click();
  const demand = page.getByRole('region', { name: 'Revisão da demanda Energisa' });
  const review = demand.getByLabel(
    'Revisei todas as cargas, potências, quantidades, grupos, reservas e o escopo',
  );
  await expect(review).toBeEnabled();
  await review.check();
  await expect(demand).toContainText('Demanda estimada: 11,386 kVA');
  await demand.getByLabel('Fonte das fases e potência de eixo de Motor QA').fill('Placa revisada');
  await expect(demand).toContainText('Demanda pendente de revisão');
  await expect(review).not.toBeChecked();
  await review.check();
  await expect(demand).toContainText('Demanda estimada: 11,386 kVA');
  await page.getByText('Localização de componentes no banheiro', { exact: true }).click();
  const geometry = page.getByRole('region', { name: 'Localização de componentes no banheiro' });
  await expect(geometry).toContainText('Volume 2');
  await expect(geometry).toContainText('Tomada/interruptor comum vedado');
  await geometry.getByLabel('X máximo de Tomada QA (m)').fill('2.1');
  await geometry.getByLabel('X mínimo de Tomada QA (m)').fill('2');
  await expect(geometry).toContainText('Volume 3');
  await expect(geometry).not.toContainText('Tomada/interruptor comum vedado');
  await page.getByText('Circuitos e entrada de energia', { exact: true }).click();
  const circuit = page.getByTestId('circuit-editor');
  await expect(circuit.getByTestId('circuit-result')).toContainText('fase: 4 mm²');
  await expect(circuit.getByTestId('circuit-result')).toContainText('Ib: 17,321 A');
  await expect(circuit.getByLabel('Configuração do circuito')).toHaveValue(
    'balanced_three_phase_without_neutral',
  );
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  const restored = await (
    await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`)
  ).json();
  expect(restored.environments[0].bathroom_geometry.points[0].x_min_m).toBe('2');
  expect(restored.environments[0].loads[0].energisa_demand.motor.source).toBe('Placa revisada');
  await page.getByLabel('Mais ações do projeto').click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  const report = JSON.parse(await readFile((await (await download).path())!, 'utf8'));
  expect(Number(report.demanda_revisada.groups[5].components[0].demand_w)).toBe(1095.2);
  expect(report.localizacao_banheiros[0].points[0].volume).toBe('3');
  expect(report.circuitos[0].phase_section_mm2).toBe('4');
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
  }
  await page.screenshot({ path: '/tmp/eletroprojeto-technical-019-desktop.png', fullPage: true });
});
