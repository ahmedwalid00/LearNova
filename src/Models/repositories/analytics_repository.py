"""
Analytics-related repository classes.

This module contains repository classes for analytics models:
AnalyticsReport.
"""

from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func
from datetime import date
from uuid import UUID

from  .base import BaseRepository
from ..DBSchemes.Schemes.analytics import AnalyticsReport


class AnalyticsRepository(BaseRepository[AnalyticsReport]):
    """Repository for AnalyticsReport model operations."""
    
    def __init__(self, session):
        super().__init__(session, AnalyticsReport)
    
    async def get_by_student_id(self, student_id: UUID) -> List[AnalyticsReport]:
        """Get all analytics reports for a specific student."""
        result = await self.session.execute(
            select(AnalyticsReport)
            .where(AnalyticsReport.student_id == student_id)
            .order_by(desc(AnalyticsReport.report_date))
        )
        return result.scalars().all()
    
    async def get_by_teacher_id(self, teacher_id: UUID) -> List[AnalyticsReport]:
        """Get all analytics reports for a specific teacher."""
        result = await self.session.execute(
            select(AnalyticsReport)
            .where(AnalyticsReport.teacher_id == teacher_id)
            .order_by(desc(AnalyticsReport.report_date))
        )
        return result.scalars().all()
    
    async def get_by_term_id(self, term_id: UUID) -> List[AnalyticsReport]:
        """Get all analytics reports for a specific term."""
        result = await self.session.execute(
            select(AnalyticsReport)
            .where(AnalyticsReport.term_id == term_id)
            .order_by(desc(AnalyticsReport.report_date))
        )
        return result.scalars().all()
    
    async def get_by_week_id(self, week_id: UUID) -> List[AnalyticsReport]:
        """Get all analytics reports for a specific week."""
        result = await self.session.execute(
            select(AnalyticsReport)
            .where(AnalyticsReport.week_id == week_id)
            .order_by(desc(AnalyticsReport.report_date))
        )
        return result.scalars().all()
    
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[AnalyticsReport]:
        """Get analytics reports within a specific date range."""
        result = await self.session.execute(
            select(AnalyticsReport).where(
                and_(
                    AnalyticsReport.report_date >= start_date,
                    AnalyticsReport.report_date <= end_date
                )
            ).order_by(desc(AnalyticsReport.report_date))
        )
        return result.scalars().all()
    
    async def get_recent_reports(self, limit: int = 10) -> List[AnalyticsReport]:
        """Get most recent analytics reports."""
        result = await self.session.execute(
            select(AnalyticsReport)
            .order_by(desc(AnalyticsReport.report_date))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_student_weekly_reports(self, student_id: UUID, term_id: UUID) -> List[AnalyticsReport]:
        """Get weekly reports for a student in a specific term."""
        result = await self.session.execute(
            select(AnalyticsReport).where(
                and_(
                    AnalyticsReport.student_id == student_id,
                    AnalyticsReport.term_id == term_id,
                    AnalyticsReport.week_id.is_not(None)
                )
            ).order_by(AnalyticsReport.report_date)
        )
        return result.scalars().all()
    
    async def get_teacher_weekly_reports(self, teacher_id: UUID, term_id: UUID) -> List[AnalyticsReport]:
        """Get weekly reports for a teacher in a specific term."""
        result = await self.session.execute(
            select(AnalyticsReport).where(
                and_(
                    AnalyticsReport.teacher_id == teacher_id,
                    AnalyticsReport.term_id == term_id,
                    AnalyticsReport.week_id.is_not(None)
                )
            ).order_by(AnalyticsReport.report_date)
        )
        return result.scalars().all()
    
    def get_model_specific_methods(self):
        """Return list of analytics-specific methods."""
        return [
            "get_by_student_id",
            "get_by_teacher_id",
            "get_by_term_id",
            "get_by_week_id",
            "get_by_date_range",
            "get_recent_reports",
            "get_student_weekly_reports",
            "get_teacher_weekly_reports"
        ]
