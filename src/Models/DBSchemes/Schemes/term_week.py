from sqlalchemy import Column, Integer, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid

class TermWeek(BaseModel):
	__tablename__ = "term_weeks"
	week_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
	term_id = Column(UUID(as_uuid=True), ForeignKey("academic_terms.term_id"), nullable=False, index=True)
	week_number = Column(Integer, nullable=False)
	start_date = Column(Date, nullable=False)
	end_date = Column(Date, nullable=False)

	# Relationships
	term = relationship("AcademicTerm", back_populates="term_weeks", lazy="select")
	analytics_reports = relationship("AnalyticsReport", back_populates="week", lazy="select")

	__table_args__ = (
		Index('ix_term_week_term_id', term_id),
		Index('ix_term_week_week_number', week_number),
	)

	def __repr__(self):
		return f"<TermWeek(term_id={self.term_id}, week_number={self.week_number})>"
