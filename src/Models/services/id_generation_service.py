from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.Enums.user_type_enums import UserIDPrefix , UserTypeEnum



class IDGenerationService:
    """Service for generating unique human-readable IDs for different user types"""
    
    @staticmethod
    async def generate_student_id(session: AsyncSession) -> str:
        """
        Generate next available student ID (22001, 22002, etc.)
        
        Args:
            session: Database session
            
        Returns:
            str: Generated student ID (e.g., "22001")
        """
        # Get the highest existing student ID using raw SQL to avoid import issues
        result = await session.execute(
            text("""
                SELECT unique_id 
                FROM students 
                WHERE unique_id LIKE :prefix
                ORDER BY unique_id DESC 
                LIMIT 1
            """),
            {"prefix": f"{UserIDPrefix.STUDENT.value}%"}
        )
        last_id = result.scalar_one_or_none()
        
        if last_id:
            try:
                last_number = int(last_id[len(UserIDPrefix.STUDENT.value):])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        return f"{UserIDPrefix.STUDENT.value}{next_number:03d}"

    @staticmethod
    async def generate_teacher_id(session: AsyncSession) -> str:
        """
        Generate next available teacher ID (11001, 11002, etc.)
        """
        result = await session.execute(
            text("""
                SELECT unique_id 
                FROM teachers 
                WHERE unique_id LIKE :prefix
                ORDER BY unique_id DESC 
                LIMIT 1
            """),
            {"prefix": f"{UserIDPrefix.TEACHER.value}%" }
        )
        last_id = result.scalar_one_or_none()
        
        if last_id:
            try:
                last_number = int(last_id[len(UserIDPrefix.TEACHER.value):])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        return f"{UserIDPrefix.TEACHER.value}{next_number:03d}"

    @staticmethod
    def generate_parent_id(student_unique_id: str) -> str:
        """
        Generate parent ID based on student ID (P22001 for student 22001)
        """
        return f"{UserIDPrefix.PARENT.value}{student_unique_id}"

    @staticmethod
    async def generate_admin_id(session: AsyncSession, admin_type: str = "ADMIN") -> str:
        """
        Generate admin ID (ADMIN001, SUPER001, etc.)
        """
        result = await session.execute(
            text("""
                SELECT unique_id 
                FROM admins 
                WHERE unique_id LIKE :prefix
                ORDER BY unique_id DESC 
                LIMIT 1
            """),
            {"prefix": f"{admin_type}%"}
        )
        last_id = result.scalar_one_or_none()
        
        if last_id:
            try:
                last_number = int(last_id[len(admin_type):])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
            
        return f"{admin_type}{next_number:03d}"
    
    @staticmethod
    def get_user_role_from_id(unique_id: str) -> str:
        """Determine user role from unique ID pattern"""
        if unique_id.startswith(UserIDPrefix.STUDENT.value):
            return UserTypeEnum.STUDENT.value
        elif unique_id.startswith(UserIDPrefix.TEACHER.value):
            return UserTypeEnum.TEACHER.value
        elif unique_id.startswith(UserIDPrefix.ADMIN.value) or unique_id.startswith("SUPER"):
            return UserTypeEnum.ADMIN.value
        elif unique_id.startswith(UserIDPrefix.PARENT.value):
            return UserTypeEnum.PARENT.value
        else:
            raise ValueError(f"Invalid unique ID format: {unique_id}")
