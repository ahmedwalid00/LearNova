"""
Question service for orchestrating question and exam creation business logic.

This module contains the QuestionService class that handles complex
operations involving practice questions, exam questions, and their answers.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from uuid import UUID
from fastapi import HTTPException, status

from ..repositories.question_repository import (
    QuestionPracticeRepository, QuestionExamRepository, AnswerRepository
)
from ..repositories.exam_repository import ExamRepository
from ..repositories.user_repository import TeacherRepository
from ..DBSchemes.Schemes.question_models import QuestionPractice, QuestionExam, Answer
from ..DBSchemes.Schemes.exam_models import Exam


class QuestionService:
    """
    Service class for question and exam creation business logic.
    
    This class orchestrates operations involving practice questions,
    exam questions, and their management.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the service with database session."""
        self.session = session
        self.practice_repo = QuestionPracticeRepository(session)
        self.exam_question_repo = QuestionExamRepository(session)
        self.answer_repo = AnswerRepository(session)
        self.exam_repo = ExamRepository(session)
        self.teacher_repo = TeacherRepository(session)
    
    async def create_practice_question(
        self, 
        teacher_id: UUID, 
        term_id: UUID,
        content: str,
        difficulty: str,
        answers_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a practice question with its answers.
        
        Args:
            teacher_id: UUID of the teacher creating the question
            term_id: UUID of the current term
            content: Question content/text
            difficulty: Difficulty level (easy, medium, hard)
            answers_data: List of answer dictionaries
            
        Returns:
            Dict with created question and answers
        """
        try:
            # Validate that exactly one answer is correct
            correct_answers = [ans for ans in answers_data if ans.get('is_correct')]
            if len(correct_answers) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Exactly one answer must be marked as correct"
                )
            
            # Create the practice question
            question_data = {
                "content": content,
                "difficulty": difficulty,
                "teacher_id": teacher_id,
                "term_id": term_id
            }
            question = await self.practice_repo.create(**question_data)
            
            # Create answers
            created_answers = []
            for answer_data in answers_data:
                answer = Answer(
                    question_practice_id=question.practice_id,
                    answer_text=answer_data['answer_text'],
                    is_correct=1 if answer_data['is_correct'] else 0
                )
                self.session.add(answer)
                created_answers.append(answer)
            
            # Flush to get IDs
            await self.session.flush()
            
            return {
                "question": question,
                "answers": created_answers,
                "total_answers": len(created_answers)
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create practice question: {str(e)}"
            )
    
    async def create_exam_with_questions(
        self,
        teacher_id: UUID,
        term_id: UUID,
        title: str,
        exam_date: date,
        questions_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create an exam with multiple questions and their answers.
        
        Args:
            teacher_id: UUID of the teacher creating the exam
            term_id: UUID of the current term
            title: Exam title
            exam_date: Date of the exam
            questions_data: List of question dictionaries with answers
            
        Returns:
            Dict with created exam, questions, and answers
        """
        try:
            # Create the exam first
            exam_data = {
                "title": title,
                "date": exam_date,
                "teacher_id": teacher_id,
                "term_id": term_id
            }
            exam = await self.exam_repo.create(**exam_data)
            
            # Create questions and answers
            created_questions = []
            total_answers = 0
            
            for question_data in questions_data:
                # Validate answers for this question
                answers_data = question_data.get('answers', [])
                correct_answers = [ans for ans in answers_data if ans.get('is_correct')]
                if len(correct_answers) != 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Each question must have exactly one correct answer"
                    )
                
                # Create the exam question
                exam_question = QuestionExam(
                    content=question_data['content'],
                    difficulty=question_data['difficulty'],
                    teacher_id=teacher_id,
                    exam_id=exam.exam_id,
                    term_id=term_id
                )
                self.session.add(exam_question)
                await self.session.flush()  # Get the question ID
                
                # Create answers for this question
                question_answers = []
                for answer_data in answers_data:
                    answer = Answer(
                        question_exam_id=exam_question.question_id,
                        answer_text=answer_data['answer_text'],
                        is_correct=1 if answer_data['is_correct'] else 0
                    )
                    self.session.add(answer)
                    question_answers.append(answer)
                
                created_questions.append({
                    "question": exam_question,
                    "answers": question_answers
                })
                total_answers += len(question_answers)
            
            await self.session.flush()
            
            return {
                "exam": exam,
                "questions": created_questions,
                "total_questions": len(created_questions),
                "total_answers": total_answers
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create exam: {str(e)}"
            )
    
    async def get_practice_questions_list(
        self, 
        teacher_id: UUID, 
        page: int = 1, 
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated list of practice questions for a teacher.
        
        Args:
            teacher_id: UUID of the teacher
            page: Page number (1-based)
            per_page: Items per page
            
        Returns:
            Dict with questions list and pagination info
        """
        try:
            offset = (page - 1) * per_page
            questions = await self.practice_repo.get_by_teacher_id(teacher_id, per_page, offset)
            total_count = await self.practice_repo.count_by_teacher_id(teacher_id)
            
            # Format questions for response
            formatted_questions = []
            for question in questions:
                formatted_questions.append({
                    "question_id": question.practice_id,
                    "content": question.content,
                    "difficulty": question.difficulty,
                    "created_at": question.created_at,
                    "answers_count": len(question.answers) if question.answers else 0
                })
            
            return {
                "questions": formatted_questions,
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_count + per_page - 1) // per_page
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve practice questions: {str(e)}"
            )
    
    async def get_exams_list(
        self, 
        teacher_id: UUID, 
        page: int = 1, 
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated list of exams for a teacher.
        
        Args:
            teacher_id: UUID of the teacher
            page: Page number (1-based)
            per_page: Items per page
            
        Returns:
            Dict with exams list and pagination info
        """
        try:
            # Get exams (exam repository already has get_by_teacher_id method)
            exams = await self.exam_repo.get_by_teacher_id(teacher_id)
            
            # Apply pagination manually (can be optimized in repository later)
            total_count = len(exams)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_exams = exams[start_idx:end_idx]
            
            # Format exams for response
            formatted_exams = []
            for exam in paginated_exams:
                questions_count = await self.exam_question_repo.count_by_exam_id(exam.exam_id)
                formatted_exams.append({
                    "exam_id": exam.exam_id,
                    "title": exam.title,
                    "date": exam.date,
                    "questions_count": questions_count,
                    "created_at": exam.created_at
                })
            
            return {
                "exams": formatted_exams,
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_count + per_page - 1) // per_page
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve exams: {str(e)}"
            )
    
    async def get_practice_question_details(
        self, 
        practice_id: UUID, 
        teacher_id: UUID
    ) -> Dict[str, Any]:
        """
        Get detailed information about a practice question.
        
        Args:
            practice_id: UUID of the practice question
            teacher_id: UUID of the teacher (for permission check)
            
        Returns:
            Dict with question and answers details
        """
        try:
            question = await self.practice_repo.get_with_answers(practice_id)
            
            if not question:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Practice question not found"
                )
            
            if question.teacher_id != teacher_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this question"
                )
            
            # Format answers
            formatted_answers = []
            for answer in question.answers:
                formatted_answers.append({
                    "answer_id": answer.answer_id,
                    "answer_text": answer.answer_text,
                    "is_correct": bool(answer.is_correct)
                })
            
            return {
                "question": {
                    "practice_id": question.practice_id,
                    "content": question.content,
                    "difficulty": question.difficulty,
                    "teacher_id": question.teacher_id,
                    "term_id": question.term_id,
                    "created_at": question.created_at
                },
                "answers": formatted_answers
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve question details: {str(e)}"
            )
    
    async def get_exam_details(
        self, 
        exam_id: UUID, 
        teacher_id: UUID
    ) -> Dict[str, Any]:
        """
        Get detailed information about an exam with all questions and answers.
        
        Args:
            exam_id: UUID of the exam
            teacher_id: UUID of the teacher (for permission check)
            
        Returns:
            Dict with exam, questions, and answers details
        """
        try:
            exam = await self.exam_repo.get_by_id(exam_id)
            
            if not exam:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exam not found"
                )
            
            if exam.teacher_id != teacher_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this exam"
                )
            
            # Get all questions for this exam
            questions = await self.exam_question_repo.get_by_exam_id(exam_id)
            
            # Format questions with answers
            formatted_questions = []
            for question in questions:
                formatted_answers = []
                for answer in question.answers:
                    formatted_answers.append({
                        "answer_id": answer.answer_id,
                        "answer_text": answer.answer_text,
                        "is_correct": bool(answer.is_correct)
                    })
                
                formatted_questions.append({
                    "question_id": question.question_id,
                    "content": question.content,
                    "difficulty": question.difficulty,
                    "answers": formatted_answers
                })
            
            return {
                "exam": {
                    "exam_id": exam.exam_id,
                    "title": exam.title,
                    "date": exam.date,
                    "teacher_id": exam.teacher_id,
                    "term_id": exam.term_id,
                    "created_at": exam.created_at
                },
                "questions": formatted_questions,
                "statistics": {
                    "total_questions": len(formatted_questions),
                    "difficulty_distribution": {
                        "easy": len([q for q in questions if q.difficulty == "easy"]),
                        "medium": len([q for q in questions if q.difficulty == "medium"]),
                        "hard": len([q for q in questions if q.difficulty == "hard"])
                    }
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve exam details: {str(e)}"
            )
