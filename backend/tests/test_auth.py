import pytest
from app import auth, database
from app.database import UserRow
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def secured(database_engine, monkeypatch):
    engine = database_engine
    sessions = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(auth, "SessionLocal", sessions)
    monkeypatch.setattr(database, "SessionLocal", sessions)
    monkeypatch.setenv("AUTH_MODE", "remote")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.test")
    with sessions() as session:
        for name in ("alice", "bob"):
            session.add(
                UserRow(
                    id=name,
                    username=name,
                    active=True,
                    password_hash=auth.passwords.hash("test-password-long"),
                )
            )
        session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://api.test") as client:
        yield client, sessions
    engine.dispose()


async def signin(client, username):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "test-password-long"},
        headers={"Origin": "https://app.test"},
    )
    assert response.status_code == 200, response.text
    assert (
        "HttpOnly" in response.headers["set-cookie"] and "Secure" in response.headers["set-cookie"]
    )
    return {"Origin": "https://app.test", "X-CSRF-Token": response.json()["csrf"]}


async def test_owner_isolation_csrf_and_revocation(secured):
    client, sessions = secured
    assert (await client.get("/api/v1/projects")).status_code == 401
    assert (await client.post("/api/v1/calculations/energisa-demand", json={})).status_code == 401
    headers = await signin(client, "alice")
    payload = {"name": "Privado", "municipality": "São Paulo", "environments": []}
    assert (await client.post("/api/v1/projects", json=payload)).status_code == 403
    created = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    project = created.json()
    project_id = project["id"]
    assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 204
    assert (await client.get("/api/v1/projects")).status_code == 401
    headers = await signin(client, "bob")
    assert (await client.get("/api/v1/projects")).json() == []
    assert (await client.get("/api/v1/projects/summaries")).json() == []
    assert (await client.get("/api/v1/projects/summaries?q=Privado")).json() == []
    collision = await client.post(
        "/api/v1/projects", json=payload, headers={**headers, "Idempotency-Key": project_id}
    )
    assert collision.status_code == 409
    for path in ("", "/history", "/report", "/revalidation"):
        assert (await client.get(f"/api/v1/projects/{project_id}{path}")).status_code == 404
    for path in ("/duplicate", "/restore?expected_version=1", "/recalculate?expected_version=1"):
        assert (
            await client.post(f"/api/v1/projects/{project_id}{path}", headers=headers)
        ).status_code == 404
    assert (
        await client.put(
            f"/api/v1/projects/{project_id}?expected_version=1", json=payload, headers=headers
        )
    ).status_code == 404
    for path in ("?expected_version=1", "/permanent?expected_version=1"):
        assert (
            await client.delete(f"/api/v1/projects/{project_id}{path}", headers=headers)
        ).status_code == 404
    headers = await signin(client, "alice")
    assert len((await client.get("/api/v1/projects")).json()) == 1
    assert (
        await client.delete(f"/api/v1/projects/{project_id}?expected_version=1", headers=headers)
    ).status_code == 204
    assert len((await client.get("/api/v1/projects?archived=true")).json()) == 1


async def test_https_origins_throttle_and_disabled_account(secured):
    client, sessions = secured
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"username": "alice", "password": "wrong"},
            headers={"Origin": "https://evil.test"},
        )
    ).status_code == 403
    for _ in range(5):
        assert (
            await client.post(
                "/api/v1/auth/login",
                json={"username": "nobody", "password": "wrong"},
                headers={"Origin": "https://app.test"},
            )
        ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "wrong"},
            headers={"Origin": "https://app.test"},
        )
    ).status_code == 429
    await signin(client, "bob")
    with sessions() as session:
        session.get(UserRow, "bob").active = False
        session.commit()
    assert (await client.get("/api/v1/projects")).status_code == 401
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://api.test"
    ) as insecure:
        assert (await insecure.get("/api/v1/projects")).status_code == 400
