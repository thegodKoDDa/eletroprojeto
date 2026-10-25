import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('three-step consumption journey stays simple and technical studies remain optional', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('.workspace-options > button')).toHaveCount(3);
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByLabel('Nome do projeto', { exact: true }).fill('Minha casa · exemplo de consumo');
  await page.getByLabel('Município', { exact: true }).fill('Cidade de exemplo');
  await page.getByLabel('Tarifa de energia (R$/kWh)', { exact: true }).fill('0.8');
  await expect(page.getByText('01 / PROJETO', { exact: true })).toBeVisible();
  await expect(page.getByText('02 / AMBIENTES', { exact: true })).toBeVisible();
  await expect(page.getByText('03 / CONFERÊNCIA', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Estudo de circuitos', exact: true })).toHaveCount(
    0,
  );
  await expect(page.getByLabel('Concessionária', { exact: true })).toBeHidden();
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
  const room = page.locator('#environments article').first();
  await room.getByLabel('Nome', { exact: true }).fill('Sala');
  await expect(room.getByLabel('Área (m²)', { exact: true })).toBeHidden();
  await room
    .getByLabel('Adicionar equipamento em Sala', { exact: true })
    .selectOption('philips-led-929001195311');
  const equipment = room.getByTestId('equipment-editor');
  // Explicit fictional scenario: two 10 W lamps, three hours/day, twenty days/month.
  await equipment.getByLabel('Quantidade', { exact: true }).fill('2');
  await equipment.getByLabel('Potência unitária (W)', { exact: true }).fill('10');
  const complete = page.getByRole('button', {
    name: 'Completar consumo dos aparelhos',
    exact: true,
  });
  await expect(complete).toBeVisible();
  await complete.click();
  await expect(equipment.getByLabel('Horas de uso por dia', { exact: true })).toBeFocused();
  await equipment.getByLabel('Horas de uso por dia', { exact: true }).fill('3');
  await complete.click();
  await expect(equipment.getByLabel('Dias de uso por mês', { exact: true })).toBeFocused();
  await equipment.getByLabel('Dias de uso por mês', { exact: true }).fill('20');
  const summary = page.getByLabel('Consumo e custo mensais', { exact: true });
  await expect(summary).toContainText('1,2 kWh/mês');
  await expect(summary).toContainText('R$ 0,96');
  await expect(complete).toHaveCount(0);
  await expect(page.getByLabel('Apresentação', { exact: true })).toBeHidden();
  await expect(page.getByText('Potência aparente · soma escalar', { exact: true })).toBeHidden();
  await expect(
    page.getByText('Estudos técnicos (opcional)', { exact: true }).locator('..'),
  ).not.toHaveAttribute('open', '');
  await expect(equipment.getByTestId('equipment-advanced')).not.toHaveAttribute('open', '');
  // Updating usage hides previous figures until the backend answers, and then shows the new estimate.
  await equipment.getByLabel('Horas de uso por dia', { exact: true }).fill('4');
  await expect(page.locator('#results')).toHaveAttribute('data-stale', 'true');
  await expect(summary).toBeHidden();
  await expect(summary).toContainText('1,6 kWh/mês');
  await expect(summary).toBeVisible();
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    if (width === 390 || width === 1440) {
      await page.screenshot({ path: `/tmp/eletroprojeto-simple-${width}.png`, fullPage: true });
    }
  }
  expect(errors).toEqual([]);
});

test('keyboard journey identifies pending appliances by room and offers a tariff shortcut', async ({
  page,
}) => {
  await page.goto('/');
  const create = page.getByRole('button', { name: /^Criar novo projeto/ });
  await expect(create).toBeVisible();
  await page.getByRole('link', { name: 'Ir para o conteúdo' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
  await create.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByLabel('Nome do projeto', { exact: true })).toBeFocused();
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
  const first = page.locator('#environments article').first();
  await first.getByLabel('Nome', { exact: true }).fill('Sala');
  await page.getByLabel('Pesquisar catálogo', { exact: true }).fill('chuveiro');
  await expect(first.getByRole('option', { name: 'Chuveiro elétrico', exact: true })).toHaveCount(
    1,
  );
  await page.getByLabel('Pesquisar catálogo', { exact: true }).fill('zzzinexistente');
  await expect(first.getByRole('status')).toContainText('Nenhum equipamento encontrado');
  await page.getByLabel('Pesquisar catálogo', { exact: true }).fill('');
  await first
    .getByLabel('Adicionar equipamento em Sala', { exact: true })
    .selectOption('philips-led-929001195311');
  await page.getByRole('button', { name: 'Adicionar ambiente', exact: true }).click();
  const second = page.locator('#environments article').nth(1);
  await second.getByLabel('Nome', { exact: true }).fill('Quarto');
  await second
    .getByLabel('Adicionar equipamento em Quarto', { exact: true })
    .selectOption('philips-led-929001195311');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  const pending = page.getByText('Aparelhos com consumo pendente', { exact: true });
  await pending.focus();
  await page.keyboard.press('Enter');
  const target = page.getByRole('button', { name: /^Informar consumo: Quarto/ });
  await target.focus();
  await page.keyboard.press('Enter');
  const hours = second.getByLabel('Horas de uso por dia', { exact: true });
  await expect(hours).toBeFocused();
  await expect(hours).toHaveAccessibleDescription(/Nenhum horário é presumido/);
  await expect(second.getByRole('group', { name: /^Equipamento:/ })).toHaveCount(1);
  await hours.fill('2');
  await second.getByLabel('Dias de uso por mês', { exact: true }).fill('20');
  await first.getByTestId('equipment-energy').locator('summary').click();
  await first.getByLabel('Consumo de energia (kWh/mês)', { exact: true }).fill('10');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  await expect(page.getByRole('button', { name: /^Informar consumo:/ })).toHaveCount(0);
  const tariff = page.getByRole('button', {
    name: 'Informar tarifa para estimar o custo',
    exact: true,
  });
  await tariff.focus();
  await page.keyboard.press('Enter');
  const field = page.getByLabel('Tarifa de energia (R$/kWh)', { exact: true });
  await expect(field).toBeFocused();
  await expect(field).toHaveAccessibleDescription(/disponível na conta de luz/);
  await field.fill('0');
  await expect(page.getByLabel('Consumo e custo mensais', { exact: true })).toContainText(
    'R$ 0,00',
  );
  await expect(tariff).toHaveCount(0);
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
});
