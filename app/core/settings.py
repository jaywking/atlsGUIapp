from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DEBUG_ADMIN: bool = False

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
