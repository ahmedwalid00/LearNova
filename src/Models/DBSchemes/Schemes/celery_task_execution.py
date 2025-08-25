from .base import BaseModel
from sqlalchemy import Column, Integer, DateTime, func, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Index
import uuid

class CeleryTaskExecution(BaseModel):

    __tablename__ = "celery_task_executions"

    execution_id = Column(Integer, primary_key=True, autoincrement=True)

    task_name = Column(String(255), nullable=False)
    task_args_hash = Column(String(64), nullable=False)  # SHA-256 hash of task arguments
    celery_task_id = Column(UUID(as_uuid=True), nullable=True)

    status = Column(String(20), nullable=False, default='PENDING')

    task_args = Column(JSONB, nullable=True)
    result = Column(JSONB, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


    __table_args__ = (
        Index('ixz_task_name_args_celery_hash', task_name, task_args_hash, celery_task_id, unique=True),
        Index('ixz_task_execution_status', status),
        Index('ixz_task_execution_started_at', started_at),
        Index('ixz_task_execution_completed_at', completed_at),
        Index('ixz_celery_task_id', celery_task_id),
    )