"""
Lesson management routes for teachers in the LearNova API.

This module provides endpoints for lesson upload, search, deletion, and retrieval
with proper role-based access control and validation.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.Api.dependencies import get_db_session, get_current_user, RoleChecker
from src.Api.Schemes.lesson_schemes import (
    LessonUploadRequest, LessonUploadResponse,
    SearchContentRequest, SearchContentResponse,
    LessonDetailsResponse, DeleteLessonResponse
)
from src.Controllers.lesson_controller import LessonController
from src.Enums.user_type_enums import UserTypeEnum

# Create router with appropriate prefix and tags
router = APIRouter(prefix="/api/v1/teacher/lessons", tags=["Teacher Lessons"])

# Role checker for teacher and admin access
teacher_admin_access = RoleChecker([UserTypeEnum.TEACHER.value, UserTypeEnum.ADMIN.value])


@router.post(
    "/upload",
    response_model=LessonUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a lesson PDF",
    description="Upload and process a PDF lesson file with automatic text extraction, chunking, and embedding generation"
)
async def upload_lesson(
    request: Request,
    file: UploadFile = File(
        ..., 
        description="PDF file containing lesson content (max 25MB)"
    ),
    request_data: LessonUploadRequest = Depends(),
    current_user = Depends(get_current_user),
    _: bool = Depends(teacher_admin_access),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Upload a lesson PDF file for processing and storage.
    
    **Process Overview:**
    1. Validates teacher permissions and file format
    2. Extracts text content from the PDF
    3. Chunks the text using the specified strategy
    4. Generates embeddings for all chunks (if service available)
    5. Stores the lesson and chunks in the database
    
    **File Requirements:**
    - Format: PDF only
    - Size: Maximum 25MB
    - Content: Must contain readable text
    
    **Chunking Strategies:**
    - `recursive`: Character-based splitting with smart separators (default)
    - `token`: Token-based splitting for embedding models
    
    **Returns:**
    Lesson information, processing statistics, and upload details.
    """
    try:
        # Get teacher ID and term_id from current user (current_user is a dict)
        teacher_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        teacher_term_id = current_user.get('term_id') if isinstance(current_user, dict) else getattr(current_user, 'term_id', None)
        
        # Verify this is a teacher user
        if not teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can upload lessons"
            )
        
        # Initialize controller with clients from request
        llm_client = getattr(request.app, 'embedding_client', None)
        vectordb_client = getattr(request.app, 'vectordb_client', None)
        controller = LessonController(session, llm_client, vectordb_client)
        
        # Process upload
        result = await controller.upload_lesson(file, request_data, teacher_id, teacher_term_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post(
    "/search",
    response_model=SearchContentResponse,
    summary="Search lesson content",
    description="Search through lesson content using semantic similarity matching"
)
async def search_lesson_content(
    request: Request,
    request_data: SearchContentRequest,
    current_user = Depends(get_current_user),
    _: bool = Depends(teacher_admin_access),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Search for lesson content using semantic similarity.
    
    This endpoint allows teachers to search through their lesson content using
    vector similarity search. The search is performed against all text chunks
    from lessons uploaded by the teacher.
    
    **Features:**
    - Semantic similarity matching using vector embeddings
    - Filter by specific subjects
    - Configurable similarity threshold
    - Ranked results by relevance score
    
    **Returns:**
    List of matching lesson chunks with similarity scores, content, and metadata.
    """
    try:
        # Get teacher ID from current user (current_user is a dict)
        teacher_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        if not teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can search their lessons"
            )
        
        # Initialize controller with clients from request
        llm_client = getattr(request.app, 'embedding_client', None)
        vectordb_client = getattr(request.app, 'vectordb_client', None)
        controller = LessonController(session, llm_client, vectordb_client)
        
        # Perform search
        result = await controller.search_lesson_content(request_data, teacher_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonDetailsResponse,
    summary="Get lesson details",
    description="Retrieve detailed information about a specific lesson"
)
async def get_lesson_details(
    request: Request,
    lesson_id: str,
    current_user = Depends(get_current_user),
    _: bool = Depends(teacher_admin_access),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get detailed information about a specific lesson.
    
    Returns comprehensive information about a lesson including:
    - Basic lesson information (title, subject, dates, etc.)
    - Processing and content statistics
    - Chunk information and metadata
    - Performance metrics
    
    **Access Control:**
    Teachers can only access lessons they have uploaded.
    Admins can access any lesson.
    
    **Returns:**
    Complete lesson details with processing statistics and chunk information.
    """
    try:
        # Validate lesson ID format
        try:
            lesson_uuid = UUID(lesson_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid lesson ID format. Must be a valid UUID."
            )
        
        # Get teacher ID from current user (current_user is a dict)
        teacher_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        if not teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can view lesson details"
            )
        
        # Initialize controller with clients from request
        llm_client = getattr(request.app, 'embedding_client', None)
        vectordb_client = getattr(request.app, 'vectordb_client', None)
        controller = LessonController(session, llm_client, vectordb_client)
        
        # Get lesson details
        result = await controller.get_lesson_details(lesson_uuid, teacher_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lesson details: {str(e)}"
        )


@router.delete(
    "/lessons/{lesson_id}",
    response_model=DeleteLessonResponse,
    summary="Delete a lesson",
    description="Delete a lesson and all its associated chunks and embeddings"
)
async def delete_lesson(
    request: Request,
    lesson_id: str,
    current_user = Depends(get_current_user),
    _: bool = Depends(teacher_admin_access),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Delete a lesson and all its associated data.
    
    This endpoint allows teachers to delete lessons they have uploaded.
    All associated data will be removed including:
    - Lesson record
    - Text chunks
    - Vector embeddings
    - Processing metadata
    
    **Warning:** This action is irreversible.
    
    **Access Control:**
    Teachers can only delete lessons they have uploaded.
    Admins can delete any lesson.
    
    **Returns:**
    Confirmation of deletion with statistics about removed data.
    """
    try:
        # Validate lesson ID format
        try:
            lesson_uuid = UUID(lesson_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid lesson ID format. Must be a valid UUID."
            )
        
        # Get teacher ID from current user (current_user is a dict)
        teacher_id = current_user.get('id') if isinstance(current_user, dict) else getattr(current_user, 'id', None)
        if not teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can delete lessons"
            )
        
        # Initialize controller with clients from request
        llm_client = getattr(request.app, 'embedding_client', None)
        vectordb_client = getattr(request.app, 'vectordb_client', None)
        controller = LessonController(session, llm_client, vectordb_client)
        
        # Delete lesson
        result = await controller.delete_lesson(lesson_uuid, teacher_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lesson: {str(e)}"
        )
