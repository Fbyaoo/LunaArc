from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LunaArc Backend"
    app_version: str = "0.1.0"

    cors_origins: str = (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    vision_model_path: str = ""
    min_confidence: float = 0.6
    max_image_size_mb: int = 10

    agent_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
