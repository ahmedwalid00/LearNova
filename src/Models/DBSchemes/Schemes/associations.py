from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import String, DateTime, Boolean
from datetime import datetime
from .base import BaseModel
import uuid

class ClassRoom(BaseModel):
	__tablename__ = "classrooms"
	classroom_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=False, index=True)
	teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.teacher_id"), nullable=False, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)
	grade_level = Column(String(10), nullable=False, index=True)  # e.g., "Grade 12", "Grade 11"
	classroom_name = Column(String(100), nullable=True, index=True)  # Optional classroom name

	# Relationships
	subject = relationship("Subject", back_populates="classrooms", lazy="select")
	teacher = relationship("Teacher", back_populates="classrooms", lazy="select")
	term = relationship("AcademicTerm", lazy="select")

	__table_args__ = (
		Index('ix_classroom_subject_teacher', subject_id, teacher_id),
		Index('ix_classroom_term_id', term_id),
		Index('ix_classroom_grade_level', grade_level),
		Index('ix_classroom_unique_setup', subject_id, teacher_id, term_id, grade_level, unique=True),
	)

	def __repr__(self):
		return f"<ClassRoom(classroom_id={self.classroom_id}, subject_id={self.subject_id}, teacher_id={self.teacher_id}, grade_level='{self.grade_level}')>"


class ClassRoomStudent(BaseModel):
	"""Association table for students assigned to classrooms"""
	__tablename__ = "classroom_students"
	
	classroom_student_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.classroom_id"), nullable=False, index=True)
	student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), nullable=False, index=True)

	# Relationships
	classroom = relationship("ClassRoom", lazy="select")
	student = relationship("Student", back_populates="classroom_assignments", lazy="select")

	__table_args__ = (
		Index('ix_classroom_student_unique', classroom_id, student_id, unique=True),
		Index('ix_classroom_students_classroom', classroom_id),
		Index('ix_classroom_students_student', student_id),
	)

	def __repr__(self):
		return f"<ClassRoomStudent(classroom_id={self.classroom_id}, student_id={self.student_id})>"
	

class ParentStudentLink(BaseModel):
    """Junction table for parent-student relationships"""
    __tablename__ = "parent_student_links"
    
    link_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("parents.parent_id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), nullable=False, index=True)
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
