import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('reviewed demand persists, exports and becomes pending after editing', async ({
  page,
  request,
}) => {
  const name = `Demanda revisada ${Date.now()}`;
  const saved = await request.post('http://127.0.0.1:8010/api/v1/projects', {
    data: {
      name,
      municipality: 'Município informado',
      state: 'SP',
      utility: 'energisa_sul_sudeste',
      energisa_demand: {
        enabled: true,
        unit_type: 'individual_residential',
        has_signage_or_display_lighting: false,
        simultaneous_lighting_outlets: false,
        confirmed_absent_groups: ['d3', 'd4', 'd5', 'd6', 'd7'],
      },
      environments: [
        {
          name: 'Casa',
          loads: [
            { name: 'Luz de teste', unit_power_w: '1000', energisa_demand: { group: 'd1' } },
            { name: 'Chuveiro de teste', unit_power_w: '5500', energisa_demand: { group: 'd2' } },
          ],
        },
      ],
    },
  });
  expect(saved.ok()).toBeTruthy();
  await page.goto('/');
  await page.locator('aside').getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  await page.getByRole('button', { name, exact: true }).click();
  const panel = page.getByRole('region', { name: 'Revisão da demanda Energisa' });
  await expect(panel).toContainText('Demanda pendente de revisão');
  const review = panel.getByLabel(
    'Revisei todas as cargas, potências, quantidades, grupos, reservas e o escopo',
  );
  await expect(review).toBeEnabled();
  await review.check();
  await expect(panel).toContainText('Demanda estimada: 6,913 kVA');
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  await page.reload();
  // A saved project remains in the library after reload.
  await page.locator('aside').getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  await page.getByRole('button', { name, exact: true }).click();
  await expect(panel).toContainText('Demanda estimada: 6,913 kVA');
  await expect(review).toBeChecked();
  await page.getByLabel('Mais ações do projeto').click();
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  const file = await downloading;
  const { readFile } = await import('node:fs/promises');
  const report = JSON.parse(await readFile((await file.path())!, 'utf8'));
  expect(report.demanda_revisada.inventory_reviewed).toBe(true);
  expect(Number(report.demanda_revisada.value)).toBeCloseTo(6.913043478, 8);

  await panel.getByText('Memória da demanda por grupo', { exact: true }).click();
  await expect(panel).toContainText('d2 · Tabela 6');
  const accessibility = await new AxeBuilder({ page })
    .include('section[aria-label="Revisão da demanda Energisa"]')
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await page.screenshot({ path: '/tmp/eletroprojeto-demand-desktop.png', fullPage: true });
  const pdfDownloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar PDF', exact: true }).click();
  const pdf = await pdfDownloading;
  expect(pdf.suggestedFilename()).toBe(`${name}.pdf`);
  await pdf.saveAs('/tmp/eletroprojeto-demand-e2e.pdf');

  const quantity = page
    .getByTestId('equipment-editor')
    .nth(1)
    .getByLabel('Quantidade', { exact: true });
  await quantity.fill('2');
  await expect(panel).toContainText('Demanda pendente de revisão');
  await expect(review).not.toBeChecked();
  await review.check();
  await expect(panel).toContainText('Demanda estimada: 9,902 kVA');
  await panel.getByLabel('Grupo NDU de Chuveiro de teste').selectOption('d6');
  await expect(panel).toContainText('Demanda fora do escopo implementado');
  await expect(page.getByLabel('Resumo de resultados')).not.toContainText('Demanda estimada');
  for (const width of [320, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth),
    ).toBe(false);
  }
});
