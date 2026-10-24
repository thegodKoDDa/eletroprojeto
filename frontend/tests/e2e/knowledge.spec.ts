import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('reference library searches real API, reads content and preserves editing', async ({
  page,
}) => {
  await page.goto('/');
  const sidebar = page.locator('.workspace-sidebar');
  await sidebar.getByRole('button', { name: 'Novo projeto', exact: true }).click();
  await page.getByLabel('Nome do projeto').fill('Rascunho preservado ao estudar');
  await sidebar.getByRole('button', { name: 'Biblioteca técnica', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Biblioteca técnica', exact: true }),
  ).toBeVisible();
  await page.getByLabel('Buscar no conteúdo e nas fontes').fill('potencia');
  await page.getByRole('button', { name: /Guia QA de chuveiro/ }).click();
  await expect(page.locator('.knowledge-text')).toContainText('não dimensiona sozinha');
  await expect(page.locator('.knowledge-text strong')).toHaveText('não dimensiona sozinha');
  await expect(page.getByRole('heading', { name: 'Guia QA de chuveiro' })).toBeFocused();
  await page.getByLabel('Buscar páginas nesta referência').fill('inexistente');
  await expect(page.getByText('Nenhuma página encontrada para este termo.')).toBeVisible();
  await page.getByLabel('Buscar páginas nesta referência').fill('potencia');
  await expect(page.locator('.knowledge-text')).toContainText('não dimensiona sozinha');
  await page.getByRole('button', { name: 'Fechar leitura' }).click();
  await page.getByLabel('Buscar no conteúdo e nas fontes').fill('');
  await page.getByLabel('Tipo de material').selectOption('diagram');
  await page.getByRole('button', { name: /Diagrama QA conceitual/ }).click();
  const diagram = page.getByRole('img', { name: /Diagrama didático/ });
  await expect(diagram).toBeVisible();
  await expect
    .poll(() => diagram.evaluate((node) => (node as HTMLImageElement).naturalWidth))
    .toBeGreaterThan(0);
  await page.getByText('Fontes e situação dos downloads', { exact: true }).click();
  await expect(page.getByText('Fonte QA indisponível')).toBeVisible();
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
  await sidebar.getByRole('button', { name: 'Projeto em edição', exact: true }).click();
  await expect(page.getByLabel('Nome do projeto')).toHaveValue('Rascunho preservado ao estudar');
});
