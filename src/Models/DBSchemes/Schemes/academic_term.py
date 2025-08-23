from sqlalchemy import Column, Integer, String, Date, Boolean , Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid

class AcademicTerm(BaseModel):
	__tablename__ = "academic_terms"
	term_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	name = Column(String(255), nullable=False)
	start_date = Column(Date, nullable=False)
	end_date = Column(Date, nullable=False)
	is_active = Column(Boolean, default=False)

	# Relationships
	term_weeks = relationship("TermWeek", back_populates="term", lazy="select")
	students = relationship("Student", back_populates="term", lazy="select")
	teachers = relationship("Teacher", back_populates="term", lazy="select")
	lessons = relationship("Lesson", back_populates="term", lazy="select")
	# Question relationships (used by QuestionPractice and QuestionExam)
	question_practices = relationship("QuestionPractice", back_populates="term", lazy="select")
	question_exams = relationship("QuestionExam", back_populates="term", lazy="select")
	exams = relationship("Exam", back_populates="term", lazy="select")
	exam_results = relationship("ExamResult", back_populates="term", lazy="select")
	analytics_reports = relationship("AnalyticsReport", back_populates="term", lazy="select")
	classrooms = relationship("ClassRoom", back_populates="term", lazy="select")
	
	__table_args__ = (
		Index('ix_academic_term_name', name),
		Index('ix_academic_term_start_date', start_date),
		Index('ix_academic_term_end_date', end_date),
	)

	def __repr__(self):
		return f"<AcademicTerm(name='{self.name}', active={self.is_active})>"
