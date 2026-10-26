// Fresh contexts deliberately do not use the exploration-session fixture.
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const labels = {
  beginner: 'USUÁRIO LEIGO',
  professional: 'USUÁRIO PROFISSIONAL',
  explore: 'ESTOU APENAS DANDO UMA OLHADA',
} as const;

async function choose(page: import('@playwright/test').Page, profile: keyof typeof labels) {
  await page.getByRole('button', { name: new RegExp(labels[profile]) }).click();
  await expect(page.getByRole('button', { name: 'Alterar perfil' })).toBeVisible();
}

test('fresh opening is accessible, responsive and offers the three choices in order', async ({
  page,
}) => {
  await page.goto('/');
  const options = page.locator('main .experience-option');
  await expect(options).toHaveCount(3);
  for (const [index, label] of Object.values(labels).entries())
    await expect(options.nth(index)).toContainText(label);
  await expect(page.getByRole('button', { name: /^Criar novo projeto/ })).toHaveCount(0);
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
  await page.keyboard.press('Tab');
  await expect(options.nth(0)).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(options.nth(1)).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(options.nth(2)).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(
    page.getByRole('heading', { name: 'Seu próximo projeto começa aqui.' }),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: /^Acessar lixeira/ })).toBeVisible();
});

for (const profile of Object.keys(labels) as (keyof typeof labels)[]) {
  test(`${profile}: all resources, calculation, save and presentation changes preserve input`, async ({
    page,
    context,
  }) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(e.message));
    let calculations = 0;
    page.on('request', (r) => {
      if (r.url().endsWith('/calculations/full')) calculations++;
    });
    await page.goto('/');
    await choose(page, profile);
    const nav = page.getByRole('navigation', { name: 'Espaço de trabalho' });
    for (const name of ['Projetos salvos', 'Lixeira', 'Biblioteca técnica'])
      await expect(nav.getByRole('button', { name, exact: true })).toBeVisible();
    await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
    const name = `Perfil ${profile} QA ${Date.now()}`;
    await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
    await page.getByLabel('Município', { exact: true }).fill('Local QA');
    await page.getByLabel('Tarifa de energia (R$/kWh)', { exact: true }).fill('0.8');
    await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
    await page
      .getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' })
      .selectOption('philips-led-929001195311');
    const energy = page.getByTestId('equipment-energy');
    if (profile === 'explore') await energy.locator('summary').click();
    await expect(energy).toHaveAttribute('open');
    await energy.getByLabel('Consumo de energia (kWh/mês)').fill('6');
    await expect(page.getByLabel('Consumo e custo mensais')).toContainText('6 kWh/mês');
    await expect(page.getByLabel('Consumo e custo mensais')).toContainText('4,80');
    if (profile === 'beginner') {
      await expect(
        page.getByRole('region', { name: 'Orientação para estimar consumo' }),
      ).toBeVisible();
      expect(await page.locator('label[data-emphasis="essential"]').count()).toBeGreaterThan(0);
      await expect(page.locator('.technical-tools')).not.toHaveAttribute('open');
    } else if (profile === 'professional') {
      await expect(page.getByRole('region', { name: 'Atalhos profissionais' })).toBeVisible();
      await expect(page.locator('.project-extra')).toHaveAttribute('open');
      await expect(page.locator('.room-measurements')).toHaveAttribute('open');
      await expect(page.locator('.technical-tools')).toHaveAttribute('open');
      await expect(page.locator('.result-details')).toHaveAttribute('open');
      await expect(
        page.getByRole('checkbox', { name: 'Mostrar verificações e memória detalhadas' }),
      ).toBeChecked();
    } else {
      await expect(page.locator('.experience-guide')).toHaveCount(0);
      await expect(page.locator('.project-extra')).not.toHaveAttribute('open');
      await expect(page.locator('.technical-tools')).not.toHaveAttribute('open');
    }
    // Every profile can reach the full circuit study without modifying its data.
    if (profile === 'professional') {
      await page
        .getByRole('navigation', { name: 'Ferramentas profissionais' })
        .getByRole('button', { name: 'Circuitos e proteções' })
        .click();
    } else {
      await page.getByText('Estudos técnicos (opcional)', { exact: true }).click();
      await page.getByText('Circuitos e entrada de energia', { exact: true }).click();
    }
    await expect(
      page.getByRole('button', { name: 'Adicionar circuito', exact: true }),
    ).toBeVisible();
    const savedResponse = page.waitForResponse(
      (r) => r.url().endsWith('/projects') && r.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
    const saved = await (await savedResponse).json();
    await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
    const pdf = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Exportar PDF', exact: true }).click();
    expect((await pdf).suggestedFilename()).toMatch(/\.pdf$/);
    await page.getByLabel('Nome do projeto', { exact: true }).fill(name + ' · rascunho');
    await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
    const count = calculations;
    for (const target of Object.keys(labels) as (keyof typeof labels)[]) {
      await page.getByRole('button', { name: 'Alterar perfil' }).click();
      await choose(page, target);
      await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveValue(
        name + ' · rascunho',
      );
      await expect(page.getByLabel('Consumo e custo mensais')).toContainText('6 kWh/mês');
    }
    await page.waitForTimeout(500); // Covers the calculation debounce after presentation-only changes.
    expect(calculations).toBe(count);
    await page.getByRole('button', { name: 'Alterar perfil' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    for (let n = 0; n < 7; n++) {
      await page.keyboard.press('Tab');
      expect(await page.evaluate(() => !!document.activeElement?.closest('dialog'))).toBeTruthy();
    }
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Alterar perfil' })).toBeFocused();
    // A new tab starts with its own chooser; the existing tab keeps its selection.
    const other = await context.newPage();
    await other.goto('/');
    await expect(
      other.getByRole('heading', { name: 'Como você quer usar o EletroProjeto?' }),
    ).toBeVisible();
    await other.close();
    expect(saved.version).toBe(1);
    expect(errors).toEqual([]);
    await page.reload();
    await expect(page.locator('.app-shell')).toHaveAttribute('data-experience', 'explore');
    await expect(page.getByRole('region', { name: 'Rascunhos recuperados' })).toContainText(
      name + ' · rascunho',
    );
    await expect(page.getByRole('button', { name: 'Continuar rascunho' })).toBeVisible();
  });
}
