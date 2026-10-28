import { test, expect } from '../support/workspace-test';
import AxeBuilder from '@axe-core/playwright';

test('shared interface and real report validation preserve the simple workflow', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByLabel('Município', { exact: true }).fill('Cidade QA');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
  await page
    .getByLabel('Adicionar equipamento em Novo ambiente', { exact: true })
    .selectOption('philips-led-929001195311');
  await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
  const titleStyle = () =>
    page.locator('.page-header h1').evaluate((element) => {
      const style = getComputedStyle(element);
      return [style.fontSize, style.fontWeight, style.lineHeight, style.letterSpacing];
    });
  const projectStyle = await titleStyle();
  expect((await page.getByLabel('Nome do projeto', { exact: true }).boundingBox())!.height).toBe(
    (await page.getByRole('button', { name: 'Salvar projeto', exact: true }).boundingBox())!.height,
  );
  // Modify only the QA report request: the actual API must return a localized 422.
  await page.route('**/reports/pdf', async (route) => {
    const body = route.request().postDataJSON();
    body.project.environments[0].loads[0].parameters.usage_days_per_month = 32;
    await route.continue({ postData: JSON.stringify(body) });
  });
  const failed = page.waitForResponse((response) => response.url().endsWith('/reports/pdf'));
  await page.getByRole('button', { name: 'Exportar PDF', exact: true }).click();
  expect((await failed).status()).toBe(422);
  await expect(page.getByTestId('project-message')).toHaveAttribute('data-tone', 'error');
  await page.getByRole('button', { name: /Corrigir informação:.*Dias de uso por mês/ }).click();
  await expect(page.getByLabel('Dias de uso por mês', { exact: true })).toBeFocused();
  await page.unroute('**/reports/pdf');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar PDF', exact: true }).click();
  expect((await download).suggestedFilename()).toMatch(/\.pdf$/);
  await expect(page.getByTestId('project-message')).toHaveAttribute('data-tone', 'success');
  const sidebar = page.locator('.workspace-sidebar');
  for (const name of ['Projetos salvos', 'Lixeira', 'Biblioteca técnica']) {
    await sidebar.getByRole('button', { name, exact: true }).click();
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
    expect(await titleStyle()).toEqual(projectStyle);
    await expect(page.locator('.pagination').first()).toHaveAttribute('aria-busy', 'false');
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      );
      if (width === 390 || width === 1440)
        await page.screenshot({
          path: `/tmp/eletroprojeto-standard-${name.replaceAll(' ', '-')}-${width}.png`,
          fullPage: true,
        });
    }
    expect(
      (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze())
        .violations,
    ).toEqual([]);
  }
  await sidebar.getByRole('button', { name: 'Projeto em edição', exact: true }).click();
  await expect(page.getByTestId('equipment-editor')).toHaveCount(1);
  await expect(page.locator('.technical-tools')).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('reading and source errors can be retried without losing reference or filters', async ({
  page,
}) => {
  let failPage = true;
  let failSource = true;
  await page.route('**/knowledge/documents/*/pages?*', async (route) => {
    if (failPage) {
      await route.fulfill({
        status: 503,
        json: { detail: 'Leitura temporariamente indisponível.' },
      });
    } else await route.continue();
  });
  await page.route('**/knowledge/sources?*', async (route) => {
    if (failSource) {
      await route.fulfill({
        status: 503,
        json: { detail: 'Fontes temporariamente indisponíveis.' },
      });
    } else await route.continue();
  });
  await page.goto('/');
  await page
    .locator('.workspace-sidebar')
    .getByRole('button', { name: 'Biblioteca técnica', exact: true })
    .click();
  await page.getByLabel('Buscar no conteúdo e nas fontes').fill('potencia');
  await page.getByRole('button', { name: /Guia QA de chuveiro/ }).click();
  await expect(page.locator('.knowledge-reader .feedback[role=alert]')).toContainText(
    'Leitura temporariamente indisponível',
  );
  failPage = false;
  await page.getByRole('button', { name: 'Tentar leitura novamente', exact: true }).click();
  await expect(page.locator('.knowledge-text')).toContainText('não dimensiona sozinha');
  await expect(page.getByLabel('Buscar no conteúdo e nas fontes')).toHaveValue('potencia');
  await page.getByText('Fontes e situação dos downloads', { exact: true }).click();
  await expect(page.locator('.feedback[role=alert]')).toContainText(
    'Fontes temporariamente indisponíveis',
  );
  failSource = false;
  await page.getByRole('button', { name: 'Tentar fontes novamente', exact: true }).click();
  await expect(page.getByText('Fonte QA indisponível', { exact: true })).toBeVisible();
  await expect(page.getByRole('combobox', { name: 'Situação da coleta', exact: true })).toHaveValue(
    'falha_download',
  );
  await expect(page.locator('.knowledge-text')).toContainText('não dimensiona sozinha');
});
