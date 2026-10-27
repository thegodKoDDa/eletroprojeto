import { test, expect } from '@playwright/test';

for (const profile of ['USUÁRIO LEIGO', 'USUÁRIO PROFISSIONAL', 'ESTOU APENAS DANDO UMA OLHADA']) {
  for (const width of [390, 1440]) {
    test(`${profile} ${width}px: recalculation and saving keep geometry stable`, async ({
      page,
    }) => {
      await page.setViewportSize({ width, height: 1000 });
      let calculations = 0;
      page.on('request', (request) => {
        if (request.url().endsWith('/calculations/full')) calculations++;
      });
      await page.goto('/');
      await page.getByRole('button', { name: new RegExp(profile) }).click();
      await page.getByRole('button', { name: /Criar novo projeto/ }).click();
      await page.getByLabel('Nome do projeto', { exact: true }).fill('Estabilidade QA');
      await page.getByLabel('Município', { exact: true }).fill('Cidade QA');
      await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
      await page
        .getByRole('combobox', { name: 'Adicionar equipamento em Novo ambiente' })
        .selectOption('philips-led-929001195311');
      const energy = page.getByTestId('equipment-energy');
      if (profile.startsWith('ESTOU')) await energy.locator(':scope > summary').click();
      await energy.getByLabel('Consumo de energia (kWh/mês)').fill('6');
      await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
      const menu = page.getByLabel('Mais ações do projeto');
      const editorBeforeMenu = await page
        .locator('#project')
        .evaluate((element) => element.getBoundingClientRect().top + scrollY);
      await menu.click();
      await expect(page.locator('.action-menu-content')).toBeVisible();
      const popup = await page.locator('.action-menu-content').boundingBox();
      expect(popup!.y).toBeGreaterThanOrEqual(0);
      expect(popup!.y + popup!.height).toBeLessThanOrEqual(1000);
      expect(
        await page
          .locator('#project')
          .evaluate((element) => element.getBoundingClientRect().top + scrollY),
      ).toBe(editorBeforeMenu);
      await menu.press('Escape');
      await expect(menu).toBeFocused();
      const measure = () =>
        page.evaluate(() => {
          const p = document.querySelector('#project')!.getBoundingClientRect();
          const r = document.querySelector('#results')!.getBoundingClientRect();
          return { project: p.top + scrollY, resultsHeight: r.height };
        });
      let release!: () => void;
      const gate = new Promise<void>((resolve) => {
        release = resolve;
      });
      let hold = true;
      await page.route('**/calculations/full', async (route) => {
        if (hold) await gate;
        await route.continue();
      });
      const before = await measure();
      await page.getByLabel('Tarifa de energia (R$/kWh)', { exact: true }).fill('0.9');
      await expect(page.locator('#results')).toHaveAttribute('data-stale', 'true');
      const during = await measure();
      console.log(profile, { before, during });
      await expect(page.getByLabel('Consumo e custo mensais')).not.toBeVisible();
      expect(Math.abs(during.project - before.project)).toBeLessThan(2);
      expect(Math.abs(during.resultsHeight - before.resultsHeight)).toBeLessThan(2);
      hold = false;
      release();
      await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
      const stable = await measure();
      const notesBeforeSave = await page
        .getByLabel('Observações', { exact: true })
        .evaluate((element) => element.getBoundingClientRect().top + scrollY);
      const countBeforeSave = calculations;
      await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
      await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
      await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
      await page.waitForTimeout(650); // Covers the calculation debounce after response normalization.
      expect(calculations).toBe(countBeforeSave);
      const after = await measure();
      expect(Math.abs(after.project - stable.project)).toBeLessThan(2);
      await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveValue(
        'Estabilidade QA',
      );
      expect(
        await page
          .getByLabel('Observações', { exact: true })
          .evaluate((element) => element.getBoundingClientRect().top + scrollY),
      ).toBe(notesBeforeSave);
      const municipalityBeforeRename = await page
        .getByLabel('Município', { exact: true })
        .evaluate((element) => element.getBoundingClientRect().top + scrollY);
      await page.getByLabel('Nome do projeto', { exact: true }).fill('Estabilidade QA — editado');
      expect(
        await page
          .getByLabel('Município', { exact: true })
          .evaluate((element) => element.getBoundingClientRect().top + scrollY),
      ).toBe(municipalityBeforeRename);
      await expect(page.locator('.project-preferences')).toContainText('Pausado');
    });
  }
}

test('autosave preserves aside focus, menu, navigation and safe export without enabling project replacement', async ({
  page,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /ESTOU APENAS DANDO UMA OLHADA/ }).click();
  await page.getByRole('button', { name: /Criar novo projeto/ }).click();
  await page.getByLabel('Nome do projeto', { exact: true }).fill('Autosave estável QA');
  await page.getByLabel('Município', { exact: true }).fill('Cidade QA');
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  await page.setViewportSize({ width: 1440, height: 720 });
  const shortMenu = page.getByLabel('Mais ações do projeto');
  await shortMenu.click();
  await expect(page.locator('.action-menu')).toHaveAttribute('data-placement', 'up');
  const shortPopup = await page.locator('.action-menu-content').boundingBox();
  expect(shortPopup!.y).toBeGreaterThanOrEqual(0);
  expect(shortPopup!.y + shortPopup!.height).toBeLessThanOrEqual(720);
  await shortMenu.press('Escape');
  await page.setViewportSize({ width: 1440, height: 1000 });

  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let started = false;
  await page.route('**/api/v1/projects/*', async (route) => {
    if (route.request().method() === 'PUT') {
      started = true;
      await gate;
    }
    await route.continue();
  });
  await page.getByLabel('Observações', { exact: true }).fill('Dados editados durante a sessão.');
  const menu = page.getByLabel('Mais ações do projeto');
  await menu.click();
  await menu.focus();
  await expect.poll(() => started).toBe(true);
  await expect(page.locator('.action-menu')).toHaveAttribute('open');
  await expect(menu).toBeFocused();
  await expect(menu).toHaveAttribute('aria-disabled', 'false');
  const nav = page.getByRole('navigation', { name: 'Espaço de trabalho' });
  await expect(nav.getByRole('button', { name: 'Início', exact: true })).toBeEnabled();
  await expect(nav.getByRole('button', { name: 'Novo projeto', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Salvar projeto', exact: true })).toHaveAttribute(
    'aria-disabled',
    'true',
  );
  await expect(page.getByRole('button', { name: 'Salvar como novo', exact: true })).toHaveAttribute(
    'aria-disabled',
    'true',
  );
  await expect(page.getByRole('button', { name: 'Exportar JSON', exact: true })).toBeEnabled();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  await download;
  await nav.getByRole('button', { name: 'Início', exact: true }).click();
  release();
  await expect(page.getByTestId('project-message')).toContainText('salvas automaticamente');
  const before = await page.locator('[data-workspace-heading]').boundingBox();
  await page.getByRole('button', { name: 'Fechar aviso da operação' }).click();
  const after = await page.locator('[data-workspace-heading]').boundingBox();
  expect(after!.y).toBe(before!.y);
  await nav.getByRole('button', { name: 'Projeto em edição', exact: true }).click();
  await expect(page.getByLabel('Observações', { exact: true })).toHaveValue(
    'Dados editados durante a sessão.',
  );
});
