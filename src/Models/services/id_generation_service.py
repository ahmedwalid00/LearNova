from typing import Optional, Dict, List, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.Enums.user_type_enums import UserIDPrefix, UserTypeEnum
from src.Api.Schemes.admin import IDGenerationRequestModel


class IDGenerationService:
    """Service for generating unique human-readable IDs for different user types"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def generate_student_id(self) -> str:
        """
        Generate next available student ID (22001, 22002, etc.)
        
        Returns:
            str: Generated student ID (e.g., "22001")
        """
        # Get the highest existing student ID using raw SQL to avoid import issues
        result = await self.session.execute(
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

    async def generate_teacher_id(self) -> str:
        """
        Generate next available teacher ID (11001, 11002, etc.)
        """
        result = await self.session.execute(
            text("""
                SELECT unique_id 
                FROM teachers 
                WHERE unique_id LIKE :prefix
                ORDER BY unique_id DESC 
                LIMIT 1
            """),
            {"prefix": f"{UserIDPrefix.TEACHER.value}%"}
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

    async def generate_admin_id(self, admin_type: str = "ADMIN") -> str:
        """
        Generate admin ID (ADMIN001, SUPER001, etc.)
        """
        result = await self.session.execute(
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

    # Admin-specific methods for bulk operations and management
    async def generate_single_id(self, request_data: IDGenerationRequestModel) -> Dict[str, Any]:
        """Generate a single ID for admin interface"""
        
        user_type = request_data.user_type.lower()

        if user_type == UserTypeEnum.STUDENT.value:
            generated_id = await self.generate_student_id()
        elif user_type == UserTypeEnum.TEACHER.value:
            generated_id = await self.generate_teacher_id()
        else:
            raise ValueError(f"Invalid user type: {user_type}")

        return {
            "user_type": request_data.user_type,
            "generated_ids": [generated_id],  # Wrap single ID in a list
            "count": 1
        }

    async def generate_bulk_ids(self, user_type: str, count: int) -> Dict[str, Any]:
        """Generate multiple IDs for admin bulk operations"""
        
        if user_type.lower() not in ["student", "teacher"]:
            raise ValueError("User type must be either 'student' or 'teacher'")

        if count <= 0 or count > 1000:  # Reasonable limit
            raise ValueError("Count must be between 1 and 1000")

        generated_ids = []
        
        # Get the base next ID first
        if user_type.lower() == UserTypeEnum.STUDENT.value:
            base_id = await self.generate_student_id()
            prefix = UserIDPrefix.STUDENT.value
        else:  # teacher
            base_id = await self.generate_teacher_id()
            prefix = UserIDPrefix.TEACHER.value
        
        # Extract the base number
        base_number = int(base_id[len(prefix):])
        
        # Generate sequential IDs
        for i in range(count):
            sequential_id = f"{prefix}{base_number + i:03d}"
            generated_ids.append(sequential_id)

        return {
            "user_type": user_type,
            "generated_ids": generated_ids,
            "count": len(generated_ids)
        }

    async def validate_id_format(self, unique_id: str) -> Dict[str, Any]:
        """Validate ID format for admin interface"""
        
        try:
            user_role = self.get_user_role_from_id(unique_id)
            return {
                "valid": True,
                "user_type": user_role,
                "unique_id": unique_id,
                "message": f"Valid {user_role} ID"
            }
        except ValueError as e:
            return {
                "valid": False,
                "unique_id": unique_id,
                "error": str(e),
                "message": "Invalid ID format"
            }

    async def check_id_availability(self, unique_id: str) -> Dict[str, Any]:
        """Check if an ID is available (not already used)"""
        
        # First validate format
        validation_result = await self.validate_id_format(unique_id)
        if not validation_result["valid"]:
            return validation_result

        user_type = validation_result["user_type"]
        
        # Check if ID exists in appropriate table
        if user_type == UserTypeEnum.STUDENT.value:
            table = "students"
        elif user_type == UserTypeEnum.TEACHER.value:
            table = "teachers"
        elif user_type == UserTypeEnum.ADMIN.value:
            table = "admins"
        elif user_type == UserTypeEnum.PARENT.value:
            table = "parents"
        else:
            return {
                "available": False,
                "error": f"Unknown user type: {user_type}"
            }

        query = text(f"SELECT COUNT(*) FROM {table} WHERE unique_id = :unique_id")
        result = await self.session.execute(query, {"unique_id": unique_id})
        count = result.scalar()
        exists = count > 0

        return {
            "unique_id": unique_id,
            "available": not exists,
            "exists": exists,
            "user_type": user_type,
            "message": "Available" if not exists else "Already in use"
        }

    async def get_id_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated IDs for admin dashboard"""
        
        # Count by user type
        statistics = {}
        
        for user_type, table in [
            ("students", "students"),
            ("teachers", "teachers"), 
            ("admins", "admins"),
            ("parents", "parents")
        ]:
            query = text(f"SELECT COUNT(*) FROM {table}")
            result = await self.session.execute(query)
            statistics[user_type] = result.scalar()

        # Get latest IDs for each type
        latest_ids = {}
        
        for user_type, table, prefix in [
            ("student", "students", UserIDPrefix.STUDENT.value),
            ("teacher", "teachers", UserIDPrefix.TEACHER.value),
            ("admin", "admins", UserIDPrefix.ADMIN.value),
            ("parent", "parents", UserIDPrefix.PARENT.value)
        ]:
            query = text(f"""
                SELECT unique_id 
                FROM {table} 
                WHERE unique_id LIKE :prefix
                ORDER BY unique_id DESC 
                LIMIT 1
            """)
            result = await self.session.execute(query, {"prefix": f"{prefix}%"})
            latest_id = result.scalar_one_or_none()
            latest_ids[user_type] = latest_id

        return {
            "total_counts": statistics,
            "total_users": sum(statistics.values()),
            "latest_ids": latest_ids,
            "generated_at": datetime.utcnow()
        }

    async def reserve_ids(self, user_type: str, count: int) -> Dict[str, Any]:
        """Reserve IDs for future use"""
        
        if user_type.lower() not in ["student", "teacher"]:
            raise ValueError("User type must be either 'student' or 'teacher'")

        if count <= 0 or count > 1000:  # Reasonable limit
            raise ValueError("Count must be between 1 and 1000")

        # Generate the IDs that would be reserved
        reserved_ids = []
        
        # Get the base next ID first
        if user_type.lower() == UserTypeEnum.STUDENT.value:
            base_id = await self.generate_student_id()
            prefix = UserIDPrefix.STUDENT.value
        else:  # teacher
            base_id = await self.generate_teacher_id()
            prefix = UserIDPrefix.TEACHER.value
        
        # Extract the base number
        base_number = int(base_id[len(prefix):])
        
        # Generate sequential IDs for reservation
        for i in range(count):
            sequential_id = f"{prefix}{base_number + i:03d}"
            reserved_ids.append(sequential_id)

        return {
            "user_type": user_type,
            "reserved_ids": reserved_ids,
            "count": len(reserved_ids),
            "message": f"Reserved {count} {user_type} IDs for future use",
            "reserved_at": datetime.utcnow()
        }
