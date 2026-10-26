# Instalação e configuração

Requisitos: Python 3.11 ou superior, Node.js 20.9 ou superior, npm e Git. O repositório é privado; o clone exige uma conta com acesso.

Os comandos de instalação abaixo são para uma cópia nova. Em uma instalação existente, reutilize o ambiente Python e `node_modules`; não recrie o banco nem reinstale dependências para iniciar a aplicação.

## Linux e macOS

A partir da pasta em que deseja manter o projeto:

```sh
git clone https://github.com/thegodKoDDa/eletroprojeto.git
cd eletroprojeto
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.lock
backend/.venv/bin/python -m pip install -e backend --no-deps
```

Prepare o banco e inicie a API:

```sh
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

## Windows

No PowerShell, para uma cópia nova:

```powershell
git clone https://github.com/thegodKoDDa/eletroprojeto.git
cd eletroprojeto
py -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock
backend/.venv/Scripts/python.exe -m pip install -e backend --no-deps
cd backend
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Em outro terminal, entre em `frontend` e execute `npm ci` e `npm run dev`. Não é necessário ativar o ambiente Python nem alterar a política de execução do PowerShell. Se a instalação existente usa `.venv-windows`, substitua o caminho do interpretador; preserve esse ambiente.

## Acessos locais

| Serviço | Endereço |
| --- | --- |
| Aplicação | http://127.0.0.1:3000 |
| API interativa | http://127.0.0.1:8000/docs |
| Saúde da API | http://127.0.0.1:8000/api/v1/health |

Confira os serviços existentes antes de iniciar outra instância. A API e a interface são processos independentes; ambos precisam estar disponíveis.

## Configuração

Os arquivos [backend/.env.example](../backend/.env.example) e [frontend/.env.example](../frontend/.env.example) documentam as variáveis disponíveis.

O backend lê as variáveis do ambiente do processo; criar um arquivo `.env` sozinho não o carrega automaticamente. Para a interface, o Next.js também lê `frontend/.env.local`. Não versione configurações privadas.

| Variável | Comportamento padrão |
| --- | --- |
| `DATABASE_URL` | SQLite em `backend/eletroprojeto.db` |
| `AUTH_MODE` | `local`, restrito a loopback |
| `CORS_ORIGINS` | Interface em localhost/127.0.0.1, porta 3000 |
| `MAX_REQUEST_BYTES` | Corpo de requisição limitado a 4 MiB |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_AUTH_MODE` | `local` |

Para SQLite fora do diretório padrão, prefira um caminho absoluto em `DATABASE_URL`. Mudanças no schema usam `alembic upgrade head`; a aplicação não cria as tabelas automaticamente. Preserve banco e histórico antes de migrar uma instalação existente.

O modo remoto exige HTTPS, contas e configuração própria de origens e sessões, descrita em [segurança](security.md). A operação documentada aqui é local.

## Biblioteca técnica e território

Os originais da biblioteca, exemplares normativos e coletas territoriais são locais e não acompanham o clone. Sem esses arquivos, recursos dependentes permanecem indisponíveis ou pendentes; isso não impede o cadastro e a estimativa de consumo.

Veja [references/README.md](../references/README.md) para a organização das fontes e [continuidade](continuity.md) para recuperar uma instalação completa. Não substitua dados locais por arquivos de exemplo.

## Próximos passos

- [Usar a aplicação](usage.md)
- [Desenvolver e executar verificações](../CONTRIBUTING.md)
- [Preservar e recuperar os dados](continuity.md)
