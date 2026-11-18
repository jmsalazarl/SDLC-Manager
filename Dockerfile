FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

WORKDIR /build
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-build

FROM python:3.12-slim AS runtime

ARG APP_UID=10001
RUN useradd --create-home --uid "${APP_UID}" appuser

WORKDIR /app
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    SDLC_MANAGER_DATABASE_URL=sqlite:////app/data/sdlc_manager.db \
    SDLC_MANAGER_POLICY_PATHS='["/app/knowledge/rules"]' \
    SDLC_MANAGER_AUTO_MIGRATE=true

COPY --from=builder /opt/venv /opt/venv
COPY alembic.ini ./
COPY migrations ./migrations
COPY knowledge ./knowledge
COPY src ./src
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser
ENTRYPOINT ["python", "-m", "sdlc_manager"]

