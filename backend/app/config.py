from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "InsightForge API"
    app_env: str = "development"
    debug: bool = False

    groq_api_key: str
    groq_model: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )


settings = Settings()