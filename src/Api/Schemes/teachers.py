"""
Teacher API Schemas

Pydantic models for teacher-related API requests and responses.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict


class TeacherProfileResponse(BaseModel):
    """Response model for teacher profile information"""
    model_config = ConfigDict(from_attributes=True)
    
    teacher_id: UUID
    unique_id: str
    name: str
    email: EmailStr
    is_verified: bool
    rating: Optional[float]
    subject_id: Optional[UUID]
    term_id: Optional[UUID]
    admin_id: Optional[UUID]
    total_classrooms: int


class TeacherProfileUpdateRequest(BaseModel):
    """Request model for updating teacher profile"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip() if v else v


class TeacherClassroomResponse(BaseModel):
    """Response model for classroom information from teacher perspective"""
    model_config = ConfigDict(from_attributes=True)
    
    classroom_id: UUID
    subject_name: str
    term_id: UUID
    grade_level: str
    classroom_name: Optional[str]
    student_count: int


class TeacherClassroomListResponse(BaseModel):
    """Response model for paginated list of teacher classrooms"""
    model_config = ConfigDict(from_attributes=True)
    
    classrooms: List[TeacherClassroomResponse]
    total_count: int
    page: int
    limit: int
