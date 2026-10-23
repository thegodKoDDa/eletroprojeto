import { test, expect } from '@playwright/test';
import { projectInputs } from '../../src/lib/api';

test('unsent drafts survive reload and conflict recovery preserves both editions', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  const name = `Rascunho recuperado ${Date.now()}`;
  await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
  await page.getByLabel('Município', { exact: true }).fill('São Paulo');
  await page.reload();
  await expect(page.getByRole('region', { name: 'Rascunhos recuperados' })).toContainText(name);
  await page.getByRole('button', { name: 'Continuar rascunho', exact: true }).click();
  await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveValue(name);
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  const listing = await request.get('http://127.0.0.1:8010/api/v1/projects');
  const saved = (await listing.json()).find((project: { name: string }) => project.name === name);
  const updated = await request.put(
    `http://127.0.0.1:8010/api/v1/projects/${saved.id}?expected_version=${saved.version}`,
    {
      data: { ...projectInputs(saved), name: `${name} servidor` },
    },
  );
  expect(updated.ok()).toBeTruthy();
  await page.getByLabel('Nome do projeto', { exact: true }).fill(`${name} local`);
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByRole('alert', { name: 'Resolver conflito de edição' })).toContainText(
    'versão 2',
  );
  await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveValue(`${name} local`);
  await page
    .getByRole('button', { name: 'Salvar minha edição como novo projeto', exact: true })
    .click();
  await expect(page.getByRole('alert', { name: 'Resolver conflito de edição' })).toHaveCount(0);
  const projects = await (await request.get('http://127.0.0.1:8010/api/v1/projects')).json();
  expect(projects.find((project: { id: string }) => project.id === saved.id).name).toBe(
    `${name} servidor`,
  );
  expect(
    projects.some(
      (project: { id: string; name: string }) =>
        project.id !== saved.id && project.name === `${name} local`,
    ),
  ).toBeTruthy();
});

