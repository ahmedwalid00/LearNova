"""
Teacher Rating Controller

Business logic for teacher rating operations.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ..Models.services.teacher_rating_service import TeacherRatingService
from ..Api.Schemes.teacher_rating import (
    TeacherRatingCreate,
    TeacherRatingUpdate,
    TeacherRatingResponse,
    TeacherRatingStatsResponse,
    TeacherRatingListResponse
)


class TeacherRatingController:
    """Controller for teacher rating operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.teacher_rating_service = TeacherRatingService(session)

    async def submit_rating(
        self,
        student_id: UUID,
        rating_data: TeacherRatingCreate
    ) -> TeacherRatingResponse:
        """Submit or update a teacher rating by a student"""
        
        try:
            print(f"DEBUG: Rating submission - Student: {student_id}, Teacher: {rating_data.teacher_id}, Classroom: {rating_data.classroom_id}")
            
            # Check if student can rate this teacher in this classroom
            can_rate = await self.teacher_rating_service.can_student_rate_teacher(
                student_id=student_id,
                teacher_id=rating_data.teacher_id,
                classroom_id=rating_data.classroom_id
            )
            print(f"DEBUG: Can rate check result: {can_rate}")
            
            if not can_rate:
                raise ValueError("Student is not authorized to rate this teacher in this classroom")
            
            rating = await self.teacher_rating_service.submit_rating(
                student_id=student_id,
                teacher_id=rating_data.teacher_id,
                classroom_id=rating_data.classroom_id,
                rating_points=rating_data.rating_points,
                feedback_text=rating_data.feedback_text,
                term_id=rating_data.term_id
            )
            print(f"DEBUG: Rating submitted successfully: {rating}")
            
            return TeacherRatingResponse.model_validate(rating)
        except Exception as e:
            print(f"DEBUG: Error in submit_rating: {type(e).__name__}: {str(e)}")
            raise

    async def get_my_ratings(
        self,
        student_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> TeacherRatingListResponse:
        """Get all ratings submitted by a student"""
        
        # This would need to be implemented in the service
        # For now, we'll return an empty list
        return TeacherRatingListResponse(
            ratings=[],
            total_count=0,
            page=offset // limit + 1,
            limit=limit
        )

    async def get_teacher_ratings(
        self,
        teacher_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> TeacherRatingListResponse:
        """Get all ratings for a teacher (for admin/teacher use)"""
        
        ratings = await self.teacher_rating_service.get_teacher_ratings(
            teacher_id=teacher_id,
            limit=limit,
            offset=offset
        )
        
        rating_responses = [TeacherRatingResponse.model_validate(rating) for rating in ratings]
        
        return TeacherRatingListResponse(
            ratings=rating_responses,
            total_count=len(rating_responses),  # This should be actual count from service
            page=offset // limit + 1,
            limit=limit
        )

    async def get_teacher_rating_stats(
        self,
        teacher_id: UUID
    ) -> TeacherRatingStatsResponse:
        """Get comprehensive rating statistics for a teacher"""
        
        stats = await self.teacher_rating_service.get_teacher_rating_stats(teacher_id)
        
        return TeacherRatingStatsResponse(**stats)
