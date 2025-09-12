"""
Teacher Rating Schemas

Pydantic models for teacher rating API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class TeacherRatingCreate(BaseModel):
    """Schema for creating a teacher rating"""
    teacher_id: UUID = Field(..., description="ID of the teacher being rated")
    classroom_id: UUID = Field(..., description="ID of the classroom context")
    rating_points: int = Field(..., ge=1, le=5, description="Rating points (1-5)")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Optional feedback text")
    term_id: Optional[UUID] = Field(None, description="Academic term ID")

    @field_validator('rating_points')
    @classmethod
    def validate_rating_points(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating points must be between 1 and 5')
        return v


class TeacherRatingUpdate(BaseModel):
    """Schema for updating a teacher rating"""
    rating_points: Optional[int] = Field(None, ge=1, le=5, description="Rating points (1-5)")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Optional feedback text")

    @field_validator('rating_points')
    @classmethod
    def validate_rating_points(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating points must be between 1 and 5')
        return v


class TeacherRatingResponse(BaseModel):
    """Schema for teacher rating response"""
    model_config = ConfigDict(from_attributes=True)
    
    rating_id: UUID
    teacher_id: UUID
    student_id: UUID
    classroom_id: UUID
    rating_points: int
    feedback_text: Optional[str]
    term_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class TeacherRatingStatsResponse(BaseModel):
    """Schema for teacher rating statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_ratings: int
    average_rating: float
    min_rating: int
    max_rating: int
    rating_distribution: dict = Field(
        description="Distribution of ratings by star count"
    )


class TeacherRatingListResponse(BaseModel):
    """Schema for paginated teacher rating list"""
    model_config = ConfigDict(from_attributes=True)
    
    ratings: list[TeacherRatingResponse]
    total_count: int
    page: int
    limit: int
