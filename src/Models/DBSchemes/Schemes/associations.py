from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class ClassRoom(BaseModel):
	__tablename__ = "classrooms"
	student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), primary_key=True)
	subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), primary_key=True)
	teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.teacher_id"), primary_key=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)

	# Relationships
	student = relationship("Student", back_populates="classrooms", lazy="select")
	subject = relationship("Subject", back_populates="classrooms", lazy="select")
	teacher = relationship("Teacher", back_populates="classrooms", lazy="select")
	term = relationship("AcademicTerm", lazy="select")

	__table_args__ = (
		Index('ix_classroom_student_subject', student_id, subject_id),
		Index('ix_classroom_teacher_subject', teacher_id, subject_id),
		Index('ix_classroom_term_id', term_id),
	)

	def __repr__(self):
		return f"<ClassRoom(student_id={self.student_id}, subject_id={self.subject_id}, teacher_id={self.teacher_id})>"
