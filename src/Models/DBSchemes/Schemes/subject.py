from sqlalchemy import Column, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid

class Subject(BaseModel):
	__tablename__ = "subjects"
	subject_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	name = Column(String(255), nullable=False, unique=True)
	description = Column(Text, nullable=True)

	# Relationships
	lessons = relationship("Lesson", back_populates="subject", lazy="select")
	classrooms = relationship("ClassRoom", back_populates="subject", lazy="select")

	__table_args__ = (
		Index('ix_subject_name', name),
	)

	def __repr__(self):
		return f"<Subject(name='{self.name}')>"
