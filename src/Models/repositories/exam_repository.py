"""
Exam-related repository classes.

This module contains repository classes for exam models:
Exam and ExamResult.
"""

from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func
from datetime import date
from uuid import UUID

from .base import BaseRepository
from ..DBSchemes.Schemes.exam_models import Exam, ExamResult


class ExamRepository(BaseRepository[Exam]):
    """Repository for Exam model operations."""
    
    def __init__(self, session):
        super().__init__(session, Exam)
    
    async def get_by_teacher_id(self, teacher_id: UUID) -> List[Exam]:
        """Get all exams by teacher ID."""
        result = await self.session.execute(
            select(Exam).where(Exam.teacher_id == teacher_id)
        )
        return result.scalars().all()
    
    async def get_by_term_id(self, term_id: UUID) -> List[Exam]:
        """Get all exams by term ID."""
        result = await self.session.execute(
            select(Exam).where(Exam.term_id == term_id)
        )
        return result.scalars().all()
    
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[Exam]:
        """Get exams within a specific date range."""
        result = await self.session.execute(
            select(Exam).where(
                and_(
                    Exam.date >= start_date,
                    Exam.date <= end_date
                )
            )
        )
        return result.scalars().all()
    
    async def get_upcoming_exams(self, teacher_id: Optional[UUID] = None) -> List[Exam]:
        """Get upcoming exams (from today onwards)."""
        from datetime import date
        today = date.today()
        
        query = select(Exam).where(Exam.date >= today)
        if teacher_id:
            query = query.where(Exam.teacher_id == teacher_id)
        
        query = query.order_by(Exam.date)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_past_exams(self, teacher_id: Optional[UUID] = None) -> List[Exam]:
        """Get past exams (before today)."""
        from datetime import date
        today = date.today()
        
        query = select(Exam).where(Exam.date < today)
        if teacher_id:
            query = query.where(Exam.teacher_id == teacher_id)
        
        query = query.order_by(desc(Exam.date))
        result = await self.session.execute(query)
        return result.scalars().all()
    
    def get_model_specific_methods(self):
        """Return list of exam-specific methods."""
        return [
            "get_by_teacher_id",
            "get_by_term_id",
            "get_by_date_range",
            "get_upcoming_exams",
            "get_past_exams"
        ]


class ExamResultRepository(BaseRepository[ExamResult]):
    """Repository for ExamResult model operations."""
    
    def __init__(self, session):
        super().__init__(session, ExamResult)
    
    async def get_by_exam_id(self, exam_id: UUID) -> List[ExamResult]:
        """Get all results for a specific exam."""
        result = await self.session.execute(
            select(ExamResult).where(ExamResult.exam_id == exam_id)
        )
        return result.scalars().all()
    
    async def get_by_student_id(self, student_id: UUID) -> List[ExamResult]:
        """Get all exam results for a specific student."""
        result = await self.session.execute(
            select(ExamResult).where(ExamResult.student_id == student_id)
        )
        return result.scalars().all()
    
    async def get_by_student_and_exam(self, student_id: UUID, exam_id: UUID) -> Optional[ExamResult]:
        """Get exam result for a specific student and exam."""
        result = await self.session.execute(
            select(ExamResult).where(
                and_(
                    ExamResult.student_id == student_id,
                    ExamResult.exam_id == exam_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_score_range(self, min_score: float, max_score: float) -> List[ExamResult]:
        """Get exam results within a specific score range."""
        result = await self.session.execute(
            select(ExamResult).where(
                and_(
                    ExamResult.score >= min_score,
                    ExamResult.score <= max_score
                )
            )
        )
        return result.scalars().all()
    
    async def get_top_performers(self, exam_id: UUID, limit: int = 10) -> List[ExamResult]:
        """Get top performers for a specific exam."""
        result = await self.session.execute(
            select(ExamResult)
            .where(ExamResult.exam_id == exam_id)
            .order_by(desc(ExamResult.score))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_average_score_by_exam(self, exam_id: UUID) -> Optional[float]:
        """Get average score for a specific exam."""
        result = await self.session.execute(
            select(func.avg(ExamResult.score))
            .where(ExamResult.exam_id == exam_id)
        )
        return result.scalar()
    
    async def get_student_average_score(self, student_id: UUID) -> Optional[float]:
        """Get average score for a specific student across all exams."""
        result = await self.session.execute(
            select(func.avg(ExamResult.score))
            .where(ExamResult.student_id == student_id)
        )
        return result.scalar()
    
    def get_model_specific_methods(self):
        """Return list of exam result-specific methods."""
        return [
            "get_by_exam_id",
            "get_by_student_id",
            "get_by_student_and_exam",
            "get_by_score_range",
            "get_top_performers",
            "get_average_score_by_exam",
            "get_student_average_score"
        ]
