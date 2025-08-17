from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
	__abstract__ = True
	created_at = Column(DateTime(timezone=True), server_default=func.now())
	updated_at = Column(DateTime(timezone=True), onupdate=func.now())
	deleted_at = Column(DateTime(timezone=True), nullable=True)

	def __repr__(self):
		return f"<{self.__class__.__name__}(id={self.id})>"
