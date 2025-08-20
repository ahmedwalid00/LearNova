from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import String, DateTime, Boolean
from datetime import datetime
from .base import BaseModel
import uuid

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
	

class ParentStudentLink(BaseModel):
    """Junction table for parent-student relationships"""
    __tablename__ = "parent_student_links"
    
    link_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("parents.parent_id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), nullable=False, index=True)
    relationship_type = Column(String(50), default="parent", nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    parent = relationship("Parent", back_populates="student_links", lazy="select")
    student = relationship("Student", back_populates="parent_links", lazy="select")
    
    __table_args__ = (
        Index('ix_parent_student_unique', parent_id, student_id, unique=True),
        Index('ix_parent_student_active', parent_id, student_id, is_active),
    )
    
    def __repr__(self):
        return f"<ParentStudentLink(parent_id='{self.parent_id}', student_id='{self.student_id}', type='{self.relationship_type}')>"
