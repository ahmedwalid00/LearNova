from typing import Optional, Dict, List, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID, uuid4
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
        from src.Enums.user_type_enums import UserIDPrefix, UserTypeEnum
        
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
    
    async def create_partial_user_record(self, user_type: str, unique_id: str, admin_id: UUID, term_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Create a partial user record in the database with basic information.
        
        This method creates incomplete user records that will be completed when users sign up.
        
        Args:
            user_type: Type of user (student/teacher/parent)
            unique_id: Generated unique ID
            admin_id: ID of the admin creating this record
            term_id: Optional term ID (will get current active term if not provided)
            
        Returns:
            Dict containing the created partial record information
            
        Raises:
            ValueError: If user creation fails or invalid user type
        """
        try:
            # Get current active term if not provided
            if not term_id:
                term_id = await self._get_current_active_term()
            
            # Generate UUID for the new user
            user_uuid = uuid4()
            
            # Create partial user record based on type
            if user_type == UserTypeEnum.STUDENT.value:
                query = text("""
                    INSERT INTO students (student_id, unique_id, name, email, password_hash, is_verified, admin_id, term_id, created_at, updated_at)
                    VALUES (:user_id, :unique_id, 'Pending Registration', :placeholder_email, 'pending', false, :admin_id, :term_id, :created_at, :updated_at)
                """)
            elif user_type == UserTypeEnum.TEACHER.value:
                query = text("""
                    INSERT INTO teachers (teacher_id, unique_id, name, email, password_hash, is_verified, admin_id, term_id, created_at, updated_at)
                    VALUES (:user_id, :unique_id, 'Pending Registration', :placeholder_email, 'pending', false, :admin_id, :term_id, :created_at, :updated_at)
                """)
            elif user_type == UserTypeEnum.PARENT.value:
                query = text("""
                    INSERT INTO parents (parent_id, unique_id, name, email, password_hash, is_verified, admin_id, created_at, updated_at)
                    VALUES (:user_id, :unique_id, 'Pending Registration', :placeholder_email, 'pending', false, :admin_id, :created_at, :updated_at)
                """)
            else:
                raise ValueError(f"Invalid user type for partial record creation: {user_type}")
            
            # Execute the insertion
            current_time = datetime.utcnow()
            params = {
                "user_id": user_uuid,
                "unique_id": unique_id,
                "placeholder_email": f"pending_{unique_id}@learnova.pending",  # Unique placeholder email
                "admin_id": admin_id,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            # Add term_id for students and teachers only
            if user_type in [UserTypeEnum.STUDENT.value, UserTypeEnum.TEACHER.value]:
                params["term_id"] = term_id
            
            await self.session.execute(query, params)
            await self.session.flush()  # Flush to ensure record is created
            
            return {
                "user_id": str(user_uuid),
                "unique_id": unique_id,
                "user_type": user_type,
                "admin_id": str(admin_id),
                "term_id": str(term_id) if term_id else None,
                "status": "partial_record_created",
                "created_at": current_time
            }
            
        except Exception as e:
            raise ValueError(f"Failed to create partial {user_type} record: {str(e)}")

    async def _get_current_active_term(self) -> Optional[UUID]:
        """
        Get the current active academic term.
        
        Returns:
            UUID of the active term or None if no active term found
        """
        try:
            result = await self.session.execute(
                text("SELECT term_id FROM academic_terms WHERE is_active = true LIMIT 1")
            )
            term_id = result.scalar_one_or_none()
            return term_id
        except Exception:
            # If no active term found, return None
            return None

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
    async def generate_single_id(self, request_data: IDGenerationRequestModel, admin_id: UUID) -> Dict[str, Any]:
        """Generate a single ID for admin interface and create partial user record"""
        
        user_type = request_data.user_type.lower()

        if user_type == UserTypeEnum.STUDENT.value:
            generated_id = await self.generate_student_id()
        elif user_type == UserTypeEnum.TEACHER.value:
            generated_id = await self.generate_teacher_id()
        else:
            raise ValueError(f"Invalid user type: {user_type}")

        # Create partial user record in the database
        partial_record = await self.create_partial_user_record(
            user_type=user_type,
            unique_id=generated_id,
            admin_id=admin_id
        )

        return {
            "user_type": request_data.user_type,
            "generated_ids": [generated_id],  # Wrap single ID in a list for consistency
            "count": 1,
            "partial_records": [partial_record]
        }

    async def generate_bulk_ids(self, user_type: str, count: int, admin_id: UUID) -> Dict[str, Any]:
        """Generate multiple IDs for admin bulk operations and create partial user records"""
        
        if user_type.lower() not in ["student", "teacher"]:
            raise ValueError("User type must be either 'student' or 'teacher'")

        if count <= 0 or count > 1000:  # Reasonable limit
            raise ValueError("Count must be between 1 and 1000")

        generated_ids = []
        partial_records = []
        
        # Get the base next ID first
        if user_type.lower() == UserTypeEnum.STUDENT.value:
            base_id = await self.generate_student_id()
            prefix = UserIDPrefix.STUDENT.value
        else:  # teacher
            base_id = await self.generate_teacher_id()
            prefix = UserIDPrefix.TEACHER.value
        
        # Extract the base number
        base_number = int(base_id[len(prefix):])
        
        # Generate sequential IDs and create partial records
        for i in range(count):
            sequential_id = f"{prefix}{base_number + i:03d}"
            generated_ids.append(sequential_id)
            
            # Create partial user record for each ID
            try:
                partial_record = await self.create_partial_user_record(
                    user_type=user_type.lower(),
                    unique_id=sequential_id,
                    admin_id=admin_id
                )
                partial_records.append(partial_record)
            except Exception as e:
                # If partial record creation fails, still return the generated ID but note the failure
                partial_records.append({
                    "unique_id": sequential_id,
                    "status": "id_generated_but_partial_record_failed",
                    "error": str(e)
                })

        return {
            "user_type": user_type,
            "generated_ids": generated_ids,
            "count": len(generated_ids),
            "partial_records": partial_records,
            "successful_records": len([r for r in partial_records if r.get("status") == "partial_record_created"]),
            "failed_records": len([r for r in partial_records if "error" in r])
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
