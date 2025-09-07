from sqlalchemy import Column, Text, Enum, ForeignKey, Index, Integer, DECIMAL, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
from datetime import datetime
import uuid

class PracticeQuestionResponse(BaseModel):
	"""Student responses to practice questions"""
	__tablename__ = "practice_question_responses"
	
	response_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), nullable=False, index=True)
	practice_id = Column(UUID(as_uuid=True), ForeignKey("question_practices.practice_id"), nullable=False, index=True)
	answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.answer_id"), nullable=False, index=True)
	is_correct = Column(Boolean, nullable=False, default=False)
	answered_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
	time_taken_seconds = Column(Integer, nullable=True)  # Time taken to answer in seconds
	
	# Relationships
	student = relationship("Student", back_populates="practice_responses", lazy="select")
	practice_question = relationship("QuestionPractice", back_populates="student_responses", lazy="select")
	answer = relationship("Answer", lazy="select")
	
	__table_args__ = (
		Index('ix_practice_response_student_id', student_id),
		Index('ix_practice_response_practice_id', practice_id),
		Index('ix_practice_response_unique', student_id, practice_id, unique=True),  # One response per student per question
		Index('ix_practice_response_answered_at', answered_at),
	)
	
	def __repr__(self):
		return f"<PracticeQuestionResponse(student_id={self.student_id}, practice_id={self.practice_id}, is_correct={self.is_correct})>"


class ExamQuestionResponse(BaseModel):
	"""Student responses to exam questions"""
	__tablename__ = "exam_question_responses"
	
	response_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), nullable=False, index=True)
	question_id = Column(UUID(as_uuid=True), ForeignKey("question_exams.question_id"), nullable=False, index=True)
	exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.exam_id"), nullable=False, index=True)
	answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.answer_id"), nullable=False, index=True)
	is_correct = Column(Boolean, nullable=False, default=False)
	answered_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
	time_taken_seconds = Column(Integer, nullable=True)  # Time taken to answer in seconds
	
	# Relationships
	student = relationship("Student", back_populates="exam_responses", lazy="select")
	exam_question = relationship("QuestionExam", back_populates="student_responses", lazy="select")
	exam = relationship("Exam", back_populates="student_responses", lazy="select")
	answer = relationship("Answer", lazy="select")
	
	__table_args__ = (
		Index('ix_exam_response_student_id', student_id),
		Index('ix_exam_response_question_id', question_id),
		Index('ix_exam_response_exam_id', exam_id),
		Index('ix_exam_response_unique', student_id, question_id, unique=True),  # One response per student per question
		Index('ix_exam_response_answered_at', answered_at),
	)
	
	def __repr__(self):
		return f"<ExamQuestionResponse(student_id={self.student_id}, question_id={self.question_id}, is_correct={self.is_correct})>"


class StudentRating(BaseModel):
	"""Student overall rating based on practice and exam performance"""
	__tablename__ = "student_ratings"
	
	rating_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), nullable=False, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)
	
	# Practice performance metrics
	practice_questions_answered = Column(Integer, nullable=False, default=0)
	practice_questions_correct = Column(Integer, nullable=False, default=0)
	practice_accuracy_rate = Column(DECIMAL(5, 4), nullable=False, default=0.0)  # 0.0000 to 1.0000
	
	# Exam performance metrics
	exams_taken = Column(Integer, nullable=False, default=0)
	total_exam_score = Column(DECIMAL(8, 2), nullable=False, default=0.0)
	average_exam_score = Column(DECIMAL(5, 2), nullable=False, default=0.0)  # 0.00 to 100.00
	
	# Overall rating (weighted combination of practice and exam performance)
	overall_rating = Column(DECIMAL(5, 2), nullable=False, default=0.0)  # 0.00 to 100.00
	
	# Timestamps
	last_updated = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)
	
	# Relationships
	student = relationship("Student", back_populates="ratings", lazy="select")
	term = relationship("AcademicTerm", back_populates="student_ratings", lazy="select")
	
	__table_args__ = (
		Index('ix_student_rating_student_id', student_id),
		Index('ix_student_rating_term_id', term_id),
		Index('ix_student_rating_unique', student_id, term_id, unique=True),  # One rating per student per term
		Index('ix_student_rating_overall', overall_rating),
	)
	
	def __repr__(self):
		return f"<StudentRating(student_id={self.student_id}, term_id={self.term_id}, overall_rating={self.overall_rating})>"
