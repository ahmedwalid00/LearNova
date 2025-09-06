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
    
    async def get_student_current_rating(self, student_id: UUID) -> Optional[float]:
        """Get the current rating for a student."""
        # For now, return a default rating since performance_score field doesn't exist yet
        # In the future, this could be calculated from exam scores, lesson completion, etc.
        # TODO: Implement proper rating calculation when performance_score field is added
        return 0.0
    
    async def get_student_classroom_performance(self, student_id: UUID, classroom_id: UUID) -> Optional[dict]:
        """Get student's performance in a specific classroom."""
        # This is a placeholder implementation
        # In a real implementation, this would join with classroom/exam data
        return {
            "average_grade": 85.0,
            "completion_rate": 75.0,
            "total_activities": 10,
            "completed_activities": 7
        }
    
    async def get_student_analytics(self, student_id: UUID, period: str) -> dict:
        """Get comprehensive analytics for a student for a given period."""
        # This is a placeholder implementation
        # In a real implementation, this would aggregate data from multiple sources
        return {
            "overall_rating": 80.0,
            "average_grade": 82.5,
            "total_assessments": 15,
            "completed_assessments": 12,
            "total_lessons_accessed": 25,
            "study_time_hours": 45.5,
            "chatbot_interactions": 23,
            "strengths": ["Mathematics", "Problem Solving"],
            "areas_for_improvement": ["Essay Writing", "Time Management"],
            "recommendations": [
                "Focus more on essay writing practice",
                "Use time management techniques during exams"
            ]
        }
    
    async def get_student_subject_performance(self, student_id: UUID, period: str) -> List[dict]:
        """Get student's performance breakdown by subject."""
        # This is a placeholder implementation
        # In a real implementation, this would aggregate subject-specific data
        return [
            {
                "subject_name": "Mathematics",
                "average_grade": 88.0,
                "total_assessments": 5,
                "completed_assessments": 5,
                "time_spent_hours": 15.0
            },
            {
                "subject_name": "Science",
                "average_grade": 79.0,
                "total_assessments": 4,
                "completed_assessments": 3,
                "time_spent_hours": 12.0
            },
            {
                "subject_name": "English",
                "average_grade": 76.0,
                "total_assessments": 6,
                "completed_assessments": 4,
                "time_spent_hours": 18.5
            }
        ]
    
    async def get_student_recent_activities(self, student_id: UUID, limit: int = 10) -> List[dict]:
        """Get student's recent activities."""
        # This is a placeholder implementation
        # In a real implementation, this would fetch from activity logs
        from datetime import datetime, timedelta
        
        activities = []
        base_time = datetime.now()
        
        for i in range(min(limit, 5)):  # Generate some sample activities
            activities.append({
                "activity_type": "lesson" if i % 2 == 0 else "quiz",
                "activity_name": f"Sample Activity {i+1}",
                "classroom_name": f"Mathematics Class {i//2 + 1}",
                "grade": 85.0 + (i * 2) if i % 2 == 1 else None,
                "timestamp": base_time - timedelta(days=i)
            })
        
        return activities

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
            "get_teacher_weekly_reports",
            "get_student_current_rating",
            "get_student_classroom_performance",
            "get_student_analytics",
            "get_student_subject_performance",
            "get_student_recent_activities"
        ]
