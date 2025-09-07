"""
Repository classes for student response models.

This module contains repository classes for managing student responses
to practice questions and exams, as well as student ratings.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, asc, case
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..DBSchemes.Schemes.student_response_models import (
    PracticeQuestionResponse, 
    ExamQuestionResponse, 
    StudentRating
)


class PracticeQuestionResponseRepository(BaseRepository[PracticeQuestionResponse]):
    """Repository for practice question responses"""
    
    def __init__(self, session):
        super().__init__(session, PracticeQuestionResponse)

    def get_model_specific_methods(self) -> List[str]:
        """Return model-specific method names"""
        return [
            "get_by_student_and_practice",
            "get_student_practice_responses",
            "get_practice_statistics",
        ]

    async def get_by_student_and_practice(
        self, 
        student_id: UUID, 
        practice_id: UUID
    ) -> Optional[PracticeQuestionResponse]:
        """Get a student's response to a specific practice question"""
        result = await self.session.execute(
            select(PracticeQuestionResponse)
            .where(
                and_(
                    PracticeQuestionResponse.student_id == student_id,
                    PracticeQuestionResponse.practice_id == practice_id
                )
            )
            .options(
                selectinload(PracticeQuestionResponse.practice_question),
                selectinload(PracticeQuestionResponse.answer)
            )
        )
        return result.scalar_one_or_none()

    async def get_student_practice_responses(
        self, 
        student_id: UUID, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[PracticeQuestionResponse]:
        """Get all practice responses for a student"""
        result = await self.session.execute(
            select(PracticeQuestionResponse)
            .where(PracticeQuestionResponse.student_id == student_id)
            .options(
                selectinload(PracticeQuestionResponse.practice_question),
                selectinload(PracticeQuestionResponse.answer)
            )
            .order_by(desc(PracticeQuestionResponse.answered_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_practice_statistics(self, student_id: UUID) -> Dict[str, Any]:
        """Get practice statistics for a student"""
        result = await self.session.execute(
            select(
                func.count(PracticeQuestionResponse.response_id).label('total_answered'),
                func.sum(
                    case(
                        (PracticeQuestionResponse.is_correct == True, 1),
                        else_=0
                    )
                ).label('total_correct'),
                func.avg(PracticeQuestionResponse.time_taken_seconds).label('avg_time_taken')
            ).where(PracticeQuestionResponse.student_id == student_id)
        )
        stats = result.one()
        
        total_answered = stats.total_answered or 0
        total_correct = stats.total_correct or 0
        accuracy_rate = (total_correct / total_answered) if total_answered > 0 else 0.0
        
        return {
            'total_answered': total_answered,
            'total_correct': total_correct,
            'accuracy_rate': accuracy_rate,
            'avg_time_taken': float(stats.avg_time_taken) if stats.avg_time_taken else 0.0
        }


class ExamQuestionResponseRepository(BaseRepository[ExamQuestionResponse]):
    """Repository for exam question responses"""
    
    def __init__(self, session):
        super().__init__(session, ExamQuestionResponse)

    def get_model_specific_methods(self) -> List[str]:
        """Return model-specific method names"""
        return [
            "get_by_student_and_question",
            "get_exam_responses",
            "get_student_exam_responses",
            "get_exam_statistics",
        ]

    async def get_by_student_and_question(
        self, 
        student_id: UUID, 
        question_id: UUID
    ) -> Optional[ExamQuestionResponse]:
        """Get a student's response to a specific exam question"""
        result = await self.session.execute(
            select(ExamQuestionResponse)
            .where(
                and_(
                    ExamQuestionResponse.student_id == student_id,
                    ExamQuestionResponse.question_id == question_id
                )
            )
            .options(
                selectinload(ExamQuestionResponse.exam_question),
                selectinload(ExamQuestionResponse.exam),
                selectinload(ExamQuestionResponse.answer)
            )
        )
        return result.scalar_one_or_none()

    async def get_exam_responses(
        self, 
        student_id: UUID, 
        exam_id: UUID
    ) -> List[ExamQuestionResponse]:
        """Get all responses for a student for a specific exam"""
        result = await self.session.execute(
            select(ExamQuestionResponse)
            .where(
                and_(
                    ExamQuestionResponse.student_id == student_id,
                    ExamQuestionResponse.exam_id == exam_id
                )
            )
            .options(
                selectinload(ExamQuestionResponse.exam_question),
                selectinload(ExamQuestionResponse.answer)
            )
            .order_by(asc(ExamQuestionResponse.answered_at))
        )
        return result.scalars().all()

    async def get_student_exam_responses(
        self, 
        student_id: UUID, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[ExamQuestionResponse]:
        """Get all exam responses for a student"""
        result = await self.session.execute(
            select(ExamQuestionResponse)
            .where(ExamQuestionResponse.student_id == student_id)
            .options(
                selectinload(ExamQuestionResponse.exam_question),
                selectinload(ExamQuestionResponse.exam),
                selectinload(ExamQuestionResponse.answer)
            )
            .order_by(desc(ExamQuestionResponse.answered_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_exam_statistics(self, student_id: UUID, exam_id: UUID) -> Dict[str, Any]:
        """Get exam statistics for a student for a specific exam"""
        result = await self.session.execute(
            select(
                func.count(ExamQuestionResponse.response_id).label('total_answered'),
                func.sum(func.cast(ExamQuestionResponse.is_correct, type_=int)).label('total_correct'),
                func.avg(ExamQuestionResponse.time_taken_seconds).label('avg_time_taken')
            ).where(
                and_(
                    ExamQuestionResponse.student_id == student_id,
                    ExamQuestionResponse.exam_id == exam_id
                )
            )
        )
        stats = result.one()
        
        total_answered = stats.total_answered or 0
        total_correct = stats.total_correct or 0
        accuracy_rate = (total_correct / total_answered) if total_answered > 0 else 0.0
        
        return {
            'total_answered': total_answered,
            'total_correct': total_correct,
            'accuracy_rate': accuracy_rate,
            'avg_time_taken': float(stats.avg_time_taken) if stats.avg_time_taken else 0.0
        }


class StudentRatingRepository(BaseRepository[StudentRating]):
    """Repository for student ratings"""
    
    def __init__(self, session):
        super().__init__(session, StudentRating)

    def get_model_specific_methods(self) -> List[str]:
        """Return model-specific method names"""
        return [
            "get_by_student_and_term",
            "get_current_rating",
            "get_top_students",
        ]

    async def get_by_student_and_term(
        self, 
        student_id: UUID, 
        term_id: UUID
    ) -> Optional[StudentRating]:
        """Get a student's rating for a specific term"""
        result = await self.session.execute(
            select(StudentRating)
            .where(
                and_(
                    StudentRating.student_id == student_id,
                    StudentRating.term_id == term_id
                )
            )
            .options(
                selectinload(StudentRating.student),
                selectinload(StudentRating.term)
            )
        )
        return result.scalar_one_or_none()

    async def get_current_rating(self, student_id: UUID) -> Optional[StudentRating]:
        """Get the student's current rating (most recent term)"""
        result = await self.session.execute(
            select(StudentRating)
            .where(StudentRating.student_id == student_id)
            .options(
                selectinload(StudentRating.student),
                selectinload(StudentRating.term)
            )
            .order_by(desc(StudentRating.last_updated))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_top_students(
        self, 
        term_id: Optional[UUID] = None, 
        limit: int = 10
    ) -> List[StudentRating]:
        """Get top students by rating"""
        query = select(StudentRating).options(
            selectinload(StudentRating.student),
            selectinload(StudentRating.term)
        )
        
        if term_id:
            query = query.where(StudentRating.term_id == term_id)
        
        query = query.order_by(desc(StudentRating.overall_rating)).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
