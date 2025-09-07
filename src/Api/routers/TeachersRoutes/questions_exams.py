"""
Teacher routes for Question and Exam management.

This module defines all the API endpoints for teachers to manage
practice questions and exams, following the project's established patterns.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from src.Api.dependencies import get_current_user, get_db_session
from src.Controllers.question_exam_controller import QuestionExamController
from src.Api.Schemes.question_exam_schemes import (
    QuestionPracticeCreate, QuestionPracticeResponse,
    ExamCreate, ExamResponse,
    PracticeQuestionListResponse, ExamListResponse,
    QuestionDetailResponse, ExamDetailResponse
)
from src.Api.dependencies import RoleChecker
from src.Enums.user_type_enums import UserTypeEnum

logger = logging.getLogger('uvicorn.error')

router = APIRouter(
    prefix="/api/v1/teachers/questions-exams",
    tags=["Teacher Questions & Exams"],
    dependencies=[Depends(get_current_user)]
)

teacher_admin_access = RoleChecker([UserTypeEnum.TEACHER.value, UserTypeEnum.ADMIN.value])


@router.post(
    "/practice-questions",
    response_model=QuestionPracticeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Practice Question",
    description="Create a new MCQ practice question for students" , 
    dependencies=[Depends(teacher_admin_access)] 
)
async def create_practice_question(
    question_data: QuestionPracticeCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user) 
):
    """
    Create a new practice question with multiple choice answers.
    
    - **content**: The question text
    - **difficulty**: Question difficulty level (easy, medium, hard)
    - **answers**: List of answer options with correct answer marked
    
    **Requirements:**
    - Must have 2-6 answer options
    - Exactly one answer must be marked as correct
    - User must be a teacher
    """
    logger.info(f"User creating practice question")
    
    # Get teacher ID from current user (dictionary)
    teacher_id = current_user.get('id')
    
    # For now, we'll need to get term_id from the teacher record
    # This is a temporary solution until we add term_id to the current_user response
    if not teacher_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid teacher data"
        )
    
    # We need to get the teacher's term_id from the database
    # For now, let's use None and handle this in the controller
    term_id = None
    
    try:
        controller = QuestionExamController(session)
        result = await controller.create_practice_question(
            request_data=question_data,
            teacher_id=teacher_id,
            term_id=term_id
        )
        
        logger.info(f"Practice question created successfully for teacher {teacher_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating practice question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create practice question"
        )


@router.post(
    "/exams",
    response_model=ExamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Exam",
    description="Create a new exam with multiple MCQ questions",
    dependencies=[Depends(teacher_admin_access)]
)
async def create_exam(
    exam_data: ExamCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Create a new exam with multiple choice questions.
    
    - **title**: Exam title/name
    - **date**: Scheduled exam date
    - **questions**: List of questions with their answer options
    
    **Requirements:**
    - Each question must have 2-6 answer options
    - Each question must have exactly one correct answer
    - User must be a teacher
    """
    logger.info(f"User creating exam: {exam_data.title}")
    
    # Get teacher ID from current user (dictionary)
    teacher_id = current_user.get('id')
    
    # Ensure we have valid teacher ID
    if not teacher_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid teacher data"
        )
    
    # We'll let the controller fetch the term_id from the teacher record
    term_id = None
    
    try:
        controller = QuestionExamController(session)
        result = await controller.create_exam(
            request_data=exam_data,
            teacher_id=teacher_id,
            term_id=term_id
        )
        
        logger.info(f"Exam '{exam_data.title}' created successfully for teacher {teacher_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating exam: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exam"
        )


@router.get(
    "/practice-questions",
    response_model=PracticeQuestionListResponse,
    summary="List Practice Questions",
    description="Get paginated list of teacher's practice questions",
    dependencies=[Depends(teacher_admin_access)]
)
async def get_practice_questions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Retrieve a paginated list of practice questions created by the teacher.
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **per_page**: Number of items per page (default: 20, max: 100)
    """
    logger.info(f"User requesting practice questions list")
    
    # Get teacher ID from current user (dictionary)
    teacher_id = current_user.get('id')
    
    try:
        controller = QuestionExamController(session)
        result = await controller.get_practice_questions(
            teacher_id=teacher_id,
            page=page,
            per_page=per_page
        )
        
        logger.info(f"Retrieved {len(result.questions)} practice questions for teacher {teacher_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving practice questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve practice questions"
        )


@router.get(
    "/exams",
    response_model=ExamListResponse,
    summary="List Exams",
    description="Get paginated list of teacher's exams",
    dependencies=[Depends(teacher_admin_access)]
)
async def get_exams(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Retrieve a paginated list of exams created by the teacher.
    
    **Query Parameters:**
    - **page**: Page number (default: 1)
    - **per_page**: Number of items per page (default: 20, max: 100)
    """
    logger.info(f"User requesting exams list")
    
    # Get teacher ID from current user (dictionary)
    teacher_id = current_user.get('id')
    
    try:
        controller = QuestionExamController(session)
        result = await controller.get_exams(
            teacher_id=teacher_id,
            page=page,
            per_page=per_page
        )
        
        logger.info(f"Retrieved {len(result.exams)} exams for teacher {teacher_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error retrieving exams: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exams"
        )


@router.get(
    "/practice-questions/{practice_id}",
    response_model=QuestionDetailResponse,
    summary="Get Practice Question Details",
    description="Get detailed view of a specific practice question",
    dependencies=[Depends(teacher_admin_access)]
)
async def get_practice_question_details(
    practice_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Retrieve detailed information about a specific practice question.
    
    **Path Parameters:**
    - **practice_id**: UUID of the practice question
    
    **Returns:**
    - Question content and metadata
    - All answer options with correct answer indicators
    """
    logger.info(f"User requesting details for practice question {practice_id}")
    
    # Get teacher ID from current user (dictionary)
    teacher_id = current_user.get('id')
    
    try:
        controller = QuestionExamController(session)
        result = await controller.get_practice_question_details(
            practice_id=practice_id,
            teacher_id=teacher_id
        )
        
        logger.info(f"Retrieved details for practice question {practice_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving practice question details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve practice question details"
        )


@router.get(
    "/exams/{exam_id}",
    response_model=ExamDetailResponse,
    summary="Get Exam Details",
    description="Get detailed view of a specific exam",
    dependencies=[Depends(teacher_admin_access)]
)
async def get_exam_details(
    exam_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user = Depends(get_current_user)
):
    """
    Retrieve detailed information about a specific exam.
    
    **Path Parameters:**
    - **exam_id**: UUID of the exam
    
    **Returns:**
    - Exam metadata and schedule information
    - All questions with their answer options
    - Basic statistics about the exam
    """
    logger.info(f"User requesting details for exam {exam_id}")
    
    # Get teacher ID from current user (dictionary)
    teacher_id = current_user.get('id')
    
    try:
        controller = QuestionExamController(session)
        result = await controller.get_exam_details(
            exam_id=exam_id,
            teacher_id=teacher_id
        )
        
        logger.info(f"Retrieved details for exam {exam_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving exam details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exam details"
        )
