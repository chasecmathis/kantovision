from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str
    frontend_url: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"
    json_logs: bool = False

    # Battle rules
    move_timeout_seconds: int = 60
    ws_grace_period_seconds: int = 30

    # Team limits
    max_teams_per_user: int = 10

    # CORS — comma-separated list of allowed origins (no spaces)
    # e.g. "https://kantovision.app,https://www.kantovision.app"
    allowed_origins: str = "http://localhost:3000"

    # WebSocket rate limiting — max messages per second per connection
    ws_rate_limit_per_second: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
