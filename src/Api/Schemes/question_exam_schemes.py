"""
Question and Exam-related Pydantic schemas for request and response validation.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date as dt_date
from pydantic import BaseModel, Field, validator
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions and exams."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ============ Practice Question Schemas ============

class AnswerCreate(BaseModel):
    """Schema for creating an answer."""
    answer_text: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="Answer text content"
    )
    is_correct: bool = Field(
        ...,
        description="Whether this answer is correct"
    )


class QuestionPracticeCreate(BaseModel):
    """Request schema for creating practice questions."""
    content: str = Field(
        ..., 
        min_length=10, 
        max_length=1000,
        description="Question content/text"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="Question difficulty level"
    )
    lesson_id: Optional[UUID] = Field(
        None,
        description="Associated lesson ID (optional)"
    )
    answers: List[AnswerCreate] = Field(
        ...,
        min_items=2,
        max_items=6,
        description="List of possible answers (2-6 answers)"
    )

    @validator('answers')
    def validate_answers(cls, v):
        if not v:
            raise ValueError('At least 2 answers are required')
        
        correct_answers = [answer for answer in v if answer.is_correct]
        if len(correct_answers) != 1:
            raise ValueError('Exactly one answer must be marked as correct')
        
        return v


class QuestionPracticeResponse(BaseModel):
    """Response schema for practice question creation."""
    success: bool = Field(..., description="Whether the creation was successful")
    question: Dict[str, Any] = Field(..., description="Created question information")
    answers: List[Dict[str, Any]] = Field(..., description="Created answers")
    

# ============ Exam Question Schemas ============

class QuestionExamCreate(BaseModel):
    """Request schema for creating exam questions."""
    content: str = Field(
        ..., 
        min_length=10, 
        max_length=1000,
        description="Question content/text"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="Question difficulty level"
    )
    answers: List[AnswerCreate] = Field(
        ...,
        min_items=2,
        max_items=6,
        description="List of possible answers (2-6 answers)"
    )

    @validator('answers')
    def validate_answers(cls, v):
        if not v:
            raise ValueError('At least 2 answers are required')
        
        correct_answers = [answer for answer in v if answer.is_correct]
        if len(correct_answers) != 1:
            raise ValueError('Exactly one answer must be marked as correct')
        
        return v


class ExamCreate(BaseModel):
    """Request schema for creating an exam with questions."""
    title: str = Field(
        ..., 
        min_length=3, 
        max_length=255,
        description="Exam title"
    )
    date: dt_date = Field(
        ...,
        description="Exam date"
    )
    questions: List[QuestionExamCreate] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of exam questions (1-50 questions)"
    )

    @validator('date')
    def validate_exam_date(cls, v):
        if v < dt_date.today():
            raise ValueError('Exam date cannot be in the past')
        return v


class ExamResponse(BaseModel):
    """Response schema for exam creation."""
    success: bool = Field(..., description="Whether the creation was successful")
    exam: Dict[str, Any] = Field(..., description="Created exam information")
    questions: List[Dict[str, Any]] = Field(..., description="Created questions with answers")
    total_questions: int = Field(..., description="Total number of questions created")


# ============ List/Retrieve Schemas ============

class QuestionInfo(BaseModel):
    """Information about a question."""
    question_id: UUID
    content: str
    difficulty: str
    created_at: datetime
    answers_count: int


class PracticeQuestionListResponse(BaseModel):
    """Response schema for listing practice questions."""
    questions: List[QuestionInfo] = Field(..., description="List of practice questions")
    total_count: int = Field(..., description="Total number of questions")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


class ExamInfo(BaseModel):
    """Information about an exam."""
    exam_id: UUID
    title: str
    date: dt_date
    questions_count: int
    created_at: datetime


class ExamListResponse(BaseModel):
    """Response schema for listing exams."""
    exams: List[ExamInfo] = Field(..., description="List of exams")
    total_count: int = Field(..., description="Total number of exams")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")


# ============ Detail Schemas ============

class AnswerInfo(BaseModel):
    """Detailed answer information."""
    answer_id: UUID
    answer_text: str
    is_correct: bool


class QuestionDetailResponse(BaseModel):
    """Detailed question information."""
    question: Dict[str, Any]
    answers: List[AnswerInfo]


class ExamDetailResponse(BaseModel):
    """Detailed exam information."""
    exam: Dict[str, Any]
    questions: List[Dict[str, Any]]
    statistics: Dict[str, Any]
