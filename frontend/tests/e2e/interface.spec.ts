import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('section hierarchy, notes, autosave and action menu stay usable across viewports', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  const name = `Polimento visual ${Date.now()}`;
  await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
  await page.getByLabel('Município', { exact: true }).fill('Município informado');
  const autosave = page.getByLabel('Salvar automaticamente após o primeiro salvamento', {
    exact: true,
  });
  const notes = page.getByLabel('Observações', { exact: true });
  await expect(autosave).toBeVisible();
  await expect(notes).toBeVisible();
  await expect(notes).toHaveAttribute('aria-describedby', 'project-notes-description');
  await expect(page.locator('.project-preferences')).toContainText('Após salvar');
  await expect(page.locator('.project-extra')).not.toHaveAttribute('open', '');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  await page
    .getByLabel('Adicionar equipamento em Novo ambiente', { exact: true })
    .selectOption('philips-led-929001195311');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  const typography = await page
    .locator(
      '#project .section-heading h2, #environments .section-heading h2, #results .section-heading h2',
    )
    .evaluateAll((nodes) =>
      nodes.map((node) => {
        const style = getComputedStyle(node);
        return [style.fontSize, style.fontWeight, style.lineHeight].join('|');
      }),
    );
  expect(typography).toHaveLength(3);
  expect(new Set(typography).size).toBe(1);
  const multiline =
    'Conferir a placa dos equipamentos.\nManter os valores informados.\nObservações preservadas no projeto.';
  await notes.fill(multiline);
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  const listing = await (await request.get('http://127.0.0.1:8010/api/v1/projects')).json();
  const saved = listing.find((project: { name: string }) => project.name === name);
  expect(saved.notes).toBe(multiline);
  await autosave.uncheck();
  await expect(page.locator('.project-preferences')).toContainText('Desativado');
  await notes.fill(multiline + '\nEdição manual.');
  // The pause exceeds the real autosave debounce and confirms that disabling it prevents a PUT.
  await page.waitForTimeout(1800);
  const unchanged = await (
    await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`)
  ).json();
  expect(unchanged.notes).toBe(multiline);
  await autosave.check();
  await expect
    .poll(
      async () =>
        (await (await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`)).json())
          .notes,
    )
    .toBe(multiline + '\nEdição manual.');
  const menu = page.getByLabel('Mais ações do projeto');
  await menu.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.action-menu')).toHaveAttribute('open', '');
  await page.keyboard.press('Escape');
  await expect(page.locator('.action-menu')).not.toHaveAttribute('open', '');
  await expect(menu).toBeFocused();
  await menu.click();
  await page.getByRole('heading', { name: 'Cargas da residência' }).click();
  await expect(page.locator('.action-menu')).not.toHaveAttribute('open', '');
  await menu.click();
  await expect(page.getByRole('button', { name: 'Salvar como novo', exact: true })).toBeVisible();
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
      .violations,
  ).toEqual([]);
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    const checkbox = await autosave.boundingBox();
    expect(checkbox!.width).toBeGreaterThanOrEqual(18);
    expect(checkbox!.width).toBeLessThanOrEqual(22);
    expect(checkbox!.height).toBeLessThanOrEqual(22);
    expect((await notes.boundingBox())!.height).toBeGreaterThanOrEqual(130);
    if (width === 390 || width === 1440) {
      await page
        .locator('#project')
        .screenshot({ path: `/tmp/eletroprojeto-project-polish-${width}.png` });
      await page
        .locator('.sidebar-actions')
        .screenshot({ path: `/tmp/eletroprojeto-actions-polish-${width}.png` });
    }
  }
});
