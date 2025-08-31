"""
Question-related repository classes.

This module contains repository classes for question models:
QuestionPractice, QuestionExam, and Answer.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import selectinload
from uuid import UUID

from .base import BaseRepository
from ..DBSchemes.Schemes.question_models import QuestionPractice, QuestionExam, Answer


class QuestionPracticeRepository(BaseRepository[QuestionPractice]):
    """Repository for QuestionPractice model operations."""
    
    def __init__(self, session):
        super().__init__(session, QuestionPractice)
    
    async def get_by_teacher_id(self, teacher_id: UUID, limit: int = 50, offset: int = 0) -> List[QuestionPractice]:
        """Get practice questions by teacher ID with pagination."""
        result = await self.session.execute(
            select(QuestionPractice)
            .where(QuestionPractice.teacher_id == teacher_id)
            .options(selectinload(QuestionPractice.answers))
            .order_by(desc(QuestionPractice.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def count_by_teacher_id(self, teacher_id: UUID) -> int:
        """Count total practice questions by teacher ID."""
        result = await self.session.execute(
            select(func.count(QuestionPractice.practice_id))
            .where(QuestionPractice.teacher_id == teacher_id)
        )
        return result.scalar() or 0
    
    async def get_by_difficulty(self, teacher_id: UUID, difficulty: str) -> List[QuestionPractice]:
        """Get practice questions by teacher and difficulty."""
        result = await self.session.execute(
            select(QuestionPractice)
            .where(and_(
                QuestionPractice.teacher_id == teacher_id,
                QuestionPractice.difficulty == difficulty
            ))
            .options(selectinload(QuestionPractice.answers))
        )
        return result.scalars().all()
    
    async def get_with_answers(self, practice_id: UUID) -> Optional[QuestionPractice]:
        """Get practice question with all answers."""
        result = await self.session.execute(
            select(QuestionPractice)
            .where(QuestionPractice.practice_id == practice_id)
            .options(selectinload(QuestionPractice.answers))
        )
        return result.scalar_one_or_none()
    
    def get_model_specific_methods(self):
        """Return model-specific methods for QuestionPractice."""
        return {
            'get_by_teacher_id': self.get_by_teacher_id,
            'count_by_teacher_id': self.count_by_teacher_id,
            'get_by_difficulty': self.get_by_difficulty,
            'get_with_answers': self.get_with_answers
        }


class QuestionExamRepository(BaseRepository[QuestionExam]):
    """Repository for QuestionExam model operations."""
    
    def __init__(self, session):
        super().__init__(session, QuestionExam)
    
    async def get_by_exam_id(self, exam_id: UUID) -> List[QuestionExam]:
        """Get all questions for a specific exam."""
        result = await self.session.execute(
            select(QuestionExam)
            .where(QuestionExam.exam_id == exam_id)
            .options(selectinload(QuestionExam.answers))
            .order_by(QuestionExam.created_at)
        )
        return result.scalars().all()
    
    async def get_by_teacher_id(self, teacher_id: UUID) -> List[QuestionExam]:
        """Get all exam questions by teacher ID."""
        result = await self.session.execute(
            select(QuestionExam)
            .where(QuestionExam.teacher_id == teacher_id)
            .options(selectinload(QuestionExam.answers))
            .order_by(desc(QuestionExam.created_at))
        )
        return result.scalars().all()
    
    async def count_by_exam_id(self, exam_id: UUID) -> int:
        """Count questions in an exam."""
        result = await self.session.execute(
            select(func.count(QuestionExam.question_id))
            .where(QuestionExam.exam_id == exam_id)
        )
        return result.scalar() or 0
    
    async def get_with_answers(self, question_id: UUID) -> Optional[QuestionExam]:
        """Get exam question with all answers."""
        result = await self.session.execute(
            select(QuestionExam)
            .where(QuestionExam.question_id == question_id)
            .options(selectinload(QuestionExam.answers))
        )
        return result.scalar_one_or_none()
    
    def get_model_specific_methods(self):
        """Return model-specific methods for QuestionExam."""
        return {
            'get_by_exam_id': self.get_by_exam_id,
            'get_by_teacher_id': self.get_by_teacher_id,
            'count_by_exam_id': self.count_by_exam_id,
            'get_with_answers': self.get_with_answers
        }


class AnswerRepository(BaseRepository[Answer]):
    """Repository for Answer model operations."""
    
    def __init__(self, session):
        super().__init__(session, Answer)
    
    async def get_by_practice_question_id(self, practice_id: UUID) -> List[Answer]:
        """Get all answers for a practice question."""
        result = await self.session.execute(
            select(Answer).where(Answer.question_practice_id == practice_id)
        )
        return result.scalars().all()
    
    async def get_by_exam_question_id(self, question_id: UUID) -> List[Answer]:
        """Get all answers for an exam question."""
        result = await self.session.execute(
            select(Answer).where(Answer.question_exam_id == question_id)
        )
        return result.scalars().all()
    
    async def get_correct_answer_for_practice(self, practice_id: UUID) -> Optional[Answer]:
        """Get the correct answer for a practice question."""
        result = await self.session.execute(
            select(Answer).where(and_(
                Answer.question_practice_id == practice_id,
                Answer.is_correct == 1
            ))
        )
        return result.scalar_one_or_none()
    
    async def get_correct_answer_for_exam(self, question_id: UUID) -> Optional[Answer]:
        """Get the correct answer for an exam question."""
        result = await self.session.execute(
            select(Answer).where(and_(
                Answer.question_exam_id == question_id,
                Answer.is_correct == 1
            ))
        )
        return result.scalar_one_or_none()
    
    def get_model_specific_methods(self):
        """Return model-specific methods for Answer."""
        return {
            'get_by_practice_question_id': self.get_by_practice_question_id,
            'get_by_exam_question_id': self.get_by_exam_question_id,
            'get_correct_answer_for_practice': self.get_correct_answer_for_practice,
            'get_correct_answer_for_exam': self.get_correct_answer_for_exam
        }
