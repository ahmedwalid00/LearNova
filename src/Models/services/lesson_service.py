"""
Lesson service for orchestrating lesson-related business logic.

This module contains the LessonService class that handles complex
operations involving lessons and lesson chunks.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ..repositories.lesson_repository import LessonRepository, LessonChunkRepository
from ..repositories.user_repository import TeacherRepository


class LessonService:
    """
    Service class for lesson-related business logic.
    
    This class orchestrates operations involving lessons, chunks,
    and related user interactions.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the service with database session."""
        self.session = session
        self.lesson_repo = LessonRepository(session)
        self.chunk_repo = LessonChunkRepository(session)
        self.teacher_repo = TeacherRepository(session)
    
    async def create_lesson_with_chunks(
        self, 
        lesson_data: Dict[str, Any], 
        chunks_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a lesson with its associated chunks in a single transaction.
        
        Args:
            lesson_data: Dictionary with lesson fields
            chunks_data: List of dictionaries with chunk data
            
        Returns:
            Dict with created lesson and chunks
        """
        try:
            # Create the lesson
            lesson = await self.lesson_repo.create(**lesson_data)
            
            # Create chunks
            chunks = []
            for chunk_data in chunks_data:
                chunk_data['lesson_id'] = lesson.lesson_id
                chunk = await self.chunk_repo.create(**chunk_data)
                chunks.append(chunk)
            
            return {
                "lesson": lesson,
                "chunks": chunks,
                "total_chunks": len(chunks)
            }
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_lesson_with_chunks(self, lesson_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a lesson with all its chunks.
        
        Args:
            lesson_id: UUID of the lesson
            
        Returns:
            Dict with lesson and chunks or None if not found
        """
        lesson = await self.lesson_repo.get_by_id(lesson_id)
        if not lesson:
            return None
        
        chunks = await self.chunk_repo.get_by_lesson_id(lesson_id)
        
        return {
            "lesson": lesson,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }
    
    async def get_teacher_lessons_with_stats(self, teacher_id: UUID) -> Dict[str, Any]:
        """
        Get all lessons for a teacher with statistics.
        
        Args:
            teacher_id: UUID of the teacher
            
        Returns:
            Dict with lessons and statistics
        """
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        lessons = await self.lesson_repo.get_by_teacher_id(teacher_id)
        
        # Calculate statistics
        total_lessons = len(lessons)
        rated_lessons = [l for l in lessons if l.rating is not None]
        avg_rating = sum(l.rating for l in rated_lessons) / len(rated_lessons) if rated_lessons else 0
        
        # Get chunk counts for each lesson
        lessons_with_chunks = []
        for lesson in lessons:
            chunk_count = await self.chunk_repo.get_chunk_count_for_lesson(lesson.lesson_id)
            lessons_with_chunks.append({
                "lesson": lesson,
                "chunk_count": chunk_count
            })
        
        return {
            "teacher": teacher,
            "lessons": lessons_with_chunks,
            "statistics": {
                "total_lessons": total_lessons,
                "average_rating": round(avg_rating, 2),
                "rated_lessons_count": len(rated_lessons)
            }
        }
    
    async def search_lessons_by_content(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search lessons by content in chunks.
        
        Args:
            search_term: Term to search for in chunk content
            
        Returns:
            List of lessons with matching chunks
        """
        # This would typically use full-text search or vector similarity
        # For now, we'll implement a basic text search
        from sqlalchemy import text
        
        # Get chunks that contain the search term
        result = await self.session.execute(
            text("""
                SELECT DISTINCT l.lesson_id, l.title, l.rating, 
                       lc.chunk_id, lc.chunk_number, lc.chunk_text
                FROM lessons l
                JOIN lesson_chunks lc ON l.lesson_id = lc.lesson_id
                WHERE LOWER(lc.chunk_text) LIKE LOWER(:search_term)
                ORDER BY l.title, lc.chunk_number
            """),
            {"search_term": f"%{search_term}%"}
        )
        
        # Group results by lesson
        lessons_dict = {}
        for row in result:
            lesson_id = str(row.lesson_id)
            if lesson_id not in lessons_dict:
                lessons_dict[lesson_id] = {
                    "lesson_id": row.lesson_id,
                    "title": row.title,
                    "rating": row.rating,
                    "matching_chunks": []
                }
            
            lessons_dict[lesson_id]["matching_chunks"].append({
                "chunk_id": row.chunk_id,
                "chunk_number": row.chunk_number,
                "chunk_text": row.chunk_text[:200] + "..." if len(row.chunk_text) > 200 else row.chunk_text
            })
        
        return list(lessons_dict.values())
    
    async def update_lesson_rating(self, lesson_id: UUID, new_rating: float) -> bool:
        """
        Update lesson rating and recalculate teacher's average rating.
        
        Args:
            lesson_id: UUID of the lesson
            new_rating: New rating value
            
        Returns:
            True if updated successfully
        """
        try:
            # Update lesson rating
            lesson = await self.lesson_repo.update(lesson_id, rating=new_rating)
            if not lesson:
                return False
            
            # Get all lessons for this teacher to recalculate average
            teacher_lessons = await self.lesson_repo.get_by_teacher_id(lesson.teacher_id)
            rated_lessons = [l for l in teacher_lessons if l.rating is not None]
            
            if rated_lessons:
                avg_rating = sum(l.rating for l in rated_lessons) / len(rated_lessons)
                await self.teacher_repo.update(lesson.teacher_id, rating=avg_rating)
            
            return True
        except Exception:
            await self.session.rollback()
            return False
