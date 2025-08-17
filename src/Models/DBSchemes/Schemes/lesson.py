from sqlalchemy import Column, String, DECIMAL, ForeignKey, Text, Integer, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel
import uuid

class Lesson(BaseModel):
	__tablename__ = "lessons"
	lesson_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	title = Column(String(255), nullable=False)
	pdf_url = Column(String(512), nullable=False)
	rating = Column(DECIMAL, nullable=True)
	teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.teacher_id"), nullable=False, index=True)
	subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=False, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)

	# Relationships
	teacher = relationship("Teacher", back_populates="lessons", lazy="select")
	subject = relationship("Subject", back_populates="lessons", lazy="select")
	term = relationship("AcademicTerm", back_populates="lessons", lazy="select")
	chunks = relationship("LessonChunk", back_populates="lesson", lazy="select")

	__table_args__ = (
		Index('ix_lesson_teacher_id', teacher_id),
		Index('ix_lesson_subject_id', subject_id),
		Index('ix_lesson_term_id', term_id),
	)

	def __repr__(self):
		return f"<Lesson(title='{self.title}', teacher_id={self.teacher_id})>"

class LessonChunk(BaseModel):
	__tablename__ = "lesson_chunks"
	chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,nullable=False,unique=True,index=True)
	lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.lesson_id"), nullable=False, index=True)
	chunk_number = Column(Integer, nullable=False)
	chunk_text = Column(Text, nullable=False)
	metadata = Column(JSONB, nullable=True)

	# Relationships
	lesson = relationship("Lesson", back_populates="chunks", lazy="select")

	__table_args__ = (
		Index('ix_lesson_chunk_lesson_id', lesson_id),
		Index('ix_lesson_chunk_number', chunk_number),
	)

	def __repr__(self):
		return f"<LessonChunk(lesson_id={self.lesson_id}, chunk_number={self.chunk_number})>"
