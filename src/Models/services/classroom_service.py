"""
Service for ClassRoom business logic.
Handles classroom creation and student assignment management in a two-step workflow.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..repositories.classroom_repository import ClassRoomRepository
from ..repositories.classroom_student_repository import ClassRoomStudentRepository
from ..repositories.user_repository import StudentRepository, TeacherRepository
from ..repositories.subject_repository import SubjectRepository
from ..repositories.academic_term_repository import AcademicTermRepository
from src.Api.Schemes.classroom import (
    ClassRoomCreate,
    StudentAssignmentRequest,
    BulkStudentAssignmentRequest,
    ClassRoomSearchFilters,
    ClassRoomStatsResponse
)


class ClassRoomService:
    """Service class for classroom management operations - Two-step workflow"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.classroom_repo = ClassRoomRepository(db)
        self.classroom_student_repo = ClassRoomStudentRepository(db)
        self.student_repo = StudentRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.subject_repo = SubjectRepository(db)
        self.term_repo = AcademicTermRepository(db)

    # Step 1: Classroom Creation Methods
    async def create_classroom(
        self, 
        classroom_data: ClassRoomCreate
    ) -> Dict[str, Any]:
        """Create a new classroom without students (Step 1)"""
        
        # Get teacher by unique_id
        teacher = await self.teacher_repo.get_by_unique_id(classroom_data.teacher_unique_id)
        if not teacher:
            raise HTTPException(
                status_code=404,
                detail=f"Teacher with unique ID {classroom_data.teacher_unique_id} not found"
            )

        # Get subject by ID (fixing the bug - was using get_by_name)
        subject = await self.subject_repo.get_by_id(classroom_data.subject_id)
        if not subject:
            raise HTTPException(
                status_code=404,
                detail=f"Subject with ID {classroom_data.subject_id} not found"
            )

        # Get term by ID (fixing the bug - was using get_by_name)
        term = await self.term_repo.get_by_id(classroom_data.term_id)
        if not term:
            raise HTTPException(
                status_code=404,
                detail=f"Academic term with ID {classroom_data.term_id} not found"
            )

        # Create classroom
        classroom = await self.classroom_repo.create_classroom(
            subject_id=subject.subject_id,
            teacher_id=teacher.teacher_id,
            term_id=term.term_id,
            grade_level=classroom_data.grade_level,
            classroom_name=classroom_data.classroom_name
        )

        return await self.classroom_repo.get_classroom_with_details(classroom.classroom_id)

    async def get_all_classrooms(
        self,
        term_id: Optional[UUID] = None,
        grade_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all classrooms with optional filters"""
        if grade_level:
            classrooms = await self.classroom_repo.get_classrooms_by_grade(
                grade_level=grade_level,
                term_id=term_id
            )
        elif term_id:
            classrooms = await self.classroom_repo.get_classrooms_by_term(term_id)
        else:
            classrooms = await self.classroom_repo.get_all()

        classroom_details = []
        for classroom in classrooms:
            details = await self.classroom_repo.get_classroom_with_details(classroom.classroom_id)
            if details:
                classroom_details.append(details)

        return classroom_details

    async def get_classroom_details(self, classroom_id: UUID) -> Dict[str, Any]:
        """Get detailed classroom information"""
        classroom_details = await self.classroom_repo.get_classroom_with_details(classroom_id)
        if not classroom_details:
            raise HTTPException(
                status_code=404,
                detail=f"Classroom with ID {classroom_id} not found"
            )
        return classroom_details

    async def update_classroom_teacher(
        self, 
        classroom_id: UUID,
        new_teacher_unique_id: str
    ) -> Dict[str, Any]:
        """Update the teacher for a classroom"""
        
        # Get teacher by unique_id
        teacher = await self.teacher_repo.get_by_unique_id(new_teacher_unique_id)
        if not teacher:
            raise HTTPException(
                status_code=404,
                detail=f"Teacher with unique ID {new_teacher_unique_id} not found"
            )

        # Update classroom
        updated_classroom = await self.classroom_repo.update_teacher_for_classroom(
            classroom_id=classroom_id,
            new_teacher_id=teacher.teacher_id
        )

        if not updated_classroom:
            raise HTTPException(
                status_code=404,
                detail=f"Classroom with ID {classroom_id} not found"
            )

        return await self.classroom_repo.get_classroom_with_details(classroom_id)

    # Step 2: Student Assignment Methods
    async def assign_student_to_classroom(
        self, 
        assignment_request: StudentAssignmentRequest
    ) -> Dict[str, Any]:
        """Assign a student to an existing classroom (Step 2)"""
        
        # Get student by unique_id
        student = await self.student_repo.get_by_unique_id(assignment_request.student_unique_id)
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Student with unique ID {assignment_request.student_unique_id} not found"
            )

        # Verify classroom exists
        classroom = await self.classroom_repo.get_by_id(assignment_request.classroom_id)
        if not classroom:
            raise HTTPException(
                status_code=404,
                detail=f"Classroom with ID {assignment_request.classroom_id} not found"
            )

        # Assign student to classroom
        assignment = await self.classroom_student_repo.assign_student_to_classroom(
            student_id=student.student_id,
            classroom_id=assignment_request.classroom_id
        )

        return {
            "assignment_id": str(assignment.classroom_student_id),
            "student_id": str(student.student_id),
            "student_unique_id": student.unique_id,
            "student_name": student.name,
            "classroom_id": str(assignment_request.classroom_id),
            "assigned_at": assignment.created_at.isoformat() if assignment.created_at else None
        }

    async def bulk_assign_students(
        self, 
        bulk_request: BulkStudentAssignmentRequest
    ) -> Dict[str, Any]:
        """Bulk assign multiple students to classrooms"""
        results = []
        errors = []

        for i, assignment in enumerate(bulk_request.assignments):
            try:
                result = await self.assign_student_to_classroom(assignment)
                results.append(result)
            except HTTPException as e:
                errors.append({
                    "index": i,
                    "assignment": assignment.dict(),
                    "error": e.detail
                })

        return {
            "successful_assignments": results,
            "failed_assignments": errors,
            "successful_count": len(results),
            "failed_count": len(errors)
        }

    async def remove_student_from_classroom(
        self, 
        classroom_id: UUID,
        student_unique_id: str
    ) -> Dict[str, str]:
        """Remove a student from a classroom"""
        
        # Get student by unique_id
        student = await self.student_repo.get_by_unique_id(student_unique_id)
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Student with unique ID {student_unique_id} not found"
            )

        # Remove student from classroom
        success = await self.classroom_student_repo.remove_student_from_classroom(
            student_id=student.student_id,
            classroom_id=classroom_id
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Student assignment to classroom not found"
            )

        return {
            "message": f"Successfully removed student {student_unique_id} from classroom"
        }

    async def get_classroom_students(self, classroom_id: UUID) -> List[Dict[str, Any]]:
        """Get all students assigned to a classroom"""
        
        # Verify classroom exists
        classroom = await self.classroom_repo.get_by_id(classroom_id)
        if not classroom:
            raise HTTPException(
                status_code=404,
                detail=f"Classroom with ID {classroom_id} not found"
            )

        # Get student assignments
        assignments = await self.classroom_student_repo.get_students_by_classroom(classroom_id)
        
        # Get detailed student information
        students = []
        for assignment in assignments:
            student = await self.student_repo.get_by_id(assignment.student_id)
            if student:
                students.append({
                    "assignment_id": str(assignment.classroom_student_id),
                    "student_id": str(student.student_id),
                    "student_unique_id": student.unique_id,
                    "student_name": student.name,
                    "student_email": student.email,
                    "assigned_at": assignment.created_at.isoformat() if assignment.created_at else None
                })
        
        return students

    async def get_student_classrooms(
        self, 
        student_unique_id: str,
        term_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all classrooms a student is assigned to"""
        
        # Get student by unique_id
        student = await self.student_repo.get_by_unique_id(student_unique_id)
        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Student with unique ID {student_unique_id} not found"
            )

        # Get student's classroom assignments
        assignments = await self.classroom_student_repo.get_classrooms_by_student(
            student_id=student.student_id
        )

        classroom_details = []
        for assignment in assignments:
            classroom_id = assignment.classroom_id
            details = await self.classroom_repo.get_classroom_with_details(classroom_id)
            if details:
                # Filter by term if specified
                if term_id is None or details["term"]["term_id"] == str(term_id):
                    classroom_details.append(details)

        return classroom_details

    # Search and Statistics Methods
    async def search_classrooms(
        self, 
        grade_level: Optional[str] = None,
        term_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None,
        teacher_unique_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search classrooms with filters"""
        
        teacher_id = None
        if teacher_unique_id:
            teacher = await self.teacher_repo.get_by_unique_id(teacher_unique_id)
            if teacher:
                teacher_id = teacher.teacher_id

        # Search classrooms
        classrooms = await self.classroom_repo.search_classrooms(
            grade_level=grade_level,
            term_id=term_id,
            subject_id=subject_id,
            teacher_id=teacher_id
        )

        classroom_details = []
        for classroom in classrooms:
            details = await self.classroom_repo.get_classroom_with_details(classroom.classroom_id)
            if details:
                classroom_details.append(details)

        return classroom_details

    async def get_teacher_classrooms(
        self, 
        teacher_unique_id: str,
        term_id: Optional[UUID] = None,
        subject_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all classrooms for a specific teacher"""
        
        # Get teacher by unique_id
        teacher = await self.teacher_repo.get_by_unique_id(teacher_unique_id)
        if not teacher:
            raise HTTPException(
                status_code=404,
                detail=f"Teacher with unique ID {teacher_unique_id} not found"
            )

        # Get teacher's classrooms
        classrooms = await self.classroom_repo.get_classrooms_by_teacher(
            teacher_id=teacher.teacher_id,
            term_id=term_id,
            subject_id=subject_id
        )

        classroom_details = []
        for classroom in classrooms:
            details = await self.classroom_repo.get_classroom_with_details(classroom.classroom_id)
            if details:
                classroom_details.append(details)

        return classroom_details

    async def get_classroom_statistics(
        self, 
        term_id: Optional[UUID] = None
    ) -> ClassRoomStatsResponse:
        """Get classroom statistics"""
        
        # Get all classrooms for the term
        if term_id:
            classrooms = await self.classroom_repo.get_classrooms_by_term(term_id)
        else:
            classrooms = await self.classroom_repo.get_all()

        # Calculate statistics
        total_classrooms = len(classrooms)
        grades = set()
        teachers = set()
        subjects = set()
        total_students = 0

        for classroom in classrooms:
            grades.add(classroom.grade_level)
            teachers.add(classroom.teacher_id)
            subjects.add(classroom.subject_id)
            
            # Count students in this classroom
            students = await self.classroom_student_repo.get_students_by_classroom(classroom.classroom_id)
            total_students += len(students)

        return ClassRoomStatsResponse(
            total_classrooms=total_classrooms,
            students_count=total_students,
            teachers_count=len(teachers),
            subjects_count=len(subjects),
            grades=list(grades)
        )
