import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '../support/workspace-test';

test('home and populated editor expose labelled controls and accessible landmarks', async ({
  page,
}) => {
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'Seu próximo projeto começa aqui.' }),
  ).toBeVisible();
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
  await page
    .getByLabel('Adicionar equipamento em Novo ambiente', { exact: true })
    .selectOption('philips-led-929001195311');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
});
