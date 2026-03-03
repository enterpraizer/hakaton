from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='postgres_',
        env_file='.env',
        extra='ignore',
    )

    host: str
    port: int
    db: str
    user: str
    password: str

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
