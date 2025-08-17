from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    # LLM Config
    OPENAI_API_KEY: str

    # Postgres Config
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DATABASE: str




    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings():
    return Settings()
