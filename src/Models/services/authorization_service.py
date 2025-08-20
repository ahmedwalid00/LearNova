from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.Enums.user_type_enums import UserIDPrefix

class AuthorizationService:
    """Enhanced authorization service with role-based unique IDs"""
    
    @staticmethod
    def get_user_role_from_id(unique_id: str) -> str:
        """Determine user role from unique ID pattern"""
        if unique_id.startswith(UserIDPrefix.STUDENT.value):
            return UserIDPrefix.STUDENT.value
        elif unique_id.startswith(UserIDPrefix.TEACHER.value):
            return UserIDPrefix.TEACHER.value
        elif unique_id.startswith(UserIDPrefix.ADMIN.value) or unique_id.startswith("SUPER"):
            return UserIDPrefix.ADMIN.value
        elif unique_id.startswith(UserIDPrefix.PARENT.value):
            return UserIDPrefix.PARENT.value
        else:
            raise ValueError(f"Invalid unique ID format: {unique_id}")
    
    @staticmethod
    async def get_user_by_unique_id(session: AsyncSession, unique_id: str) -> Optional[dict]:
        """
        Get user data by unique ID from appropriate table
        
        Args:
            session: Database session
            unique_id: The unique ID to search for
            
        Returns:
            dict: User data or None if not found
        """
        role = AuthorizationService.get_user_role_from_id(unique_id)

        if role == UserIDPrefix.STUDENT.value:
            result = await session.execute(
                text("""
                    SELECT student_id, unique_id, name, email, is_verified, 
                           password_hash, rating, admin_id, term_id
                    FROM students 
                    WHERE unique_id = :unique_id
                """),
                {"unique_id": unique_id}
            )
        elif role == UserIDPrefix.TEACHER.value:
            result = await session.execute(
                text("""
                    SELECT teacher_id, unique_id, name, email, is_verified, 
                           password_hash, rating, subject_id, admin_id, term_id
                    FROM teachers 
                    WHERE unique_id = :unique_id
                """),
                {"unique_id": unique_id}
            )
        elif role == UserIDPrefix.ADMIN.value:
            result = await session.execute(
                text("""
                    SELECT admin_id, unique_id, name, email, password_hash
                    FROM admins 
                    WHERE unique_id = :unique_id
                """),
                {"unique_id": unique_id}
            )
        elif role == UserIDPrefix.PARENT.value:
            result = await session.execute(
                text("""
                    SELECT parent_id, unique_id, name, email, password_hash, 
                           is_verified, admin_id
                    FROM parents 
                    WHERE unique_id = :unique_id
                """),
                {"unique_id": unique_id}
            )
        else:
            return None
        
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return None
    
    @staticmethod
    async def _verify_parent_student_access(session: AsyncSession, parent_unique_id: str, student_unique_id: str) -> bool:
        """
        Verify if parent has access to specific student's data
        
        Args:
            session: Database session
            parent_unique_id: Parent's unique ID
            student_unique_id: Student's unique ID
            
        Returns:
            bool: True if parent has access to student, False otherwise
        """
        result = await session.execute(
            text("""
                SELECT 1 FROM parent_student_links psl
                JOIN parents p ON p.parent_id = psl.parent_id
                JOIN students s ON s.student_id = psl.student_id
                WHERE p.unique_id = :parent_id 
                AND s.unique_id = :student_id
                AND psl.is_active = true
            """),
            {"parent_id": parent_unique_id, "student_id": student_unique_id}
        )
        
        return result.scalar_one_or_none() is not None
    
    
    @staticmethod
    async def _get_parent_accessible_students(session: AsyncSession, parent_unique_id: str) -> list:
        """Get list of student IDs that parent can access"""
        result = await session.execute(
            text("""
                SELECT s.unique_id FROM parent_student_links psl
                JOIN parents p ON p.parent_id = psl.parent_id
                JOIN students s ON s.student_id = psl.student_id
                WHERE p.unique_id = :parent_id 
                AND psl.is_active = true
            """),
            {"parent_id": parent_unique_id}
        )
        
        return [row[0] for row in result.fetchall()]
