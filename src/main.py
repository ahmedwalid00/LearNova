from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.Helpers.config import get_settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.Api.routers.GeneralRoutes.auth_route import auth_router
from src.Api.routers.AdminRoutes import admin_router
from src.Api.routers.TeachersRoutes.lesson import router as lesson_router
from src.Api.routers.TeachersRoutes.questions_exams import router as questions_exams_router
from src.Stores.VectorDB.vectordb_factory import VectorDBProviderFactory
from src.Stores.LLM.llm_facatory import LLMProviderFactory
import aioredis

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup: Create DB engine and session factory
    # Use asyncpg driver for SQLAlchemy async engine
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    
    engine = create_async_engine(postgres_conn)
    session_local = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    
    vectordb_provider_factory = VectorDBProviderFactory(config=settings, db_client=session_local)
    llm_provider_factory = LLMProviderFactory(config=settings)

    # generation client
    app.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(model_id = settings.GENERATION_MODEL_ID)

    # embedding client
    app.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                             embedding_size=settings.EMBEDDING_MODEL_SIZE)

    # vectordb client
    app.vectordb_client = vectordb_provider_factory.create(
        provider=settings.VECTOR_DB_BACKEND
    )
    await app.vectordb_client.connect()
    # Store the session factory in the app's state
    app.state.db_session_factory = session_local
    # Create and store redis client
    redis = await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
        encoding="utf-8",
        decode_responses=True,
    )
    app.state.redis = redis
    
    print("--- DB connection established ---")
    yield
    # Shutdown: Close the engine
    await engine.dispose()
    # Close redis
    try:
        await app.state.redis.close()
    except Exception:
        pass
    print("--- DB connection closed ---")


app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(lesson_router)
app.include_router(questions_exams_router)