jwt_secret_key: str = "change-me"
jwt_algorithm: str = "HS256"

access_token_minutes: int = 30
refresh_token_days: int = 30

default_daily_reading_limit: int = 3
from functools import lru_cache
from typing import Literal

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

    # mock：使用后端 Mock Agent，适合测试和 CI
    # real：调用 agent.tarot_agent.TarotAgent
    agent_mode: Literal["mock", "real"] = "mock"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.siliconflow.cn/v1"
    openai_model: str = "deepseek-ai/DeepSeek-V3"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
