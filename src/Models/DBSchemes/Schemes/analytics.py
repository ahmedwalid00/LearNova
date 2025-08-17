from sqlalchemy import Column, String, Text, Date, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid

class AnalyticsReport(BaseModel):
	__tablename__ = "analytics_reports"
	report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True , unique=True , nullable=False)
	content = Column(Text, nullable=False)
	report_date = Column(Date, nullable=False)
	student_id = Column(UUID(as_uuid=True), nullable=True, index=True)
	teacher_id = Column(UUID(as_uuid=True), nullable=True, index=True)
	week_id = Column(UUID(as_uuid=True), nullable=True, index=True)
	term_id = Column(UUID(as_uuid=True), nullable=False, index=True)

	# Relationships
	student = relationship("Student", back_populates="analytics_reports", lazy="select")
	teacher = relationship("Teacher", back_populates="analytics_reports", lazy="select")
	week = relationship("TermWeek", back_populates="analytics_reports", lazy="select")
	term = relationship("AcademicTerm", back_populates="analytics_reports", lazy="select")

	__table_args__ = (
		Index('ix_analytics_student_report_date', student_id, report_date),
		Index('ix_analytics_teacher_report_date', teacher_id, report_date),
		Index('ix_analytics_report_date', report_date),
	)

	def __repr__(self):
		return f"<AnalyticsReport(report_date={self.report_date}, term_id={self.term_id})>"
