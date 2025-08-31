"""
Lesson Controller for handling lesson-related business logic.

This module contains the LessonController class that orchestrates
lesson operations and can be reused across different endpoints.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, UploadFile
import logging
import time
from datetime import datetime

from src.Models.services.lesson_service import LessonService
from src.Api.Schemes.lesson_schemes import (
    LessonUploadRequest, LessonUploadResponse,
    SearchContentRequest, SearchContentResponse, SearchResult,
    LessonDetailsResponse, DeleteLessonResponse,
    LessonInfo, LessonChunkInfo, LessonStatistics
)
from src.Enums.signal_response import SignalResponse

logger = logging.getLogger('uvicorn.error')


class LessonController:
    """
    Controller class for lesson operations.
    
    Handles lesson upload, search, deletion, and detail retrieval
    in a reusable and extensible manner.
    """
    
    def __init__(self, session: AsyncSession, llm_client=None, vectordb_client=None):
        """
        Initialize the controller with database session and optional clients.
        
        Args:
            session: Database session
            llm_client: LLM client for embeddings
            vectordb_client: Vector database client
        """
        self.session = session
        self.lesson_service = LessonService(session, llm_client, vectordb_client)
    
    def _validate_file_upload(self, file: UploadFile) -> None:
        """
        Validate uploaded file constraints.
        
        Args:
            file: Uploaded file to validate
            
        Raises:
            HTTPException: If file validation fails
        """
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SignalResponse.NO_FILE_UPLOADED.value
            )
        
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SignalResponse.NO_FILE_NAME_PROVIDED.value
            )
        
        # Check file extension
        allowed_extensions = ['.pdf', '.txt']
        file_extension = None
        for ext in allowed_extensions:
            if file.filename.lower().endswith(ext):
                file_extension = ext
                break
        
        if not file_extension:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {', '.join(allowed_extensions).upper()} files are allowed"
            )
        
        # Additional file size validation can be added here
        # The actual size validation is handled in the service layer
    
    def _format_upload_response(self, service_result: Dict[str, Any]) -> LessonUploadResponse:
        """
        Format lesson upload service result into response schema.
        
        Args:
            service_result: Result from lesson service upload
            
        Returns:
            Formatted upload response
        """
        return LessonUploadResponse(
            success=service_result.get('success', False),
            lesson=service_result.get('lesson', {}),
            processing_stats=service_result.get('processing_stats', {}),
            upload_info=service_result.get('upload_info', {})
        )
    
    def _format_search_response(
        self, 
        results: List[Dict[str, Any]], 
        query: str, 
        processing_time: float
    ) -> SearchContentResponse:
        """
        Format search results into response schema.
        
        Args:
            results: Search results from service
            query: Original search query
            processing_time: Time taken for processing
            
        Returns:
            Formatted search response
        """
        search_results = [
            SearchResult(
                record_id=result.get('record_id', ''),
                content=result.get('content', ''),
                similarity_score=result.get('similarity_score', 0.0),
                metadata=result.get('metadata', {})
            )
            for result in results
        ]
        
        return SearchContentResponse(
            results=search_results,
            total_results=len(search_results),
            query=query,
            processing_time_ms=round(processing_time * 1000, 2)
        )
    
    def _format_lesson_details(self, service_result: Dict[str, Any]) -> LessonDetailsResponse:
        """
        Format lesson details service result into response schema.
        
        Args:
            service_result: Result from lesson service
            
        Returns:
            Formatted lesson details response
        """
        lesson_data = service_result.get('lesson', {})
        chunks_data = service_result.get('chunks', {})
        stats_data = service_result.get('statistics', {})
        
        # Format lesson info
        lesson_info = LessonInfo(
            id=UUID(lesson_data.get('id')),
            title=lesson_data.get('title', ''),
            pdf_url=lesson_data.get('pdf_url', ''),
            subject_id=UUID(lesson_data.get('subject_id')),
            subject_name=lesson_data.get('subject_name'),
            teacher_id=UUID(lesson_data.get('teacher_id')),
            term_id=UUID(lesson_data.get('term_id')),
            rating=lesson_data.get('rating'),
            created_at=datetime.fromisoformat(lesson_data['created_at']) if lesson_data.get('created_at') else None,
            updated_at=datetime.fromisoformat(lesson_data['updated_at']) if lesson_data.get('updated_at') else None
        )
        
        # Format statistics
        statistics = LessonStatistics(
            total_characters=stats_data.get('total_characters', 0),
            total_words=stats_data.get('total_words', 0),
            total_chunks=stats_data.get('total_chunks', 0)
        )
        
        return LessonDetailsResponse(
            lesson=lesson_info,
            chunks=chunks_data,
            statistics=statistics
        )
    
    def _format_delete_response(self, service_result: Dict[str, Any]) -> DeleteLessonResponse:
        """
        Format lesson deletion service result into response schema.
        
        Args:
            service_result: Result from lesson service
            
        Returns:
            Formatted deletion response
        """
        return DeleteLessonResponse(
            success=service_result.get('success', False),
            message=service_result.get('message', ''),
            deleted_lesson=service_result.get('deleted_lesson', {})
        )
    
    async def upload_lesson(
        self, 
        file: UploadFile, 
        request_data: LessonUploadRequest, 
        teacher_id: UUID,
        teacher_term_id: UUID
    ) -> LessonUploadResponse:
        """
        Handle lesson upload process.
        
        Args:
            file: Uploaded PDF file
            request_data: Validated upload request data
            teacher_id: ID of the teacher uploading the lesson
            teacher_term_id: Teacher's current academic term ID
            
        Returns:
            Upload response with lesson info and processing stats
            
        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate file
            self._validate_file_upload(file)
            
            # Use teacher's term_id if not specified in request
            term_id = request_data.term_id or teacher_term_id
            
            if not term_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Term ID is required. Teacher must be assigned to an academic term."
                )
            
            # Call lesson service
            result = await self.lesson_service.upload_lesson(
                file=file,
                title=request_data.title,
                subject_id=request_data.subject_id,
                teacher_id=teacher_id,
                term_id=term_id,
                pdf_url=request_data.pdf_url,
                chunking_strategy=request_data.chunking_strategy.value,
                chunk_size=request_data.chunk_size,
                chunk_overlap=request_data.chunk_overlap
            )
            
            # Format and return response
            return self._format_upload_response(result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Lesson upload error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lesson upload failed: {str(e)}"
            )
    
    async def search_lesson_content(
        self, 
        request_data: SearchContentRequest, 
        teacher_id: UUID
    ) -> SearchContentResponse:
        """
        Handle lesson content search.
        
        Args:
            request_data: Validated search request data
            teacher_id: ID of the teacher performing the search
            
        Returns:
            Search response with matching results
            
        Raises:
            HTTPException: If search fails
        """
        try:
            start_time = time.time()
            
            # Call lesson service
            results = await self.lesson_service.search_lesson_content(
                teacher_id=teacher_id,
                query_text=request_data.query,
                subject_ids=request_data.subject_ids,
                limit=request_data.limit
            )
            
            # Filter by similarity threshold if specified
            if request_data.similarity_threshold > 0.0:
                results = [
                    result for result in results 
                    if result.get('similarity_score', 0.0) >= request_data.similarity_threshold
                ]
            
            processing_time = time.time() - start_time
            
            # Format and return response
            return self._format_search_response(results, request_data.query, processing_time)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Content search error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Content search failed: {str(e)}"
            )
    
    async def get_lesson_details(self, lesson_id: UUID, teacher_id: UUID) -> LessonDetailsResponse:
        """
        Handle lesson details retrieval.
        
        Args:
            lesson_id: ID of the lesson to retrieve
            teacher_id: ID of the teacher requesting the details
            
        Returns:
            Detailed lesson information
            
        Raises:
            HTTPException: If retrieval fails
        """
        try:
            # Call lesson service
            result = await self.lesson_service.get_lesson_details(
                lesson_id=lesson_id,
                teacher_id=teacher_id
            )
            
            # Format and return response
            return self._format_lesson_details(result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get lesson details error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get lesson details: {str(e)}"
            )
    
    async def delete_lesson(self, lesson_id: UUID, teacher_id: UUID) -> DeleteLessonResponse:
        """
        Handle lesson deletion.
        
        Args:
            lesson_id: ID of the lesson to delete
            teacher_id: ID of the teacher deleting the lesson
            
        Returns:
            Deletion confirmation response
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Call lesson service
            result = await self.lesson_service.delete_lesson(
                lesson_id=lesson_id,
                teacher_id=teacher_id
            )
            
            # Format and return response
            return self._format_delete_response(result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete lesson error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete lesson: {str(e)}"
            )
