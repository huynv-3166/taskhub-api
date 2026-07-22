from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str

    jwt_secret_key: str = Field(
        min_length=32,
    )

    jwt_algorithm: Literal["HS256"] = "HS256"

    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
    )

    refresh_token_expire_days: int = Field(
        default=7,
        gt=0,
    )


settings = Settings()
