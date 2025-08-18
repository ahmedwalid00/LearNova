"""
Exam service for orchestrating exam-related business logic.

This module contains the ExamService class that handles complex
operations involving exams, results, and analytics.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from uuid import UUID

from ..repositories.exam_repository import ExamRepository, ExamResultRepository
from ..repositories.user_repository import StudentRepository, TeacherRepository


class ExamService:
    """
    Service class for exam-related business logic.
    
    This class orchestrates operations involving exams, results,
    and performance analytics.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the service with database session."""
        self.session = session
        self.exam_repo = ExamRepository(session)
        self.result_repo = ExamResultRepository(session)
        self.student_repo = StudentRepository(session)
        self.teacher_repo = TeacherRepository(session)
    
    async def create_exam_with_results(
        self, 
        exam_data: Dict[str, Any], 
        student_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Create an exam and initialize empty results for specified students.
        
        Args:
            exam_data: Dictionary with exam fields
            student_ids: List of student UUIDs to create results for
            
        Returns:
            Dict with created exam and result records
        """
        try:
            # Create the exam
            exam = await self.exam_repo.create(**exam_data)
            
            # Create empty results for each student
            results = []
            for student_id in student_ids:
                result_data = {
                    "exam_id": exam.exam_id,
                    "student_id": student_id,
                    "score": 0.0,
                    "exam_rating": None,
                    "term_id": exam.term_id
                }
                result = await self.result_repo.create(**result_data)
                results.append(result)
            
            return {
                "exam": exam,
                "results": results,
                "total_students": len(results)
            }
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def submit_exam_result(
        self, 
        student_id: UUID, 
        exam_id: UUID, 
        score: float,
        exam_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Submit or update an exam result and update student rating.
        
        Args:
            student_id: UUID of the student
            exam_id: UUID of the exam
            score: Score achieved
            exam_rating: Optional rating given to the exam
            
        Returns:
            Dict with result and updated student info
        """
        try:
            # Update or create exam result
            existing_result = await self.result_repo.get_by_student_and_exam(student_id, exam_id)
            
            if existing_result:
                result = await self.result_repo.update(
                    existing_result.result_id,
                    score=score,
                    exam_rating=exam_rating
                )
            else:
                exam = await self.exam_repo.get_by_id(exam_id)
                result_data = {
                    "exam_id": exam_id,
                    "student_id": student_id,
                    "score": score,
                    "exam_rating": exam_rating,
                    "term_id": exam.term_id
                }
                result = await self.result_repo.create(**result_data)
            
            # Recalculate student's average rating
            student_avg = await self.result_repo.get_student_average_score(student_id)
            if student_avg is not None:
                await self.student_repo.update(student_id, rating=student_avg)
            
            return {
                "result": result,
                "new_average": student_avg
            }
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_exam_analytics(self, exam_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive analytics for an exam.
        
        Args:
            exam_id: UUID of the exam
            
        Returns:
            Dict with exam analytics
        """
        exam = await self.exam_repo.get_by_id(exam_id)
        if not exam:
            return {}
        
        results = await self.result_repo.get_by_exam_id(exam_id)
        
        if not results:
            return {
                "exam": exam,
                "total_students": 0,
                "analytics": {}
            }
        
        # Calculate statistics
        scores = [r.score for r in results if r.score is not None]
        ratings = [r.exam_rating for r in results if r.exam_rating is not None]
        
        analytics = {
            "total_students": len(results),
            "submitted_count": len(scores),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "average_exam_rating": sum(ratings) / len(ratings) if ratings else 0,
            "pass_rate": len([s for s in scores if s >= 60]) / len(scores) * 100 if scores else 0
        }
        
        # Get top performers
        top_performers = await self.result_repo.get_top_performers(exam_id, limit=5)
        
        return {
            "exam": exam,
            "analytics": analytics,
            "top_performers": top_performers,
            "score_distribution": {
                "90-100": len([s for s in scores if s >= 90]),
                "80-89": len([s for s in scores if 80 <= s < 90]),
                "70-79": len([s for s in scores if 70 <= s < 80]),
                "60-69": len([s for s in scores if 60 <= s < 70]),
                "below_60": len([s for s in scores if s < 60])
            }
        }
    
    async def get_student_exam_history(self, student_id: UUID) -> Dict[str, Any]:
        """
        Get complete exam history for a student.
        
        Args:
            student_id: UUID of the student
            
        Returns:
            Dict with student exam history and analytics
        """
        student = await self.student_repo.get_by_id(student_id)
        results = await self.result_repo.get_by_student_id(student_id)
        
        if not results:
            return {
                "student": student,
                "total_exams": 0,
                "analytics": {}
            }
        
        # Get exam details for each result
        exam_history = []
        for result in results:
            exam = await self.exam_repo.get_by_id(result.exam_id)
            exam_history.append({
                "exam": exam,
                "result": result
            })
        
        # Sort by exam date
        exam_history.sort(key=lambda x: x["exam"].date, reverse=True)
        
        # Calculate analytics
        scores = [r.score for r in results if r.score is not None]
        avg_score = await self.result_repo.get_student_average_score(student_id)
        
        return {
            "student": student,
            "exam_history": exam_history,
            "analytics": {
                "total_exams": len(results),
                "completed_exams": len(scores),
                "average_score": avg_score or 0,
                "best_score": max(scores) if scores else 0,
                "recent_trend": self._calculate_trend(exam_history[-5:]) if len(exam_history) >= 3 else "insufficient_data"
            }
        }
    
    def _calculate_trend(self, recent_exams: List[Dict]) -> str:
        """Calculate performance trend from recent exams."""
        if len(recent_exams) < 3:
            return "insufficient_data"
        
        scores = [exam["result"].score for exam in recent_exams if exam["result"].score is not None]
        if len(scores) < 3:
            return "insufficient_data"
        
        # Simple trend calculation
        first_half_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        
        if second_half_avg > first_half_avg + 5:
            return "improving"
        elif second_half_avg < first_half_avg - 5:
            return "declining"
        else:
            return "stable"
