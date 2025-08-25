from celery import Celery
from src.Helpers.config import get_settings

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

settings = get_settings()

async def get_setup_utils():

    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"

    db_engine = create_async_engine(postgres_conn)
    db_client = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    return (db_engine, db_client)

# Create Celery application instance
celery_app = Celery(
    "learnova",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.Tasks.sending_email",
        "src.Tasks.maintentance",
    ]
)

# Configure Celery with essential settings
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=[
        settings.CELERY_TASK_SERIALIZER
    ],

    # Task safety - Late acknowledgment prevents task loss on worker crash
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,

    # Time limits - Prevent hanging tasks
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,

    # Result backend - Store results for status tracking
    task_ignore_result=False,
    result_expires=3600,

    # Worker settings
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,

    # Connection settings for better reliability
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    worker_cancel_long_running_tasks_on_connection_loss=True,

    task_routes={
        "src.Tasks.sending_email.send_verification_email": {"queue": "email_queue"},
        "src.Tasks.sending_email.send_password_reset_email": {"queue": "email_queue"},
        "src.Tasks.maintentance.clean_celery_executions_table": {"queue": "default"},
    },

    beat_schedule={
        'cleanup-old-task-records': {
            'task': "src.Tasks.maintentance.clean_celery_executions_table",
            'schedule': 86400,  # Run daily
            'args': ()
        }
    },

    timezone='UTC',

)

celery_app.conf.task_default_queue = "default"