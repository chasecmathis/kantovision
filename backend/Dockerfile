# ─── Stage 1: export model to ONNX ────────────────────────────────────────────
FROM python:3.12-slim AS export

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY scripts/ ./scripts/

# Install export deps (torch + transformers) — only used in this stage
RUN uv sync --frozen --no-dev --group export --no-install-project \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Run the export script to produce models/*.onnx + models/config.json
RUN /app/.venv/bin/python scripts/export_onnx.py

# ─── Stage 2: install runtime dependencies ────────────────────────────────────
FROM python:3.12-slim AS deps

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install production deps only (onnxruntime, fastapi, etc. — no torch)
RUN uv sync --frozen --no-dev --no-install-project

# ─── Stage 3: runtime image ───────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m appuser

WORKDIR /app

# Pull the lightweight virtualenv (no torch)
COPY --from=deps /app/.venv /app/.venv

# Pull the exported ONNX model from the export stage
COPY --from=export /app/models ./models/

# Copy application source
COPY app/ ./app/
COPY entrypoint.sh ./entrypoint.sh

RUN chown -R appuser:appgroup /app && \
    chmod +x /app/entrypoint.sh

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c \
    "import urllib.request, os; \
     urllib.request.urlopen('http://localhost:{}/health'.format(os.environ.get('PORT', '8000')))" \
  || exit 1

CMD ["/app/entrypoint.sh"]
