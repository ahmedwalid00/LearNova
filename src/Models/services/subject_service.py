"""
Service for Subject business logic.
Handles subject management and lesson associations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.repositories.subject_repository import SubjectRepository
from src.Models.repositories.lesson_repository import LessonRepository
from src.Api.Schemes.admin import (
    SubjectCreateModel,
    SubjectUpdateModel,
    SubjectResponseModel,
    SubjectListResponseModel
)


class SubjectService:
    """Service for subject business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.subject_repo = SubjectRepository(session)
        self.lesson_repo = LessonRepository(session)

    async def create_subject(self, subject_data: SubjectCreateModel) -> SubjectResponseModel:
        """Create a new subject"""
        try:
            # Check if subject with same name already exists
            existing_subject = await self.subject_repo.get_by_name(subject_data.name)
            if existing_subject:
                raise ValueError(f"Subject with name '{subject_data.name}' already exists")

            # Create using the dict() method with exclude_none to avoid None values
            subject_dict = subject_data.dict(exclude_none=True)
            subject = await self.subject_repo.create(**subject_dict)
            await self.session.flush()
            
            return SubjectResponseModel(
                subject_id=subject.subject_id,
                name=subject.name,
                description=subject.description,
                created_at=subject.created_at,
                updated_at=subject.updated_at
            )
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_subject(self, subject_id: UUID) -> Optional[SubjectResponseModel]:
        """Get subject by ID"""
        subject = await self.subject_repo.get_by_id(subject_id)
        if not subject:
            return None
            
        return SubjectResponseModel(
            subject_id=subject.subject_id,
            name=subject.name,
            description=subject.description,
            created_at=subject.created_at,
            updated_at=subject.updated_at
        )

    async def get_all_subjects(self, skip: int = 0, limit: int = 100) -> SubjectListResponseModel:
        """Get all subjects with pagination"""
        subjects = await self.subject_repo.get_all(offset=skip, limit=limit)
        total = await self.subject_repo.count()
        
        subject_responses = [
            SubjectResponseModel(
                subject_id=subject.subject_id,
                name=subject.name,
                description=subject.description,
                created_at=subject.created_at,
                updated_at=subject.updated_at
            )
            for subject in subjects
        ]
        
        return SubjectListResponseModel(
            subjects=subject_responses,
            total=total,
            page=(skip // limit) + 1,
            size=limit
        )

    async def get_subjects_with_lesson_counts(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get subjects with their lesson counts"""
        subjects_with_counts = await self.subject_repo.get_subjects_with_lessons_count(skip=skip, limit=limit)
        
        return [
            {
                "subject_id": str(subject_dict["subject_id"]),
                "name": subject_dict["name"],
                "description": subject_dict["description"],
                "lesson_count": subject_dict["lessons_count"],
                "created_at": subject_dict["created_at"],
                "updated_at": subject_dict["updated_at"]
            }
            for subject_dict in subjects_with_counts
        ]

    async def get_popular_subjects(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular subjects based on lesson count"""
        popular_subjects = await self.subject_repo.get_popular_subjects(limit=limit)
        
        return [
            {
                "subject_id": str(subject.subject_id),
                "name": subject.name,
                "description": subject.description,
                "popularity_rank": rank + 1,
                "created_at": subject.created_at,
                "updated_at": subject.updated_at
            }
            for rank, subject in enumerate(popular_subjects)
        ]

    async def get_subject_by_name(self, name: str) -> Optional[SubjectResponseModel]:
        """Get subject by name"""
        subject = await self.subject_repo.get_by_name(name)
        if not subject:
            return None
            
        return SubjectResponseModel(
            subject_id=subject.subject_id,
            name=subject.name,
            description=subject.description,
            created_at=subject.created_at,
            updated_at=subject.updated_at
        )

    async def update_subject(self, subject_id: UUID, update_data: SubjectUpdateModel) -> Optional[SubjectResponseModel]:
        """Update an existing subject"""
        try:
            # Check if subject exists
            existing_subject = await self.subject_repo.get_by_id(subject_id)
            if not existing_subject:
                return None

            # Check if name is being changed and if new name already exists
            if update_data.name and update_data.name != existing_subject.name:
                name_exists = await self.subject_repo.get_by_name(update_data.name)
                if name_exists:
                    raise ValueError(f"Subject with name '{update_data.name}' already exists")

            # Update only provided fields
            update_dict = update_data.dict(exclude_none=True)
            
            updated_subject = await self.subject_repo.update(subject_id, **update_dict)
            if not updated_subject:
                return None
                
            await self.session.flush()
            
            return SubjectResponseModel(
                subject_id=updated_subject.subject_id,
                name=updated_subject.name,
                description=updated_subject.description,
                created_at=updated_subject.created_at,
                updated_at=updated_subject.updated_at
            )
        except Exception as e:
            await self.session.rollback()
            raise e

    async def delete_subject(self, subject_id: UUID) -> bool:
        """Delete a subject"""
        try:
            # Check if subject has associated lessons
            lesson_count = await self.lesson_repo.count_by_subject_id(subject_id)
            if lesson_count > 0:
                raise ValueError(f"Cannot delete subject. It has {lesson_count} associated lessons")

            success = await self.subject_repo.delete(subject_id)
            if success:
                await self.session.flush()
            return success
        except Exception as e:
            await self.session.rollback()
            raise e

    async def search_subjects(self, query: str, skip: int = 0, limit: int = 100) -> SubjectListResponseModel:
        """Search subjects by name or description"""
        subjects = await self.subject_repo.search_by_name(query, skip=skip, limit=limit)
        total = await self.subject_repo.search_count(query)
        
        subject_responses = [
            SubjectResponseModel(
                subject_id=subject.subject_id,
                name=subject.name,
                description=subject.description,
                created_at=subject.created_at,
                updated_at=subject.updated_at
            )
            for subject in subjects
        ]
        
        return SubjectListResponseModel(
            subjects=subject_responses,
            total=total,
            page=(skip // limit) + 1,
            size=limit
        )

    async def get_subject_lessons(self, subject_id: UUID, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all lessons for a specific subject"""
        # Verify subject exists
        subject = await self.subject_repo.get_by_id(subject_id)
        if not subject:
            raise ValueError("Subject not found")
            
        lessons = await self.lesson_repo.get_by_subject_id(subject_id, skip=skip, limit=limit)
        total = await self.lesson_repo.count_by_subject_id(subject_id)
        
        return {
            "subject": SubjectResponseModel(
                subject_id=subject.subject_id,
                name=subject.name,
                description=subject.description,
                created_at=subject.created_at,
                updated_at=subject.updated_at
            ),
            "lessons": lessons,
            "total_lessons": total,
            "page": (skip // limit) + 1,
            "size": limit
        }

