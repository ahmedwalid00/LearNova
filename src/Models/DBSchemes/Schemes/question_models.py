from sqlalchemy import Column, Text, Enum, ForeignKey, Index , Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid

class QuestionPractice(BaseModel):
	__tablename__ = "question_practices"
	practice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	content = Column(Text, nullable=False)
	difficulty = Column(Enum('easy', 'medium', 'hard', name='difficulty_enum'), nullable=False)
	teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.teacher_id"), nullable=False, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)

	# Relationships
	teacher = relationship("Teacher", back_populates="question_practices", lazy="select")
	term = relationship("AcademicTerm", back_populates="question_practices", lazy="select")
	answers = relationship("Answer", back_populates="question_practice", lazy="select")

	__table_args__ = (
		Index('ix_question_practice_teacher_id', teacher_id),
		Index('ix_question_practice_term_id', term_id),
	)

	def __repr__(self):
		return f"<QuestionPractice(difficulty={self.difficulty}, teacher_id={self.teacher_id})>"

class QuestionExam(BaseModel):
	__tablename__ = "question_exams"
	question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,nullable=False,unique=True,index=True)
	content = Column(Text, nullable=False)
	difficulty = Column(Enum('easy', 'medium', 'hard', name='difficulty_enum'), nullable=False)
	teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.teacher_id"), nullable=False, index=True)
	exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.exam_id"), nullable=False, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)

	# Relationships
	teacher = relationship("Teacher", back_populates="question_exams", lazy="select")
	exam = relationship("Exam", back_populates="question_exams", lazy="select")
	term = relationship("AcademicTerm", back_populates="question_exams", lazy="select")
	answers = relationship("Answer", back_populates="question_exam", lazy="select")

	__table_args__ = (
		Index('ix_question_exam_teacher_id', teacher_id),
		Index('ix_question_exam_exam_id', exam_id),
		Index('ix_question_exam_term_id', term_id),
	)

	def __repr__(self):
		return f"<QuestionExam(difficulty={self.difficulty}, exam_id={self.exam_id})>"
	

class Answer(BaseModel):
	__tablename__ = "answers"
	answer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,nullable=False,unique=True,index=True)
	question_practice_id = Column(UUID(as_uuid=True), ForeignKey("question_practices.practice_id"), nullable=True, index=True)
	question_exam_id = Column(UUID(as_uuid=True), ForeignKey("question_exams.question_id"), nullable=True, index=True)
	answer_text = Column(Text, nullable=False)
	is_correct = Column(Integer, nullable=False, default=0)

	# Relationships
	question_practice = relationship("QuestionPractice", back_populates="answers", lazy="select")
	question_exam = relationship("QuestionExam", back_populates="answers", lazy="select")

	__table_args__ = (
		Index('ix_answer_question_practice_id', question_practice_id),
		Index('ix_answer_question_exam_id', question_exam_id),
	)

	def __repr__(self):
		return f"<Answer(answer_text='{self.answer_text}', is_correct={self.is_correct})>"
