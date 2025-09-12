"""
Teacher API Routes

FastAPI routes for teacher-related operations including:
- Profile management
- Classroom access
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.Api.dependencies import get_current_user, get_db_session, RoleChecker
from src.Controllers.teacher_controller import TeacherController
from src.Api.Schemes.teachers import (
    TeacherProfileResponse,
    TeacherProfileUpdateRequest,
    TeacherClassroomListResponse
)
from src.Enums.user_type_enums import UserTypeEnum


# Create router with prefix and tags
router = APIRouter(
    prefix="/api/v1/teachers",
    tags=["Teachers"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Teacher not found"},
        500: {"description": "Internal Server Error"}
    }
)


@router.get(
    "/me/profile",
    response_model=TeacherProfileResponse,
    summary="Get Teacher Profile",
    description="Retrieve the current teacher's profile information"
)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
    _: bool = Depends(RoleChecker([UserTypeEnum.TEACHER.value, UserTypeEnum.ADMIN.value]))
):
    """Get the current teacher's profile information"""
    try:
        controller = TeacherController(db_session)
        teacher_id = UUID(current_user["id"])
        
        profile = await controller.get_teacher_profile(teacher_id)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve teacher profile"
        )


@router.put(
    "/me/profile",
    response_model=TeacherProfileResponse,
    summary="Update Teacher Profile",
    description="Update the current teacher's profile information"
)
async def update_my_profile(
    update_data: TeacherProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
    _: bool = Depends(RoleChecker([UserTypeEnum.TEACHER.value, UserTypeEnum.ADMIN.value]))
):
    """Update the current teacher's profile information"""
    try:
        controller = TeacherController(db_session)
        teacher_id = UUID(current_user["id"])
        
        updated_profile = await controller.update_teacher_profile(
            teacher_id=teacher_id,
            update_data=update_data
        )
        return updated_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update teacher profile"
        )


@router.get(
    "/me/classrooms",
    response_model=TeacherClassroomListResponse,
    summary="Get Teacher Classrooms",
    description="Retrieve all classrooms assigned to the current teacher"
)
async def get_my_classrooms(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
    _: bool = Depends(RoleChecker([UserTypeEnum.TEACHER.value, UserTypeEnum.ADMIN.value]))
):
    """Get all classrooms assigned to the current teacher"""
    try:
        controller = TeacherController(db_session)
        teacher_id = UUID(current_user["id"])
        
        classrooms = await controller.get_teacher_classrooms(
            teacher_id=teacher_id,
            page=page,
            page_size=page_size
        )
        return classrooms
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve teacher classrooms"
        )
