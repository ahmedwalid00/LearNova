"""
Student Response Service

This module handles business logic for student responses to practice questions
and exams, including rating calculations and classroom validation.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.Models.repositories.student_response_repository import (
    PracticeQuestionResponseRepository,
    ExamQuestionResponseRepository,
    StudentRatingRepository
)
from src.Models.repositories.user_repository import StudentRepository
from src.Models.repositories.question_repository import QuestionPracticeRepository, QuestionExamRepository
from src.Models.repositories.exam_repository import ExamRepository
from src.Models.repositories.classroom_repository import ClassRoomRepository
from src.Models.repositories.classroom_student_repository import ClassRoomStudentRepository
from src.Models.repositories.academic_term_repository import AcademicTermRepository

from ..DBSchemes.Schemes.student_response_models import (
    PracticeQuestionResponse,
    ExamQuestionResponse,
    StudentRating
)
from ..DBSchemes.Schemes.user_models import Student
from ..DBSchemes.Schemes.question_models import QuestionPractice, QuestionExam
from ..DBSchemes.Schemes.exam_models import Exam
from ..DBSchemes.Schemes.associations import ClassRoomStudent


class StudentResponseService:
    """Service for handling student responses to questions and exams"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.practice_response_repo = PracticeQuestionResponseRepository(session)
        self.exam_response_repo = ExamQuestionResponseRepository(session)
        self.rating_repo = StudentRatingRepository(session)
        self.student_repo = StudentRepository(session)
        self.practice_question_repo = QuestionPracticeRepository(session)
        self.exam_question_repo = QuestionExamRepository(session)
        self.exam_repo = ExamRepository(session)
        self.classroom_repo = ClassRoomRepository(session)
        self.classroom_student_repo = ClassRoomStudentRepository(session)
        self.term_repo = AcademicTermRepository(session)

    async def answer_practice_question(
        self,
        student_id: UUID,
        practice_id: UUID,
        answer_id: UUID,
        time_taken_seconds: Optional[int] = None
    ) -> Tuple[PracticeQuestionResponse, bool]:
        """
        Submit a student's answer to a practice question.
        
        Returns:
            Tuple of (response, is_first_attempt)
        """
        # Check if student already answered this question
        existing_response = await self.practice_response_repo.get_by_student_and_practice(
            student_id, practice_id
        )
        
        if existing_response:
            # Student already answered this question
            return existing_response, False
        
        # Get the practice question
        question = await self.practice_question_repo.get_by_id(practice_id)
        if not question:
            raise ValueError("Practice question not found")
        
        # Verify student is enrolled in a classroom with this teacher and term
        await self._verify_student_teacher_access(student_id, question.teacher_id, question.term_id)
        
        # Get the answer to check if it's correct
        from ..repositories.question_repository import AnswerRepository
        answer_repo = AnswerRepository(self.session)
        answer = await answer_repo.get_by_id(answer_id)
        if not answer:
            raise ValueError("Answer not found")
        
        # Verify the answer belongs to this practice question
        if answer.question_practice_id != practice_id:
            raise ValueError("Answer does not belong to this practice question")
        
        # Check if the answer is correct (is_correct = 1 means true)
        is_correct = answer.is_correct == 1
        
        # Create the response
        response = await self.practice_response_repo.create(
            student_id=student_id,
            practice_id=practice_id,
            answer_id=answer_id,
            is_correct=is_correct,
            time_taken_seconds=time_taken_seconds or 0,
            answered_at=datetime.utcnow()
        )
        
        # Update student rating after practice answer
        await self._update_student_rating(student_id)
        
        return response, True

    async def answer_exam_question(
        self,
        student_id: UUID,
        exam_id: UUID,
        question_id: UUID,
        answer_id: UUID,
        time_taken_seconds: Optional[int] = None
    ) -> Tuple[ExamQuestionResponse, bool]:
        """
        Submit a student's answer to an exam question.
        
        Returns:
            Tuple of (response, is_first_attempt)
        """
        # Check if student already answered this question
        existing_response = await self.exam_response_repo.get_by_student_and_question(
            student_id, question_id
        )
        
        if existing_response:
            # Student already answered this question
            return existing_response, False
        
        # Get the exam and question
        exam = await self.exam_repo.get_by_id(exam_id)
        if not exam:
            raise ValueError("Exam not found")
        
        question = await self.exam_question_repo.get_by_id(question_id)
        if not question:
            raise ValueError("Exam question not found")
        
        # Verify the question belongs to this exam
        if question.exam_id != exam_id:
            raise ValueError("Question does not belong to this exam")
        
        # Verify student is enrolled in a classroom with this teacher and term
        await self._verify_student_teacher_access(student_id, exam.teacher_id, exam.term_id)
        
        # Get the answer to check if it's correct
        from ..repositories.question_repository import AnswerRepository
        answer_repo = AnswerRepository(self.session)
        answer = await answer_repo.get_by_id(answer_id)
        if not answer:
            raise ValueError("Answer not found")
        
        # Verify the answer belongs to this exam question
        if answer.question_exam_id != question_id:
            raise ValueError("Answer does not belong to this exam question")
        
        # Check if the answer is correct (is_correct = 1 means true)
        is_correct = answer.is_correct == 1
        
        # Create the response
        response = await self.exam_response_repo.create(
            student_id=student_id,
            exam_id=exam_id,
            question_id=question_id,
            answer_id=answer_id,
            is_correct=is_correct,
            time_taken_seconds=time_taken_seconds or 0,
            answered_at=datetime.utcnow()
        )
        
        # Update student rating after exam answer
        await self._update_student_rating(student_id)
        
        return response, True

    async def get_student_practice_responses(
        self,
        student_id: UUID,
        classroom_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[PracticeQuestionResponse]:
        """Get student's practice question responses with optional classroom filter"""
        # Note: classroom_id filtering temporarily disabled until proper teacher/term filtering is implemented
        # TODO: Implement proper access control based on teacher_id/term_id
        
        responses = await self.practice_response_repo.get_student_practice_responses(
            student_id, limit, offset
        )
        
        return responses

    async def get_student_exam_responses(
        self,
        student_id: UUID,
        exam_id: Optional[UUID] = None,
        classroom_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ExamQuestionResponse]:
        """Get student's exam responses with optional filters"""
        # Note: classroom_id filtering temporarily disabled until proper teacher/term filtering is implemented
        # TODO: Implement proper access control based on teacher_id/term_id
        
        if exam_id:
            # Get responses for specific exam
            responses = await self.exam_response_repo.get_exam_responses(student_id, exam_id)
        else:
            # Get all exam responses for student
            responses = await self.exam_response_repo.get_student_exam_responses(
                student_id, limit, offset
            )
        
        return responses

    async def get_student_performance_summary(self, student_id: UUID) -> Dict[str, Any]:
        """Get comprehensive performance summary for a student"""
        # Get practice statistics
        practice_stats = await self.practice_response_repo.get_practice_statistics(student_id)
        
        # Get exam statistics - we need to calculate this manually since it's across all exams
        exam_responses = await self.exam_response_repo.get_student_exam_responses(student_id)
        
        total_exam_answered = len(exam_responses)
        total_exam_correct = sum(1 for r in exam_responses if r.is_correct)
        exam_accuracy = (total_exam_correct / total_exam_answered) if total_exam_answered > 0 else 0.0
        avg_exam_time = sum(r.time_taken_seconds or 0 for r in exam_responses) / total_exam_answered if total_exam_answered > 0 else 0.0
        
        # Get current rating
        current_rating = await self.rating_repo.get_current_rating(student_id)
        
        return {
            'practice_statistics': practice_stats,
            'exam_statistics': {
                'total_answered': total_exam_answered,
                'total_correct': total_exam_correct,
                'accuracy_rate': exam_accuracy,
                'avg_time_taken': avg_exam_time
            },
            'current_rating': {
                'overall_rating': current_rating.overall_rating if current_rating else 0.0,
                'practice_accuracy': current_rating.practice_accuracy_rate if current_rating else 0.0,
                'average_exam_score': current_rating.average_exam_score if current_rating else 0.0,
                'last_updated': current_rating.last_updated if current_rating else None
            }
        }

    async def _verify_student_teacher_access(self, student_id: UUID, teacher_id: UUID, term_id: UUID) -> None:
        """Verify that a student is enrolled in a classroom with the specified teacher and term"""
        # First, get all classrooms for this teacher and term
        from sqlalchemy import and_
        from ..DBSchemes.Schemes.associations import ClassRoom
        
        classrooms = await self.session.execute(
            select(ClassRoom).where(
                and_(
                    ClassRoom.teacher_id == teacher_id,
                    ClassRoom.term_id == term_id
                )
            )
        )
        classroom_ids = [classroom.classroom_id for classroom in classrooms.scalars().all()]
        
        if not classroom_ids:
            raise ValueError("No classrooms found for this teacher and term")
        
        # Then check if student is enrolled in any of these classrooms
        enrollment = None
        for classroom_id in classroom_ids:
            enrollment = await self.classroom_student_repo.get_by_classroom_and_student(
                classroom_id, student_id
            )
            if enrollment:
                break
        
        if not enrollment:
            raise ValueError("Student is not enrolled in any classroom with this teacher for this term")

    async def _update_student_rating(self, student_id: UUID) -> None:
        """Update student rating based on recent performance"""
        # Get student's current term
        student = await self.student_repo.get_by_id(student_id)
        if not student or not student.term_id:
            return
        
        # Calculate new ratings
        practice_stats = await self.practice_response_repo.get_practice_statistics(student_id)
        
        # Get recent exam responses for exam stats
        exam_responses = await self.exam_response_repo.get_student_exam_responses(student_id)
        total_exam_correct = sum(1 for r in exam_responses if r.is_correct)
        total_exam_answered = len(exam_responses)
        average_exam_score = (total_exam_correct / total_exam_answered * 100) if total_exam_answered > 0 else 0.0
        
        # Calculate overall rating (60% exam, 40% practice)
        practice_rating = practice_stats['accuracy_rate'] * 100
        overall_rating = (average_exam_score * 0.6) + (practice_rating * 0.4)
        
        # Get or create rating record
        existing_rating = await self.rating_repo.get_by_student_and_term(
            student_id, student.term_id
        )
        
        if existing_rating:
            # Update existing rating
            await self.rating_repo.update(
                existing_rating.rating_id,
                practice_questions_answered=practice_stats['total_answered'],
                practice_questions_correct=practice_stats['total_correct'],
                practice_accuracy_rate=practice_stats['accuracy_rate'],
                exams_taken=total_exam_answered,
                total_exam_score=total_exam_correct,
                average_exam_score=average_exam_score,
                overall_rating=overall_rating,
                last_updated=datetime.utcnow()
            )
        else:
            # Create new rating
            await self.rating_repo.create(
                student_id=student_id,
                term_id=student.term_id,
                practice_questions_answered=practice_stats['total_answered'],
                practice_questions_correct=practice_stats['total_correct'],
                practice_accuracy_rate=practice_stats['accuracy_rate'],
                exams_taken=total_exam_answered,
                total_exam_score=total_exam_correct,
                average_exam_score=average_exam_score,
                overall_rating=overall_rating,
                last_updated=datetime.utcnow()
            )

