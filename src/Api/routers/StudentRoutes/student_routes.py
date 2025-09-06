# """
# Student API Routes

# FastAPI routes for student-related operations including:
# - Profile management
# - Classroom access
# - Analytics viewing
# """

# from typing import List
# from uuid import UUID
# from fastapi import APIRouter, Depends, HTTPException, status, Query
# from sqlalchemy.ext.asyncio import AsyncSession

# from src.Api.dependencies import get_current_user, get_db_session
# from src.Controllers.student_controller import StudentController
# from src.Api.dependencies import RoleChecker
# from src.Api.Schemes.student import (
#     StudentProfileResponse,
#     StudentClassroomResponse,
#     StudentClassroomListResponse,
#     StudentAnalyticsResponse,
#     StudentProfileUpdateRequest
# )
# from src.Enums.user_type_enums import UserTypeEnum


# # Create router with prefix and tags
# router = APIRouter(
#     prefix="/api/v1/students",
#     tags=["Students"],
#     responses={
#         401: {"description": "Unauthorized - Invalid or missing authentication"},
#         403: {"description": "Forbidden - Insufficient permissions"},
#         404: {"description": "Not Found - Student not found"},
#         500: {"description": "Internal Server Error"}
#     }
# )

# student_admin_checker = RoleChecker(allowed_roles=[UserTypeEnum.STUDENT.value , UserTypeEnum.ADMIN.value])



# @router.get("/me/profile", response_model=StudentProfileResponse)
# async def get_my_profile(
#     current_user: dict = Depends(get_current_user),
#     _: bool = Depends(student_admin_checker),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     Get current student's profile information
    
#     Returns:
#         StudentProfileResponse: Complete student profile with statistics
#     """
    
#     try:
#         controller = StudentController(db_session)
#         student_id = UUID(current_user["id"])  # Convert string ID to UUID
#         profile = await controller.get_student_profile(student_id)
#         return profile
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=str(e)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve student profile"
#         )


# @router.put("/me/profile", response_model=StudentProfileResponse)
# async def update_my_profile(
#     update_data: StudentProfileUpdateRequest,
#     current_user: dict = Depends(get_current_user),
#     _: bool = Depends(student_admin_checker),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     Update current student's profile information
    
#     Args:
#         update_data: Fields to update in student profile
        
#     Returns:
#         StudentProfileResponse: Updated student profile
#     """
    
#     try:
#         controller = StudentController(db_session)
        
#         # Convert Pydantic model to dict, excluding None values
#         update_dict = update_data.dict(exclude_none=True)
        
#         if not update_dict:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="No valid fields provided for update"
#             )
        
#         # Update student profile
#         updated_profile = await controller.update_student_profile(
#             student_id=UUID(current_user["id"]),
#             update_data=update_data
#         )
#         return updated_profile
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to update student profile"
#         )


# @router.get("/me/classrooms", response_model=StudentClassroomListResponse)
# async def get_my_classrooms(
#     page: int = Query(1, ge=1, description="Page number"),
#     page_size: int = Query(10, ge=1, le=100, description="Items per page"),
#     current_user: dict = Depends(get_current_user),
#     _: bool = Depends(student_admin_checker),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     Get current student's enrolled classrooms with pagination
    
#     Args:
#         page: Page number (1-based)
#         page_size: Number of classrooms per page
        
#     Returns:
#         StudentClassroomListResponse: Paginated list of student's classrooms
#     """
    
#     try:
#         controller = StudentController(db_session)
        
#         # Calculate offset for pagination
#         offset = (page - 1) * page_size
        
#         # Get classrooms
#         classrooms = await controller.get_student_classrooms(
#             student_id=UUID(current_user["id"]),
#             limit=page_size,
#             offset=offset
#         )
        
#         # Get total count for pagination info
#         # Note: This would require a separate method in the controller
#         # For now, we'll estimate based on returned results
#         total_count = len(classrooms) + offset
#         has_more = len(classrooms) == page_size
        
#         return StudentClassroomListResponse(
#             classrooms=classrooms,
#             total_count=total_count,
#             page=page,
#             page_size=page_size,
#             has_more=has_more
#         )
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=str(e)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve student classrooms"
#         )


# @router.get("/me/classrooms/{classroom_id}", response_model=StudentClassroomResponse)
# async def get_my_classroom_details(
#     classroom_id: UUID,
#     current_user: dict = Depends(get_current_user),
#     _: bool = Depends(student_admin_checker),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     Get detailed information about a specific classroom the student is enrolled in
    
#     Args:
#         classroom_id: UUID of the classroom
        
#     Returns:
#         StudentClassroomResponse: Detailed classroom information
#     """
    
#     try:
#         controller = StudentController(db_session)
        
#         # Get all student's classrooms and find the specific one
#         classrooms = await controller.get_student_classrooms(
#             student_id=UUID(current_user["id"]),
#             limit=1000  # Large limit to get all classrooms
#         )
        
#         # Find the requested classroom
#         classroom = next(
#             (c for c in classrooms if c.classroom_id == classroom_id),
#             None
#         )
        
#         if not classroom:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Classroom not found or not enrolled"
#             )
        
#         return classroom
#     except HTTPException:
#         raise
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=str(e)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve classroom details"
#         )


# @router.get("/me/analytics", response_model=StudentAnalyticsResponse)
# async def get_my_analytics(
#     period: str = Query("current_semester", description="Analytics period"),
#     current_user: dict = Depends(get_current_user),
#     _: bool = Depends(student_admin_checker),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     Get comprehensive analytics for the current student
    
#     Args:
#         period: Time period for analytics ("current_semester", "current_week", "all_time")
        
#     Returns:
#         StudentAnalyticsResponse: Comprehensive performance analytics
#     """
    
#     try:
#         controller = StudentController(db_session)
#         analytics = await controller.get_student_analytics(
#             student_id=UUID(current_user["id"]),
#             period=period
#         )
#         return analytics
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to retrieve student analytics"
#         )


# # Future endpoints that could be added:

# @router.get("/me/roadmap")
# async def get_my_roadmap(
#     current_user: dict = Depends(get_current_user),
#     _: bool = Depends(student_admin_checker),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     Get personalized learning roadmap for the student
    
#     Note: This endpoint is a placeholder for future implementation
#     """
    
#     return {
#         "message": "Roadmap feature coming soon",
#         "student_id": current_user["id"]
#     }


# @router.get("/me/practice")
# async def get_practice_questions(
#     current_user: dict = Depends(get_current_user),
#     _: bool = Depends(student_admin_checker),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     Get practice questions for the student
    
#     Note: This endpoint is a placeholder for future implementation
#     """
    
#     return {
#         "message": "Practice questions feature coming soon",
#         "student_id": current_user["id"]
#     }


# @router.get("/me/chatbot/history")
# async def get_chatbot_history(
#     current_user: dict = Depends(get_current_user),
#     _: bool = Depends(student_admin_checker),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     Get student's chatbot interaction history
    
#     Note: This endpoint is a placeholder for future implementation
#     """
    
#     return {
#         "message": "Chatbot history feature coming soon",
#         "student_id": current_user["id"]
#     }
