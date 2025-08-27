from sqlalchemy import Column, String, DECIMAL, Boolean, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid

class Student(BaseModel):
	__tablename__ = "students"
	student_id =  Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	unique_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "22001", "22002"
	name = Column(String(255), nullable=False)
	email = Column(String(255), nullable=False, unique=True, index=True)
	is_verified = Column(Boolean, default=False)
	password_hash = Column(String(255), nullable=False)
	rating = Column(DECIMAL, nullable=True)
	admin_id = Column(UUID(as_uuid=True), ForeignKey("admins.admin_id"), nullable=True, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=True, index=True)

	# Relationships
	admin = relationship("Admin", back_populates="students", lazy="select")
	term = relationship("AcademicTerm", back_populates="students", lazy="select")
	parent_links = relationship("ParentStudentLink", back_populates="student", lazy="select")
	classrooms = relationship("ClassRoom", back_populates="student", lazy="select")
	exam_results = relationship("ExamResult", back_populates="student", lazy="select")
	# analytics_reports = relationship("AnalyticsReport", back_populates="student", lazy="select")

	__table_args__ = (
		Index('ix_student_unique_id', unique_id),
		Index('ix_student_email', email),
		Index('ix_student_rating', rating),
	)

	def __repr__(self):
		return f"<Student(name='{self.name}', email='{self.email}')>"

class Teacher(BaseModel):
	__tablename__ = "teachers"
	teacher_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	unique_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "11001", "11002"
	name = Column(String(255), nullable=False)
	email = Column(String(255), nullable=False, unique=True, index=True)
	is_verified = Column(Boolean, default=False)
	password_hash = Column(String(255), nullable=False)
	rating = Column(DECIMAL, nullable=True)
	subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=True, index=True)
	admin_id = Column(UUID(as_uuid=True), ForeignKey("admins.admin_id"), nullable=False, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=True, index=True)

	# Relationships
	admin = relationship("Admin", back_populates="teachers", lazy="select")
	term = relationship("AcademicTerm", back_populates="teachers", lazy="select")
	classrooms = relationship("ClassRoom", back_populates="teacher", lazy="select")
	lessons = relationship("Lesson", back_populates="teacher", lazy="select")
	question_practices = relationship("QuestionPractice", back_populates="teacher", lazy="select")
	question_exams = relationship("QuestionExam", back_populates="teacher", lazy="select")
	exams = relationship("Exam", back_populates="teacher", lazy="select")
	# analytics_reports = relationship("AnalyticsReport", back_populates="teacher", lazy="select")

	__table_args__ = (
		Index('ix_teacher_unique_id', unique_id),
		Index('ix_teacher_email', email),
		Index('ix_teacher_rating', rating),
	)

	def __repr__(self):
		return f"<Teacher(name='{self.name}', email='{self.email}')>"

class Parent(BaseModel):
	__tablename__ = "parents"
	parent_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	unique_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "P22001"
	name = Column(String(255), nullable=False)
	email = Column(String(255), nullable=False, unique=True, index=True)
	password_hash = Column(String(255), nullable=True)  # Optional for Option A registration flow
	is_verified = Column(Boolean, default=False)
	admin_id = Column(UUID(as_uuid=True), ForeignKey("admins.admin_id"), nullable=False, index=True)

	# Relationships
	admin = relationship("Admin", back_populates="parents", lazy="select")
	student_links = relationship("ParentStudentLink", back_populates="parent", lazy="select")

	__table_args__ = (
		Index('ix_parent_unique_id', unique_id),
		Index('ix_parent_email', email),
	)

	def __repr__(self):
		return f"<Parent(name='{self.name}', email='{self.email}')>"

class Admin(BaseModel):
	__tablename__ = "admins"
	admin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False, index=True)
	unique_id = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "ADMIN001", "SUPER001"
	name = Column(String(255), nullable=False)
	email = Column(String(255), nullable=False, unique=True, index=True)
	password_hash = Column(String(255), nullable=False)

	# Relationships
	students = relationship("Student", back_populates="admin", lazy="select")
	teachers = relationship("Teacher", back_populates="admin", lazy="select")
	parents = relationship("Parent", back_populates="admin", lazy="select")

	__table_args__ = (
		Index('ix_admin_unique_id', unique_id),
		Index('ix_admin_email', email),
	)

	def __repr__(self):
		return f"<Admin(name='{self.name}', email='{self.email}')>"
