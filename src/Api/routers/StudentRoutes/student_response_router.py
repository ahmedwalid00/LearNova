"""
Student Response API Routes

This module contains FastAPI routes for student responses to practice questions
and exams, including performance tracking and rating system.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.Helpers.db_session import get_db_session
from src.Api.dependencies import get_current_user, RoleChecker
from src.Controllers.student_response_controller import StudentResponseController
from src.Api.Schemes.student_response_schemes import (
    AnswerPracticeQuestionRequest,
    AnswerExamQuestionRequest,
    AnswerSubmissionResponse,
    PracticeResponsesResponse,
    ExamResponsesResponse,
    PerformanceSummaryResponse
)
from src.Enums.user_type_enums import UserTypeEnum

# Create router instance
router = APIRouter(
    prefix="/api/v1/student/responses",
    tags=["Student Responses"],
    dependencies=[Depends(RoleChecker([UserTypeEnum.STUDENT.value, UserTypeEnum.ADMIN.value]))]
)


@router.post(
    "/practice/answer",
    response_model=AnswerSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Answer Practice Question",
    description="Submit an answer to a practice question. Students can only answer questions from classrooms they are enrolled in."
)
async def answer_practice_question(
    request: AnswerPracticeQuestionRequest,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Submit an answer to a practice question"""
    controller = StudentResponseController(session)
    
    # If user is admin, allow them to specify student_id via query param
    # Otherwise, use current user's ID
    student_id = current_user.get('id')
    
    return await controller.answer_practice_question(
        student_id=student_id,
        practice_id=request.practice_id,
        answer_id=request.answer_id,
        time_taken_seconds=request.time_taken_seconds
    )


@router.post(
    "/exam/answer",
    response_model=AnswerSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Answer Exam Question",
    description="Submit an answer to an exam question. Students can only answer questions from exams in classrooms they are enrolled in."
)
async def answer_exam_question(
    request: AnswerExamQuestionRequest,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Submit an answer to an exam question"""
    controller = StudentResponseController(session)
    
    # If user is admin, allow them to specify student_id via query param
    # Otherwise, use current user's ID
    student_id = current_user.get('id')
    
    return await controller.answer_exam_question(
        student_id=student_id,
        exam_id=request.exam_id,
        question_id=request.question_id,
        answer_id=request.answer_id,
        time_taken_seconds=request.time_taken_seconds
    )


@router.get(
    "/practice",
    response_model=PracticeResponsesResponse,
    summary="Get Practice Responses",
    description="Get student's practice question responses with optional filtering by classroom."
)
async def get_practice_responses(
    classroom_id: Optional[UUID] = Query(None, description="Filter by classroom ID"),
    limit: int = Query(50, description="Maximum number of responses to return", ge=1, le=100),
    offset: int = Query(0, description="Number of responses to skip", ge=0),
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get student's practice question responses"""
    controller = StudentResponseController(session)
    
    # If user is admin, allow them to specify student_id via query param
    # Otherwise, use current user's ID
    student_id = current_user.get('id')
    
    return await controller.get_practice_responses(
        student_id=student_id,
        classroom_id=classroom_id,
        limit=limit,
        offset=offset
    )


@router.get(
    "/exam",
    response_model=ExamResponsesResponse,
    summary="Get Exam Responses",
    description="Get student's exam responses with optional filtering by exam or classroom."
)
async def get_exam_responses(
    exam_id: Optional[UUID] = Query(None, description="Filter by exam ID"),
    classroom_id: Optional[UUID] = Query(None, description="Filter by classroom ID"),
    limit: int = Query(50, description="Maximum number of responses to return", ge=1, le=100),
    offset: int = Query(0, description="Number of responses to skip", ge=0),
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get student's exam responses"""
    controller = StudentResponseController(session)
    
    # If user is admin, allow them to specify student_id via query param
    # Otherwise, use current user's ID
    student_id = current_user.get('id')
    
    return await controller.get_exam_responses(
        student_id=student_id,
        exam_id=exam_id,
        classroom_id=classroom_id,
        limit=limit,
        offset=offset
    )


@router.get(
    "/performance",
    response_model=PerformanceSummaryResponse,
    summary="Get Performance Summary",
    description="Get comprehensive performance summary including practice and exam statistics with current rating."
)
async def get_performance_summary(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive performance summary for the student"""
    controller = StudentResponseController(session)
    
    # If user is admin, allow them to specify student_id via query param
    # Otherwise, use current user's ID
    student_id = current_user.get('id')
    
    return await controller.get_performance_summary(student_id)


# Admin-only endpoints for managing student responses
@router.get(
    "/admin/student/{student_id}/practice",
    response_model=PracticeResponsesResponse,
    summary="[Admin] Get Student Practice Responses",
    description="Admin endpoint to get any student's practice question responses.",
    dependencies=[Depends(RoleChecker([UserTypeEnum.ADMIN.value]))]
)
async def admin_get_student_practice_responses(
    student_id: UUID,
    classroom_id: Optional[UUID] = Query(None, description="Filter by classroom ID"),
    limit: int = Query(50, description="Maximum number of responses to return", ge=1, le=100),
    offset: int = Query(0, description="Number of responses to skip", ge=0),
    session: AsyncSession = Depends(get_db_session)
):
    """Admin endpoint to get any student's practice responses"""
    controller = StudentResponseController(session)
    
    return await controller.get_practice_responses(
        student_id=student_id,
        classroom_id=classroom_id,
        limit=limit,
        offset=offset
    )


@router.get(
    "/admin/student/{student_id}/exam",
    response_model=ExamResponsesResponse,
    summary="[Admin] Get Student Exam Responses",
    description="Admin endpoint to get any student's exam responses.",
    dependencies=[Depends(RoleChecker([UserTypeEnum.ADMIN.value]))]
)
async def admin_get_student_exam_responses(
    student_id: UUID,
    exam_id: Optional[UUID] = Query(None, description="Filter by exam ID"),
    classroom_id: Optional[UUID] = Query(None, description="Filter by classroom ID"),
    limit: int = Query(50, description="Maximum number of responses to return", ge=1, le=100),
    offset: int = Query(0, description="Number of responses to skip", ge=0),
    session: AsyncSession = Depends(get_db_session)
):
    """Admin endpoint to get any student's exam responses"""
    controller = StudentResponseController(session)
    
    return await controller.get_exam_responses(
        student_id=student_id,
        exam_id=exam_id,
        classroom_id=classroom_id,
        limit=limit,
        offset=offset
    )


@router.get(
    "/admin/student/{student_id}/performance",
    response_model=PerformanceSummaryResponse,
    summary="[Admin] Get Student Performance Summary",
    description="Admin endpoint to get any student's performance summary.",
    dependencies=[Depends(RoleChecker([UserTypeEnum.ADMIN.value]))]
)
async def admin_get_student_performance_summary(
    student_id: UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """Admin endpoint to get any student's performance summary"""
    controller = StudentResponseController(session)
    
    return await controller.get_performance_summary(student_id)
