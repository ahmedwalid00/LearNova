"""
Question and Exam Controller for handling question/exam-related business logic.

This module contains the QuestionExamController class that orchestrates
question and exam operations and can be reused across different endpoints.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import logging
from datetime import date

from src.Models.services.question_service import QuestionService
from src.Api.Schemes.question_exam_schemes import (
    QuestionPracticeCreate, QuestionPracticeResponse,
    ExamCreate, ExamResponse,
    PracticeQuestionListResponse, ExamListResponse,
    QuestionDetailResponse, ExamDetailResponse,
    QuestionInfo, ExamInfo, AnswerInfo
)

logger = logging.getLogger('uvicorn.error')


class QuestionExamController:
    """
    Controller class for question and exam operations.
    
    Handles practice question creation, exam creation, listing,
    and detail retrieval in a reusable and extensible manner.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the controller with database session.
        
        Args:
            session: Database session
        """
        self.session = session
        self.question_service = QuestionService(session)
    
    async def create_practice_question(
        self, 
        request_data: QuestionPracticeCreate, 
        teacher_id: UUID, 
        term_id: UUID
    ) -> QuestionPracticeResponse:
        """
        Handle practice question creation.
        
        Args:
            request_data: Question creation request data
            teacher_id: ID of the teacher creating the question
            term_id: ID of the current term
            
        Returns:
            Question creation response
        """
        try:
            # Prepare answers data
            answers_data = []
            for answer in request_data.answers:
                answers_data.append({
                    'answer_text': answer.answer_text,
                    'is_correct': answer.is_correct
                })
            
            # Create the question
            result = await self.question_service.create_practice_question(
                teacher_id=teacher_id,
                term_id=term_id,
                content=request_data.content,
                difficulty=request_data.difficulty.value,
                answers_data=answers_data
            )
            
            # Format response
            question_info = {
                'practice_id': str(result['question'].practice_id),
                'content': result['question'].content,
                'difficulty': result['question'].difficulty,
                'teacher_id': str(result['question'].teacher_id),
                'term_id': str(result['question'].term_id),
                'created_at': result['question'].created_at.isoformat() if result['question'].created_at else None
            }
            
            answers_info = []
            for answer in result['answers']:
                answers_info.append({
                    'answer_id': str(answer.answer_id),
                    'answer_text': answer.answer_text,
                    'is_correct': bool(answer.is_correct)
                })
            
            return QuestionPracticeResponse(
                success=True,
                question=question_info,
                answers=answers_info
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Practice question creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create practice question: {str(e)}"
            )
    
    async def create_exam(
        self, 
        request_data: ExamCreate, 
        teacher_id: UUID, 
        term_id: UUID
    ) -> ExamResponse:
        """
        Handle exam creation with questions.
        
        Args:
            request_data: Exam creation request data
            teacher_id: ID of the teacher creating the exam
            term_id: ID of the current term
            
        Returns:
            Exam creation response
        """
        try:
            # Prepare questions data
            questions_data = []
            for question in request_data.questions:
                answers_data = []
                for answer in question.answers:
                    answers_data.append({
                        'answer_text': answer.answer_text,
                        'is_correct': answer.is_correct
                    })
                
                questions_data.append({
                    'content': question.content,
                    'difficulty': question.difficulty.value,
                    'answers': answers_data
                })
            
            # Create the exam
            result = await self.question_service.create_exam_with_questions(
                teacher_id=teacher_id,
                term_id=term_id,
                title=request_data.title,
                exam_date=request_data.date,
                questions_data=questions_data
            )
            
            # Format response
            exam_info = {
                'exam_id': str(result['exam'].exam_id),
                'title': result['exam'].title,
                'date': result['exam'].date.isoformat(),
                'teacher_id': str(result['exam'].teacher_id),
                'term_id': str(result['exam'].term_id),
                'created_at': result['exam'].created_at.isoformat() if result['exam'].created_at else None
            }
            
            questions_info = []
            for question_data in result['questions']:
                question = question_data['question']
                answers = question_data['answers']
                
                answers_info = []
                for answer in answers:
                    answers_info.append({
                        'answer_id': str(answer.answer_id),
                        'answer_text': answer.answer_text,
                        'is_correct': bool(answer.is_correct)
                    })
                
                questions_info.append({
                    'question_id': str(question.question_id),
                    'content': question.content,
                    'difficulty': question.difficulty,
                    'answers': answers_info
                })
            
            return ExamResponse(
                success=True,
                exam=exam_info,
                questions=questions_info,
                total_questions=result['total_questions']
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Exam creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create exam: {str(e)}"
            )
    
    async def get_practice_questions(
        self, 
        teacher_id: UUID, 
        page: int = 1, 
        per_page: int = 20
    ) -> PracticeQuestionListResponse:
        """
        Handle practice questions listing.
        
        Args:
            teacher_id: ID of the teacher
            page: Page number
            per_page: Items per page
            
        Returns:
            Practice questions list response
        """
        try:
            result = await self.question_service.get_practice_questions_list(
                teacher_id=teacher_id,
                page=page,
                per_page=per_page
            )
            
            # Format questions
            questions = []
            for question_data in result['questions']:
                questions.append(QuestionInfo(
                    question_id=question_data['question_id'],
                    content=question_data['content'],
                    difficulty=question_data['difficulty'],
                    created_at=question_data['created_at'],
                    answers_count=question_data['answers_count']
                ))
            
            return PracticeQuestionListResponse(
                questions=questions,
                total_count=result['total_count'],
                page=result['page'],
                per_page=result['per_page']
            )
            
        except Exception as e:
            logger.error(f"Practice questions list error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve practice questions: {str(e)}"
            )
    
    async def get_exams(
        self, 
        teacher_id: UUID, 
        page: int = 1, 
        per_page: int = 20
    ) -> ExamListResponse:
        """
        Handle exams listing.
        
        Args:
            teacher_id: ID of the teacher
            page: Page number
            per_page: Items per page
            
        Returns:
            Exams list response
        """
        try:
            result = await self.question_service.get_exams_list(
                teacher_id=teacher_id,
                page=page,
                per_page=per_page
            )
            
            # Format exams
            exams = []
            for exam_data in result['exams']:
                exams.append(ExamInfo(
                    exam_id=exam_data['exam_id'],
                    title=exam_data['title'],
                    date=exam_data['date'],
                    questions_count=exam_data['questions_count'],
                    created_at=exam_data['created_at']
                ))
            
            return ExamListResponse(
                exams=exams,
                total_count=result['total_count'],
                page=result['page'],
                per_page=result['per_page']
            )
            
        except Exception as e:
            logger.error(f"Exams list error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve exams: {str(e)}"
            )
    
    async def get_practice_question_details(
        self, 
        practice_id: UUID, 
        teacher_id: UUID
    ) -> QuestionDetailResponse:
        """
        Handle practice question details retrieval.
        
        Args:
            practice_id: ID of the practice question
            teacher_id: ID of the teacher
            
        Returns:
            Question detail response
        """
        try:
            result = await self.question_service.get_practice_question_details(
                practice_id=practice_id,
                teacher_id=teacher_id
            )
            
            # Format answers
            answers = []
            for answer_data in result['answers']:
                answers.append(AnswerInfo(
                    answer_id=answer_data['answer_id'],
                    answer_text=answer_data['answer_text'],
                    is_correct=answer_data['is_correct']
                ))
            
            return QuestionDetailResponse(
                question=result['question'],
                answers=answers
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Question details error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve question details: {str(e)}"
            )
    
    async def get_exam_details(
        self, 
        exam_id: UUID, 
        teacher_id: UUID
    ) -> ExamDetailResponse:
        """
        Handle exam details retrieval.
        
        Args:
            exam_id: ID of the exam
            teacher_id: ID of the teacher
            
        Returns:
            Exam detail response
        """
        try:
            result = await self.question_service.get_exam_details(
                exam_id=exam_id,
                teacher_id=teacher_id
            )
            
            return ExamDetailResponse(
                exam=result['exam'],
                questions=result['questions'],
                statistics=result['statistics']
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Exam details error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve exam details: {str(e)}"
            )
