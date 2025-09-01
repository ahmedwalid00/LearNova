from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


# Step 1: Classroom Initialization (without students)
class ClassRoomCreateBase(BaseModel):
    """Base schema for creating a classroom without students"""
    teacher_unique_id: str = Field(..., description="Teacher unique ID (e.g., '11001')")
    subject_id: UUID = Field(..., description="Subject ID")
    term_id: UUID = Field(..., description="Academic Term ID")
    grade_level: str = Field(..., min_length=1, max_length=10, description="Grade level (e.g., Grade 12)")
    classroom_name: Optional[str] = Field(None, description="Optional classroom name")


class ClassRoomCreate(ClassRoomCreateBase):
    """Schema for creating a classroom (Step 1: without students)"""
    pass


class ClassRoomBulkCreate(BaseModel):
    """Schema for bulk creating classrooms"""
    classrooms: List[ClassRoomCreate] = Field(..., description="List of classrooms to create")


# Step 2: Student Assignment
class StudentAssignmentRequest(BaseModel):
    """Schema for assigning a student to an existing classroom"""
    classroom_id: UUID = Field(..., description="Classroom ID to assign student to")
    student_unique_id: str = Field(..., description="Student unique ID (e.g., '22001')")


class BulkStudentAssignmentRequest(BaseModel):
    """Schema for bulk student assignments"""
    assignments: List[StudentAssignmentRequest] = Field(..., description="List of student assignments")


class ClassRoomUpdate(BaseModel):
    """Schema for updating a classroom"""
    grade_level: Optional[str] = Field(None, min_length=1, max_length=10, description="New grade level")
    classroom_name: Optional[str] = Field(None, description="New classroom name")


class ClassRoomResponse(BaseModel):
    """Schema for classroom response"""
    classroom_id: UUID = Field(..., description="Classroom ID")
    subject_id: UUID = Field(..., description="Subject ID")
    teacher_id: UUID = Field(..., description="Teacher ID")
    term_id: UUID = Field(..., description="Academic Term ID")
    grade_level: str = Field(..., description="Grade level")
    classroom_name: Optional[str] = Field(None, description="Classroom name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class StudentInfo(BaseModel):
    """Student information for classroom details"""
    student_id: UUID
    unique_id: str
    first_name: str
    last_name: str
    email: str


class TeacherInfo(BaseModel):
    """Teacher information for classroom details"""
    teacher_id: UUID
    unique_id: str
    first_name: str
    last_name: str
    email: str


class SubjectInfo(BaseModel):
    """Subject information for classroom details"""
    subject_id: UUID
    subject_name: str
    description: Optional[str] = None


class TermInfo(BaseModel):
    """Term information for classroom details"""
    term_id: UUID
    term_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ClassRoomDetailResponse(BaseModel):
    """Detailed classroom response with full information"""
    classroom_id: UUID
    grade_level: str
    student: Optional[StudentInfo] = None
    teacher: Optional[TeacherInfo] = None
    subject: Optional[SubjectInfo] = None
    term: Optional[TermInfo] = None
    created_at: str
    updated_at: str


class StudentClassRoomInfo(BaseModel):
    """Student classroom information for teacher view"""
    classroom_id: UUID
    student_id: UUID
    unique_id: str
    first_name: str
    last_name: str
    email: str
    grade_level: str


class ClassRoomRemovalRequest(BaseModel):
    """Request schema for removing a classroom"""
    classroom_id: UUID = Field(..., description="Classroom ID to remove")


class StudentRemovalRequest(BaseModel):
    """Request schema for removing student from classroom"""
    classroom_id: UUID = Field(..., description="Classroom ID")
    student_id: UUID = Field(..., description="Student ID to remove")


class TeacherReassignmentRequest(BaseModel):
    """Request schema for reassigning teacher to a classroom"""
    classroom_id: UUID = Field(..., description="Classroom ID")
    new_teacher_id: UUID = Field(..., description="New teacher ID")


class ClassRoomSearchFilters(BaseModel):
    """Search filters for classroom queries"""
    grade_level: Optional[str] = Field(None, description="Filter by grade level")
    term_id: Optional[UUID] = Field(None, description="Filter by term ID")
    subject_id: Optional[UUID] = Field(None, description="Filter by subject ID")
    teacher_id: Optional[UUID] = Field(None, description="Filter by teacher ID")
    has_students: Optional[bool] = Field(None, description="Filter by whether classroom has students assigned")


class ClassRoomStatsResponse(BaseModel):
    """Statistics response for classroom management"""
    total_classrooms: int = Field(..., description="Total number of classroom assignments")
    students_count: int = Field(..., description="Number of unique students")
    teachers_count: int = Field(..., description="Number of unique teachers")
    subjects_count: int = Field(..., description="Number of unique subjects")
    grades: List[str] = Field(..., description="List of grade levels")
    
    
class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")


class ErrorResponse(BaseModel):
    """Generic error response"""
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Error code")
