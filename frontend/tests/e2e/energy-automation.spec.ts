import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

for (const profile of ['USUÁRIO LEIGO', 'USUÁRIO PROFISSIONAL', 'ESTOU APENAS DANDO UMA OLHADA']) {
  test(`${profile}: automated energy arithmetic, safe batch entry and exports persist`, async ({
    page,
  }) => {
    await page.goto('/');
    await page.getByRole('button', { name: new RegExp(profile) }).click();
    await page.getByRole('button', { name: /Criar novo projeto/ }).click();
    const name = `Automação ${profile} ${Date.now()}`;
    await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
    await page.getByLabel('Município', { exact: true }).fill('Cidade QA');
    await page.getByLabel('Tarifa de energia (R$/kWh)', { exact: true }).fill('0.8');
    await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
    const picker = page.getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' });
    for (let i = 0; i < 3; i++) await picker.selectOption('philips-led-929001195311');
    const equipment = page.getByTestId('equipment-editor');
    await equipment.nth(0).getByLabel('Quantidade', { exact: true }).fill('2');
    for (let i = 0; i < 3; i++) {
      if (profile === 'ESTOU APENAS DANDO UMA OLHADA')
        await equipment.nth(i).getByTestId('equipment-energy').locator(':scope > summary').click();
    }
    await equipment.nth(0).getByLabel('Consumo de energia (kWh/mês)').fill('6');
    await equipment.nth(1).getByLabel('Potência unitária (W)', { exact: true }).fill('2000');
    await equipment.nth(2).getByText('Minha etiqueta informa kWh/ano', { exact: true }).click();
    await equipment.nth(2).getByLabel('Consumo de energia (kWh/ano)').fill('120');
    await page.getByText('Preencher uma rotina para vários aparelhos', { exact: true }).click();
    const batch = page.locator('.usage-batch');
    await expect(batch).toContainText('1 aparelho(s) sem rotina');
    await batch.getByLabel('Unidade da rotina comum').selectOption('minutes');
    await batch.getByLabel('Tempo de uso da rotina comum').fill('15');
    await batch.getByLabel('Dias por mês da rotina comum').fill('20');
    await batch
      .getByRole('button', { name: 'Aplicar aos aparelhos sem rotina', exact: true })
      .click();
    await expect(equipment.nth(1).getByLabel('Minutos de uso por dia')).toHaveValue('15');
    await expect(equipment.nth(0).getByLabel('Consumo de energia (kWh/mês)')).toHaveValue('6');
    await expect(equipment.nth(2).getByLabel('Consumo de energia (kWh/ano)')).toHaveValue('120');
    await expect(page.getByLabel('Consumo e custo mensais')).toContainText('32 kWh/mês');
    await expect(page.getByLabel('Consumo e custo mensais')).toContainText('25,60');
    await page
      .getByText('Contas automáticas: ambientes, maiores consumos e 12 meses', { exact: true })
      .click();
    const breakdown = page.locator('.energy-breakdown');
    await expect(breakdown).toContainText('384 kWh');
    await expect(breakdown).toContainText('307,20');
    await expect(breakdown).toContainText('37,5% do subtotal');
    await expect(breakdown).toContainText('31,25% do subtotal');
    const savedResponse = page.waitForResponse(
      (response) => response.url().endsWith('/projects') && response.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
    const saved = await (await savedResponse).json();
    expect(saved.environments[0].loads[1].parameters.usage_time_unit).toBe('minutes');
    expect(saved.environments[0].loads[1].parameters.usage_minutes_per_day).toBe('15');
    expect(saved.environments[0].loads[2].parameters.annual_energy_kwh).toBe('120');
    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Exportar PDF', exact: true }).click();
    expect((await download).suggestedFilename()).toMatch(/\.pdf$/);
    await page.reload();
    await page.getByRole('button', { name: /Abrir projetos salvos/ }).click();
    await page.getByRole('button', { name, exact: true }).click();
    if (profile === 'ESTOU APENAS DANDO UMA OLHADA')
      await equipment.nth(1).getByTestId('equipment-energy').locator(':scope > summary').click();
    await expect(equipment.nth(1).getByLabel('Minutos de uso por dia')).toHaveValue('15');
    await equipment.nth(1).getByLabel('Minutos de uso por dia').fill('30');
    await expect(page.getByLabel('Consumo e custo mensais')).toContainText('42 kWh/mês');
    await page
      .getByText('Contas automáticas: ambientes, maiores consumos e 12 meses', { exact: true })
      .click();
    await expect(breakdown).toContainText('504 kWh');
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
    await breakdown.screenshot({
      path: `/tmp/eletroprojeto-energy-${profile.includes('LEIGO') ? 'beginner' : profile.includes('PROFISSIONAL') ? 'professional' : 'explore'}.png`,
    });
  });
}
