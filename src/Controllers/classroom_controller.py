"""
Classroom Controller for handling classroom management business logic orchestration.
This controller coordinates between classroom services and routes using a two-step workflow.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.Models.services.classroom_service import ClassRoomService
from src.Api.Schemes.classroom import (
    ClassRoomCreate,
    StudentAssignmentRequest,
    BulkStudentAssignmentRequest,
    ClassRoomSearchFilters,
    ClassRoomStatsResponse,
    SuccessResponse
)


class ClassRoomController:
    """Controller for classroom management operations - Two-step workflow"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.classroom_service = ClassRoomService(db)

    # Step 1: Classroom Creation Methods
    async def create_classroom(
        self, 
        classroom_data: ClassRoomCreate
    ) -> Dict[str, Any]:
        """
        Create a new classroom without students (Step 1).
        
        Args:
            classroom_data: Classroom creation details
            
        Returns:
            Dict: Detailed classroom information
            
        Raises:
            HTTPException: If teacher, subject, or term not found
        """
        try:
            classroom_details = await self.classroom_service.create_classroom(
                classroom_data
            )
            return classroom_details
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create classroom: {str(e)}"
            )

    async def get_all_classrooms(
        self,
        term_id: Optional[UUID] = None,
        grade_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all classrooms with optional filters.
        
        Args:
            term_id: Optional term filter
            grade_level: Optional grade level filter
            
        Returns:
            List[Dict]: List of classroom details
        """
        try:
            classrooms = await self.classroom_service.get_all_classrooms(
                term_id=term_id,
                grade_level=grade_level
            )
            return classrooms
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get classrooms: {str(e)}"
            )

    async def get_classroom_details(self, classroom_id: UUID) -> Dict[str, Any]:
        """
        Get detailed information about a specific classroom.
        
        Args:
            classroom_id: UUID of the classroom
            
        Returns:
            Dict: Detailed classroom information
        """
        try:
            classroom_details = await self.classroom_service.get_classroom_details(
                classroom_id
            )
            return classroom_details
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get classroom details: {str(e)}"
            )

    async def update_classroom_teacher(
        self, 
        classroom_id: UUID,
        new_teacher_unique_id: str
    ) -> Dict[str, Any]:
        """
        Update the teacher for a classroom.
        
        Args:
            classroom_id: UUID of the classroom
            new_teacher_unique_id: Unique ID of the new teacher
            
        Returns:
            Dict: Updated classroom information
        """
        try:
            updated_classroom = await self.classroom_service.update_classroom_teacher(
                classroom_id=classroom_id,
                new_teacher_unique_id=new_teacher_unique_id
            )
            return updated_classroom
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update classroom teacher: {str(e)}"
            )

    # Step 2: Student Assignment Methods
    async def assign_student_to_classroom(
        self, 
        assignment_request: StudentAssignmentRequest
    ) -> Dict[str, Any]:
        """
        Assign a student to an existing classroom (Step 2).
        
        Args:
            assignment_request: Student assignment details
            
        Returns:
            Dict: Assignment information
            
        Raises:
            HTTPException: If student or classroom not found
        """
        try:
            assignment_details = await self.classroom_service.assign_student_to_classroom(
                assignment_request
            )
            return assignment_details
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to assign student to classroom: {str(e)}"
            )

    async def bulk_assign_students(
        self, 
        bulk_request: BulkStudentAssignmentRequest
    ) -> Dict[str, Any]:
        """
        Bulk assign multiple students to classrooms.
        
        Args:
            bulk_request: Bulk assignment request
            
        Returns:
            Dict containing successful assignments and any errors
        """
        try:
            results = await self.classroom_service.bulk_assign_students(bulk_request)
            return {
                "message": f"Successfully assigned {results['successful_count']} students to classrooms",
                "successful_assignments": results["successful_assignments"],
                "failed_assignments": results["failed_assignments"],
                "successful_count": results["successful_count"],
                "failed_count": results["failed_count"]
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk assignment failed: {str(e)}"
            )

    async def remove_student_from_classroom(
        self, 
        classroom_id: UUID,
        student_unique_id: str
    ) -> SuccessResponse:
        """
        Remove a student from a classroom.
        
        Args:
            classroom_id: UUID of the classroom
            student_unique_id: Unique ID of the student
            
        Returns:
            SuccessResponse: Success message
        """
        try:
            result = await self.classroom_service.remove_student_from_classroom(
                classroom_id=classroom_id,
                student_unique_id=student_unique_id
            )
            return SuccessResponse(message=result["message"])
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove student from classroom: {str(e)}"
            )

    async def get_classroom_students(self, classroom_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all students assigned to a classroom.
        
        Args:
            classroom_id: UUID of the classroom
            
        Returns:
            List[Dict]: List of students in the classroom
        """
        try:
            students = await self.classroom_service.get_classroom_students(classroom_id)
            return students
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get classroom students: {str(e)}"
            )

    async def get_student_classrooms(
        self, 
        student_unique_id: str,
        term_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all classrooms a student is assigned to.
        
        Args:
            student_unique_id: Unique ID of the student
            term_id: Optional term filter
            
        Returns:
            List[Dict]: List of classrooms the student is in
        """
        try:
            classrooms = await self.classroom_service.get_student_classrooms(
                student_unique_id=student_unique_id,
                term_id=term_id
            )
            return classrooms
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get student classrooms: {str(e)}"
            )

    # Search and Statistics Methods
    async def search_classrooms(
        self,
        grade_level: Optional[str] = None,
        term_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        teacher_unique_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search classrooms with filters.
        
        Args:
            grade_level: Optional grade level filter
            term_id: Optional term filter
            subject_id: Optional subject filter
            teacher_unique_id: Optional teacher filter
            
        Returns:
            List[Dict]: List of matching classrooms
        """
        try:
            classrooms = await self.classroom_service.search_classrooms(
                grade_level=grade_level,
                term_id=term_id,
                subject_id=subject_id,
                teacher_unique_id=teacher_unique_id
            )
            return classrooms
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search classrooms: {str(e)}"
            )

    async def get_teacher_classrooms(
        self, 
        teacher_unique_id: str,
        term_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all classrooms for a specific teacher.
        
        Args:
            teacher_unique_id: Unique ID of the teacher
            term_id: Optional term filter
            subject_id: Optional subject filter
            
        Returns:
            List[Dict]: List of teacher's classrooms
        """
        try:
            classrooms = await self.classroom_service.get_teacher_classrooms(
                teacher_unique_id=teacher_unique_id,
                term_id=term_id,
                subject_id=subject_id
            )
            return classrooms
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get teacher classrooms: {str(e)}"
            )

    async def get_classroom_statistics(
        self, 
        term_id: Optional[UUID] = None
    ) -> ClassRoomStatsResponse:
        """
        Get classroom statistics.
        
        Args:
            term_id: Optional term filter
            
        Returns:
            ClassRoomStatsResponse: Classroom statistics
        """
        try:
            stats = await self.classroom_service.get_classroom_statistics(term_id)
            return stats
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get classroom statistics: {str(e)}"
            )