test('full reference workflow, stable editing, persistence and mobile layout', async ({ page }) => {
  const browserErrors: string[] = [];
  page.on('pageerror', (error) => browserErrors.push(error.message));
  page.on('dialog', (dialog) => dialog.accept());
  const calculations: string[] = [];
  page.on('request', (request) => {
    if (request.url().endsWith('/calculations/full')) calculations.push(request.postData() ?? '');
  });
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'Seu próximo projeto começa aqui.' }),
  ).toBeVisible();
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  const projectName = `Casa E2E ${Date.now()}`;
  await page.getByLabel('Nome do projeto', { exact: true }).fill(projectName);
  await page.getByLabel('Município').fill('Município informado');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  let bedroom = page.locator('main article').first();
  await bedroom.getByLabel('Nome', { exact: true }).fill('Quarto');
  await bedroom.getByLabel('Tipo', { exact: true }).selectOption('bedroom');
  const bedroomCatalog = bedroom.getByRole('combobox', { name: 'Adicionar equipamento em Quarto' });
  await bedroomCatalog.selectOption('philips-led-929001195311');
  await bedroomCatalog.selectOption('samsung-tv43-au7700');
  await bedroomCatalog.selectOption('lg-ac-12000-s3w12ja33b');
  const led = bedroom.getByTestId('equipment-editor').nth(0);
  await led.getByLabel('Quantidade', { exact: true }).fill('4');
  const ac = bedroom.getByTestId('equipment-editor').nth(2);
  await expect(ac.getByLabel('Capacidade térmica (BTU/h)')).toHaveValue('12000');
  await expect(ac.getByLabel('Potência unitária (W)')).toHaveValue('1130');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  await expect(page.getByLabel('Resumo de resultados')).toContainText('1,296');

  // A mounted row, focused input and expanded memory survive debounce/recalculation.
  await page.locator('#results').getByText('Referências e rastreabilidade').click();
  await page.evaluate(() => {
    const section = document.querySelector('#results')!;
    (window as unknown as { savedMemoryNode: Element | null }).savedMemoryNode =
      section.querySelector('.divide-y > div');
  });
  const power = led.getByLabel('Potência unitária (W)', { exact: true });
  await power.fill('12');
  await expect(power).toBeFocused();
  await expect(page.locator('#results')).toHaveAttribute('data-stale', 'true');
  await page.getByLabel('Mais ações do projeto').click();
  await expect(page.getByRole('button', { name: 'Exportar JSON' })).toBeDisabled();
  await expect(
    page
      .locator('#results details')
      .filter({ has: page.getByText('Referências e rastreabilidade', { exact: true }) }),
  ).toHaveAttribute('open', '');
  await expect(page.locator('#results')).toHaveAttribute('data-stale', 'false');
  expect(
    await page.evaluate(
      () =>
        (window as unknown as { savedMemoryNode: Element | null }).savedMemoryNode ===
        document.querySelector('#results .divide-y > div'),
    ),
  ).toBe(true);
  await led.getByRole('button', { name: 'Restaurar sugestão' }).click();

  await page.getByRole('button', { name: 'Adicionar ambiente', exact: true }).click();
  const bathroom = page.locator('main article').nth(1);
  await bathroom.getByLabel('Nome', { exact: true }).fill('Banheiro');
  await bathroom.getByLabel('Tipo', { exact: true }).selectOption('bathroom');
  await bathroom
    .getByRole('combobox', { name: 'Adicionar equipamento em Banheiro' })
    .selectOption('lorenzetti-advanced-220-7500');
  const shower = bathroom.getByTestId('equipment-editor').first();
  await shower.getByLabel('Potência unitária (W)').fill('5500');
  await shower.getByText(/Configurações avançadas/).click();
  await shower.getByLabel('Tensão nominal (V)').fill('127');
  await shower.getByRole('button', { name: 'Duplicar equipamento' }).click();
  const secondShower = bathroom.getByTestId('equipment-editor').nth(1);
  await secondShower.getByLabel('Potência unitária (W)').fill('7500');
  await secondShower.getByText(/Configurações avançadas/).click();
  await secondShower.getByLabel('Tensão nominal (V)').fill('220');
  await secondShower.getByLabel('Origem da potência').selectOption('nameplate');
  await expect(page.getByLabel('Resumo de resultados')).toContainText('14,296');
  await expect(page.locator('#results')).toContainText('Dados do projeto a revisar');
  await page.getByLabel('Requisitos para').selectOption('current');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  const correctVoltage = page.getByRole('button', {
    name: /Corrigir informação: Quarto → Lâmpada LED · Tensão nominal/,
  });
  await correctVoltage.click();
  await expect(led.getByLabel('Tensão nominal (V)')).toBeFocused();
  await led.getByLabel('Tensão nominal (V)').fill('127');
  await expect(correctVoltage).toHaveCount(0);
  await page
    .getByRole('button', {
      name: /Corrigir informação: Quarto → Lâmpada LED · Configuração para corrente/,
    })
    .click();
  await expect(led.getByTestId('equipment-advanced')).toHaveAttribute('open', '');
  await expect(led.getByLabel('Configuração para corrente')).toBeFocused();
  await led.getByLabel('Configuração para corrente').selectOption('single_phase');
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  await page.reload();
  await page.locator('aside').getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  await page
    .getByRole('region', { name: 'Projetos salvos' })
    .getByRole('button', { name: projectName, exact: true })
    .click();
  await expect(page.getByLabel('Resumo de resultados')).toContainText('14,296');
  bedroom = page.locator('main article').first();
  await expect(
    bedroom.getByTestId('equipment-editor').nth(2).getByLabel('Capacidade térmica (BTU/h)'),
  ).toHaveValue('12000');
  await expect(
    page
      .locator('main article')
      .nth(1)
      .getByTestId('equipment-editor')
      .nth(1)
      .getByLabel('Potência unitária (W)'),
  ).toHaveValue('7500');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar PDF', exact: true }).click();
  expect((await download).suggestedFilename()).toBe(`${projectName}.pdf`);
  const count = calculations.length;
  await page.waitForTimeout(1200);
  expect(calculations).toHaveLength(count); // no idle calculation loop
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
  expect(browserErrors).toEqual([]);
});

