"""
Teacher Rating Repository

Repository for managing teacher ratings and feedback.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..DBSchemes.Schemes.teacher_rating_models import TeacherRating


class TeacherRatingRepository(BaseRepository[TeacherRating]):
    """Repository for teacher rating operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, TeacherRating)

    def get_model_specific_methods(self) -> List[str]:
        """Return model-specific method names"""
        return [
            "get_rating_by_student_teacher_classroom",
            "get_ratings_for_teacher",
            "get_teacher_rating_stats",
            "calculate_teacher_average_rating",
        ]

    async def get_rating_by_student_teacher_classroom(
        self, 
        student_id: UUID, 
        teacher_id: UUID, 
        classroom_id: UUID
    ) -> Optional[TeacherRating]:
        """Get existing rating by student for teacher in specific classroom"""
        result = await self.session.execute(
            select(TeacherRating)
            .where(
                and_(
                    TeacherRating.student_id == student_id,
                    TeacherRating.teacher_id == teacher_id,
                    TeacherRating.classroom_id == classroom_id
                )
            )
            .options(
                selectinload(TeacherRating.teacher),
                selectinload(TeacherRating.student),
                selectinload(TeacherRating.classroom)
            )
        )
        return result.scalar_one_or_none()

    async def get_ratings_for_teacher(
        self, 
        teacher_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[TeacherRating]:
        """Get all ratings for a specific teacher"""
        result = await self.session.execute(
            select(TeacherRating)
            .where(TeacherRating.teacher_id == teacher_id)
            .options(
                selectinload(TeacherRating.student),
                selectinload(TeacherRating.classroom),
                selectinload(TeacherRating.term)
            )
            .order_by(desc(TeacherRating.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_teacher_rating_stats(self, teacher_id: UUID) -> Dict[str, Any]:
        """Get comprehensive rating statistics for a teacher"""
        result = await self.session.execute(
            select(
                func.count(TeacherRating.rating_id).label('total_ratings'),
                func.avg(TeacherRating.rating_points).label('average_rating'),
                func.min(TeacherRating.rating_points).label('min_rating'),
                func.max(TeacherRating.rating_points).label('max_rating'),
                func.sum(
                    func.case(
                        (TeacherRating.rating_points == 5, 1),
                        else_=0
                    )
                ).label('five_star_count'),
                func.sum(
                    func.case(
                        (TeacherRating.rating_points == 4, 1),
                        else_=0
                    )
                ).label('four_star_count'),
                func.sum(
                    func.case(
                        (TeacherRating.rating_points == 3, 1),
                        else_=0
                    )
                ).label('three_star_count'),
                func.sum(
                    func.case(
                        (TeacherRating.rating_points == 2, 1),
                        else_=0
                    )
                ).label('two_star_count'),
                func.sum(
                    func.case(
                        (TeacherRating.rating_points == 1, 1),
                        else_=0
                    )
                ).label('one_star_count')
            ).where(TeacherRating.teacher_id == teacher_id)
        )
        stats = result.one()
        
        total_ratings = stats.total_ratings or 0
        
        return {
            'total_ratings': total_ratings,
            'average_rating': float(stats.average_rating) if stats.average_rating else 0.0,
            'min_rating': stats.min_rating or 0,
            'max_rating': stats.max_rating or 0,
            'rating_distribution': {
                '5_star': stats.five_star_count or 0,
                '4_star': stats.four_star_count or 0,
                '3_star': stats.three_star_count or 0,
                '2_star': stats.two_star_count or 0,
                '1_star': stats.one_star_count or 0
            }
        }

    async def calculate_teacher_average_rating(self, teacher_id: UUID) -> float:
        """Calculate the current average rating for a teacher"""
        result = await self.session.execute(
            select(func.avg(TeacherRating.rating_points))
            .where(TeacherRating.teacher_id == teacher_id)
        )
        average = result.scalar()
        return float(average) if average else 0.0
