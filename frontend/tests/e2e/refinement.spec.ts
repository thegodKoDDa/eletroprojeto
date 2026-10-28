import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

for (const profile of ['LEIGO', 'PROFISSIONAL']) {
  test(`${profile}: mobile navigation and consumption alternatives remain usable`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await page.getByRole('button', { name: new RegExp(`USUÁRIO ${profile}`) }).click();
    const navigation = page.getByRole('navigation', { name: 'Espaço de trabalho' });
    const toggle = page.getByRole('button', { name: 'Navegação', exact: true });
    await expect(navigation).not.toBeVisible();
    await toggle.click();
    await expect(navigation).toBeVisible();
    await navigation.getByRole('button', { name: 'Biblioteca técnica', exact: true }).click();
    await expect(navigation).not.toBeVisible();
    await toggle.click();
    await navigation.getByRole('button', { name: 'Novo projeto', exact: true }).click();
    await page.getByLabel('Nome do projeto', { exact: true }).fill('Refinamento mobile');
    await expect(page.getByRole('button', { name: 'Salvar projeto', exact: true })).toBeVisible();
    await toggle.click();
    page.once('dialog', (dialog) => dialog.dismiss());
    await navigation.getByRole('button', { name: 'Novo projeto', exact: true }).click();
    await expect(navigation).toBeVisible();
    await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveValue(
      'Refinamento mobile',
    );
    await toggle.click();
    await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
    await page
      .getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' })
      .selectOption('philips-led-929001195311');
    const energy = page.getByTestId('equipment-energy');
    await expect(energy.getByRole('group', { name: 'Etiqueta ou medição' })).toBeVisible();
    const hours = energy.getByLabel('Horas de uso por dia');
    await hours.fill('5');
    await energy.getByLabel('Consumo de energia (kWh/mês)').fill('0');
    await expect(hours).toBeDisabled();
    await expect(hours).toHaveValue('5');
    await energy.getByLabel('Consumo de energia (kWh/mês)').fill('');
    await expect(hours).toBeEnabled();
    await expect(hours).toHaveValue('5');
    if (profile === 'PROFISSIONAL') {
      await page.getByRole('button', { name: 'Parâmetros dos aparelhos', exact: true }).click();
      await expect(page.locator('[id$=".unit_power_w"]').first()).toBeFocused();
      await page.locator('#results-memory').click();
      await page.getByRole('button', { name: 'Resultados e memória', exact: true }).click();
      await expect(page.locator('.result-details')).toHaveAttribute('open');
    }
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 950 });
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      ).toBeTruthy();
    }
    expect(
      (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
        .violations,
    ).toEqual([]);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: `/tmp/eletroprojeto-refinement-${profile}.png`, fullPage: true });
  });
}