test('five saved projects survive reload, library navigation and independent updates', async ({
  page,
  request,
}) => {
  page.on('dialog', (dialog) => dialog.accept());
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  const prefix = `Casas independentes ${Date.now()}`;
  const ids: string[] = [];
  for (let i = 0; i < 5; i++) {
    if (i) {
      await page.getByLabel('Mais ações do projeto').click();
      await page.getByRole('button', { name: 'Novo projeto', exact: true }).click();
    }
    await page.getByLabel('Nome do projeto', { exact: true }).fill(`${prefix} ${i}`);
    await page.getByLabel('Município', { exact: true }).fill('Cidade informada');
    const response = page.waitForResponse(
      (r) => r.url().endsWith('/api/v1/projects') && r.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
    ids.push((await (await response).json()).id);
    await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  }
  expect(new Set(ids).size).toBe(5);
  const workspace = page.locator('aside');
  await expect(workspace.locator('article')).toHaveCount(0);
  await page.reload();
  await expect(workspace.locator('article')).toHaveCount(0);
  await workspace.getByRole('button', { name: 'Projetos salvos' }).click();
  const library = page.getByRole('region', { name: 'Projetos salvos' });
  await library.getByLabel('Pesquisar projetos').fill(prefix);
  await expect(library.locator('article')).toHaveCount(5);
  for (const id of ids)
    expect((await request.get(`http://127.0.0.1:8010/api/v1/projects/${id}`)).ok()).toBe(true);
  await library.getByRole('button', { name: `${prefix} 0`, exact: true }).click();
  await page.getByLabel('Nome do projeto', { exact: true }).fill(`${prefix} editada`);
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  for (let i = 1; i < ids.length; i++) {
    const data = await (
      await request.get(`http://127.0.0.1:8010/api/v1/projects/${ids[i]}`)
    ).json();
    expect(data.name).toBe(`${prefix} ${i}`);
  }
});

test('home, draft continuity, library, duplication, trash and exports work together', async ({
  page,
  request,
}) => {
  const { readFile } = await import('node:fs/promises');
  page.on('dialog', (dialog) => dialog.accept());
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'Seu próximo projeto começa aqui.' }),
  ).toBeVisible();
  await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveCount(0);
  await page.screenshot({ path: '/tmp/eletroprojeto-home-desktop.png', fullPage: true });
  const name = `Casa integrada ${Date.now()}`;
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
  await page.getByLabel('Município', { exact: true }).fill('Cidade de teste');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  const room = page.locator('main article').first();
  await room.getByLabel('Nome', { exact: true }).fill('Sala');
  await room.getByLabel('Área (m²)', { exact: true }).fill('12.5');
  await room.getByLabel('Perímetro (m)', { exact: true }).fill('15');
  await room.getByLabel('Pontos de luz', { exact: true }).fill('2');
  await room.getByLabel('Pontos de tomadas', { exact: true }).fill('4');
  await room
    .getByRole('combobox', { name: 'Adicionar equipamento em Sala' })
    .selectOption('philips-led-929001195311');
  await room.getByLabel('Quantidade', { exact: true }).fill('3');
  await page.getByRole('button', { name: 'Início', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Continuar edição', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Continuar edição', exact: true }).click();
  await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveValue(name);
  await expect(page.getByLabel('Resumo de resultados')).toContainText('27 W');
  const saving = page.waitForResponse(
    (r) => r.url().endsWith('/api/v1/projects') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  const id = (await (await saving).json()).id;
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  await page.getByLabel('Mais ações do projeto').click();
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  const downloaded = await downloading;
  expect(downloaded.suggestedFilename()).toBe(`${name}.json`);
  const json = JSON.parse(await readFile((await downloaded.path())!, 'utf8'));
  expect(json.ambientes[0]).toMatchObject({
    area_m2: '12.5',
    perimetro_m: '15',
    pontos_de_luz: 2,
    tug: 4,
    potencia_conhecida_w: '27',
  });
  expect(json.emissao.fuso).toBe('America/Sao_Paulo');
  const sidebar = page.locator('aside');
  await sidebar.getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  const library = page.getByRole('region', { name: 'Projetos salvos' });
  await library.getByLabel('Pesquisar projetos').fill(name);
  await library.getByRole('button', { name: `Duplicar ${name}`, exact: true }).click();
  await expect(library.locator('article')).toHaveCount(2);
  await library.getByRole('button', { name: `Excluir ${name}`, exact: true }).click();
  await expect(library.locator('article')).toHaveCount(1);
  await sidebar.getByRole('button', { name: 'Início', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Seu próximo projeto começa aqui.' }),
  ).toBeVisible();
  await sidebar.getByRole('button', { name: 'Lixeira', exact: true }).click();
  const trash = page.getByRole('region', { name: 'Lixeira' });
  await trash.getByRole('button', { name: `Restaurar ${name}`, exact: true }).click();
  await expect(trash.locator('article')).toHaveCount(0);
  await sidebar.getByRole('button', { name: 'Início', exact: true }).click();
  const restored = await (await request.get(`http://127.0.0.1:8010/api/v1/projects/${id}`)).json();
  expect(restored.environments[0].loads[0].quantity).toBe(3);
  // Delete only this test's restored record, then exercise the confirmed purge flow.
  await sidebar.getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  await library.getByRole('button', { name: `Excluir ${name}`, exact: true }).click();
  await sidebar.getByRole('button', { name: 'Início', exact: true }).click();
  await sidebar.getByRole('button', { name: 'Lixeira', exact: true }).click();
  await trash.getByRole('button', { name: `Excluir definitivamente ${name}`, exact: true }).click();
  await expect(trash.locator('article')).toHaveCount(0);
  await sidebar.getByRole('button', { name: 'Início', exact: true }).click();
  expect((await request.get(`http://127.0.0.1:8010/api/v1/projects/${id}`)).status()).toBe(404);
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
    expect(await sidebar.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(
      true,
    );
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: '/tmp/eletroprojeto-home-mobile.png', fullPage: true });
});

