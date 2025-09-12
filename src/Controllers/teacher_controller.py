"""
Teacher Controller

Handles business logic for teacher-related operations including
profile management and classroom access.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.repositories.user_repository import TeacherRepository
from src.Models.repositories.classroom_repository import ClassRoomRepository
from src.Models.repositories.classroom_student_repository import ClassRoomStudentRepository
from src.Models.services.teacher_rating_service import TeacherRatingService
from src.Api.Schemes.teachers import (
    TeacherProfileResponse,
    TeacherProfileUpdateRequest,
    TeacherClassroomResponse,
    TeacherClassroomListResponse
)


class TeacherController:
    """Controller for teacher operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.teacher_repo = TeacherRepository(session)
        self.classroom_repo = ClassRoomRepository(session)
        self.classroom_student_repo = ClassRoomStudentRepository(session)

    async def get_teacher_profile(self, teacher_id: UUID) -> TeacherProfileResponse:
        """Get teacher profile information"""
        try:
            # Get teacher from database
            teacher_rating_service = TeacherRatingService(self.session)
            result = await teacher_rating_service.get_teacher_profile(teacher_id)

            return result  # Service returns the response object directly

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve teacher profile: {str(e)}"
            )

    async def update_teacher_profile(
        self, 
        teacher_id: UUID, 
        update_data: TeacherProfileUpdateRequest
    ) -> TeacherProfileResponse:
        """Update teacher profile information"""
        try:
            teacher_rating_service = TeacherRatingService(self.session)
            result = await teacher_rating_service.update_teacher_profile(
                teacher_id, update_data
            )
            return result  # Service returns the response object directly

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update teacher profile: {str(e)}"
            )

    async def get_teacher_classrooms(
        self, 
        teacher_id: UUID,
        page: int = 1,
        page_size: int = 10
    ) -> TeacherClassroomListResponse:
        """Get all classrooms for a teacher with pagination"""
        try:
            
            teacher_rating_service = TeacherRatingService(self.session)
            result = await teacher_rating_service.get_teacher_classrooms(
                teacher_id, page, page_size
            )
            return result  # No need for from_orm since service returns the response object

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve teacher classrooms: {str(e)}"
            )
