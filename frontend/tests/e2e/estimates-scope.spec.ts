import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

for (const [profile, kind, stage] of [
  ['USUÁRIO LEIGO', 'Casa', 'planned'],
  ['USUÁRIO PROFISSIONAL', 'Apartamento', 'ready'],
  ['ESTOU APENAS DANDO UMA OLHADA', 'Kitnet', 'construction'],
]) {
  test(`${profile}: residential estimate independent of installations`, async ({
    page,
    request,
  }) => {
    const obsolete: string[] = [];
    page.on('request', (r) => {
      if (/\/technical\/|\/standards|\/calculations\/.*demand|\/revalidation/.test(r.url()))
        obsolete.push(r.url());
    });
    await page.goto('/');
    await page.getByRole('button', { name: new RegExp(profile) }).click();
    await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
    const name = `Estimativa ${kind} ${Date.now()}`;
    await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
    await page.getByLabel('Tarifa de energia (R$/kWh)', { exact: true }).fill('0.8');
    await page.getByText('Outros dados do projeto', { exact: true }).evaluate((node) => {
      node.closest('details')!.open = true;
    });
    await page.getByLabel('Tipo de residência', { exact: true }).fill(kind);
    await page.getByLabel('Estágio do imóvel', { exact: true }).selectOption(stage);
    await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
    const room = page.locator('.environment-card').first();
    await room.getByLabel('Nome', { exact: true }).fill('Escritório');
    await room
      .getByRole('combobox', { name: 'Adicionar equipamento em Escritório' })
      .selectOption('enel-computer');
    const load = room.getByTestId('equipment-editor').first();
    await load.getByLabel('Potência unitária (W)', { exact: true }).fill('600');
    await load.getByLabel('Quantidade', { exact: true }).fill('2');
    await load.getByTestId('equipment-energy').evaluate((node) => {
      (node as HTMLDetailsElement).open = true;
    });
    await load.getByLabel('Horas de uso por dia', { exact: true }).fill('4');
    await load.getByLabel('Dias de uso por mês', { exact: true }).fill('20');
    await expect(page.locator('#results')).toContainText('96 kWh/mês');
    await expect(page.locator('#results')).toContainText('76,80');
    await expect(page.getByRole('combobox', { name: 'Concessionária', exact: true })).toHaveValue(
      'unconfirmed',
    );
    await page
      .getByRole('combobox', { name: 'Concessionária', exact: true })
      .selectOption('energisa_sul_sudeste');
    await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
    await expect(page.locator('#results')).toContainText('96 kWh/mês');
    await load.getByLabel('Potência unitária (W)', { exact: true }).fill('300');
    await expect(page.locator('#results')).toContainText('48 kWh/mês');
    await load.getByLabel('Horas de uso por dia', { exact: true }).fill('2');
    await expect(page.locator('#results')).toContainText('24 kWh/mês');
    const savedResponse = page.waitForResponse(
      (r) => r.url().endsWith('/projects') && r.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
    const saved = await (await savedResponse).json();
    expect(saved.environments[0].loads[0].unit_power_w).toBe('300');
    expect(saved.property_stage).toBe(stage);
    await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
    const pdf = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Exportar PDF', exact: true }).click();
    expect((await pdf).suggestedFilename()).toMatch(/\.pdf$/);
    const reread = await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`);
    expect((await reread.json()).environments[0].loads[0].unit_power_w).toBe('300');
    await page.reload();
    await page.getByRole('button', { name: /^Abrir projetos salvos/ }).click();
    await page
      .getByRole('region', { name: 'Projetos salvos' })
      .getByRole('button', { name, exact: true })
      .click();
    await expect(page.locator('#results')).toContainText('24 kWh/mês');
    await expect(page.getByText('Estudos técnicos (opcional)', { exact: true })).toHaveCount(0);
    await expect(page.getByLabel('Requisitos para', { exact: true })).toHaveCount(0);
    await page.getByText('Comparar cenários de consumo', { exact: true }).click();
    await page.getByTestId('equipment-energy').evaluate((node) => {
      (node as HTMLDetailsElement).open = true;
    });
    await page.getByLabel('Horas de uso por dia', { exact: true }).fill('4');
    await expect(page.locator('#results')).toContainText('48 kWh/mês');
    await page.getByRole('button', { name: 'Comparar com versão salva', exact: true }).click();
    const comparison = page.getByRole('table', {
      name: /Diferença: edição atual menos versão salva/,
    });
    await expect(comparison.getByRole('row').filter({ hasText: 'Consumo mensal' })).toContainText(
      '24 kWh',
    );
    expect(obsolete).toEqual([]);
    for (const width of [390, 1440]) {
      await page.setViewportSize({ width, height: 950 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
    }
    expect(
      (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
        .violations,
    ).toEqual([]);
  });
}
