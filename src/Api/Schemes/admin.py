"""
Admin-related Pydantic schemas for request/response validation.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from uuid import UUID


# Academic Term Schemas
class AcademicTermCreateModel(BaseModel):
    """Schema for creating a new academic term"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the academic term")
    start_date: date = Field(..., description="Start date of the term")
    end_date: date = Field(..., description="End date of the term")
    is_active: bool = Field(default=False, description="Whether this term is currently active")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Fall 2025",
                "start_date": "2025-09-01",
                "end_date": "2025-12-15",
                "is_active": True
            }
        }


class AcademicTermUpdateModel(BaseModel):
    """Schema for updating an academic term"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class AcademicTermResponseModel(BaseModel):
    """Schema for academic term response"""
    term_id: UUID
    name: str
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Term Week Schemas
class TermWeekCreateModel(BaseModel):
    """Schema for creating a new term week"""
    term_id: UUID = Field(..., description="ID of the academic term")
    week_number: int = Field(..., ge=1, le=52, description="Week number within the term")
    start_date: date = Field(..., description="Start date of the week")
    end_date: date = Field(..., description="End date of the week")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    class Config:
        schema_extra = {
            "example": {
                "term_id": "123e4567-e89b-12d3-a456-426614174000",
                "week_number": 1,
                "start_date": "2025-09-01",
                "end_date": "2025-09-07"
            }
        }


class TermWeekUpdateModel(BaseModel):
    """Schema for updating a term week"""
    week_number: Optional[int] = Field(None, ge=1, le=52)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class TermWeekResponseModel(BaseModel):
    """Schema for term week response"""
    week_id: UUID
    term_id: UUID
    week_number: int
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Subject Schemas
class SubjectCreateModel(BaseModel):
    """Schema for creating a new subject"""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the subject")
    description: Optional[str] = Field(None, description="Description of the subject")

    class Config:
        schema_extra = {
            "example": {
                "name": "Mathematics",
                "description": "Basic mathematics covering algebra, geometry, and calculus"
            }
        }


class SubjectUpdateModel(BaseModel):
    """Schema for updating a subject"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class SubjectResponseModel(BaseModel):
    """Schema for subject response"""
    subject_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ID Generation Schemas
class IDGenerationRequestModel(BaseModel):
    """Schema for ID generation request"""
    user_type: str = Field(..., description="Type of user (student/teacher)")
    count: int = Field(default=1, ge=1, le=100, description="Number of IDs to generate")

    @validator('user_type')
    def validate_user_type(cls, v):
        allowed_types = ['student', 'teacher', 'admin']
        if v.lower() not in allowed_types:
            raise ValueError(f'User type must be one of: {allowed_types}')
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "user_type": "student",
                "count": 5
            }
        }


class IDGenerationResponseModel(BaseModel):
    """Schema for ID generation response"""
    user_type: str
    generated_ids: List[str]
    count: int

    class Config:
        schema_extra = {
            "example": {
                "user_type": "student",
                "generated_ids": ["22001", "22002", "22003", "22004", "22005"],
                "count": 5
            }
        }


# Analytics Report Schemas
class AnalyticsReportCreateModel(BaseModel):
    """Schema for creating analytics report"""
    student_id: Optional[UUID] = Field(None, description="Student ID for individual report")
    teacher_id: Optional[UUID] = Field(None, description="Teacher ID for teacher report")
    week_id: Optional[UUID] = Field(None, description="Week ID for weekly report")
    term_id: UUID = Field(..., description="Term ID for the report")
    report_type: str = Field(..., description="Type of report (weekly/semester)")

    @validator('report_type')
    def validate_report_type(cls, v):
        allowed_types = ['weekly', 'semester']
        if v.lower() not in allowed_types:
            raise ValueError(f'Report type must be one of: {allowed_types}')
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "term_id": "123e4567-e89b-12d3-a456-426614174000",
                "week_id": "123e4567-e89b-12d3-a456-426614174001",
                "report_type": "weekly"
            }
        }


class AnalyticsReportResponseModel(BaseModel):
    """Schema for analytics report response"""
    report_id: UUID
    content: str
    report_date: date
    student_id: Optional[UUID]
    teacher_id: Optional[UUID]
    week_id: Optional[UUID]
    term_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Bulk Analytics Generation Schema
class BulkAnalyticsGenerationModel(BaseModel):
    """Schema for bulk analytics generation"""
    term_id: UUID = Field(..., description="Term ID")
    week_id: Optional[UUID] = Field(None, description="Week ID for weekly reports")
    report_type: str = Field(..., description="Type of report")
    target_users: List[str] = Field(default=["students", "teachers", "parents"], description="Target user types")

    @validator('report_type')
    def validate_report_type(cls, v):
        allowed_types = ['weekly', 'semester']
        if v.lower() not in allowed_types:
            raise ValueError(f'Report type must be one of: {allowed_types}')
        return v.lower()

    @validator('target_users')
    def validate_target_users(cls, v):
        allowed_users = ['students', 'teachers', 'parents']
        for user_type in v:
            if user_type.lower() not in allowed_users:
                raise ValueError(f'Target user must be one of: {allowed_users}')
        return [user.lower() for user in v]

    class Config:
        schema_extra = {
            "example": {
                "term_id": "123e4567-e89b-12d3-a456-426614174000",
                "week_id": "123e4567-e89b-12d3-a456-426614174001",
                "report_type": "weekly",
                "target_users": ["students", "parents"]
            }
        }


# Response models for lists
class AcademicTermListResponseModel(BaseModel):
    """Schema for academic term list response"""
    terms: List[AcademicTermResponseModel]
    total: int
    page: int
    size: int


class TermWeekListResponseModel(BaseModel):
    """Schema for term week list response"""
    weeks: List[TermWeekResponseModel]
    total: int
    page: int
    size: int


class SubjectListResponseModel(BaseModel):
    """Schema for subject list response"""
    subjects: List[SubjectResponseModel]
    total: int
    page: int
    size: int
