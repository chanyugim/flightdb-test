from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    app_name: str = "항공권 예매 서비스"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_statement_timeout_ms: int = Field(default=5000, ge=100, le=60000)
    db_name: str = "airline_reservation"
    db_user: str
    db_password: str = Field(repr=False)

    jwt_secret_key: str = Field(repr=False)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    chatbot_enabled: bool = False
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = Field(
        default="gemini-3.5-flash-lite", pattern=r"^[a-zA-Z0-9._-]+$"
    )
    gemini_timeout_seconds: float = Field(default=15, gt=0, le=60)
    chatbot_requests_per_minute: int = Field(default=10, ge=1, le=1000)
    sensitive_requests_per_minute: int = Field(default=30, ge=1, le=1000)

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
