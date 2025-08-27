"""
Repository for Subject operations.
Handles database operations for subjects.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..DBSchemes.Schemes.subject import Subject
from ..DBSchemes.Schemes.lesson import Lesson


class SubjectRepository(BaseRepository[Subject]):
    """Repository for subject operations"""

    def __init__(self, session):
        super().__init__(session, Subject)

    async def get_by_name(self, name: str) -> Optional[Subject]:
        """Get subject by name"""
        result = await self.session.execute(
            select(Subject).where(Subject.name == name)
        )
        return result.scalar_one_or_none()

    async def search_by_name(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Subject]:
        """Search subjects by name"""
        result = await self.session.execute(
            select(Subject)
            .where(Subject.name.ilike(f"%{search_term}%"))
            .order_by(Subject.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_count(self, search_term: str) -> int:
        """Get count of subjects matching search term"""
        result = await self.session.execute(
            select(func.count(Subject.subject_id))
            .where(Subject.name.ilike(f"%{search_term}%"))
        )
        return result.scalar()

    async def exists_by_name(self, name: str, exclude_subject_id: UUID = None) -> bool:
        """Check if a subject with the given name exists"""
        query = select(Subject.subject_id).where(Subject.name == name)
        
        if exclude_subject_id:
            query = query.where(Subject.subject_id != exclude_subject_id)
            
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_subjects_with_lessons_count(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get subjects with their lesson count"""
        # Use join with lesson table to get actual lesson counts
        result = await self.session.execute(
            select(
                Subject.subject_id,
                Subject.name,
                Subject.description,
                Subject.created_at,
                Subject.updated_at,
                func.count(Lesson.lesson_id).label('lessons_count')
            )
            .outerjoin(Lesson, Subject.subject_id == Lesson.subject_id)
            .group_by(
                Subject.subject_id,
                Subject.name,
                Subject.description,
                Subject.created_at,
                Subject.updated_at
            )
            .order_by(Subject.name)
            .offset(skip)
            .limit(limit)
        )
        
        return [
            {
                "subject_id": row.subject_id,
                "name": row.name,
                "description": row.description,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "lessons_count": row.lessons_count or 0
            }
            for row in result
        ]

    async def get_popular_subjects(self, limit: int = 10) -> List[Subject]:
        """Get most popular subjects (those with most lessons)"""
        result = await self.session.execute(
            select(Subject)
            .outerjoin(Lesson, Subject.subject_id == Lesson.subject_id)
            .group_by(Subject.subject_id)
            .order_by(func.count(Lesson.lesson_id).desc(), Subject.name)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_create(self, subjects_data: List[dict]) -> List[Subject]:
        """Create multiple subjects at once"""
        subjects = [Subject(**data) for data in subjects_data]
        self.session.add_all(subjects)
        await self.session.flush()  # Use flush instead of commit for consistency
        
        # Refresh all subjects to get their IDs
        for subject in subjects:
            await self.session.refresh(subject)
            
        return subjects

    async def get_subjects_by_ids(self, subject_ids: List[UUID]) -> List[Subject]:
        """Get multiple subjects by their IDs"""
        result = await self.session.execute(
            select(Subject)
            .where(Subject.subject_id.in_(subject_ids))
            .order_by(Subject.name)
        )
        return list(result.scalars().all())

    def get_model_specific_methods(self):
        """Return list of subject-specific methods."""
        return [
            "get_by_name",
            "search_by_name", 
            "search_count",
            "exists_by_name",
            "get_subjects_with_lessons_count",
            "get_popular_subjects",
            "bulk_create",
            "get_subjects_by_ids"
        ]
