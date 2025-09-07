"""
API Schemas for Student Response endpoints.

This module contains Pydantic models for request and response validation
for student question and exam response endpoints.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


# Request Schemas
class AnswerPracticeQuestionRequest(BaseModel):
    """Request schema for answering a practice question"""
    practice_id: UUID = Field(..., description="ID of the practice question")
    answer_id: UUID = Field(..., description="ID of the selected answer")
    time_taken_seconds: Optional[int] = Field(None, description="Time taken to answer in seconds", ge=0)


class AnswerExamQuestionRequest(BaseModel):
    """Request schema for answering an exam question"""
    exam_id: UUID = Field(..., description="ID of the exam")
    question_id: UUID = Field(..., description="ID of the exam question")
    answer_id: UUID = Field(..., description="ID of the selected answer")
    time_taken_seconds: Optional[int] = Field(None, description="Time taken to answer in seconds", ge=0)


# Response Schemas
class AnswerSubmissionResponse(BaseModel):
    """Response schema for answer submission"""
    success: bool
    message: str
    data: dict


class PracticeResponseData(BaseModel):
    """Data schema for practice question response"""
    response_id: str
    practice_id: str
    question_text: Optional[str]
    is_correct: bool
    time_taken_seconds: int
    answered_at: str
    classroom_id: Optional[str]


class ExamResponseData(BaseModel):
    """Data schema for exam question response"""
    response_id: str
    exam_id: str
    question_id: str
    question_text: Optional[str]
    is_correct: bool
    time_taken_seconds: int
    answered_at: str
    exam_title: Optional[str]


class PracticeResponsesResponse(BaseModel):
    """Response schema for practice responses list"""
    success: bool
    data: dict


class ExamResponsesResponse(BaseModel):
    """Response schema for exam responses list"""
    success: bool
    data: dict


class PerformanceMetrics(BaseModel):
    """Performance metrics schema"""
    total_answered: int
    total_correct: int
    accuracy_rate: float = Field(..., description="Accuracy rate as percentage")
    average_time_seconds: float


class RatingInfo(BaseModel):
    """Rating information schema"""
    overall_rating: float
    practice_rating: float
    exam_rating: float
    last_updated: Optional[str]


class PerformanceSummaryResponse(BaseModel):
    """Response schema for performance summary"""
    success: bool
    data: dict
