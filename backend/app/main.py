from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import battles, health, profiles, teams
from app.sockets import battle as battle_ws


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(title="KantoVision API")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(teams.router)
    application.include_router(profiles.router)
    application.include_router(battles.router)
    application.include_router(battle_ws.router)

    return application


app = create_app()
