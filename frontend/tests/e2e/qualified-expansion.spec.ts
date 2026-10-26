import { test, expect } from '../support/workspace-test';
import AxeBuilder from '@axe-core/playwright';
import { readFile } from 'node:fs/promises';

test('90°C cable and product coordination persist, recalculate and export', async ({
  page,
  request,
}) => {
  const name = `Cabos e coordenação QA ${Date.now()}`;
  const load = '22222222-2222-4222-8222-222222222299';
  const response = await request.post('http://127.0.0.1:8010/api/v1/projects', {
    data: {
      name,
      municipality: 'Local QA',
      environments: [
        {
          name: 'Sala QA',
          loads: [
            {
              id: load,
              name: 'Carga QA',
              unit_power_w: '4400',
              voltage_v: '220',
              power_factor: '1',
              parameters: { configuration: 'single_phase' },
            },
          ],
        },
      ],
      circuits: [
        {
          id: 'new',
          name: 'Circuito QA',
          load_ids: [load],
          method: 'E',
          insulation: 'XLPE90',
          terminals_90c_confirmed: true,
          voltage_v: '220',
          length_m: '1',
          ambient_temperature_c: 30,
          grouped_circuits: 1,
          scope_confirmed: true,
          voltage_drop_model_confirmed: true,
          overload_duration_confirmed: true,
          breaker_ratings_a: ['25'],
          breaker_i2_factor: '1.45',
          breaker_source: 'Fabricante fictício QA',
          prospective_short_circuit_ka: '3',
          breaking_capacity_ka: '6',
          supply_origin: 'public_lv_delivery',
          upstream_drop_percent: '0',
          hot_resistivity_ohm_mm2_m: '.025',
          reactance_ohm_m: '0',
          impedance_source: 'Impedância fictícia QA',
          protections: {
            selectivity: {
              upstream_device: 'A fictício',
              downstream_device: 'B fictício',
              downstream_rated_a: '25',
              source: 'Tabela fictícia QA',
              conditions_confirmed: true,
              limit_ka: '6',
            },
            surge: {
              device: 'DPS fictício QA',
              source: 'Produto fictício QA',
              requirements_source: 'Estudo fictício QA',
              conditions_confirmed: true,
              uc_v: '275',
              required_uc_v: '242',
              effective_up_v: '1500',
              withstand_voltage_v: '1500',
              discharge_ka: '20',
              required_discharge_ka: '20',
              waveform: '8/20',
              requirement_waveform: '8/20',
              short_withstand_ka: '6',
            },
          },
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
  await page.getByText('Circuitos e entrada de energia', { exact: true }).click();
  const circuit = page.getByTestId('circuit-editor');
  await expect(circuit.getByTestId('circuit-result')).toContainText('fase: 2,5 mm²');
  await expect(circuit.getByTestId('circuit-result')).toContainText(
    'Seletividade de curto: Ik máximo < limite tabelado (kA): atende ao critério informado',
  );
  await expect(circuit.getByLabel('Isolação do cabo de cobre')).toHaveValue('XLPE90');
  await circuit
    .getByText('Curto térmico, desligamento e DR — dados complementares', { exact: true })
    .click();
  await circuit.getByText('DPS e seletividade — comparação documental', { exact: true }).click();
  await circuit.getByLabel('Limite de seletividade do par (kA)').fill('3');
  await expect(circuit.getByTestId('circuit-result')).toContainText(
    'Seletividade de curto: Ik máximo < limite tabelado (kA): não atende',
  );
  await circuit.getByLabel('Onda exigida no estudo').selectOption('10/350');
  await expect(circuit.getByTestId('circuit-result')).toContainText(
    'DPS: corrente de descarga/impulso ≥ requisito na mesma onda (kA): pendente',
  );
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  const restored = await (
    await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`)
  ).json();
  expect(restored.circuits[0].protections.selectivity.limit_ka).toBe('3');
  expect(restored.circuits[0].insulation).toBe('XLPE90');
  await page.getByLabel('Mais ações do projeto').click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  const report = JSON.parse(await readFile((await (await download).path())!, 'utf8'));
  expect(Number(report.circuitos[0].voltage_drop_v)).toBe(0.4);
  expect(
    report.circuitos[0].protection_checks.find(
      (c: { code: string }) => c.code === 'selectivity_short',
    ).passed,
  ).toBe(false);
  await circuit.getByLabel('Método de instalação').selectOption('D');
  await expect(circuit.getByTestId('circuit-result')).toContainText(
    'Confirme cabo multipolar em eletroduto enterrado',
  );
  await circuit.getByLabel('Temperatura do solo (°C)').selectOption('20');
  await circuit.getByLabel(/Confirmei cabo multipolar não armado/).check();
  await circuit.getByRole('checkbox', { name: /Conferi instalação fixa/ }).check();
  await expect(circuit.getByTestId('circuit-result')).toContainText('fase: 2,5 mm²');
  await circuit.getByLabel('Método de instalação').selectOption('F');
  await circuit.getByRole('checkbox', { name: /Conferi instalação fixa/ }).check();
  await expect(circuit.getByTestId('circuit-result')).toContainText('fase: 2,5 mm²');
  await circuit.getByLabel('Método de instalação').selectOption('G');
  await expect(circuit.getByTestId('circuit-result')).toContainText(
    'G somente três fases equilibradas sem neutro',
  );
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
  }
});