test('workspace buttons remain usable between sections, with clear focus and busy states', async ({
  page,
}) => {
  await page.goto('/');
  const sidebar = page.locator('aside');
  await expect(sidebar.getByText('Recentes', { exact: true })).toHaveCount(0);
  await sidebar.getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Projetos salvos', exact: true })).toBeFocused();
  await page.getByLabel('Pesquisar projetos').fill('Filtro sem correspondência');
  await sidebar.getByRole('button', { name: 'Lixeira', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Lixeira' })).toBeVisible();
  await expect(page.getByLabel('Pesquisar projetos')).toHaveValue('');
  await expect(sidebar.getByRole('button', { name: 'Lixeira', exact: true })).toHaveAttribute(
    'aria-current',
    'page',
  );
  await sidebar.getByRole('button', { name: 'Novo projeto', exact: true }).focus();
  await page.keyboard.press('Enter');
  const name = `Polimento ${Date.now()} ${'Projeto residencial '.repeat(5)}`.trim();
  await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
  await page.getByLabel('Município', { exact: true }).fill('Cidade de teste');
  const menu = page.getByLabel('Mais ações do projeto');
  await menu.click();
  await menu.press('Escape');
  await expect(menu).toBeFocused();
  await expect(menu.locator('..')).not.toHaveAttribute('open', '');
  let releaseSave!: () => void;
  const saveGate = new Promise<void>((resolve) => {
    releaseSave = resolve;
  });
  await page.route('**/api/v1/projects', async (route) => {
    if (route.request().method() === 'POST') await saveGate;
    await route.continue();
  });
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Salvando…', exact: true })).toBeDisabled();
  await expect(sidebar.getByRole('button', { name: 'Início', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Exportar PDF', exact: true })).toBeDisabled();
  await expect(menu).toHaveAttribute('aria-disabled', 'true');
  releaseSave();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  await sidebar.getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  await page.getByLabel('Pesquisar projetos').fill(name);
  await expect(page.getByRole('button', { name, exact: true })).toBeVisible();
  await page.screenshot({ path: '/tmp/eletroprojeto-library-desktop.png', fullPage: true });
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    ).toBe(true);
    expect(await sidebar.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(
      true,
    );
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: '/tmp/eletroprojeto-library-mobile.png', fullPage: true });
  await sidebar.getByRole('button', { name: 'Projeto em edição', exact: true }).click();
  await expect(page.getByLabel('Nome do projeto', { exact: true })).toHaveValue(name);
  await sidebar.getByRole('button', { name: 'Início', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(
    page.getByRole('heading', { name: 'Seu próximo projeto começa aqui.' }),
  ).toBeFocused();
});

test('monthly energy, cost, manual recalculation and saved schedules stay consistent', async ({
  page,
}) => {
  page.on('dialog', (dialog) => dialog.accept());
  const response = await page.goto('/');
  expect(response?.headers()['x-content-type-options']).toBe('nosniff');
  expect(response?.headers()['x-frame-options']).toBe('DENY');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  const name = `Consumo ${Date.now()}`;
  await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
  await page.getByLabel('Município', { exact: true }).fill('Cidade de teste');
  await page.getByText('Outros dados do projeto', { exact: true }).click();
  await page.getByLabel('Tarifa de energia (R$/kWh)').fill('0.8');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  const room = page.locator('main article').first();
  await room
    .getByRole('combobox', { name: /Adicionar equipamento em/ })
    .selectOption('philips-led-929001195311');
  const load = room.getByTestId('equipment-editor');
  await load.getByLabel('Quantidade', { exact: true }).fill('4');
  await load.getByText('Consumo mensal (opcional)', { exact: true }).click();
  await load.getByLabel('Horas de uso por dia').fill('5');
  await load.getByLabel('Dias de uso por mês').fill('30');
  const energy = page.getByLabel('Consumo e custo mensais');
  await expect(energy).toContainText('5,4 kWh/mês');
  await expect(energy).toContainText('R$ 4,32');
  await load.getByLabel('Potência unitária (W)').fill('20');
  await expect(energy).toContainText('12 kWh/mês');
  await expect(energy).toContainText('R$ 9,6');
  await load.getByLabel('Dias de uso por mês').fill('32');
  await expect(load.getByLabel('Dias de uso por mês')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.getByRole('button', { name: 'Exportar PDF', exact: true })).toBeDisabled();
  await load.getByLabel('Dias de uso por mês').fill('30');
  await load.getByLabel('Consumo de energia (kWh/mês)').fill('40');
  await expect(load.getByLabel('Horas de uso por dia')).toBeDisabled();
  await expect(energy).toContainText('160 kWh/mês');
  await load.getByLabel('Consumo de energia (kWh/mês)').fill('');
  await expect(energy).toContainText('12 kWh/mês');
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  await page.reload();
  await page.locator('aside').getByRole('button', { name: 'Projetos salvos', exact: true }).click();
  await page.getByRole('button', { name, exact: true }).click();
  await expect(page.getByLabel('Consumo e custo mensais')).toContainText('12 kWh/mês');
  await load.getByText('Consumo mensal (opcional)', { exact: true }).click();
  await expect(load.getByLabel('Horas de uso por dia')).toHaveValue('5');
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: '/tmp/eletroprojeto-energy-mobile.png', fullPage: true });
});

test('research coverage is informative while real input problems remain correctable', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByLabel('Município', { exact: true }).fill('Cidade de teste');
  await page.getByLabel('Concessionária', { exact: true }).selectOption('energisa_sul_sudeste');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  const room = page.locator('main article').first();
  await room
    .getByRole('combobox', { name: /Adicionar equipamento em/ })
    .selectOption('philips-led-929001195311');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  await expect(page.locator('#results')).toContainText(
    'Nenhum dado pendente para o cálculo selecionado.',
  );
  await expect(page.getByLabel('Resumo de resultados')).not.toContainText('Demanda');
  await expect(page.locator('#results')).not.toContainText('Procedimento não validado');
  const coverage = page.getByLabel('Cobertura normativa');
  await expect(coverage.locator('details').first()).not.toHaveAttribute('open', '');
  await coverage.getByText('Recursos normativos ainda indisponíveis (1)', { exact: true }).click();
  await expect(coverage).toContainText('Não indicam erros na sua instalação');
  await coverage
    .getByText('Pesquisa e fontes de demanda da distribuidora', { exact: true })
    .click();
  await expect(
    coverage.getByRole('link', { name: 'Energisa NDU-001 — PDF oficial' }),
  ).toBeVisible();
  const registry = await (
    await request.get(
      'http://127.0.0.1:8010/api/v1/technical/rules?utility=energisa_sul_sudeste&state=SP',
    )
  ).json();
  expect(registry.coverage.filter((item: { available: boolean }) => item.available)).toHaveLength(
    2,
  );
  expect(
    registry.coverage
      .find((item: { code: string }) => item.code === 'demand')
      .evidence.some((item: { section: string | null }) => item.section?.includes('9.1')),
  ).toBe(true);
  const power = room.getByLabel('Potência unitária (W)');
  await power.fill('');
  await expect(
    page
      .locator('#results')
      .getByRole('button', { name: /Corrigir informação:.*Potência unitária/ }),
  ).toBeVisible();
  await power.fill('9');
  await expect(
    page
      .locator('#results')
      .getByRole('button', { name: /Corrigir informação:.*Potência unitária/ }),
  ).toHaveCount(0);
  await page.getByLabel('Concessionária', { exact: true }).selectOption('cpfl_paulista');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  await expect(coverage.getByRole('link', { name: 'Energisa NDU-001 — PDF oficial' })).toHaveCount(
    0,
  );
  await coverage
    .getByText('Pesquisa e fontes de demanda da distribuidora', { exact: true })
    .click();
  await expect(coverage.getByRole('link', { name: 'CPFL GED-13' })).toBeVisible();
  await page.screenshot({ path: '/tmp/eletroprojeto-coverage-desktop.png', fullPage: true });
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: '/tmp/eletroprojeto-coverage-mobile.png', fullPage: true });
});

