"""
Student API Schemas

Pydantic models for student-related API requests and responses.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, validator


class StudentProfileResponse(BaseModel):
    """Response model for student profile information"""
    student_id: UUID
    unique_id: str
    name: str
    email: EmailStr
    is_verified: bool
    term_id: Optional[UUID]
    current_rating: Optional[float]
    total_practice_answered: int
    total_exams_taken: int
    overall_accuracy: float
    joined_classrooms: int

    class Config:
        from_attributes = True


class StudentProfileUpdateRequest(BaseModel):
    """Request model for updating student profile"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip() if v else v


class StudentClassroomResponse(BaseModel):
    """Response model for classroom information from student perspective"""
    classroom_id: UUID
    subject_name: str
    teacher_name: str
    teacher_id: UUID
    term_id: UUID
    grade_level: str
    classroom_name: Optional[str]

    class Config:
        from_attributes = True


class StudentClassroomListResponse(BaseModel):
    """Response model for paginated list of student's classrooms"""
    classrooms: List[StudentClassroomResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class PracticeQuestionForStudentResponse(BaseModel):
    """Response model for practice questions from student perspective"""
    practice_id: UUID
    content: str
    difficulty: str
    teacher_name: str
    subject_name: str
    answers: List[Dict[str, Any]]  # List of answer options
    already_answered: bool

    class Config:
        from_attributes = True


class PracticeQuestionsListResponse(BaseModel):
    """Response model for paginated list of practice questions"""
    questions: List[PracticeQuestionForStudentResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class ExamForStudentResponse(BaseModel):
    """Response model for exams from student perspective"""
    exam_id: UUID
    title: str
    date: date
    teacher_name: str
    subject_name: str
    questions_count: int
    already_taken: bool
    score: Optional[float]  # Percentage score if already taken

    class Config:
        from_attributes = True


class ExamsListResponse(BaseModel):
    """Response model for paginated list of exams"""
    exams: List[ExamForStudentResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class StudentAnalyticsResponse(BaseModel):
    """Response model for student analytics"""
    student_id: UUID
    period: str
    practice_stats: Dict[str, Any]
    exam_stats: Dict[str, Any]
    rating_info: Optional[Dict[str, Any]]
    performance_trends: Dict[str, Any]

    class Config:
        from_attributes = True
