from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://cloudiaas:cloudiaas@postgres:5432/cloudiaas"
    SECRET_KEY: str = "changeme"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DOCKER_HOST: str = "unix:///var/run/docker.sock"
    FIRST_ADMIN_EMAIL: str = "admin@cloud.local"
    FIRST_ADMIN_PASSWORD: str = "changeme"

    class Config:
        env_file = ".env"


settings = Settings()
