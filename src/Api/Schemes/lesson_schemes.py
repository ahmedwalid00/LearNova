"""
Lesson-related Pydantic schemas for request and response validation.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ChunkingStrategy(str, Enum):
    """Supported text chunking strategies."""
    RECURSIVE = "recursive"
    TOKEN = "token"


class LessonUploadRequest(BaseModel):
    """Request schema for lesson upload."""
    title: str = Field(
        ..., 
        min_length=3, 
        max_length=255, 
        example="Introduction to Python Programming",
        description="Lesson title (3-255 characters)"
    )
    subject_id: UUID = Field(
        ..., 
        example="550e8400-e29b-41d4-a716-446655440000",
        description="UUID of the subject this lesson belongs to"
    )
    term_id: UUID = Field(
        ..., 
        example="550e8400-e29b-41d4-a716-446655440001",
        description="UUID of the academic term (defaults to teacher's current term)"
    )
    pdf_url: Optional[str] = Field(
        "",
        max_length=512,
        example="https://storage.example.com/lessons/python_intro.pdf",
        description="URL/path where the PDF file is stored"
    )
    chunking_strategy: ChunkingStrategy = Field(
        ChunkingStrategy.RECURSIVE,
        description="Text chunking strategy: 'recursive' or 'token'"
    )
    chunk_size: Optional[int] = Field(
        None,
        ge=100,
        le=2000,
        example=1000,
        description="Target chunk size in characters (100-2000)"
    )
    chunk_overlap: Optional[int] = Field(
        None,
        ge=0,
        le=500,
        example=200,
        description="Overlap between chunks in characters (0-500)"
    )


class LessonUploadResponse(BaseModel):
    """Response schema for lesson upload."""
    success: bool = Field(..., description="Whether the upload was successful")
    lesson: Dict[str, Any] = Field(..., description="Created lesson information")
    processing_stats: Dict[str, Any] = Field(..., description="Processing statistics")
    upload_info: Dict[str, Any] = Field(..., description="Upload metadata")


class SearchContentRequest(BaseModel):
    """Request schema for lesson content search."""
    query: str = Field(
        ..., 
        min_length=3, 
        max_length=500,
        example="machine learning algorithms",
        description="Search query text (3-500 characters)"
    )
    subject_ids: Optional[List[UUID]] = Field(
        None,
        max_items=10,
        example=["550e8400-e29b-41d4-a716-446655440000"],
        description="Optional list of subject UUIDs to filter by (max 10)"
    )
    limit: int = Field(
        10,
        ge=1,
        le=50,
        example=10,
        description="Maximum number of results to return (1-50)"
    )
    similarity_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        example=0.7,
        description="Minimum similarity score (0.0-1.0)"
    )


class SearchResult(BaseModel):
    """Individual search result."""
    record_id: str = Field(..., description="Unique identifier for the chunk")
    content: str = Field(..., description="Text content of the matching chunk")
    similarity_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Similarity score (0.0-1.0)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Additional metadata about the chunk"
    )


class SearchContentResponse(BaseModel):
    """Response schema for lesson content search."""
    results: List[SearchResult] = Field(..., description="List of search results")
    total_results: int = Field(..., description="Total number of results found")
    query: str = Field(..., description="Original search query")
    processing_time_ms: Optional[float] = Field(
        None, 
        description="Time taken to process the search in milliseconds"
    )


class LessonChunkInfo(BaseModel):
    """Information about a lesson chunk."""
    chunk_id: UUID = Field(..., description="Unique identifier for the chunk")
    chunk_number: int = Field(..., description="Sequence number of the chunk")
    content_length: int = Field(..., description="Length of the chunk content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Chunk metadata"
    )


class LessonInfo(BaseModel):
    """Basic lesson information."""
    id: UUID = Field(..., description="Lesson UUID")
    title: str = Field(..., description="Lesson title")
    pdf_url: str = Field(..., description="URL/path to the PDF file")
    subject_id: UUID = Field(..., description="Subject UUID")
    subject_name: Optional[str] = Field(None, description="Subject name")
    teacher_id: UUID = Field(..., description="Teacher UUID")
    term_id: UUID = Field(..., description="Academic term UUID")
    rating: Optional[float] = Field(None, description="Lesson rating")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class LessonStatistics(BaseModel):
    """Lesson processing and content statistics."""
    total_characters: int = Field(..., description="Total character count")
    total_words: int = Field(..., description="Total word count")
    total_chunks: int = Field(..., description="Total number of chunks")


class LessonDetailsResponse(BaseModel):
    """Response schema for lesson details."""
    lesson: LessonInfo = Field(..., description="Lesson information")
    chunks: Dict[str, Any] = Field(..., description="Chunk information")
    statistics: LessonStatistics = Field(..., description="Lesson statistics")


class DeleteLessonResponse(BaseModel):
    """Response schema for lesson deletion."""
    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Deletion confirmation message")
    deleted_lesson: Dict[str, Any] = Field(
        ..., 
        description="Information about the deleted lesson"
    )


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: Optional[datetime] = Field(None, description="Error timestamp")


# Validation helpers
class LessonValidationMixin:
    """Mixin providing common validation methods for lesson schemas."""
    
    @validator('title')
    def validate_title(cls, v):
        """Validate lesson title."""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query."""
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()


# Apply validation mixins
LessonUploadRequest.__bases__ = (BaseModel, LessonValidationMixin)
SearchContentRequest.__bases__ = (BaseModel, LessonValidationMixin)
