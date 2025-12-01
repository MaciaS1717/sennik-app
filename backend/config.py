from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

# folder backend/
BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    environment: str = "dev"
    debug: bool = True

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
         env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    @property
    def database_url(self) -> str:
        # PostgreSQL URL dla SQLAlchemy/SQLModel
        return (
            f"postgresql+psycopg2://{self.db_user}:"
            f"{self.db_password}@{self.db_host}:"
            f"{self.db_port}/{self.db_name}"
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()
