from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    postgres_url: str = Field(default="sqlite:///./sentinelai.db", validation_alias=AliasChoices("POSTGRES_URL", "DATABASE_URL"))
    jwt_secret: str = "development-only-change-me"
    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4.1-mini"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,https://localhost,capacitor://localhost"

@lru_cache
def get_settings() -> Settings:
    return Settings()
