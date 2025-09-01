from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_
from sqlalchemy.future import select
from .base import BaseRepository
from ..DBSchemes.Schemes.associations import ClassRoomStudent


class ClassRoomStudentRepository(BaseRepository[ClassRoomStudent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ClassRoomStudent)

    def get_model_specific_methods(self) -> List[str]:
        """Return list of model-specific methods"""
        return [
            "assign_student_to_classroom",
            "remove_student_from_classroom",
            "get_students_by_classroom",
            "get_classrooms_by_student",
            "bulk_assign_students",
            "is_student_in_classroom"
        ]

    async def assign_student_to_classroom(
        self, 
        classroom_id: UUID, 
        student_id: UUID
    ) -> ClassRoomStudent:
        """Assign a student to a classroom"""
        # Check if assignment already exists
        existing = await self.get_by_classroom_and_student(classroom_id, student_id)
        if existing:
            return existing

        assignment_data = {
            "classroom_id": classroom_id,
            "student_id": student_id
        }
        return await self.create(**assignment_data)

    async def remove_student_from_classroom(
        self, 
        classroom_id: UUID, 
        student_id: UUID
    ) -> bool:
        """Remove a student from a classroom"""
        assignment = await self.get_by_classroom_and_student(classroom_id, student_id)
        if assignment:
            await self.delete(assignment.classroom_student_id)
            return True
        return False

    async def get_by_classroom_and_student(
        self, 
        classroom_id: UUID, 
        student_id: UUID
    ) -> Optional[ClassRoomStudent]:
        """Get assignment by classroom and student"""
        result = await self.session.execute(
            select(self.model).filter(
                and_(
                    self.model.classroom_id == classroom_id,
                    self.model.student_id == student_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_students_by_classroom(self, classroom_id: UUID) -> List[ClassRoomStudent]:
        """Get all students assigned to a classroom"""
        result = await self.session.execute(
            select(self.model).filter(self.model.classroom_id == classroom_id)
        )
        return result.scalars().all()

    async def get_classrooms_by_student(self, student_id: UUID) -> List[ClassRoomStudent]:
        """Get all classrooms a student is assigned to"""
        result = await self.session.execute(
            select(self.model).filter(self.model.student_id == student_id)
        )
        return result.scalars().all()

    async def bulk_assign_students(
        self, 
        assignments: List[Dict[str, UUID]]
    ) -> List[ClassRoomStudent]:
        """Bulk assign students to classrooms"""
        results = []
        for assignment in assignments:
            classroom_assignment = await self.assign_student_to_classroom(
                classroom_id=assignment["classroom_id"],
                student_id=assignment["student_id"]
            )
            results.append(classroom_assignment)
        return results

    async def is_student_in_classroom(
        self, 
        classroom_id: UUID, 
        student_id: UUID
    ) -> bool:
        """Check if a student is assigned to a classroom"""
        assignment = await self.get_by_classroom_and_student(classroom_id, student_id)
        return assignment is not None
