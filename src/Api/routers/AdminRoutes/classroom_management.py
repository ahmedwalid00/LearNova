"""
Admin Routes for Classroom Management - Two-Step Workflow.

This module contains FastAPI routes for admin-only classroom management operations
using a two-step workflow: 1) Create classrooms, 2) Assign students.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.Api.dependencies import get_db_session, RoleChecker
from src.Controllers.classroom_controller import ClassRoomController
from src.Api.Schemes.classroom import (
    ClassRoomCreate,
    StudentAssignmentRequest,
    BulkStudentAssignmentRequest,
    ClassRoomStatsResponse,
    SuccessResponse
)
from src.Enums.user_type_enums import UserTypeEnum

# Create router with admin-only access
router = APIRouter(
    prefix="/classrooms",
    tags=["Admin - Classroom Management"],
    dependencies=[Depends(RoleChecker([UserTypeEnum.ADMIN.value]))]
)


# Step 1: Classroom Creation Routes
@router.post(
    "/create",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create Classroom (Step 1)",
    description="Create a new classroom with teacher, subject, and term assignment (without students)."
)
async def create_classroom(
    classroom_data: ClassRoomCreate,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Create a new classroom (Step 1 of two-step workflow).
    
    **Admin Only Endpoint**
    
    This endpoint allows admins to create classrooms by providing:
    - Teacher unique ID (e.g., "11001")
    - Subject ID
    - Academic term ID
    - Grade level
    - Optional classroom name
    
    Students are assigned separately in Step 2.
    Returns detailed classroom information.
    """
    controller = ClassRoomController(session)
    return await controller.create_classroom(classroom_data)


