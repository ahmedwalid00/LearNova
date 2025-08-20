from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .id_generation_service import IDGenerationService
import secrets
import string

class ParentRegistrationFlow:
    """
    Service for handling parent registration flow (Option A)
    
    Flow:
    1. Admin creates student account with unique ID (e.g., 22001)
    2. Admin provides parent with:
       - Student's unique ID (22001)
       - Temporary parent access code
    3. Parent visits registration page and enters:
       - Student's unique ID (22001)
       - Their email
       - Creates password
    4. System generates parent unique ID (P22001)
    5. Parent gets access to their child's analytics only
    """
    
    @staticmethod
    def generate_access_code(length: int = 8) -> str:
        """Generate a temporary access code for parent registration"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    async def create_parent_access_code(
        session: AsyncSession,
        student_unique_id: str,
        admin_unique_id: str
    ) -> Dict[str, Any]:
        """
        Create a temporary access code for parent registration
        
        Args:
            session: Database session
            student_unique_id: Student's unique ID
            admin_unique_id: Admin who is creating the code
            
        Returns:
            dict: Access code details
        """
        # Verify student exists
        student_result = await session.execute(
            text("SELECT student_id, name FROM students WHERE unique_id = :id"),
            {"id": student_unique_id}
        )
        student = student_result.fetchone()
        
        if not student:
            raise ValueError(f"Student with ID {student_unique_id} not found")
        
        # Verify admin exists and has permission
        admin_result = await session.execute(
            text("SELECT admin_id FROM admins WHERE unique_id = :id"),
            {"id": admin_unique_id}
        )
        admin = admin_result.fetchone()
        
        if not admin:
            raise ValueError(f"Admin with ID {admin_unique_id} not found")
        
        # Generate access code
        access_code = ParentRegistrationFlow.generate_access_code()
        parent_unique_id = IDGenerationService.generate_parent_id(student_unique_id)
        
        # Store access code in database (you might want to create a separate table for this)
        # For now, we'll return the details
        
        return {
            "access_code": access_code,
            "student_unique_id": student_unique_id,
            "student_name": student.name,
            "parent_unique_id": parent_unique_id,
            "expires_in_hours": 48,  # Access code expires in 48 hours
            "created_by_admin": admin_unique_id
        }
    
    @staticmethod
    async def register_parent(
        session: AsyncSession,
        student_unique_id: str,
        parent_email: str,
        parent_name: str,
        password_hash: str,
        access_code: str
    ) -> Dict[str, Any]:
        """
        Register a parent using the access code flow
        
        Args:
            session: Database session
            student_unique_id: Student's unique ID from the access code
            parent_email: Parent's email address
            parent_name: Parent's full name
            password_hash: Hashed password
            access_code: Temporary access code provided by admin
            
        Returns:
            dict: Registration result
        """
        # Verify student exists
        student_result = await session.execute(
            text("SELECT student_id, admin_id FROM students WHERE unique_id = :id"),
            {"id": student_unique_id}
        )
        student = student_result.fetchone()
        
        if not student:
            raise ValueError(f"Student with ID {student_unique_id} not found")
        
        # TODO: Verify access code (would need to check against stored codes)
        # For now, we'll skip this verification
        
        # Generate parent unique ID
        parent_unique_id = IDGenerationService.generate_parent_id(student_unique_id)
        
        # Check if parent already exists
        existing_parent = await session.execute(
            text("SELECT parent_id FROM parents WHERE unique_id = :id OR email = :email"),
            {"id": parent_unique_id, "email": parent_email}
        )
        if existing_parent.fetchone():
            raise ValueError("Parent with this ID or email already exists")
        
        # Create parent record
        parent_insert = await session.execute(
            text("""
                INSERT INTO parents (parent_id, unique_id, name, email, password_hash, is_verified, admin_id)
                VALUES (gen_random_uuid(), :unique_id, :name, :email, :password_hash, false, :admin_id)
                RETURNING parent_id
            """),
            {
                "unique_id": parent_unique_id,
                "name": parent_name,
                "email": parent_email,
                "password_hash": password_hash,
                "admin_id": student.admin_id
            }
        )
        parent_id = parent_insert.scalar_one()
        
        # Create parent-student link
        await session.execute(
            text("""
                INSERT INTO parent_student_links (link_id, parent_id, student_id, relationship_type, is_active)
                VALUES (gen_random_uuid(), :parent_id, :student_id, 'parent', true)
            """),
            {
                "parent_id": parent_id,
                "student_id": student.student_id
            }
        )
        
        await session.commit()
        
        return {
            "parent_id": str(parent_id),
            "parent_unique_id": parent_unique_id,
            "parent_email": parent_email,
            "student_unique_id": student_unique_id,
            "status": "registered",
            "message": f"Parent account created successfully with ID {parent_unique_id}"
        }
    
    