test('residential prevision recalculates geometry and manual points, and exports concise results', async ({
  page,
}) => {
  const { readFile } = await import('node:fs/promises');
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  const name = `Previsão residencial ${Date.now()}`;
  await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
  await page.getByLabel('Município', { exact: true }).fill('Cidade');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  const room = page.locator('main article').first();
  await room.getByLabel('Nome', { exact: true }).fill('Quarto residencial');
  await room.getByLabel('Tipo', { exact: true }).selectOption('bedroom');
  await page.getByLabel('Requisitos para').selectOption('normative');
  await expect(
    page.locator('#results').getByRole('button', { name: /Corrigir informação:.*Área/ }),
  ).toBeVisible();
  await room.getByLabel('Área (m²)', { exact: true }).fill('12');
  await room.getByLabel('Perímetro (m)', { exact: true }).fill('14');
  await room.getByLabel('Pontos de tomadas', { exact: true }).fill('5');
  const prevision = page.getByLabel('Previsão residencial por ambiente');
  await expect(prevision).toContainText('Iluminação: 160 VA');
  await expect(prevision).toContainText('TUG: 5 cadastrado(s) · mínimo 3');
  await expect(prevision).toContainText('500 VA · 5 ponto(s) considerados');
  await room.getByLabel('Área (m²)', { exact: true }).fill('14');
  await expect(prevision).toContainText('Iluminação: 220 VA');
  await expect(room.getByLabel('Pontos de tomadas', { exact: true })).toHaveValue('5');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  await page.getByLabel('Mais ações do projeto').click();
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  const file = await downloading;
  expect(file.suggestedFilename()).toBe(`${name}.json`);
  const data = JSON.parse(await readFile((await file.path())!, 'utf8'));
  expect(data.previsao_residencial_por_ambiente[0]).toMatchObject({
    iluminacao_va: '220',
    minimo_pontos_tug: 3,
    pontos_tug_considerados: 5,
    previsao_tug_va: '500',
  });
  expect(data.previsoes_normativas.demand.valor).toBeNull();
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: '/tmp/eletroprojeto-residential-mobile.png', fullPage: true });
});

