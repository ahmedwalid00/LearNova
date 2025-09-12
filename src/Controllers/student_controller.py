"""
Student Controller

Handles business logic for student-related operations including
profile management, classroom access, and analytics.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.repositories.user_repository import StudentRepository
from src.Models.repositories.classroom_repository import ClassRoomRepository  
from src.Models.repositories.classroom_student_repository import ClassRoomStudentRepository
from src.Models.repositories.student_response_repository import StudentRatingRepository
from src.Models.repositories.question_repository import QuestionPracticeRepository
from src.Models.repositories.exam_repository import ExamRepository
from src.Api.Schemes.student import (
    StudentProfileResponse,
    StudentProfileUpdateRequest,
    StudentClassroomResponse,
    StudentClassroomListResponse,
    PracticeQuestionForStudentResponse,
    PracticeQuestionsListResponse,
    ExamForStudentResponse,
    ExamsListResponse,
    StudentAnalyticsResponse
)


class StudentController:
    """Controller for student operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.student_repo = StudentRepository(session)
        self.classroom_repo = ClassRoomRepository(session)
        self.classroom_student_repo = ClassRoomStudentRepository(session)
        self.rating_repo = StudentRatingRepository(session)
        self.practice_repo = QuestionPracticeRepository(session)
        self.exam_repo = ExamRepository(session)

    async def get_student_profile(self, student_id: UUID) -> StudentProfileResponse:
        """Get comprehensive student profile information"""
        # Get student basic info
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError("Student not found")

        # Get current rating
        current_rating_obj = await self.rating_repo.get_current_rating(student_id)
        current_rating = current_rating_obj.overall_rating if current_rating_obj else None

        # Get practice statistics
        from src.Models.repositories.student_response_repository import PracticeQuestionResponseRepository
        practice_response_repo = PracticeQuestionResponseRepository(self.session)
        practice_stats = await practice_response_repo.get_practice_statistics(student_id)

        # Get exam statistics  
        from src.Models.repositories.student_response_repository import ExamQuestionResponseRepository
        exam_response_repo = ExamQuestionResponseRepository(self.session)
        
        # Count unique exams taken
        exam_responses = await exam_response_repo.get_student_exam_responses(student_id, limit=1000)
        unique_exams = len(set(response.exam_id for response in exam_responses))

        # Get classroom count
        classroom_assignments = await self.classroom_student_repo.get_classrooms_by_student(student_id)
        joined_classrooms = len(classroom_assignments)

        # Calculate overall accuracy
        total_practice_correct = practice_stats.get('total_correct', 0)
        total_practice_answered = practice_stats.get('total_answered', 0)
        
        # Calculate exam accuracy
        exam_correct = sum(1 for response in exam_responses if response.is_correct)
        exam_total = len(exam_responses)
        
        # Overall accuracy across practice and exams
        total_correct = total_practice_correct + exam_correct
        total_answered = total_practice_answered + exam_total
        overall_accuracy = (total_correct / total_answered) if total_answered > 0 else 0.0

        return StudentProfileResponse(
            student_id=student.student_id,
            unique_id=student.unique_id,
            name=student.name,
            email=student.email,
            is_verified=student.is_verified,
            term_id=student.term_id,
            current_rating=current_rating,
            total_practice_answered=total_practice_answered,
            total_exams_taken=unique_exams,
            overall_accuracy=round(overall_accuracy, 3),
            joined_classrooms=joined_classrooms
        )

    async def update_student_profile(
        self, 
        student_id: UUID, 
        update_data: StudentProfileUpdateRequest
    ) -> StudentProfileResponse:
        """Update student profile information"""
        # Get existing student
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise ValueError("Student not found")

        # Update fields
        update_dict = update_data.dict(exclude_none=True)
        
        # Check if email is being updated and if it's unique
        if 'email' in update_dict:
            existing_student = await self.student_repo.get_by_email(update_dict['email'])
            if existing_student and existing_student.student_id != student_id:
                raise ValueError("Email already exists")

        # Update student
        updated_student = await self.student_repo.update(student_id, **update_dict)
        
        # Return updated profile
        return await self.get_student_profile(student_id)

    async def get_student_classrooms(
        self, 
        student_id: UUID, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[StudentClassroomResponse]:
        """Get student's enrolled classrooms"""
        # Get student's classroom assignments
        assignments = await self.classroom_student_repo.get_classrooms_by_student(student_id)
        
        # Apply pagination
        paginated_assignments = assignments[offset:offset + limit]
        
        classrooms = []
        for assignment in paginated_assignments:
            # Get classroom details with relationships
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            from src.Models.DBSchemes.Schemes.associations import ClassRoom
            
            result = await self.session.execute(
                select(ClassRoom)
                .where(ClassRoom.classroom_id == assignment.classroom_id)
                .options(
                    selectinload(ClassRoom.subject),
                    selectinload(ClassRoom.teacher),
                    selectinload(ClassRoom.term)
                )
            )
            classroom = result.scalar_one_or_none()
            
            if classroom:
                classrooms.append(StudentClassroomResponse(
                    classroom_id=classroom.classroom_id,
                    subject_name=classroom.subject.name if classroom.subject else "Unknown",
                    teacher_name=classroom.teacher.name if classroom.teacher else "Unknown",
                    teacher_id=classroom.teacher_id,
                    term_id=classroom.term_id,
                    grade_level=classroom.grade_level,
                    classroom_name=classroom.classroom_name
                ))
        
        return classrooms

    async def get_practice_questions(
        self, 
        student_id: UUID, 
        page: int = 1, 
        page_size: int = 20
    ) -> PracticeQuestionsListResponse:
        """Get practice questions available to the student"""
        # Get student's classrooms to determine accessible questions
        classroom_assignments = await self.classroom_student_repo.get_classrooms_by_student(student_id)
        
        if not classroom_assignments:
            return PracticeQuestionsListResponse(
                questions=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False
            )

        # Get classroom details to find teachers
        classroom_ids = [assignment.classroom_id for assignment in classroom_assignments]
        
        from sqlalchemy import select, and_, or_
        from sqlalchemy.orm import selectinload
        from src.Models.DBSchemes.Schemes.associations import ClassRoom
        from src.Models.DBSchemes.Schemes.question_models import QuestionPractice
        
        # Get all classrooms student is enrolled in
        result = await self.session.execute(
            select(ClassRoom)
            .where(ClassRoom.classroom_id.in_(classroom_ids))
            .options(
                selectinload(ClassRoom.subject),
                selectinload(ClassRoom.teacher),
                selectinload(ClassRoom.term)
            )
        )
        classrooms = result.scalars().all()
        
        # Get unique teacher_id and term_id combinations
        teacher_term_pairs = [(classroom.teacher_id, classroom.term_id) for classroom in classrooms]
        
        if not teacher_term_pairs:
            return PracticeQuestionsListResponse(
                questions=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False
            )

        # Build query for practice questions from student's teachers
        conditions = []
        for teacher_id, term_id in teacher_term_pairs:
            conditions.append(
                and_(
                    QuestionPractice.teacher_id == teacher_id,
                    QuestionPractice.term_id == term_id
                )
            )

        offset = (page - 1) * page_size

        # Get practice questions
        result = await self.session.execute(
            select(QuestionPractice)
            .where(or_(*conditions))
            .options(
                selectinload(QuestionPractice.answers),
                selectinload(QuestionPractice.teacher),
                selectinload(QuestionPractice.term)
            )
            .offset(offset)
            .limit(page_size)
        )
        practice_questions = result.scalars().all()

        # Count total questions
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(QuestionPractice.practice_id))
            .where(or_(*conditions))
        )
        total_count = result.scalar() or 0

        # Check which questions student has already answered
        from src.Models.repositories.student_response_repository import PracticeQuestionResponseRepository
        response_repo = PracticeQuestionResponseRepository(self.session)
        
        questions = []
        for question in practice_questions:
            # Check if already answered
            existing_response = await response_repo.get_by_student_and_practice(
                student_id, question.practice_id
            )
            
            # Find subject name from classrooms
            subject_name = "Unknown"
            for classroom in classrooms:
                if (classroom.teacher_id == question.teacher_id and 
                    classroom.term_id == question.term_id):
                    subject_name = classroom.subject.name if classroom.subject else "Unknown"
                    break

            # Format answers (hide correct answer)
            answers = [
                {
                    "answer_id": str(answer.answer_id),
                    "answer_text": answer.answer_text
                }
                for answer in question.answers
            ]

            questions.append(PracticeQuestionForStudentResponse(
                practice_id=question.practice_id,
                content=question.content,
                difficulty=question.difficulty,
                teacher_name=question.teacher.name if question.teacher else "Unknown",
                subject_name=subject_name,
                answers=answers,
                already_answered=existing_response is not None
            ))

        return PracticeQuestionsListResponse(
            questions=questions,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=(offset + page_size) < total_count
        )

    async def get_exams(
        self, 
        student_id: UUID, 
        page: int = 1, 
        page_size: int = 20
    ) -> ExamsListResponse:
        """Get exams available to the student"""
        # Get student's classrooms to determine accessible exams
        classroom_assignments = await self.classroom_student_repo.get_classrooms_by_student(student_id)
        
        if not classroom_assignments:
            return ExamsListResponse(
                exams=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False
            )

        # Get classroom details
        classroom_ids = [assignment.classroom_id for assignment in classroom_assignments]
        
        from sqlalchemy import select, and_, or_
        from sqlalchemy.orm import selectinload
        from src.Models.DBSchemes.Schemes.associations import ClassRoom
        from src.Models.DBSchemes.Schemes.exam_models import Exam
        
        result = await self.session.execute(
            select(ClassRoom)
            .where(ClassRoom.classroom_id.in_(classroom_ids))
            .options(
                selectinload(ClassRoom.subject),
                selectinload(ClassRoom.teacher),
                selectinload(ClassRoom.term)
            )
        )
        classrooms = result.scalars().all()
        
        # Get unique teacher_id and term_id combinations
        teacher_term_pairs = [(classroom.teacher_id, classroom.term_id) for classroom in classrooms]
        
        if not teacher_term_pairs:
            return ExamsListResponse(
                exams=[],
                total_count=0,
                page=page,
                page_size=page_size,
                has_more=False
            )

        # Build query for exams from student's teachers
        conditions = []
        for teacher_id, term_id in teacher_term_pairs:
            conditions.append(
                and_(
                    Exam.teacher_id == teacher_id,
                    Exam.term_id == term_id
                )
            )

        offset = (page - 1) * page_size

        # Get exams
        result = await self.session.execute(
            select(Exam)
            .where(or_(*conditions))
            .options(
                selectinload(Exam.teacher),
                selectinload(Exam.term),
                selectinload(Exam.question_exams)
            )
            .offset(offset)
            .limit(page_size)
        )
        exams = result.scalars().all()

        # Count total exams
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(Exam.exam_id))
            .where(or_(*conditions))
        )
        total_count = result.scalar() or 0

        # Check which exams student has already taken and calculate scores
        from src.Models.repositories.student_response_repository import ExamQuestionResponseRepository
        exam_response_repo = ExamQuestionResponseRepository(self.session)
        
        exam_list = []
        for exam in exams:
            # Check if already taken
            exam_responses = await exam_response_repo.get_exam_responses(student_id, exam.exam_id)
            already_taken = len(exam_responses) > 0
            
            # Calculate score if taken
            score = None
            if already_taken:
                correct_answers = sum(1 for response in exam_responses if response.is_correct)
                total_questions = len(exam_responses)
                score = (correct_answers / total_questions * 100) if total_questions > 0 else 0

            # Find subject name from classrooms
            subject_name = "Unknown"
            for classroom in classrooms:
                if (classroom.teacher_id == exam.teacher_id and 
                    classroom.term_id == exam.term_id):
                    subject_name = classroom.subject.name if classroom.subject else "Unknown"
                    break

            exam_list.append(ExamForStudentResponse(
                exam_id=exam.exam_id,
                title=exam.title,
                date=exam.date,
                teacher_name=exam.teacher.name if exam.teacher else "Unknown",
                subject_name=subject_name,
                questions_count=len(exam.question_exams),
                already_taken=already_taken,
                score=score
            ))

        return ExamsListResponse(
            exams=exam_list,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=(offset + page_size) < total_count
        )
