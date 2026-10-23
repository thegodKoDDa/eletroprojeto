"""Small ASGI boundary: bound actual request bytes before JSON validation.

This is resource protection, not authentication. Public deployment still needs
identity, project authorization and an ingress-level rate limiter.
"""

import os

from starlette.responses import JSONResponse


class RequestBoundary:
    def __init__(self, app, max_bytes=None):
        self.app = app
        self.max_bytes = (
            max_bytes if max_bytes is not None else int(os.getenv("MAX_REQUEST_BYTES", "4194304"))
        )
        if self.max_bytes < 1024:
            raise ValueError("MAX_REQUEST_BYTES must be at least 1024")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def secure_send(message):
            if message["type"] == "http.response.start":
                message = {
                    **message,
                    "headers": [
                        *message.get("headers", []),
                        (b"x-content-type-options", b"nosniff"),
                        (b"cache-control", b"no-store"),
                    ],
                }
            await send(message)

        # Check actual chunks, including requests without Content-Length.
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_bytes:
                return await JSONResponse(
                    {"detail": "Requisição muito grande. Reduza o tamanho do projeto."},
                    status_code=413,
                )(scope, receive, secure_send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, secure_send)


def cors_origins(value):
    """Only explicit HTTP origins; wildcard CORS is never silently accepted."""
    from urllib.parse import urlsplit

    origins = []
    for raw in value.split(","):
        origin = raw.strip().rstrip("/")
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or "*" in origin
        ):
            raise ValueError(
                "CORS_ORIGINS deve conter origens HTTP explícitas, sem caminhos ou credenciais"
            )
        origins.append(origin)
    return list(dict.fromkeys(origins))
