from sqlalchemy import Column, String, Date, DECIMAL, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid

class Exam(BaseModel):
	__tablename__ = "exams"
	exam_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	title = Column(String(255), nullable=False)
	date = Column(Date, nullable=False)
	teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.teacher_id"), nullable=False, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)

	# Relationships
	teacher = relationship("Teacher", back_populates="exams", lazy="select")
	term = relationship("AcademicTerm", back_populates="exams", lazy="select")
	# Question relationship
	question_exams = relationship("QuestionExam", back_populates="exam", lazy="select")
	exam_results = relationship("ExamResult", back_populates="exam", lazy="select")

	__table_args__ = (
		Index('ix_exam_teacher_date', teacher_id, date),
		Index('ix_exam_term_date', term_id, date),
	)

	def __repr__(self):
		return f"<Exam(title='{self.title}', date={self.date})>"

class ExamResult(BaseModel):
	__tablename__ = "exam_results"
	result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.exam_id"), nullable=False, index=True)
	student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), nullable=False, index=True)
	score = Column(DECIMAL, nullable=False)
	exam_rating = Column(DECIMAL, nullable=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)

	# Relationships
	exam = relationship("Exam", back_populates="exam_results", lazy="select")
	student = relationship("Student", back_populates="exam_results", lazy="select")
	term = relationship("AcademicTerm", back_populates="exam_results", lazy="select")

	__table_args__ = (
		Index('ix_exam_result_student_score', student_id, score),
		Index('ix_exam_result_exam_id', exam_id),
	)

	def __repr__(self):
		return f"<ExamResult(student_id={self.student_id}, score={self.score})>"
