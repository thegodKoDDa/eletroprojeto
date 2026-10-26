import { test, expect } from '../support/workspace-test';
import AxeBuilder from '@axe-core/playwright';
import { readFile } from 'node:fs/promises';

test('circuits and entry calculate on server, survive saving and export with pending checks', async ({
  page,
  request,
}) => {
  const response = await request.post('http://127.0.0.1:8010/api/v1/projects', {
    data: {
      name: 'Circuitos QA',
      municipality: 'Município QA',
      state: 'SP',
      utility: 'energisa_sul_sudeste',
      environments: [
        {
          id: '11111111-1111-4111-8111-111111111111',
          name: 'Ambiente QA',
          type: 'other',
          loads: [
            {
              id: '22222222-2222-4222-8222-222222222222',
              name: 'Carga fictícia',
              category: 'Outros',
              quantity: 1,
              unit_power_w: '4400',
              voltage_v: '220',
              power_factor: '1',
              source: 'Exemplo fictício independente',
              equipment_type: 'custom',
              parameters: { configuration: 'single_phase' },
            },
          ],
        },
      ],
      circuits: [
        {
          id: 'circuit-qa',
          name: 'Circuito QA',
          purpose: 'sockets',
          load_ids: ['22222222-2222-4222-8222-222222222222'],
          method: 'B1',
          voltage_v: '220',
          length_m: '30',
          ambient_temperature_c: 30,
          grouped_circuits: 1,
          scope_confirmed: true,
          voltage_drop_model_confirmed: true,
          overload_duration_confirmed: true,
          breaker_ratings_a: ['16', '25', '40'],
          breaker_i2_factor: '1.45',
          breaker_source: 'Dados fictícios QA',
          prospective_short_circuit_ka: '3',
          breaking_capacity_ka: '6',
          supply_origin: 'public_lv_delivery',
          upstream_drop_percent: '0',
        },
      ],
      service_entry: {
        network: '220_127',
        route: 'embedded',
        insulation: 'PVC70',
        scope_confirmed: true,
        special_loads_reviewed: true,
      },
    },
  });
  expect(response.ok(), await response.text()).toBe(true);
  const saved = await response.json();
  await page.goto('/');
  await page.getByRole('button', { name: /^Abrir projetos salvos/ }).click();
  await page.getByRole('button', { name: 'Circuitos QA', exact: true }).click();
  await page.getByText('Estudos técnicos (opcional)', { exact: true }).click();
  await page.getByText('Circuitos e entrada de energia', { exact: true }).click();
  const editor = page.getByTestId('circuit-editor');
  await expect(editor.getByTestId('circuit-result')).toContainText('fase: 4 mm²');
  await expect(editor.getByTestId('circuit-result')).toContainText('Ib: 20 A');
  await expect(page.getByTestId('entry-result')).toContainText('Categoria: B1');
  await editor.getByLabel('Comprimento de ida (m)').fill('3000');
  await expect(editor.getByTestId('circuit-result')).toContainText('Nenhuma seção até95mm²');
  await expect(editor.getByTestId('circuit-result')).toContainText('fase: —');
  await editor.getByLabel('Comprimento de ida (m)').fill('30');
  await expect(editor.getByTestId('circuit-result')).toContainText('fase: 4 mm²');
  await expect
    .poll(
      async () =>
        (await (await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`)).json())
          .circuits[0].length_m,
    )
    .toBe('30');
  await editor.getByLabel('Nome do circuito', { exact: true }).fill('Circuito QA revisado');
  await expect
    .poll(
      async () =>
        (await (await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`)).json())
          .circuits[0].name,
    )
    .toBe('Circuito QA revisado');
  const download = page.waitForEvent('download');
  await page.getByLabel('Mais ações do projeto').click();
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  const json = JSON.parse(await readFile((await (await download).path())!, 'utf8'));
  expect(json.formato_versao).toBe('1.4');
  expect(json.circuitos[0].phase_section_mm2).toBe('4');
  expect(json.entrada_de_energia.category).toBe('B1');
  expect(json.circuitos[0].pending_checks.length).toBeGreaterThan(0);
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  }
  await page.reload();
  await page.getByRole('button', { name: /^Abrir projetos salvos/ }).click();
  await page.getByRole('button', { name: 'Circuitos QA', exact: true }).click();
  await page.getByText('Estudos técnicos (opcional)', { exact: true }).click();
  await page.getByText('Circuitos e entrada de energia', { exact: true }).click();
  await expect(page.getByTestId('circuit-editor').getByTestId('circuit-result')).toContainText(
    'fase: 4 mm²',
  );
  page.on('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Remover carga', exact: true }).click();
  await expect(page.getByTestId('circuit-result')).toContainText('Associe ao menos uma carga');
  await expect
    .poll(
      async () =>
        (await (await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`)).json())
          .circuits[0].load_ids,
    )
    .toEqual([]);
});
