# """
# Student Controller - Business Logic for Student Operations

# Handles student-specifi        # Verify student exists
#         student = await self.student_repo.get_by_id(student_id)
#         if not student:
#             raise ValueError("Student not found")erations including:
# - Retrieving student profile information
# - Accessing student's classrooms
# - Managing student analytics
# """

# from typing import List, Dict, Any, Optional
# from uuid import UUID
# from sqlalchemy.ext.asyncio import AsyncSession

# from src.Models.repositories.user_repository import StudentRepository
# from src.Models.repositories.classroom_repository import ClassroomRepository
# from src.Models.repositories.analytics_repository import AnalyticsRepository
# from src.Api.Schemes.student import (
#     StudentProfileResponse,
#     StudentClassroomResponse,
#     StudentAnalyticsResponse
# )
# from src.Enums.user_type_enums import UserTypeEnum


# class StudentController:
#     """Controller for handling student-related business logic"""
    
#     def __init__(self, db_session: AsyncSession):
#         self.db_session = db_session
#         self.student_repo = StudentRepository(db_session)
#         self.classroom_repo = ClassroomRepository(db_session)
#         self.analytics_repo = AnalyticsRepository(db_session)

#     async def get_student_profile(self, student_id: UUID) -> StudentProfileResponse:
#         """
#         Retrieve student profile information
        
#         Args:
#             student_id: UUID of the student
            
#         Returns:
#             StudentProfileResponse with student details
            
#         Raises:
#             ValueError: If student not found or not a student user type
#         """
#         # Get student user record
#         student = await self.student_repo.get_by_id(student_id)
#         if not student:
#             raise ValueError("Student not found")
        
#         # Get additional student metrics
#         total_classrooms = await self.classroom_repo.count_student_classrooms(student_id)
#         current_rating = await self.analytics_repo.get_student_current_rating(student_id)
        
#         return StudentProfileResponse(
#             user_id=student.student_id,
#             unique_id=student.unique_id,
#             name=student.name,
#             email=student.email,
#             user_type=UserTypeEnum.STUDENT,
#             rating=current_rating or 0.0,
#             total_classrooms=total_classrooms,
#             created_at=student.created_at,
#             is_verified=student.is_verified
#         )

#     async def get_student_classrooms(
#         self, 
#         student_id: UUID,
#         limit: int = 10,
#         offset: int = 0
#     ) -> List[StudentClassroomResponse]:
#         """
#         Get all classrooms the student is enrolled in
        
#         Args:
#             student_id: UUID of the student
#             limit: Maximum number of results to return
#             offset: Number of results to skip for pagination
            
#         Returns:
#             List of StudentClassroomResponse objects
            
#         Raises:
#             ValueError: If student not found
#         """
#         # Verify student exists
#         student = await self.student_repo.get_by_id(student_id)
#         if not student:
#             raise ValueError("Student not found")
        
#         # Get student's classrooms with details
#         classrooms = await self.classroom_repo.get_student_classrooms_with_details(
#             student_id=student_id,
#             limit=limit,
#             offset=offset
#         )
        
#         classroom_responses = []
#         for classroom_data in classrooms:
#             classroom, teacher_name, subject_name, lesson_count = classroom_data
            
#             # Get student's performance in this classroom
#             performance = await self.analytics_repo.get_student_classroom_performance(
#                 student_id=student_id,
#                 classroom_id=classroom.classroom_id
#             )
            
#             classroom_responses.append(StudentClassroomResponse(
#                 classroom_id=classroom.classroom_id,
#                 name=classroom.classroom_name or f"Classroom {classroom.classroom_id}",
#                 description=f"{subject_name} - {teacher_name}",  # Create description from subject and teacher
#                 subject_name=subject_name,
#                 teacher_name=teacher_name,
#                 lesson_count=lesson_count,
#                 student_grade=performance.get('average_grade', 0.0) if performance else 0.0,
#                 completion_rate=performance.get('completion_rate', 0.0) if performance else 0.0,
#                 created_at=classroom.created_at
#             ))
        
#         return classroom_responses

#     async def get_student_analytics(
#         self,
#         student_id: UUID,
#         period: str = "current_semester"
#     ) -> StudentAnalyticsResponse:
#         """
#         Get comprehensive analytics for a student
        
#         Args:
#             student_id: UUID of the student
#             period: Time period for analytics ("current_semester", "current_week", "all_time")
            
#         Returns:
#             StudentAnalyticsResponse with performance metrics
            
#         Raises:
#             ValueError: If student not found or invalid period
#         """
#         # Verify student exists
#         student = await self.student_repo.get_by_id(student_id)
#         if not student:
#             raise ValueError("Student not found")
        
#         # Validate period
#         valid_periods = ["current_semester", "current_week", "all_time"]
#         if period not in valid_periods:
#             raise ValueError(f"Invalid period. Must be one of: {valid_periods}")
        
#         # Get analytics data based on period
#         analytics = await self.analytics_repo.get_student_analytics(
#             student_id=student_id,
#             period=period
#         )
        
#         # Get subject-wise performance
#         subject_performance = await self.analytics_repo.get_student_subject_performance(
#             student_id=student_id,
#             period=period
#         )
        
#         # Get recent activity
#         recent_activities = await self.analytics_repo.get_student_recent_activities(
#             student_id=student_id,
#             limit=10
#         )
        
#         return StudentAnalyticsResponse(
#             student_id=student_id,
#             period=period,
#             overall_rating=analytics.get('overall_rating', 0.0),
#             average_grade=analytics.get('average_grade', 0.0),
#             total_assessments=analytics.get('total_assessments', 0),
#             completed_assessments=analytics.get('completed_assessments', 0),
#             total_lessons_accessed=analytics.get('total_lessons_accessed', 0),
#             study_time_hours=analytics.get('study_time_hours', 0.0),
#             chatbot_interactions=analytics.get('chatbot_interactions', 0),
#             subject_performance=subject_performance,
#             recent_activities=recent_activities,
#             strengths=analytics.get('strengths', []),
#             areas_for_improvement=analytics.get('areas_for_improvement', []),
#             recommendations=analytics.get('recommendations', [])
#         )

#     async def update_student_profile(
#         self,
#         student_id: UUID,
#         update_data: Dict[str, Any]
#     ) -> StudentProfileResponse:
#         """
#         Update student profile information
        
#         Args:
#             student_id: UUID of the student
#             update_data: Dictionary containing fields to update
            
#         Returns:
#             Updated StudentProfileResponse
            
#         Raises:
#             ValueError: If student not found or invalid update data
#         """
#         # Verify student exists
#         student = await self.student_repo.get_by_id(student_id)
#         if not student:
#             raise ValueError("Student not found")
        
#         # Define allowed fields for student profile updates
#         allowed_fields = {'name', 'email'}
        
#         # Filter update data to only allowed fields
#         filtered_data = {
#             key: value for key, value in update_data.items() 
#             if key in allowed_fields and value is not None
#         }
        
#         if not filtered_data:
#             raise ValueError("No valid fields provided for update")
        
#         # Update student record
#         updated_student = await self.student_repo.update(
#             student_id,
#             **filtered_data
#         )
        
#         if not updated_student:
#             raise ValueError("Failed to update student profile")
        
#         # Return updated profile
#         return await self.get_student_profile(student_id)
