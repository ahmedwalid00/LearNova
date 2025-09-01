from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_
from sqlalchemy.future import select
from .base import BaseRepository
from ..DBSchemes.Schemes.associations import ClassRoom
from ..DBSchemes.Schemes.user_models import Teacher
from ..DBSchemes.Schemes.subject import Subject
from ..DBSchemes.Schemes.academic_term import AcademicTerm


class ClassRoomRepository(BaseRepository[ClassRoom]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ClassRoom)

    def get_model_specific_methods(self) -> List[str]:
        """Return list of model-specific methods"""
        return [
            "create_classroom",
            "get_classrooms_by_grade",
            "get_classrooms_by_teacher",
            "get_classrooms_by_subject",
            "get_classrooms_by_term",
            "get_classroom_with_details",
            "update_teacher_for_classroom",
            "search_classrooms"
        ]

    async def create_classroom(
        self,
        subject_id: UUID,
        teacher_id: UUID,
        term_id: UUID,
        grade_level: str,
        classroom_name: Optional[str] = None
    ) -> ClassRoom:
        """Create a new classroom"""
        # Check if classroom already exists with same configuration
        existing = await self.get_by_configuration(
            subject_id, teacher_id, term_id, grade_level
        )
        if existing:
            return existing

        classroom_data = {
            "subject_id": subject_id,
            "teacher_id": teacher_id,
            "term_id": term_id,
            "grade_level": grade_level,
            "classroom_name": classroom_name
        }
        return await self.create(**classroom_data)

    async def get_by_configuration(
        self,
        subject_id: UUID,
        teacher_id: UUID,
        term_id: UUID,
        grade_level: str
    ) -> Optional[ClassRoom]:
        """Get classroom by configuration parameters"""
        result = await self.session.execute(
            select(self.model).filter(
                and_(
                    self.model.subject_id == subject_id,
                    self.model.teacher_id == teacher_id,
                    self.model.term_id == term_id,
                    self.model.grade_level == grade_level
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_classrooms_by_grade(
        self,
        grade_level: str,
        term_id: Optional[UUID] = None
    ) -> List[ClassRoom]:
        """Get all classrooms for a specific grade level"""
        query = select(self.model).filter(self.model.grade_level == grade_level)
        if term_id:
            query = query.filter(self.model.term_id == term_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_classrooms_by_teacher(
        self,
        teacher_id: UUID,
        term_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None
    ) -> List[ClassRoom]:
        """Get all classrooms for a specific teacher"""
        query = select(self.model).filter(self.model.teacher_id == teacher_id)
        if term_id:
            query = query.filter(self.model.term_id == term_id)
        if subject_id:
            query = query.filter(self.model.subject_id == subject_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_classrooms_by_subject(
        self,
        subject_id: UUID,
        term_id: Optional[UUID] = None
    ) -> List[ClassRoom]:
        """Get all classrooms for a specific subject"""
        query = select(self.model).filter(self.model.subject_id == subject_id)
        if term_id:
            query = query.filter(self.model.term_id == term_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_classrooms_by_term(self, term_id: UUID) -> List[ClassRoom]:
        """Get all classrooms for a specific term"""
        result = await self.session.execute(
            select(self.model).filter(self.model.term_id == term_id)
        )
        return result.scalars().all()

    async def get_classroom_with_details(self, classroom_id: UUID) -> Optional[Dict[str, Any]]:
        """Get classroom with full details including related entities"""
        result = await self.session.execute(
            select(self.model).filter(self.model.classroom_id == classroom_id)
        )
        classroom = result.scalar_one_or_none()
        
        if not classroom:
            return None

        # Get teacher details
        teacher_result = await self.session.execute(
            select(Teacher).filter(Teacher.teacher_id == classroom.teacher_id)
        )
        teacher = teacher_result.scalar_one_or_none()

        # Get subject details
        subject_result = await self.session.execute(
            select(Subject).filter(Subject.subject_id == classroom.subject_id)
        )
        subject = subject_result.scalar_one_or_none()

        # Get term details
        term_result = await self.session.execute(
            select(AcademicTerm).filter(AcademicTerm.term_id == classroom.term_id)
        )
        term = term_result.scalar_one_or_none()

        return {
            "classroom_id": str(classroom.classroom_id),
            "grade_level": classroom.grade_level,
            "classroom_name": classroom.classroom_name,
            "subject_id": str(classroom.subject_id),
            "teacher_id": str(classroom.teacher_id),
            "term_id": str(classroom.term_id),
            "teacher": {
                "teacher_id": str(teacher.teacher_id),
                "unique_id": teacher.unique_id,
                "name": teacher.name,
                "email": teacher.email
            } if teacher else None,
            "subject": {
                "subject_id": str(subject.subject_id),
                "name": subject.name,
                "description": subject.description
            } if subject else None,
            "term": {
                "term_id": str(term.term_id),
                "name": term.name,
                "start_date": term.start_date.isoformat() if term.start_date else None,
                "end_date": term.end_date.isoformat() if term.end_date else None
            } if term else None,
            "created_at": classroom.created_at.isoformat() if classroom.created_at else None,
            "updated_at": classroom.updated_at.isoformat() if classroom.updated_at else None
        }

    async def update_teacher_for_classroom(
        self,
        classroom_id: UUID,
        new_teacher_id: UUID
    ) -> Optional[ClassRoom]:
        """Update the teacher for a classroom"""
        classroom = await self.get_by_id(classroom_id)
        if classroom:
            await self.update(classroom_id, teacher_id=new_teacher_id)
            return await self.get_by_id(classroom_id)
        return None

    async def search_classrooms(
        self,
        grade_level: Optional[str] = None,
        term_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        teacher_id: Optional[UUID] = None
    ) -> List[ClassRoom]:
        """Search classrooms with filters"""
        query = select(self.model)
        
        if grade_level:
            query = query.filter(self.model.grade_level == grade_level)
        if term_id:
            query = query.filter(self.model.term_id == term_id)
        if subject_id:
            query = query.filter(self.model.subject_id == subject_id)
        if teacher_id:
            query = query.filter(self.model.teacher_id == teacher_id)
            
        result = await self.session.execute(query)
        return result.scalars().all()
