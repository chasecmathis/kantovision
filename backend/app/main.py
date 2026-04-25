import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.logging_config import setup_logging
from app.routers import battles, health, pokedex, profiles, teams
from app.sockets import battle as battle_ws
from app.sockets.connections import manager as ws_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(level=settings.log_level, json_logs=settings.json_logs)
    logger.info("KantoVision API starting up — allowed_origins=%s", settings.allowed_origins)
    yield
    logger.info("KantoVision API shutting down — notifying active connections")
    await ws_manager.broadcast_all(
        {"type": "server_shutdown", "message": "Server is shutting down"}
    )


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(title="KantoVision API", lifespan=_lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(pokedex.router)
    application.include_router(teams.router)
    application.include_router(profiles.router)
    application.include_router(battles.router)
    application.include_router(battle_ws.router)

    return application


app = create_app()
