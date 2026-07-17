from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://taskhub:taskhub@localhost:5432/taskhub"

    class Config:
        env_file = ".env"


settings = Settings()
