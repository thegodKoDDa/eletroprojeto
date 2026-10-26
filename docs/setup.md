# Instalação e configuração

O EletroProjeto é uma aplicação web local com frontend e API. Você pode baixar um pacote de fontes com iniciadores, usar Docker ou executar os serviços manualmente. Banco, credenciais e acervo técnico são independentes do código baixado.

## ZIP com iniciadores

[Baixe a versão estável](https://github.com/thegodKoDDa/eletroprojeto/releases/latest/download/EletroProjeto-source.zip), extraia toda a pasta e instale [Python 3.11+](https://www.python.org/downloads/) e [Node.js com npm](https://nodejs.org/en/download/) (20.9+; Node 24 LTS recomendado). Não precisa de Git. Há instruções rápidas em `LEIA-ME.txt`.

### Windows

Abra **Iniciar-EletroProjeto.cmd**. O comando equivalente é:

```powershell
py -3 scripts/start_local.py --setup
```

Não é necessário ativar o ambiente Python nem mudar a política de execução do PowerShell. Mantenha o terminal aberto enquanto usa a aplicação. Se os runtimes não forem encontrados, confira a instalação e o PATH; o pacote não inclui Python/Node nem um `.exe` independente.

### Linux e macOS

Na pasta extraída:

```sh
sh iniciar-eletroprojeto.sh
```

O comando equivalente é `python3 scripts/start_local.py --setup`. A primeira execução prepara dependências pelos arquivos lock, compila a interface e aplica migrações sem reset. Depois, dependências compatíveis e build atual são reutilizados. A preparação inicial precisa de internet; o uso já preparado é local.

### Portas e diretório de dados

O navegador abre após HTTP confirmado. Por padrão: interface 3000, API 8000 e escuta somente no próprio computador. Portas ocupadas são recusadas; nenhum serviço existente é fechado.

```sh
python3 scripts/start_local.py --setup --port 3005 --api-port 8005 --data-dir ./meus-dados
```

- Cópia nova: `data/eletroprojeto.db`.
- Instalação legada com `backend/eletroprojeto.db`: esse banco continua sendo usado.
- `--data-dir`: escolhe explicitamente uma pasta separada.
- `--prepare-only`: prepara/compila sem manter serviços em execução.
- `--no-browser`: inicia sem abrir uma janela do navegador.

O iniciador não altera `.env` nem instala serviço do sistema. Ele escolhe SQLite local; para uma configuração avançada com outra `DATABASE_URL`, use a execução manual. Migrações realmente necessárias em banco existente criam antes uma cópia em `backups/`, junto ao banco. Não delete essa pasta como cache.

## Docker Compose

Com Docker e Compose instalados, entre na pasta extraída ou clonada:

```sh
docker compose up --build
```

Abra **http://127.0.0.1:3000**. O build instala runtimes e dependências dentro da imagem, sem instalar Python/Node no host. O volume `projects` conserva o SQLite em `/data`; não recebe banco ou acervo do desenvolvedor.

Somente a porta da interface é publicada, em loopback. A API fica interna e é acessada pela interface em `/api/v1`. A imagem usa um usuário sem privilégios e preserva avisos de licença. A distribuição é para uso local; não exponha esse modo diretamente na internet.

Para outra porta no Linux/macOS:

```sh
ELETROPROJETO_PORT=3005 docker compose up --build
```

No PowerShell, defina `$env:ELETROPROJETO_PORT = '3005'` antes do comando.

Para encerrar, use Ctrl+C ou `docker compose down`. Para atualizar o código/imagem sem apagar dados:

```sh
docker compose up -d --build
```

Não use `down -v` ou remoção de volumes para atualizar. Native/SQLite legado e Docker têm dados separados; não copie o arquivo ativo entre os modos. Recuperação deve usar uma cópia consistente do banco, com os serviços correspondentes parados. Consulte [continuidade](continuity.md).

## Clone e execução manual

O repositório é público:

```sh
git clone https://github.com/thegodKoDDa/eletroprojeto.git
cd eletroprojeto
```

Você pode usar o mesmo iniciador do ZIP. Para desenvolver com os serviços separados, prepare uma cópia nova:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.lock
backend/.venv/bin/python -m pip install -e backend --no-deps
cd backend
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Em outro terminal, a partir da raiz:

```sh
cd frontend
npm ci
npm run dev
```

No Windows, crie o ambiente com `py -3 -m venv backend/.venv` e use `.venv/Scripts/python.exe`. Se já existe `.venv-windows`, preserve e use esse ambiente. Em uma instalação existente, reutilize dependências e não recrie o banco.

## Configuração manual

Os exemplos estão em [backend/.env.example](../backend/.env.example) e [frontend/.env.example](../frontend/.env.example). O backend lê o ambiente do processo; criar `.env` sozinho não o carrega automaticamente. Next.js também lê `frontend/.env.local`.

| Variável | Uso |
| --- | --- |
| `DATABASE_URL` | Banco da execução manual; padrão `backend/eletroprojeto.db` |
| `AUTH_MODE` | `local` em loopback; remoto exige configuração HTTPS própria |
| `CORS_ORIGINS` | Origens permitidas; localhost/127.0.0.1:3000 por padrão |
| `MAX_REQUEST_BYTES` | Limite de corpo HTTP, 4 MiB por padrão |
| `NEXT_PUBLIC_API_URL` | URL da API; `/api/v1` nos iniciadores e Docker |
| `NEXT_PUBLIC_AUTH_MODE` | Modo do frontend; padrão `local` |
| `API_PROXY_TARGET` | Destino interno do proxy Next; configurado pelo iniciador/Docker |

`NEXT_PUBLIC_*` e rewrites são definidos na compilação; mudar o destino exige novo build. A execução de desenvolvimento mantém o comportamento direto da API quando não há proxy configurado. Modo remoto, contas e sessões estão em [segurança](security.md).

## Atualização e recuperação

Antes de substituir uma versão, encerre sua instância e preserve o banco/pasta de dados ou volume. Em Git, revise alterações locais antes de atualizar. No ZIP, preserve `data/`, o banco legado e os backups; não extraia um pacote de terceiros sobre seus dados.

Relatórios PDF/JSON não restauram projetos completos. A cópia de dados é responsabilidade de cada instalação; publicar o código não copia esses dados para o GitHub.

## Biblioteca técnica e território

Originais normativos, biblioteca importada e coletas territoriais não acompanham fonte, ZIP ou imagem. Sem esses arquivos, recursos dependentes permanecem indisponíveis ou pendentes; cadastro e consumo continuam funcionando. Organização das fontes em [references](../references/README.md).

## Compatibilidade e verificações

Inicialização nativa e Docker foram conferidas em Linux, incluindo HTTP, cálculo, salvamento, PDF e persistência. Windows/macOS têm iniciadores/instruções compatíveis preparados; não foram validados em máquinas desses sistemas nesta entrega. A imagem Docker testada é Linux amd64; não há promessa de executável Windows ou imagem multi-arquitetura pronta.

Para desenvolver e testar, veja [CONTRIBUTING](../CONTRIBUTING.md).
