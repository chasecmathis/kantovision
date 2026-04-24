# ─── Stage 1: install dependencies ───────────────────────────────────────────
FROM python:3.12-slim AS deps

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first — Docker caches this layer until they change
COPY pyproject.toml uv.lock ./

# Install production deps only into an isolated .venv
RUN uv sync --frozen --no-dev --no-install-project

# ─── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Non-root user — running as root in containers is a security risk
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m appuser

WORKDIR /app

# Pull the virtualenv from the build stage (no uv needed at runtime)
COPY --from=deps /app/.venv /app/.venv

# Copy application source
COPY app/ ./app/
COPY entrypoint.sh ./entrypoint.sh

RUN chown -R appuser:appgroup /app && \
    chmod +x /app/entrypoint.sh

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
# Prevent .pyc files and ensure logs stream immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Healthcheck — uses stdlib urllib so no extra deps required.
# Reads $PORT so it matches the port uvicorn is actually bound to.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c \
    "import urllib.request, os; \
     urllib.request.urlopen('http://localhost:{}/health'.format(os.environ.get('PORT', '8000')))" \
  || exit 1

# entrypoint.sh runs `exec uvicorn ...` so uvicorn is PID 1 and receives SIGTERM
# directly — this triggers our graceful shutdown lifespan.
CMD ["/app/entrypoint.sh"]
