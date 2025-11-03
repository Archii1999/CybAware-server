from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "CybAware API"
    DEBUG: bool = True
    SECRET_KEY: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    APP_VERSION: str = "0.1.0"

    class Config:
        env_file = ".env"

settings = Settings()
