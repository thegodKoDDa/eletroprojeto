FROM node:24-bookworm-slim AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/src ./src
COPY frontend/next.config.ts frontend/next-env.d.ts frontend/tsconfig.json frontend/postcss.config.mjs ./
ENV NEXT_PUBLIC_API_URL=/api/v1 \
    NEXT_PUBLIC_AUTH_MODE=local \
    API_PROXY_TARGET=http://127.0.0.1:8000 \
    NEXT_OUTPUT_STANDALONE=1 \
    NEXT_TELEMETRY_DISABLED=1
COPY docker/collect-licenses.mjs /tmp/collect-licenses.mjs
RUN npm run build:webpack && node /tmp/collect-licenses.mjs

FROM python:3.14-slim-bookworm AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=frontend /usr/local/bin/node /usr/local/bin/node
COPY --from=frontend /usr/local/LICENSE /app/licenses/NODE-LICENSE
COPY --from=frontend /licenses /app/licenses
COPY backend/requirements-runtime.lock /tmp/requirements.lock
RUN python -m pip install --no-cache-dir -r /tmp/requirements.lock
WORKDIR /app/backend
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
COPY --from=frontend /web/.next/standalone /app/web
COPY --from=frontend /web/.next/static /app/web/.next/static
COPY scripts/start_local.py /app/scripts/start_local.py
COPY LICENSE THIRD_PARTY_NOTICES.md /app/
RUN useradd --create-home --uid 10001 eletroprojeto \
    && mkdir /data \
    && chown eletroprojeto:eletroprojeto /data
USER eletroprojeto
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
VOLUME ["/data"]
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=4 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3000/api/v1/health', timeout=3)"
CMD ["python", "/app/scripts/start_local.py", "--container", "--no-browser"]
