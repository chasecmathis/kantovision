#!/bin/sh
# exec replaces this shell with uvicorn, making uvicorn PID 1.
# That ensures SIGTERM from Docker/Railway reaches uvicorn directly,
# triggering our graceful shutdown lifespan.
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1 \
  --timeout-graceful-shutdown 15
