import { test, expect } from '../support/workspace-test';

test('comparison keeps its original snapshot before and after autosave until explicit reset', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page
    .getByLabel('Nome do projeto', { exact: true })
    .fill(`Auditoria cenários ${Date.now()}`);
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  await page
    .getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' })
    .selectOption('philips-led-929001195311');
  const energy = page.getByTestId('equipment-energy');
  await energy.locator(':scope > summary').click();
  const monthly = energy.getByLabel('Consumo de energia (kWh/mês)', { exact: true });
  await monthly.fill('12');
  const saving = page.waitForResponse(
    (r) => r.url().endsWith('/projects') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  const saved = await (await saving).json();
  await page.getByText('Comparar cenários de consumo', { exact: true }).click();
  const firstAutosave = page.waitForResponse(
    (r) =>
      r.url().includes(`/projects/${saved.id}?expected_version=1`) &&
      r.request().method() === 'PUT',
  );
  await monthly.fill('24');
  expect((await (await firstAutosave).json()).version).toBe(2);
  await expect(page.locator('#results')).toContainText('24 kWh/mês');
  await page.getByRole('button', { name: 'Comparar com versão salva', exact: true }).click();
  const table = page.getByRole('table', { name: /Diferença: edição atual menos versão salva 1/ });
  await expect(table.getByRole('row').filter({ hasText: 'Consumo mensal' })).toContainText(
    '12 kWh',
  );
  const nextAutosave = page.waitForResponse(
    (r) =>
      r.url().includes(`/projects/${saved.id}?expected_version=2`) &&
      r.request().method() === 'PUT',
  );
  await monthly.fill('36');
  await expect(table).toHaveCount(0);
  expect((await (await nextAutosave).json()).version).toBe(3);
  await expect(page.locator('#results')).toContainText('36 kWh/mês');
  await page.getByRole('button', { name: 'Comparar com versão salva', exact: true }).click();
  await expect(table.getByRole('row').filter({ hasText: 'Consumo mensal' })).toContainText(
    '24 kWh',
  );
  await page
    .getByRole('button', { name: 'Usar versão salva mais recente como referência' })
    .click();
  await expect(table).toHaveCount(0);
  await page.getByRole('button', { name: 'Comparar com versão salva', exact: true }).click();
  await expect(
    page
      .getByRole('table', { name: /versão salva 3/ })
      .getByRole('row')
      .filter({ hasText: 'Consumo mensal' }),
  ).toContainText('0 kWh');
  expect(errors).toEqual([]);
});

test('declared energy, unknown power, partial coverage and empty rooms have accurate labels', async ({
  page,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByLabel('Tarifa de energia (R$/kWh)', { exact: true }).fill('0.8');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  const room = page.locator('.environment-card').first();
  await room
    .getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' })
    .selectOption('custom');
  const appliance = room.getByTestId('equipment-editor').first();
  await appliance.getByLabel('Descrição', { exact: true }).fill('Geladeira com etiqueta');
  await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
  await expect(
    page.locator('#results').getByText('Informe o consumo para estimar o custo', { exact: true }),
  ).toHaveCount(2);
  await appliance.getByTestId('equipment-energy').locator(':scope > summary').click();
  await appliance.getByLabel('Consumo de energia (kWh/mês)', { exact: true }).fill('35');
  await expect(page.locator('#results')).toContainText('35 kWh/mês');
  await expect(page.locator('#results')).toContainText('R$ 28,00');
  await expect(page.locator('#results')).toContainText('Potência ainda não informada');
  await expect(appliance.getByLabel('Potência unitária (W)', { exact: true })).toHaveAttribute(
    'aria-required',
    'false',
  );
  await expect(page.locator('#results .notice-group[data-tone="error"]')).toHaveCount(0);
  await room
    .getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' })
    .selectOption('custom');
  await expect(
    page
      .locator('#results')
      .getByText('Consumo mensal estimado · subtotal conhecido', { exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Adicionar ambiente', exact: true }).click();
  await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
  await expect(page.locator('#results').getByText('Sem aparelhos', { exact: true })).toBeVisible();
  await expect(page.locator('#results')).toContainText('35 kWh/mês');
  for (const width of [390, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    await page
      .locator('#results')
      .screenshot({ path: `/tmp/eletro-inspection-partial-${width}.png` });
  }
});
