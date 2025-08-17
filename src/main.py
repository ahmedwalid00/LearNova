from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.Helpers.config import get_settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create DB engine and session factory
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    
    engine = create_async_engine(postgres_conn)
    session_local = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Store the session factory in the app's state
    app.state.db_session_factory = session_local
    
    print("--- DB connection established ---")
    yield
    # Shutdown: Close the engine
    await engine.dispose()
    print("--- DB connection closed ---")


app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.APP_VERSION,
    lifespan=lifespan
)