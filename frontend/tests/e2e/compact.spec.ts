import { test, expect } from '../support/workspace-test';
import AxeBuilder from '@axe-core/playwright';

test('home preserves sidebar branding and equipment disclosures stay compact and functional', async ({
  page,
}) => {
  await page.goto('/');
  const sidebar = page.locator('.workspace-sidebar');
  await expect(sidebar).toBeVisible();
  await expect(sidebar.locator('.brand-name')).toHaveText('EletroProjeto');
  await expect(page.locator('.workspace-footer')).toContainText(
    'Estimativa de consumo residencial',
  );
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    if (width === 1440)
      expect(
        (await page.locator('.workspace-footer').boundingBox())!.y +
          (await page.locator('.workspace-footer').boundingBox())!.height,
      ).toBeLessThanOrEqual(900);
    if (width === 390 || width === 1440) {
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({
        path: `/tmp/eletroprojeto-home-compact-${width}.png`,
        fullPage: true,
      });
    }
  }
  await page.getByRole('button', { name: /^Acessar lixeira/ }).click();
  await expect(sidebar).toBeVisible();
  await sidebar.getByRole('button', { name: 'Início', exact: true }).click();
  await expect(sidebar).toBeVisible();
  await page.getByRole('button', { name: /^Abrir projetos salvos/ }).click();
  await expect(sidebar).toBeVisible();
  await sidebar.getByRole('button', { name: 'Início', exact: true }).click();
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await expect(sidebar).toBeVisible();
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  await page
    .getByLabel('Adicionar equipamento em Novo ambiente', { exact: true })
    .selectOption('philips-led-929001195311');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  const equipment = page.getByTestId('equipment-editor');
  const summaries = equipment.locator('.equipment-options > details > summary');
  await expect(summaries).toHaveCount(3);
  const geometry = await summaries.evaluateAll((nodes) =>
    nodes.map((node) => ({
      y:
        node.getBoundingClientRect().y -
        node.closest('[data-testid="equipment-editor"]')!.getBoundingClientRect().y,
      height: node.getBoundingClientRect().height,
    })),
  );
  expect(geometry.every((item) => item.height >= 36 && item.height <= 40)).toBe(true);
  expect(
    Math.max(...geometry.map((item) => item.y)) - Math.min(...geometry.map((item) => item.y)),
  ).toBeLessThan(2);
  for (const key of ['equipment-advanced', 'equipment-energy', 'equipment-reference']) {
    const disclosure = equipment.getByTestId(key);
    await disclosure.locator(':scope > summary').click();
    await expect(disclosure).toHaveAttribute('open', '');
    const expandedPositions = await summaries.evaluateAll((nodes) =>
      nodes.map((node) => ({
        x: node.getBoundingClientRect().x,
        y:
          node.getBoundingClientRect().y -
          node.closest('[data-testid="equipment-editor"]')!.getBoundingClientRect().y,
      })),
    );
    for (let i = 0; i < geometry.length; i++) {
      expect(Math.abs(expandedPositions[i].y - geometry[i].y)).toBeLessThan(2);
    }

    await disclosure.locator(':scope > summary').click();
    await expect(disclosure).not.toHaveAttribute('open', '');
  }
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    const beforeOpen = await summaries.evaluateAll((nodes) =>
      nodes.map((node) => ({
        x: node.getBoundingClientRect().x,
        y:
          node.getBoundingClientRect().y -
          node.closest('[data-testid="equipment-editor"]')!.getBoundingClientRect().y,
      })),
    );
    for (let index = 0; index < 3; index++) {
      await summaries.nth(index).evaluate((node) => (node as HTMLElement).click());
      const afterOpen = await summaries.evaluateAll((nodes) =>
        nodes.map((node) => ({
          x: node.getBoundingClientRect().x,
          y:
            node.getBoundingClientRect().y -
            node.closest('[data-testid="equipment-editor"]')!.getBoundingClientRect().y,
        })),
      );
      afterOpen.forEach((position, i) => {
        expect(Math.abs(position.x - beforeOpen[i].x)).toBeLessThan(2);
        expect(Math.abs(position.y - beforeOpen[i].y)).toBeLessThan(2);
      });
    }
    await expect(
      equipment.getByLabel('Consumo de energia (kWh/mês)', { exact: true }),
    ).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    for (let index = 0; index < 3; index++)
      await summaries.nth(index).evaluate((node) => (node as HTMLElement).click());
    if (width === 390 || width === 1440)
      await equipment.screenshot({ path: `/tmp/eletroprojeto-equipment-compact-${width}.png` });
  }
  await sidebar.getByRole('button', { name: 'Início', exact: true }).click();
  await expect(sidebar).toBeVisible();
  await page.getByRole('button', { name: 'Continuar edição', exact: true }).click();
  await expect(sidebar).toBeVisible();
  await expect(page.getByTestId('equipment-editor')).toHaveCount(1);
});
