import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

for (const profile of ['LEIGO', 'PROFISSIONAL']) {
  test(`${profile}: completed guidance advances and reopens for changed inputs`, async ({
    page,
  }) => {
    await page.goto('/');
    await page.getByRole('button', { name: new RegExp(`USUÁRIO ${profile}`) }).click();
    await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
    if (profile === 'PROFISSIONAL')
      await page.getByText(/^Acompanhar as etapas da estimativa/).click();
    const steps = page.getByRole('list', { name: 'Tarefas da estimativa' });
    await page.getByLabel('Nome do projeto', { exact: true }).fill('');
    await expect(steps.locator('[data-state="current"]')).toContainText('Identificar');
    await page.getByLabel('Nome do projeto', { exact: true }).fill(`Percurso ${profile}`);
    await expect(page.getByLabel('Município', { exact: true })).toHaveValue('');
    await expect(page.getByLabel('Município', { exact: true })).toHaveAttribute(
      'aria-required',
      'false',
    );
    await expect(steps.locator('[data-state="current"]')).toContainText('Cadastrar');
    await expect(steps.locator('[data-state="complete"]')).toHaveCount(1);
    await page.getByRole('button', { name: 'Ir para cadastro', exact: true }).click();
    await expect(page.locator('#add-environment')).toBeFocused();
    await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
    await page
      .getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' })
      .selectOption('philips-led-929001195311');
    await expect(steps.locator('[data-state="current"]')).toContainText('Informar o uso');
    const energy = page.getByTestId('equipment-energy').getByLabel('Consumo de energia (kWh/mês)');
    await energy.fill('0');
    await expect(steps.locator('[data-state="current"]')).toContainText('Conferir');
    await expect(energy).toBeFocused(); // Completion never interrupts typing.
    await expect(
      page.getByRole('button', { name: 'Já conferi a estimativa', exact: true }),
    ).toBeVisible();
    await page.getByRole('button', { name: 'Ir para conferência', exact: true }).click();
    await expect(page.locator('#results')).toBeFocused();
    await page.locator('#estimate-confirm').click();
    await expect(steps.locator('[data-state="current"]')).toContainText('Salvar');
    await page.getByRole('button', { name: 'Ir para salvamento', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Salvar projeto', exact: true })).toBeFocused();
    await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
    await expect(steps.locator('[data-state="complete"]')).toHaveCount(5);
    await expect(page.locator('.journey-next')).toContainText('conferida e salva');
    await energy.fill('6');
    await expect(
      page.getByRole('button', { name: 'Conferência concluída', exact: true }),
    ).toHaveCount(0);
    await expect(steps.locator('[data-state="current"]')).toContainText('Conferir');
    await page
      .getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' })
      .selectOption('philips-led-929001195311');
    await expect(steps.locator('[data-state="current"]')).toContainText('Informar o uso');
    await page.getByRole('button', { name: 'Ir para dados de uso', exact: true }).click();
    await expect(
      page.getByTestId('equipment-energy').nth(1).getByLabel('Horas de uso por dia'),
    ).toBeFocused();
    await page
      .getByTestId('equipment-energy')
      .nth(1)
      .getByLabel('Consumo de energia (kWh/mês)')
      .fill('2');
    await expect(steps.locator('[data-state="current"]')).toContainText('Conferir');
    const power = page.getByLabel('Potência unitária (W)', { exact: true }).first();
    await power.fill('-1');
    await expect(page.getByTestId('calculation-status')).toContainText('Entradas inválidas');
    await expect(page.locator('.journey-next')).toContainText('O cálculo não terminou');
    await page.getByRole('button', { name: 'Ir para dados de uso', exact: true }).click();
    await expect(power).toBeFocused();
    await power.fill('9');
    await expect(steps.locator('[data-state="current"]')).toContainText('Conferir');
    await page
      .getByText('Precisa de ajuda? Entenda os campos e os avisos', { exact: true })
      .click();
    await expect(
      page.getByRole('heading', { name: 'Desconhecido pode ficar pendente' }),
    ).toBeVisible();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.locator('.journey-steps')).toBeHidden();
    await page.getByRole('button', { name: 'Ver todas as etapas', exact: true }).click();
    await expect(page.locator('.journey-steps')).toBeVisible();
    await page.getByRole('button', { name: 'Recolher etapas', exact: true }).click();
    await expect(page.locator('.journey-steps')).toBeHidden();
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
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page
      .locator('.experience-guide')
      .screenshot({ path: `/tmp/eletroprojeto-journey-${profile}.png` });
  });
}

test('shared design and help remain accessible on home, saved projects, trash and library', async ({
  page,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /ESTOU APENAS DANDO UMA OLHADA/ }).click();
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  const nav = page.getByRole('navigation', { name: 'Espaço de trabalho' });
  for (const destination of ['Início', 'Projetos salvos', 'Lixeira', 'Biblioteca técnica']) {
    await nav.getByRole('button', { name: destination, exact: true }).click();
    await expect(page.locator('[data-workspace-heading]')).toBeFocused();
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
    await page.screenshot({
      path: `/tmp/eletroprojeto-design-${destination.replaceAll(' ', '-')}.png`,
    });
  }
  expect(errors).toEqual([]);
});
