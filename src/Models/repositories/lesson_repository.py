"""
Lesson-related repository classes.

This module contains repository classes for lesson models:
Lesson and LessonChunk.
"""

from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import and_, desc , func
from sqlalchemy.orm import selectinload
from uuid import UUID

from .base import BaseRepository
from ..DBSchemes.Schemes.lesson import Lesson, LessonChunk


class LessonRepository(BaseRepository[Lesson]):
    """Repository for Lesson model operations."""
    
    def __init__(self, session):
        super().__init__(session, Lesson)
    
    async def get_by_teacher_id(self, teacher_id: UUID) -> List[Lesson]:
        """Get all lessons by teacher ID."""
        result = await self.session.execute(
            select(Lesson).where(Lesson.teacher_id == teacher_id)
        )
        return result.scalars().all()
    
    async def get_by_subject_id(self, subject_id: UUID, skip: int = 0, limit: int = 100) -> List[Lesson]:
        """Get all lessons by subject ID with pagination."""
        result = await self.session.execute(
            select(Lesson)
            .where(Lesson.subject_id == subject_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_by_subject_id(self, subject_id: UUID) -> int:
        """Count lessons by subject ID."""
        result = await self.session.execute(
            select(func.count(Lesson.lesson_id)).where(Lesson.subject_id == subject_id)
        )
        return result.scalar() or 0
    
    async def get_by_term_id(self, term_id: UUID) -> List[Lesson]:
        """Get all lessons by term ID."""
        result = await self.session.execute(
            select(Lesson).where(Lesson.term_id == term_id)
        )
        return result.scalars().all()
    
    async def get_by_teacher_and_subject(self, teacher_id: UUID, subject_id: UUID) -> List[Lesson]:
        """Get lessons by teacher and subject."""
        result = await self.session.execute(
            select(Lesson).where(
                and_(
                    Lesson.teacher_id == teacher_id,
                    Lesson.subject_id == subject_id
                )
            )
        )
        return result.scalars().all()
    
    async def get_by_rating_range(self, min_rating: float, max_rating: float) -> List[Lesson]:
        """Get lessons within a specific rating range."""
        result = await self.session.execute(
            select(Lesson).where(
                and_(
                    Lesson.rating >= min_rating,
                    Lesson.rating <= max_rating
                )
            )
        )
        return result.scalars().all()
    
    async def get_top_rated_lessons(self, limit: int = 10) -> List[Lesson]:
        """Get top rated lessons."""
        result = await self.session.execute(
            select(Lesson)
            .where(Lesson.rating.is_not(None))
            .order_by(desc(Lesson.rating))
            .limit(limit)
        )
        return result.scalars().all()
    
    def get_model_specific_methods(self):
        """Return list of lesson-specific methods."""
        return [
            "get_by_teacher_id",
            "get_by_subject_id",
            "get_by_term_id",
            "get_by_teacher_and_subject",
            "get_by_rating_range",
            "get_top_rated_lessons"
        ]


class LessonChunkRepository(BaseRepository[LessonChunk]):
    """Repository for LessonChunk model operations."""
    
    def __init__(self, session):
        super().__init__(session, LessonChunk)
    
    async def get_by_lesson_id(
        self, 
        lesson_id: UUID, 
        offset: int = 0, 
        limit: int = 20
    ) -> List[LessonChunk]:
        """
        Get paginated chunks for a specific lesson, ordered by chunk number.
        Uses eager loading to avoid N+1 problem.
        """

        result = await self.session.execute(
            select(LessonChunk)
            .options(selectinload(LessonChunk.lesson))  # eager load related lesson
            .where(LessonChunk.lesson_id == lesson_id)
            .order_by(LessonChunk.chunk_number)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_chunk_number(self, lesson_id: UUID, chunk_number: int) -> Optional[LessonChunk]:
        """Get a specific chunk by lesson ID and chunk number."""
        result = await self.session.execute(
            select(LessonChunk).where(
                and_(
                    LessonChunk.lesson_id == lesson_id,
                    LessonChunk.chunk_number == chunk_number
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_chunks_with_metadata(self, lesson_id: UUID) -> List[LessonChunk]:
        """Get all chunks for a lesson that have metadata."""
        result = await self.session.execute(
            select(LessonChunk).where(
                and_(
                    LessonChunk.lesson_id == lesson_id,
                    LessonChunk.chunk_metadata.is_not(None)
                )
            ).order_by(LessonChunk.chunk_number)
        )
        return result.scalars().all()
    
    async def get_chunk_count_for_lesson(self, lesson_id: UUID) -> int:
        """Get the total number of chunks for a lesson."""
        result = await self.session.execute(
            select(func.count(LessonChunk.chunk_id))
            .where(LessonChunk.lesson_id == lesson_id)
        )
        return result.scalar()

    async def insert_many_chunks(self, chunks: List[LessonChunk], batch_size: int = 100) -> List[LessonChunk]:
        """
        Insert many LessonChunk instances in batches.
        
        Args:
            chunks: List of LessonChunk instances to insert
            batch_size: Number of records per batch (default 100)
            
        Returns:
            List of created LessonChunk instances
            
        Raises:
            ValueError: If chunks is invalid or contains non-LessonChunk instances
        """
        if not chunks:
            return []
        
        if batch_size <= 0 or batch_size > 1000:
            raise ValueError("batch_size must be between 1 and 1000")
        
        # Validate all items are LessonChunk instances
        for idx, chunk in enumerate(chunks):
            if not isinstance(chunk, LessonChunk):
                raise ValueError(f"Item at index {idx} is not a LessonChunk instance")

        created: List[LessonChunk] = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            self.session.add_all(batch)
            await self.session.flush()   # send INSERTs without committing
            for inst in batch:
                try:
                    await self.session.refresh(inst)
                except Exception:
                    pass  # Best effort refresh
            created.extend(batch)

        return created
  


    
    def get_model_specific_methods(self):
        """Return list of lesson chunk-specific methods."""
        return [
            "get_by_lesson_id",
            "get_by_chunk_number",
            "get_chunks_with_metadata",
            "get_chunk_count_for_lesson",
            "insert_many_chunks"
        ]
