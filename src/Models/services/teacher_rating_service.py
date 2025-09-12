"""
Teacher Rating Service

Service for managing teacher ratings and feedback.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from ..repositories.teacher_rating_repository import TeacherRatingRepository
from ..repositories.user_repository import TeacherRepository
from ..repositories.classroom_repository import ClassRoomRepository
from ..repositories.classroom_student_repository import ClassRoomStudentRepository
from src.Api.Schemes.teachers import TeacherProfileResponse , TeacherProfileUpdateRequest , TeacherClassroomListResponse , TeacherClassroomResponse
from ..DBSchemes.Schemes.teacher_rating_models import TeacherRating


class TeacherRatingService:
    """Service for teacher rating operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.teacher_rating_repo = TeacherRatingRepository(session)
        self.teacher_repo = TeacherRepository(session)
        self.classroom_repo = ClassRoomRepository(session)
        self.classroom_student_repo = ClassRoomStudentRepository(session)

    async def submit_rating(
        self,
        student_id: UUID,
        teacher_id: UUID,
        classroom_id: UUID,
        rating_points: int,
        feedback_text: Optional[str] = None,
        term_id: Optional[UUID] = None
    ) -> TeacherRating:
        """Submit or update a teacher rating by a student"""
        
        try:
            print(f"DEBUG SERVICE: Starting submit_rating - student: {student_id}, teacher: {teacher_id}, classroom: {classroom_id}")
            
            # Validate rating points
            if rating_points < 1 or rating_points > 5:
                raise ValueError("Rating points must be between 1 and 5")
            
            print(f"DEBUG SERVICE: Rating points validated: {rating_points}")
            
            # Check if rating already exists
            existing_rating = await self.teacher_rating_repo.get_rating_by_student_teacher_classroom(
                student_id=student_id,
                teacher_id=teacher_id,
                classroom_id=classroom_id
            )
            
            print(f"DEBUG SERVICE: Existing rating check complete: {existing_rating is not None}")
            
            if existing_rating:
                # Update existing rating
                update_data = {"rating_points": rating_points}
                if feedback_text is not None:
                    update_data["feedback_text"] = feedback_text
                if term_id is not None:
                    update_data["term_id"] = term_id
                
                print(f"DEBUG SERVICE: Updating existing rating with data: {update_data}")
                rating = await self.teacher_rating_repo.update(existing_rating.id, **update_data)
            else:
                # Create new rating
                rating_data = {
                    "student_id": student_id,
                    "teacher_id": teacher_id,
                    "classroom_id": classroom_id,
                    "rating_points": rating_points,
                    "feedback_text": feedback_text,
                    "term_id": term_id
                }
                print(f"DEBUG SERVICE: Creating new rating with data: {rating_data}")
                rating = await self.teacher_rating_repo.create(rating_data)
            
            print(f"DEBUG SERVICE: Rating operation completed successfully")
            
            # Update teacher's overall rating
            await self._update_teacher_overall_rating(teacher_id)
            
            print(f"DEBUG SERVICE: Teacher overall rating updated")
            
            return rating
        except Exception as e:
            print(f"DEBUG SERVICE: Error in submit_rating: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        else:
            # Create new rating
            rating_data = {
                "student_id": student_id,
                "teacher_id": teacher_id,
                "classroom_id": classroom_id,
                "rating_points": rating_points,
                "feedback_text": feedback_text,
                "term_id": term_id
            }
            rating = await self.teacher_rating_repo.create(rating_data)
        
        # Update teacher's overall rating
        await self._update_teacher_overall_rating(teacher_id)
        
        return rating

    async def get_teacher_ratings(
        self,
        teacher_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> list[TeacherRating]:
        """Get all ratings for a teacher"""
        return await self.teacher_rating_repo.get_ratings_for_teacher(
            teacher_id=teacher_id,
            limit=limit,
            offset=offset
        )

    async def get_teacher_rating_stats(self, teacher_id: UUID) -> Dict[str, Any]:
        """Get comprehensive rating statistics for a teacher"""
        return await self.teacher_rating_repo.get_teacher_rating_stats(teacher_id)

    async def _update_teacher_overall_rating(self, teacher_id: UUID) -> None:
        """Update the teacher's overall rating field"""
        average_rating = await self.teacher_rating_repo.calculate_teacher_average_rating(teacher_id)
        
        # Update teacher record
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if teacher:
            teacher.rating = round(average_rating, 2)
            await self.teacher_repo.update(teacher)

    async def can_student_rate_teacher(
        self,
        student_id: UUID,
        teacher_id: UUID,
        classroom_id: UUID
    ) -> bool:
        """Check if a student can rate a teacher (e.g., if they share a classroom)"""
        # This would need to check if the student is enrolled in the classroom
        # and the teacher teaches that classroom
        # For now, we'll return True, but this should be implemented based on
        # classroom enrollment logic
        return True
    
    async def get_teacher_profile(self, teacher_id: UUID) -> TeacherProfileResponse:
        """Get teacher profile information"""
        try:
            # Get teacher from database
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found"
                )
            
            # Count teacher's classrooms
            from sqlalchemy import select, func
            from src.Models.DBSchemes.Schemes.associations import ClassRoom
            
            result = await self.session.execute(
                select(func.count(ClassRoom.classroom_id))
                .where(ClassRoom.teacher_id == teacher_id)
            )
            total_classrooms = result.scalar() or 0

            # get teacher's subject
            classrooms = await self.classroom_repo.get_classrooms_by_teacher(teacher_id=teacher_id)
            if classrooms:
                teacher.subject_id = classrooms[0].subject_id
            
            # Prepare response data
            teacher_data = {
                "teacher_id": teacher.teacher_id,
                "unique_id": teacher.unique_id,
                "name": teacher.name,
                "email": teacher.email,
                "is_verified": teacher.is_verified,
                "rating": float(teacher.rating) if teacher.rating else None,
                "subject_id": teacher.subject_id,
                "term_id": teacher.term_id,
                "admin_id": teacher.admin_id,
                "total_classrooms": total_classrooms
            }
            
            return TeacherProfileResponse(**teacher_data)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve teacher profile: {str(e)}"
            )
    
    async def update_teacher_profile(
        self, 
        teacher_id: UUID, 
        update_data: TeacherProfileUpdateRequest
    ) -> TeacherProfileResponse:
        """Update teacher profile information"""
        try:
            # Get teacher from database
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found"
                )
            
            # Update only provided fields
            update_dict = update_data.model_dump(exclude_none=True)
            if not update_dict:
                # No updates provided, return current profile
                return await self.get_teacher_profile(teacher_id)
            
            # Check if email is being updated and if it already exists
            if "email" in update_dict:
                existing_teacher = await self.teacher_repo.get_by_email(update_dict["email"])
                if existing_teacher and existing_teacher.teacher_id != teacher_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists for another teacher"
                    )
            
            # Update teacher data
            updated_teacher = await self.teacher_repo.update(teacher_id, **update_dict)
            if not updated_teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found"
                )
            
            # Return updated profile
            return await self.get_teacher_profile(teacher_id)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update teacher profile: {str(e)}"
            )
        
    async def get_teacher_classrooms(
        self, 
        teacher_id: UUID,
        page: int = 1,
        page_size: int = 10
    ) -> TeacherClassroomListResponse:
        """Get all classrooms for a teacher with pagination"""
        try:
            # Verify teacher exists
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not teacher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Teacher not found"
                )
            
            # Get teacher's classrooms using session directly
            from sqlalchemy import select
            from src.Models.DBSchemes.Schemes.associations import ClassRoom
            
            result = await self.session.execute(
                select(ClassRoom).where(ClassRoom.teacher_id == teacher_id)
            )
            classrooms = result.scalars().all()
            
            # Calculate pagination
            total_count = len(classrooms)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_classrooms = classrooms[start_idx:end_idx]
            
            # Convert to response format
            classroom_responses = []
            for classroom in paginated_classrooms:
                # Get student count for this classroom
                try:
                    from sqlalchemy import select, func
                    from src.Models.DBSchemes.Schemes.associations import ClassRoomStudent
                    
                    result = await self.session.execute(
                        select(func.count(ClassRoomStudent.classroom_student_id))
                        .where(ClassRoomStudent.classroom_id == classroom.classroom_id)
                    )
                    student_count = result.scalar() or 0
                except Exception:
                    student_count = 0
                
                classroom_data = {
                    "classroom_id": classroom.classroom_id,
                    "subject_name": "Unknown Subject",  # Default value for now
                    "term_id": classroom.term_id,
                    "grade_level": classroom.grade_level,
                    "classroom_name": classroom.classroom_name,
                    "student_count": student_count
                }
                classroom_responses.append(TeacherClassroomResponse(**classroom_data))
            
            return TeacherClassroomListResponse(
                classrooms=classroom_responses,
                total_count=total_count,
                page=page,
                limit=page_size
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve teacher classrooms: {str(e)}"
            )


