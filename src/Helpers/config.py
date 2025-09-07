from pydantic_settings import BaseSettings

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

    # JWT Config
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int

    # Email Config
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_SERVER: str
    MAIL_PORT: int
    DOMAIN: str

    # Redis Config
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0

    # Celery Config
    CELERY_BROKER_URL: str 
    CELERY_RESULT_BACKEND: str 
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_TASK_ACKS_LATE: bool 
    CELERY_TASK_TIME_LIMIT: int 
    CELERY_WORKER_CONCURRENCY: int 

    # VectorDB Config
    VECTOR_DB_BACKEND: str
    VECTOR_DB_DISTANCE_METHOD: str
    VECTOR_DB_PGVEC_INDEX_THRESHOLD: int

    # LLM Config
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str
    OPENAI_API_KEY: str
    GENERATION_MODEL_ID: str
    EMBEDDING_MODEL_ID: str
    EMBEDDING_MODEL_SIZE: int
    INPUT_DEFAULT_MAX_CHARACTERS: int
    GENERATION_DEFAULT_MAX_TOKENS: int
    GENERATION_DEFAULT_TEMPERATURE: float

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings():
    return Settings()
