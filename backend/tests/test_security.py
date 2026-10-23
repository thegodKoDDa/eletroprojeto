import asyncio

from app.security import RequestBoundary


def test_chunked_request_without_length_is_bounded_before_application():
    called = False
    messages = []
    chunks = iter(
        [
            {"type": "http.request", "body": b"a" * 700, "more_body": True},
            {"type": "http.request", "body": b"b" * 700, "more_body": False},
        ]
    )

    async def app(scope, receive, send):
        nonlocal called
        called = True

    async def receive():
        return next(chunks)

    async def send(message):
        messages.append(message)

    asyncio.run(RequestBoundary(app, max_bytes=1024)({"type": "http"}, receive, send))
    assert not called
    assert messages[0]["status"] == 413


def test_cors_configuration_rejects_wildcards_credentials_and_paths():
    import pytest
    from app.security import cors_origins

    assert cors_origins(" http://localhost:3000/,http://localhost:3000 ") == [
        "http://localhost:3000"
    ]
    for value in [
        "*",
        "https://*.example.com",
        "http://user:secret@example.com",
        "https://example.com/path",
        "null",
        "https://example.com?token=x",
    ]:
        with pytest.raises(ValueError):
            cors_origins(value)
