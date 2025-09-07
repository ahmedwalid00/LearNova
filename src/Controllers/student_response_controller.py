"""
Student Response Controller

This module handles HTTP endpoints for student responses to practice questions
and exams, including performance tracking and rating system.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.services.student_response_service import StudentResponseService


class StudentResponseController:
    """Controller for student response endpoints"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.service = StudentResponseService(session)

    async def answer_practice_question(
        self,
        student_id: UUID,
        practice_id: UUID,
        answer_id: UUID,
        time_taken_seconds: Optional[int] = None
    ) -> dict:
        """Handle student answering a practice question"""
        try:
            response, is_first_attempt = await self.service.answer_practice_question(
                student_id=student_id,
                practice_id=practice_id,
                answer_id=answer_id,
                time_taken_seconds=time_taken_seconds
            )
            
            return {
                "success": True,
                "message": "Answer submitted successfully" if is_first_attempt else "You have already answered this question",
                "data": {
                    "response_id": str(response.response_id),
                    "is_correct": response.is_correct,
                    "is_first_attempt": is_first_attempt,
                    "answered_at": response.answered_at.isoformat(),
                    "time_taken_seconds": response.time_taken_seconds
                }
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit answer: {str(e)}"
            )

    async def answer_exam_question(
        self,
        student_id: UUID,
        exam_id: UUID,
        question_id: UUID,
        answer_id: UUID,
        time_taken_seconds: Optional[int] = None
    ) -> dict:
        """Handle student answering an exam question"""
        try:
            response, is_first_attempt = await self.service.answer_exam_question(
                student_id=student_id,
                exam_id=exam_id,
                question_id=question_id,
                answer_id=answer_id,
                time_taken_seconds=time_taken_seconds
            )
            
            return {
                "success": True,
                "message": "Answer submitted successfully" if is_first_attempt else "You have already answered this question",
                "data": {
                    "response_id": str(response.response_id),
                    "is_correct": response.is_correct,
                    "is_first_attempt": is_first_attempt,
                    "answered_at": response.answered_at.isoformat(),
                    "time_taken_seconds": response.time_taken_seconds
                }
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit answer: {str(e)}"
            )

    async def get_practice_responses(
        self,
        student_id: UUID,
        classroom_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """Get student's practice question responses"""
        try:
            responses = await self.service.get_student_practice_responses(
                student_id=student_id,
                classroom_id=classroom_id,
                limit=limit,
                offset=offset
            )
            
            response_data = []
            for response in responses:
                response_data.append({
                    "response_id": str(response.response_id),
                    "practice_id": str(response.practice_id),
                    "question_text": response.practice_question.content if response.practice_question else None,
                    "is_correct": response.is_correct,
                    "time_taken_seconds": response.time_taken_seconds,
                    "answered_at": response.answered_at.isoformat(),
                    "teacher_id": str(response.practice_question.teacher_id) if response.practice_question else None,
                    "term_id": str(response.practice_question.term_id) if response.practice_question else None
                })
            
            return {
                "success": True,
                "data": {
                    "responses": response_data,
                    "total_count": len(response_data),
                    "limit": limit,
                    "offset": offset
                }
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get practice responses: {str(e)}"
            )

    async def get_exam_responses(
        self,
        student_id: UUID,
        exam_id: Optional[UUID] = None,
        classroom_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """Get student's exam responses"""
        try:
            responses = await self.service.get_student_exam_responses(
                student_id=student_id,
                exam_id=exam_id,
                classroom_id=classroom_id,
                limit=limit,
                offset=offset
            )
            
            response_data = []
            for response in responses:
                response_data.append({
                    "response_id": str(response.response_id),
                    "exam_id": str(response.exam_id),
                    "question_id": str(response.question_id),
                    "question_text": response.exam_question.content if response.exam_question else None,
                    "is_correct": response.is_correct,
                    "time_taken_seconds": response.time_taken_seconds,
                    "answered_at": response.answered_at.isoformat(),
                    "exam_title": response.exam.title if response.exam else None
                })
            
            return {
                "success": True,
                "data": {
                    "responses": response_data,
                    "total_count": len(response_data),
                    "limit": limit,
                    "offset": offset
                }
            }
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get exam responses: {str(e)}"
            )

    async def get_performance_summary(self, student_id: UUID) -> dict:
        """Get comprehensive performance summary for a student"""
        try:
            summary = await self.service.get_student_performance_summary(student_id)
            
            return {
                "success": True,
                "data": {
                    "student_id": str(student_id),
                    "practice_performance": {
                        "total_answered": summary['practice_statistics']['total_answered'],
                        "total_correct": summary['practice_statistics']['total_correct'],
                        "accuracy_rate": round(summary['practice_statistics']['accuracy_rate'] * 100, 2),
                        "average_time_seconds": round(summary['practice_statistics']['avg_time_taken'], 2)
                    },
                    "exam_performance": {
                        "total_answered": summary['exam_statistics']['total_answered'],
                        "total_correct": summary['exam_statistics']['total_correct'],
                        "accuracy_rate": round(summary['exam_statistics']['accuracy_rate'] * 100, 2),
                        "average_time_seconds": round(summary['exam_statistics']['avg_time_taken'], 2)
                    },
                    "rating": {
                        "overall_rating": round(summary['current_rating']['overall_rating'], 2),
                        "practice_accuracy": round(summary['current_rating']['practice_accuracy'] * 100, 2),
                        "average_exam_score": round(summary['current_rating']['average_exam_score'], 2),
                        "last_updated": summary['current_rating']['last_updated'].isoformat() if summary['current_rating']['last_updated'] else None
                    }
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get performance summary: {str(e)}"
            )