@router.get(
    "/",
    response_model=List[Dict[str, Any]],
    summary="Get All Classrooms",
    description="Get all classrooms with optional filters."
)
async def get_all_classrooms(
    term_id: Optional[UUID] = Query(None, description="Filter by term ID"),
    grade_level: Optional[str] = Query(None, description="Filter by grade level"),
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get all classrooms with optional filters.
    
    **Admin Only Endpoint**
    
    Retrieve all classrooms in the system, optionally filtered by:
    - Academic term ID
    - Grade level
    
    Returns detailed information for each classroom.
    """
    controller = ClassRoomController(session)
    return await controller.get_all_classrooms(term_id=term_id, grade_level=grade_level)


@router.get(
    "/search",
    response_model=List[Dict[str, Any]],
    summary="Search Classrooms",
    description="Search and filter classrooms with various criteria."
)
async def search_classrooms(
    grade_level: Optional[str] = Query(None, description="Filter by grade level"),
    term_id: Optional[UUID] = Query(None, description="Filter by term ID"),
    subject_id: Optional[UUID] = Query(None, description="Filter by subject ID"),
    teacher_unique_id: Optional[str] = Query(None, description="Filter by teacher unique ID"),
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Search classrooms with filters.
    
    **Admin Only Endpoint**
    
    Search and filter classrooms using various criteria:
    - Grade level (e.g., "Grade 12")
    - Term ID
    - Subject ID
    - Teacher unique ID
    
    Returns detailed classroom information for all matches.
    """
    controller = ClassRoomController(session)
    return await controller.search_classrooms(
        grade_level=grade_level,
        term_id=term_id,
        subject_id=subject_id,
        teacher_unique_id=teacher_unique_id
    )


@router.get(
    "/statistics",
    response_model=ClassRoomStatsResponse,
    summary="Get Classroom Statistics",
    description="Get comprehensive statistics about classroom assignments."
)
async def get_classroom_statistics(
    term_id: Optional[UUID] = Query(None, description="Optional term ID filter"),
    session: AsyncSession = Depends(get_db_session)
) -> ClassRoomStatsResponse:
    """
    Get classroom management statistics.
    
    **Admin Only Endpoint**
    
    Retrieve comprehensive statistics about classroom assignments including:
    - Total number of classrooms
    - Number of assigned students
    - Number of unique teachers
    - Number of unique subjects
    - List of grade levels
    
    Optionally filter by academic term.
    """
    controller = ClassRoomController(session)
    return await controller.get_classroom_statistics(term_id)


@router.get(
    "/{classroom_id}",
    response_model=Dict[str, Any],
    summary="Get Classroom Details",
    description="Get detailed information about a specific classroom."
)
async def get_classroom_details(
    classroom_id: UUID,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get detailed classroom information.
    
    **Admin Only Endpoint**
    
    Retrieve comprehensive information about a classroom including:
    - Teacher details
    - Subject details
    - Academic term details
    - Grade level and classroom name
    - Creation and update timestamps
    - Assigned students (if any)
    """
    controller = ClassRoomController(session)
    return await controller.get_classroom_details(classroom_id)


@router.put(
    "/{classroom_id}/teacher",
    response_model=Dict[str, Any],
    summary="Update Classroom Teacher",
    description="Update the teacher assigned to a classroom."
)
async def update_classroom_teacher(
    classroom_id: UUID,
    new_teacher_unique_id: str = Query(..., description="New teacher's unique ID"),
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Update the teacher for a classroom.
    
    **Admin Only Endpoint**
    
    Change the teacher assigned to a classroom. This affects all students
    currently assigned to this classroom.
    """
    controller = ClassRoomController(session)
    return await controller.update_classroom_teacher(classroom_id, new_teacher_unique_id)


# Step 2: Student Assignment Routes
@router.post(
    "/assign-student",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Assign Student to Classroom (Step 2)",
    description="Assign a student to an existing classroom."
)
async def assign_student_to_classroom(
    assignment_request: StudentAssignmentRequest,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Assign a student to an existing classroom (Step 2 of two-step workflow).
    
    **Admin Only Endpoint**
    
    This endpoint allows admins to assign students to existing classrooms by providing:
    - Student unique ID (e.g., "22001")
    - Classroom ID (from Step 1)
    
    Returns assignment information including student and classroom details.
    """
    controller = ClassRoomController(session)
    return await controller.assign_student_to_classroom(assignment_request)


@router.post(
    "/bulk-assign-students",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Assign Students",
    description="Assign multiple students to classrooms in a single operation."
)
async def bulk_assign_students(
    bulk_request: BulkStudentAssignmentRequest,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Bulk assign multiple students to classrooms.
    
    **Admin Only Endpoint**
    
    Allows admins to assign multiple students to their respective classrooms
    in a single API call. If any assignments fail, the endpoint returns details
    about both successful and failed assignments.
    
    Request body should contain a list of StudentAssignmentRequest objects.
    """
    if not bulk_request.assignments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No assignments provided"
        )
    
    if len(bulk_request.assignments) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 assignments allowed per request"
        )
    
    controller = ClassRoomController(session)
    return await controller.bulk_assign_students(bulk_request)


@router.delete(
    "/{classroom_id}/students/{student_unique_id}",
    response_model=SuccessResponse,
    summary="Remove Student from Classroom",
    description="Remove a student from a specific classroom."
)
async def remove_student_from_classroom(
    classroom_id: UUID,
    student_unique_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> SuccessResponse:
    """
    Remove a student from a classroom.
    
    **Admin Only Endpoint**
    
    Remove a student from a specific classroom assignment by providing:
    - Classroom ID
    - Student unique ID
    """
    controller = ClassRoomController(session)
    return await controller.remove_student_from_classroom(classroom_id, student_unique_id)


@router.get(
    "/{classroom_id}/students",
    response_model=List[Dict[str, Any]],
    summary="Get Classroom Students",
    description="Get all students assigned to a specific classroom."
)
async def get_classroom_students(
    classroom_id: UUID,
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get all students assigned to a classroom.
    
    **Admin Only Endpoint**
    
    Retrieve a list of all students currently assigned to a specific classroom.
    Includes student details and assignment information.
    """
    controller = ClassRoomController(session)
    return await controller.get_classroom_students(classroom_id)


@router.get(
    "/students/{student_unique_id}/classrooms",
    response_model=List[Dict[str, Any]],
    summary="Get Student's Classrooms",
    description="Get all classrooms a student is assigned to."
)
async def get_student_classrooms(
    student_unique_id: str,
    term_id: Optional[UUID] = Query(None, description="Optional term filter"),
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get all classrooms a student is assigned to.
    
    **Admin Only Endpoint**
    
    Retrieve all classroom assignments for a student including:
    - All subjects they're enrolled in
    - Their teachers for each subject
    - Grade levels and classroom names
    - Academic terms
    
    Optionally filter by academic term.
    """
    controller = ClassRoomController(session)
    return await controller.get_student_classrooms(student_unique_id, term_id)


# Statistics Routes
@router.get(
    "/teachers/{teacher_unique_id}/classrooms",
    response_model=List[Dict[str, Any]],
    summary="Get Teacher's Classrooms",
    description="Get all classrooms assigned to a specific teacher."
)
async def get_teacher_classrooms(
    teacher_unique_id: str,
    term_id: Optional[UUID] = Query(None, description="Optional term filter"),
    subject_id: Optional[UUID] = Query(None, description="Optional subject filter"),
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get all classrooms for a specific teacher.
    
    **Admin Only Endpoint**
    
    Retrieve all classrooms assigned to a teacher, optionally filtered by:
    - Academic term ID
    - Subject ID
    
    Useful for:
    - Viewing teacher workloads
    - Managing class assignments
    - Planning schedule changes
    """
    controller = ClassRoomController(session)
    return await controller.get_teacher_classrooms(
        teacher_unique_id=teacher_unique_id,
        term_id=term_id,
        subject_id=subject_id
    )
