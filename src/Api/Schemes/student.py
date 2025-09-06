"""
Student API Schemas

Pydantic models for student-related API requests and responses
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from src.Enums.user_type_enums import UserTypeEnum


class StudentProfileResponse(BaseModel):
    """Response model for student profile information"""
    user_id: UUID = Field(..., description="Unique identifier for the student")
    unique_id: str = Field(..., description="Student's unique ID (e.g., 22001)")
    name: str = Field(..., description="Student's full name")
    email: str = Field(..., description="Student's email address")
    user_type: UserTypeEnum = Field(..., description="User type (should be STUDENT)")
    rating: float = Field(default=0.0, description="Current student rating")
    total_classrooms: int = Field(default=0, description="Total number of classrooms enrolled")
    created_at: datetime = Field(..., description="Account creation timestamp")
    is_verified: bool = Field(default=False, description="Email verification status")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class StudentClassroomResponse(BaseModel):
    """Response model for student's classroom information"""
    classroom_id: UUID = Field(..., description="Unique identifier for the classroom")
    name: str = Field(..., description="Classroom name")
    description: str = Field(default="", description="Classroom description")
    subject_name: str = Field(..., description="Subject name")
    teacher_name: str = Field(..., description="Teacher's name")
    lesson_count: int = Field(default=0, description="Number of lessons in classroom")
    student_grade: float = Field(default=0.0, description="Student's average grade in this classroom")
    completion_rate: float = Field(default=0.0, description="Student's completion rate (0-100%)")
    created_at: datetime = Field(..., description="Classroom creation timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class SubjectPerformance(BaseModel):
    """Model for subject-wise performance data"""
    subject_name: str = Field(..., description="Name of the subject")
    average_grade: float = Field(default=0.0, description="Average grade in this subject")
    total_assessments: int = Field(default=0, description="Total assessments in this subject")
    completed_assessments: int = Field(default=0, description="Completed assessments in this subject")
    time_spent_hours: float = Field(default=0.0, description="Time spent studying this subject (hours)")


class RecentActivity(BaseModel):
    """Model for recent student activities"""
    activity_type: str = Field(..., description="Type of activity (lesson, quiz, exam, etc.)")
    activity_name: str = Field(..., description="Name or description of the activity")
    classroom_name: str = Field(..., description="Classroom where activity occurred")
    grade: Optional[float] = Field(None, description="Grade received (if applicable)")
    timestamp: datetime = Field(..., description="When the activity occurred")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StudentAnalyticsResponse(BaseModel):
    """Response model for comprehensive student analytics"""
    student_id: UUID = Field(..., description="Student's unique identifier")
    period: str = Field(..., description="Analytics period (current_semester, current_week, all_time)")
    overall_rating: float = Field(default=0.0, description="Overall student rating")
    average_grade: float = Field(default=0.0, description="Average grade across all subjects")
    total_assessments: int = Field(default=0, description="Total number of assessments")
    completed_assessments: int = Field(default=0, description="Number of completed assessments")
    total_lessons_accessed: int = Field(default=0, description="Total lessons accessed")
    study_time_hours: float = Field(default=0.0, description="Total study time in hours")
    chatbot_interactions: int = Field(default=0, description="Number of chatbot interactions")
    subject_performance: List[SubjectPerformance] = Field(default=[], description="Performance by subject")
    recent_activities: List[RecentActivity] = Field(default=[], description="Recent activities")
    strengths: List[str] = Field(default=[], description="Identified strengths")
    areas_for_improvement: List[str] = Field(default=[], description="Areas needing improvement")
    recommendations: List[str] = Field(default=[], description="AI-generated recommendations")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class StudentProfileUpdateRequest(BaseModel):
    """Request model for updating student profile"""
    name: Optional[str] = Field(None, description="Updated student name", min_length=2, max_length=100)
    email: Optional[str] = Field(None, description="Updated email address")

    class Config:
        schema_extra = {
            "example": {
                "name": "Ahmed Al-Walid",
                "email": "ahmed.walid@example.com"
            }
        }


class StudentClassroomListResponse(BaseModel):
    """Response model for paginated classroom list"""
    classrooms: List[StudentClassroomResponse] = Field(default=[], description="List of student's classrooms")
    total_count: int = Field(default=0, description="Total number of classrooms")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Number of items per page")
    has_more: bool = Field(default=False, description="Whether more pages are available")

    class Config:
        from_attributes = True


# Query parameter models for API endpoints
class StudentAnalyticsQuery(BaseModel):
    """Query parameters for student analytics endpoint"""
    period: str = Field(default="current_semester", description="Analytics period")

    class Config:
        schema_extra = {
            "example": {
                "period": "current_semester"
            }
        }


class PaginationQuery(BaseModel):
    """Query parameters for pagination"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=10, ge=1, le=100, description="Number of items per page")

    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "page_size": 10
            }
        }
