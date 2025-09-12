"""
Student API Routes

FastAPI routes for student-related operations including:
- Profile management
- Classroom access
- Analytics viewing
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.Api.dependencies import get_current_user, get_db_session
from src.Controllers.student_controller import StudentController
from src.Controllers.teacher_rating_controller import TeacherRatingController
from src.Api.dependencies import RoleChecker
from src.Api.Schemes.student import (
    StudentProfileResponse,
    StudentClassroomResponse,
    StudentClassroomListResponse,
    StudentAnalyticsResponse,
    StudentProfileUpdateRequest,
    PracticeQuestionsListResponse,
    ExamsListResponse
)
from src.Api.Schemes.teacher_rating import (
    TeacherRatingCreate,
    TeacherRatingResponse,
    TeacherRatingListResponse
)
from src.Enums.user_type_enums import UserTypeEnum


# Create router with prefix and tags
router = APIRouter(
    prefix="/api/v1/students",
    tags=["Students"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Student not found"},
        500: {"description": "Internal Server Error"}
    }
)

student_admin_checker = RoleChecker(allowed_roles=[UserTypeEnum.STUDENT.value , UserTypeEnum.ADMIN.value])



@router.get("/me/profile", response_model=StudentProfileResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(student_admin_checker),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get current student's profile information
    
    Returns:
        StudentProfileResponse: Complete student profile with statistics
    """
    
    try:
        controller = StudentController(db_session)
        student_id = UUID(current_user["id"])  # Convert string ID to UUID
        profile = await controller.get_student_profile(student_id)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student profile"
        )


@router.put("/me/profile", response_model=StudentProfileResponse)
async def update_my_profile(
    update_data: StudentProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(student_admin_checker),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Update current student's profile information
    
    Args:
        update_data: Fields to update in student profile
        
    Returns:
        StudentProfileResponse: Updated student profile
    """
    
    try:
        controller = StudentController(db_session)
        
        # Convert Pydantic model to dict, excluding None values
        update_dict = update_data.dict(exclude_none=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )
        
        # Update student profile
        updated_profile = await controller.update_student_profile(
            student_id=UUID(current_user["id"]),
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
            detail="Failed to update student profile"
        )


@router.get("/me/classrooms", response_model=StudentClassroomListResponse)
async def get_my_classrooms(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(student_admin_checker),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get current student's enrolled classrooms with pagination
    
    Args:
        page: Page number (1-based)
        page_size: Number of classrooms per page
        
    Returns:
        StudentClassroomListResponse: Paginated list of student's classrooms
    """
    
    try:
        controller = StudentController(db_session)
        
        # Calculate offset for pagination
        offset = (page - 1) * page_size
        
        # Get classrooms
        classrooms = await controller.get_student_classrooms(
            student_id=UUID(current_user["id"]),
            limit=page_size,
            offset=offset
        )
        
        # Get total count for pagination info
        # Note: This would require a separate method in the controller
        # For now, we'll estimate based on returned results
        total_count = len(classrooms) + offset
        has_more = len(classrooms) == page_size
        
        return StudentClassroomListResponse(
            classrooms=classrooms,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student classrooms"
        )


# Future endpoints that could be added:



@router.get("/me/practice", response_model=PracticeQuestionsListResponse)
async def get_practice_questions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(student_admin_checker),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get practice questions available to the student
    
    Returns practice questions from all teachers in classrooms the student is enrolled in.
    
    Args:
        page: Page number (1-based)
        page_size: Number of questions per page
        
    Returns:
        PracticeQuestionsListResponse: Paginated list of practice questions
    """
    
    try:
        controller = StudentController(db_session)
        student_id = UUID(current_user["id"])
        
        questions = await controller.get_practice_questions(
            student_id=student_id,
            page=page,
            page_size=page_size
        )
        return questions
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve practice questions"
        )


@router.get("/me/exams", response_model=ExamsListResponse)
async def get_exams(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(student_admin_checker),
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Get exams available to the student
    
    Returns exams from all teachers in classrooms the student is enrolled in.
    Shows exam status (taken/not taken) and scores for completed exams.
    
    Args:
        page: Page number (1-based)
        page_size: Number of exams per page
        
    Returns:
        ExamsListResponse: Paginated list of exams
    """
    
    try:
        controller = StudentController(db_session)
        student_id = UUID(current_user["id"])
        
        exams = await controller.get_exams(
            student_id=student_id,
            page=page,
            page_size=page_size
        )
        return exams
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exams"
        )


@router.post(
    "/me/rate-teacher",
    response_model=TeacherRatingResponse,
    summary="Rate a Teacher",
    description="Submit a rating for a teacher in a specific classroom"
)
async def rate_teacher(
    rating_data: TeacherRatingCreate,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
    _: bool = Depends(RoleChecker([UserTypeEnum.STUDENT.value, UserTypeEnum.ADMIN.value]))
):
    """Rate a teacher in a specific classroom"""
    try:
        print(f"DEBUG ROUTE: Current user: {current_user}")
        controller = TeacherRatingController(db_session)
        student_id = UUID(current_user["id"])
        print(f"DEBUG ROUTE: Student ID: {student_id}")
        
        rating = await controller.submit_rating(
            student_id=student_id,
            rating_data=rating_data
        )
        return rating
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"DEBUG ROUTE: Exception: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit teacher rating"
        )