test('room duplication preserves manual data, creates independent IDs and survives saving', async ({
  page,
  request,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByLabel('Nome do projeto', { exact: true }).fill(`Ambientes ${Date.now()}`);
  await page.getByLabel('Município', { exact: true }).fill('Cidade');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  const rooms = page.locator('#environments > .space-y-5 > article');
  const original = rooms.nth(0);
  await original.getByLabel('Nome', { exact: true }).fill('Quarto');
  await original.getByLabel('Área (m²)', { exact: true }).fill('12');
  await original.getByLabel('Perímetro (m)', { exact: true }).fill('14');
  await original.getByLabel('Pontos de tomadas', { exact: true }).fill('5');
  await original
    .getByRole('combobox', { name: 'Adicionar equipamento em Quarto' })
    .selectOption('philips-led-929001195311');
  await original.getByLabel('Potência unitária (W)', { exact: true }).fill('12');
  await original.getByLabel('Quantidade', { exact: true }).fill('3');
  await original.getByRole('button', { name: 'Duplicar ambiente Quarto', exact: true }).click();
  await expect(rooms).toHaveCount(2);
  const copy = rooms.nth(1);
  await expect(copy.getByLabel('Nome', { exact: true })).toBeFocused();
  await expect(copy.getByLabel('Nome', { exact: true })).toHaveValue('Quarto — cópia');
  await expect(copy.getByLabel('Área (m²)', { exact: true })).toHaveValue('12');
  await expect(copy.getByLabel('Potência unitária (W)', { exact: true })).toHaveValue('12');
  await copy.getByLabel('Potência unitária (W)', { exact: true }).fill('20');
  await expect(original.getByLabel('Potência unitária (W)', { exact: true })).toHaveValue('12');
  await expect(page.getByLabel('Resumo de resultados')).toContainText('96 W');
  const saving = page.waitForResponse(
    (r) => r.url().endsWith('/api/v1/projects') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  const saved = await (await saving).json();
  expect(new Set(saved.environments.map((r: { id: string }) => r.id)).size).toBe(2);
  expect(
    new Set(
      saved.environments.flatMap((r: { loads: { id: string }[] }) => r.loads.map((l) => l.id)),
    ).size,
  ).toBe(2);
  const restored = await (
    await request.get(`http://127.0.0.1:8010/api/v1/projects/${saved.id}`)
  ).json();
  expect(
    restored.environments.map(
      (r: { loads: { unit_power_w: string }[] }) => r.loads[0].unit_power_w,
    ),
  ).toEqual(['12', '20']);
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    await expect(
      page.getByRole('button', { name: 'Adicionar ambiente', exact: true }),
    ).toBeVisible();
  }
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: '/tmp/eletroprojeto-design-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: '/tmp/eletroprojeto-design-mobile.png', fullPage: true });
});

test('PDF and JSON exports carry energy coverage, use assumptions and residential measures', async ({
  page,
}) => {
  const { readFile } = await import('node:fs/promises');
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  const name = `Relatório de consumo ${Date.now()}`;
  await page.getByLabel('Nome do projeto', { exact: true }).fill(name);
  await page.getByLabel('Município', { exact: true }).fill('Cidade');
  await page.getByLabel('Concessionária', { exact: true }).selectOption('energisa_sul_sudeste');
  await page.getByText('Outros dados do projeto', { exact: true }).click();
  await page.getByLabel('Tarifa de energia (R$/kWh)').fill('0.8');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente' }).click();
  const room = page.locator('#environments article').first();
  await room.getByLabel('Nome', { exact: true }).fill('Quarto');
  await room.getByLabel('Tipo', { exact: true }).selectOption('bedroom');
  await room.getByLabel('Área (m²)', { exact: true }).fill('12');
  await room.getByLabel('Perímetro (m)', { exact: true }).fill('14');
  await room.getByLabel('Pontos de tomadas', { exact: true }).fill('5');
  await page.getByLabel('Requisitos para').selectOption('normative');
  const picker = room.getByRole('combobox', { name: 'Adicionar equipamento em Quarto' });
  await picker.selectOption('philips-led-929001195311');
  const led = room.getByTestId('equipment-editor').first();
  await led.getByLabel('Quantidade', { exact: true }).fill('4');
  await led.getByText('Consumo mensal (opcional)', { exact: true }).click();
  await led.getByLabel('Horas de uso por dia').fill('5');
  await led.getByLabel('Dias de uso por mês').fill('30');
  await picker.selectOption('samsung-tv43-au7700');
  await expect(page.getByTestId('calculation-status')).toContainText('Resultados atualizados');
  await page.getByLabel('Mais ações do projeto').click();
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  const jsonFile = await downloading;
  expect(jsonFile.suggestedFilename()).toBe(`${name}.json`);
  const data = JSON.parse(await readFile((await jsonFile.path())!, 'utf8'));
  expect(Number(data.resultados.consumo_mensal.valor)).toBe(5.4);
  expect(Number(data.resultados.custo_mensal_estimado.valor)).toBe(4.32);
  expect(data.consumo).toMatchObject({
    situacao: 'parcial',
    cargas_com_estimativa: 1,
    cargas_sem_estimativa: 1,
    tarifa_brl_por_kwh: '0.8',
  });
  expect(data.pendencias_consumo[0].equipamento).toBeTruthy();
  expect(data.equipamentos[0]).toMatchObject({
    quantidade: 4,
    horas_por_dia: '5',
    dias_por_mes: 30,
  });
  expect(data.ambientes[0]).toMatchObject({ area_m2: '12', perimetro_m: '14', tug: 5 });
  expect(data.previsao_residencial_por_ambiente[0]).toMatchObject({
    minimo_pontos_tug: 3,
    pontos_tug_considerados: 5,
  });
  expect(data.atendimento_distribuidora.demanda_disponivel).toBe(false);
  expect(data.previsoes_normativas.demand.valor).toBeNull();
  expect(JSON.stringify(data)).not.toContain('source_url');
  await expect(page.getByRole('button', { name: 'Exportar PDF', exact: true })).toBeEnabled();
  const pdfDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar PDF', exact: true }).click();
  const pdf = await pdfDownload;
  expect(pdf.suggestedFilename()).toBe(`${name}.pdf`);
  expect((await readFile((await pdf.path())!)).subarray(0, 4).toString()).toBe('%PDF');
});

test('shower reference variants retain usage through restoration, saving and JSON export', async ({
  page,
}) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Criar novo projeto/ }).click();
  await page.getByLabel('Nome do projeto', { exact: true }).fill(`Variantes ${Date.now()}`);
  await page.getByLabel('Município', { exact: true }).fill('São Paulo');
  await page.getByRole('button', { name: 'Adicionar primeiro ambiente', exact: true }).click();
  const room = page.locator('#environments article').first();
  await room.getByLabel('Nome', { exact: true }).fill('Banheiro');
  await room.getByLabel('Tipo', { exact: true }).selectOption('bathroom');
  await room
    .getByLabel('Adicionar equipamento em Banheiro', { exact: true })
    .selectOption('lorenzetti-advanced-220-7500');
  const load = room.getByTestId('equipment-editor');
  await load.getByTestId('equipment-energy').locator('summary').click();
  await load.getByLabel('Horas de uso por dia', { exact: true }).fill('0.5');
  await load.getByLabel('Dias de uso por mês', { exact: true }).fill('30');
  await load.getByTestId('equipment-advanced').locator('summary').click();
  await load
    .getByLabel('Variante de referência', { exact: true })
    .selectOption('lorenzetti-advanced-127-5500');
  await expect(load.getByLabel('Potência unitária (W)', { exact: true })).toHaveValue('5500');
  await expect(load.getByLabel('Tensão nominal (V)', { exact: true })).toHaveValue('127');
  await load.getByLabel('Potência unitária (W)', { exact: true }).fill('5000');
  await load
    .getByLabel('Variante de referência', { exact: true })
    .selectOption('lorenzetti-advanced-220-7500');
  await expect(load.getByLabel('Potência unitária (W)', { exact: true })).toHaveValue('5000');
  await load.getByRole('button', { name: 'Restaurar sugestão' }).click();
  await expect(load.getByLabel('Potência unitária (W)', { exact: true })).toHaveValue('7500');
  await expect(load.getByLabel('Horas de uso por dia', { exact: true })).toHaveValue('0.5');
  await expect(page.getByLabel('Consumo e custo mensais')).toContainText('112,5 kWh/mês');
  await page.getByRole('button', { name: 'Salvar projeto', exact: true }).click();
  await expect(page.getByTestId('project-message')).toContainText('Projeto salvo');
  await page.getByLabel('Mais ações do projeto').click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Exportar JSON', exact: true }).click();
  const { readFile } = await import('node:fs/promises');
  const file = await download;
  const report = JSON.parse(await readFile((await file.path())!, 'utf8'));
  expect(report.formato_versao).toBe('1.2');
  expect(report.equipamentos[0].potencia_personalizada).toBe(false);
  expect(report.equipamentos[0].horas_por_dia).toBe('0.5');
  expect(Number(report.resultados.consumo_mensal.valor)).toBe(112.5);
});
