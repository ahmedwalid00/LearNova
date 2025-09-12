"""
Teacher Rating Models

Database models for teacher rating and feedback system.
"""

from sqlalchemy import Column, Text, Integer, DECIMAL, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid


class TeacherRating(BaseModel):
    """Model for individual teacher ratings submitted by students"""
    __tablename__ = "teacher_ratings"
    
    rating_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.teacher_id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"), nullable=False, index=True)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.classroom_id"), nullable=False, index=True)
    rating_points = Column(Integer, nullable=False)  # 1-5 points
    feedback_text = Column(Text, nullable=True)  # Optional feedback
    term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)

    # Relationships
    teacher = relationship("Teacher", lazy="select")
    student = relationship("Student", lazy="select")
    classroom = relationship("ClassRoom", lazy="select")
    term = relationship("AcademicTerm", lazy="select")

    __table_args__ = (
        Index('ix_teacher_rating_teacher_id', teacher_id),
        Index('ix_teacher_rating_student_id', student_id),
        Index('ix_teacher_rating_classroom_id', classroom_id),
        Index('ix_teacher_rating_term_id', term_id),
        # Ensure one rating per student per teacher per classroom
        Index('ix_teacher_rating_unique', teacher_id, student_id, classroom_id, unique=True),
    )

    def __repr__(self):
        return f"<TeacherRating(teacher_id={self.teacher_id}, student_id={self.student_id}, rating={self.rating_points})>"
