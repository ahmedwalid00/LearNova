"""
Authentication Controller for handling authentication business logic.

This module contains the AuthController class that orchestrates
authentication operations and can be reused across different endpoints.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import logging
import logging

from src.Models.repositories.user_repository import StudentRepository, TeacherRepository, ParentRepository, AdminRepository
from src.Enums.signal_response import SignalResponse
from src.Enums.user_type_enums import UserTypeEnum
from src.Models.services.id_generation_service import IDGenerationService
from src.Api.utils import PasswordHandler, JWTHandler, TokenSerializer
from src.Api.Schemes.auth_schemes import UserSignUpModel
from src.Helpers.config import get_settings
# Import Celery tasks
from src.Tasks.sending_email import send_verification_email, send_password_reset_email

settings = get_settings()
logger = logging.getLogger('uvicorn.error')


class AuthController:
    """
    Controller class for authentication operations.
    
    Handles signup, login, and other authentication-related business logic
    in a reusable and extensible manner.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize the controller with database session."""
        self.session = session
    
    def _get_repository_by_user_type(self, user_type: str, allow_admin: bool = False):
        """
        Get the appropriate repository based on user type.
        
        Args:
            user_type: The type of user (student, teacher, parent, admin)
            allow_admin: Whether to allow admin repository (default False for signup, True for login)
            
        Returns:
            Repository instance for the specified user type
            
        Raises:
            HTTPException: If user type is invalid or not allowed
        """
        # Accept either the enum or its string value
        if isinstance(user_type, UserTypeEnum):
            user_type = user_type.value

        if user_type == UserTypeEnum.ADMIN.value:
            if not allow_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Admin accounts cannot self-register"
                )
            return AdminRepository(self.session)
        
        if user_type == UserTypeEnum.STUDENT.value:
            return StudentRepository(self.session)
        elif user_type == UserTypeEnum.TEACHER.value:
            return TeacherRepository(self.session)
        elif user_type == UserTypeEnum.PARENT.value:
            return ParentRepository(self.session)
        else:
            logger.error(f"Invalid user type: {user_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid user type"
            )
    
    async def _validate_user_data(self, user_data: UserSignUpModel) -> None:
        """
        Validate user signup data.
        
        Args:
            user_data: User signup data to validate
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate user type matches unique ID format
        expected_raw = None
        try:
            expected_raw = IDGenerationService.get_user_role_from_id(unique_id=user_data.user_unique_id)
        except Exception:
            expected_raw = None

        # Normalize provided user_type to a string value
        provided_type = (
            user_data.user_type.value
            if isinstance(user_data.user_type, UserTypeEnum)
            else str(user_data.user_type)
        )

        # Determine expected role string from the ID service output
        expected_role = None
        if isinstance(expected_raw, UserTypeEnum):
            expected_role = expected_raw.value
        elif isinstance(expected_raw, str):
            # If service returned a numeric prefix like '22' or '11', map to role
            if expected_raw.isdigit():
                prefix_map = {
                    "22": UserTypeEnum.STUDENT.value,
                    "11": UserTypeEnum.TEACHER.value,
                }
                expected_role = prefix_map.get(expected_raw, expected_raw)
            elif expected_raw.upper().startswith("P"):
                expected_role = UserTypeEnum.PARENT.value
            else:
                expected_role = expected_raw

        # If we could determine an expected role, compare; otherwise skip strict check
        if expected_role and expected_role != provided_type:
            logger.error(f"User type mismatch: expected {expected_role}, got {user_data.user_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SignalResponse.ID_DOESNT_MATCH_ROLE.value,
            )

        # Validate password confirmation
        if user_data.password != user_data.confirm_password:
            logger.error("Passwords do not match")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=SignalResponse.PASSWORD_NOT_MATCH.value,
            )
    
    async def _check_existing_user(self, user_repo, email: str, unique_id: str) -> Optional[Any]:
        """
        Check if user already exists by email or unique ID.
        
        Returns the existing user if found as a partial record (for completion),
        otherwise raises HTTPException if fully registered user exists.
        
        Args:
            user_repo: Repository instance
            email: User email to check
            unique_id: User unique ID to check
            
        Returns:
            Existing partial user record if found, None if no conflicts
            
        Raises:
            HTTPException: If user already exists and is fully registered
        """
        # Check email - this should never exist for partial records
        existing_email = await user_repo.get_by_email(email)
        if existing_email:
            logger.error(f"Email already registered: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=SignalResponse.EMAIL_ALREADY_REGISTERED.value
            )
        
        # Check unique ID - this might exist as a partial record
        existing_unique_id = await user_repo.get_by_unique_id(unique_id)
        if existing_unique_id:
            # Check if this is a partial record (placeholder email indicates partial)
            if (existing_unique_id.email.endswith("@learnova.pending") and 
                existing_unique_id.name == "Pending Registration"):
                # This is a partial record - return it for completion
                logger.info(f"Found partial record for unique_id: {unique_id}")
                return existing_unique_id
            else:
                # This is a fully registered user
                logger.error(f"Unique ID already registered: {unique_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=SignalResponse.UNIQUE_ID_ALREADY_REGISTERED.value
                )
        
        return None
    
    def _format_user_response(self, user) -> Dict[str, Any]:
        """
        Format user data for response.
        
        Args:
            user: User instance from database
            
        Returns:
            Formatted user data dictionary
        """
        # Extract the appropriate ID field based on user type
        user_id = (
            getattr(user, "student_id", None) or 
            getattr(user, "teacher_id", None) or 
            getattr(user, "parent_id", None) or
            getattr(user, "admin_id", None)
        )
        
        return {
            "id": str(user_id) if user_id else None,
            "unique_id": getattr(user, "unique_id", None),
            "email": getattr(user, "email", None),
            "name": getattr(user, "name", None),
        }
    
    def send_verification_email_async(self, user_email: str, user_name: str, unique_id: str) -> str:
        """
        Queue verification email sending using Celery.
        
        Args:
            user_email: User's email address
            user_name: User's name
            unique_id: User's unique identifier
            
        Returns:
            Task ID for tracking
        """
        try:
            # Queue the email sending task
            task = send_verification_email.delay(user_email, user_name, unique_id)
            logger.info(f"Verification email task queued for {user_email}, task_id: {task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to queue verification email for {user_email}: {str(e)}")
            # Don't raise exception - email failure shouldn't block signup
            return None

    def send_password_reset_email_async(self, user_email: str, user_name: str, unique_id: str) -> str:
        """
        Queue password reset email sending using Celery.
        
        Args:
            user_email: User's email address
            user_name: User's name
            unique_id: User's unique identifier
            
        Returns:
            Task ID for tracking
        """
        try:
            # Queue the email sending task
            task = send_password_reset_email.delay(user_email, user_name, unique_id)
            logger.info(f"Password reset email task queued for {user_email}, task_id: {task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"Failed to queue password reset email for {user_email}: {str(e)}")
            return None

    async def verify_email(self, token: str) -> Dict[str, Any]:
        """
        Verify user email using verification token.
        
        Args:
            token: Verification token from email link
            
        Returns:
            Success response
            
        Raises:
            HTTPException: If verification fails
        """
        try:
            # Decode token
            token_data = TokenSerializer.decode_url_safe_token(token)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification token"
                )
            
            # Validate token purpose
            if token_data.get("purpose") != "email_verification":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token purpose"
                )
            
            email = token_data.get("email")
            unique_id = token_data.get("unique_id")
            
            if not email or not unique_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token data"
                )
            
            # Determine user type and get repository
            user_type = IDGenerationService.get_user_role_from_id(unique_id)
            user_repo = self._get_repository_by_user_type(user_type)
            
            # Find user
            user = await user_repo.get_by_unique_id(unique_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if email matches
            if user.email.lower() != email.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email mismatch"
                )
            
            # Check if already verified
            if user.is_verified:
                return {
                    "message": "Email already verified",
                    "verified": True
                }
            
            # Update verification status using primary key
            user_pk = (
                getattr(user, "student_id", None)
                or getattr(user, "teacher_id", None)
                or getattr(user, "parent_id", None)
                or getattr(user, "admin_id", None)
            )
            if not user_pk:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to determine user primary key",
                )
            await user_repo.update(user_pk, is_verified=True)
            logger.info(f"Email verified for user {unique_id}")
            
            return {
                "message": "Email verified successfully",
                "verified": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Email verification failed"
            )

    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request password reset for a user.
        
        Args:
            email: User's email address
            
        Returns:
            Success response
            
        Raises:
            HTTPException: If user not found or other errors
        """
        try:
            email = email.lower()
            user = None
            user_type = None
            
            # Search across all user types to find the user by email
            for user_type_enum, repo_class in [
                (UserTypeEnum.STUDENT.value, StudentRepository),
                (UserTypeEnum.TEACHER.value, TeacherRepository),
                (UserTypeEnum.PARENT.value, ParentRepository)
            ]:
                repo = repo_class(self.session)
                try:
                    user = await repo.get_by_email(email)
                    if user:
                        user_type = user_type_enum
                        break
                except Exception:
                    continue
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Queue password reset email using Celery
            task_id = self.send_password_reset_email_async(
                user_email=email,
                user_name=user.name,
                unique_id=user.unique_id
            )
            
            return {
                "message": "Password reset email sent successfully",
                "email": email,
                "task_id": task_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset request error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process password reset request"
            )

    async def confirm_password_reset(self, token: str, new_password: str, confirm_password: str) -> Dict[str, Any]:
        """
        Confirm password reset using reset token.
        
        Args:
            token: Password reset token from email
            new_password: New password
            confirm_password: Password confirmation
            
        Returns:
            Success response
            
        Raises:
            HTTPException: If validation fails or token invalid
        """
        try:
            # Validate password confirmation
            if new_password != confirm_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Passwords do not match"
                )
            
            # Decode token
            token_data = TokenSerializer.decode_url_safe_token(token)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            
            email = token_data.get("email")
            unique_id = token_data.get("unique_id")
            
            if not email or not unique_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token data"
                )
            
            # Determine user type and get repository
            user_type = IDGenerationService.get_user_role_from_id(unique_id)
            user_repo = self._get_repository_by_user_type(user_type)
            
            # Find user
            user = await user_repo.get_by_unique_id(unique_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if email matches
            if user.email.lower() != email.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email mismatch"
                )
            
            # Hash new password
            hashed_password = PasswordHandler.hash_password(new_password)
            
            # Update password using primary key
            user_pk = (
                getattr(user, "student_id", None)
                or getattr(user, "teacher_id", None)
                or getattr(user, "parent_id", None)
                or getattr(user, "admin_id", None)
            )
            if not user_pk:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to determine user primary key",
                )
            await user_repo.update(user_pk, password_hash=hashed_password)
            logger.info(f"Password reset completed for user {unique_id}")
            
            return {
                "message": "Password reset completed successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset confirmation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )

    async def signup_user(self, user_data: UserSignUpModel) -> Dict[str, Any]:
        """
        Handle user signup process.
        
        This method now handles both new user creation and completion of partial user records.
        
        Args:
            user_data: User signup data
            
        Returns:
            Success response with user data
            
        Raises:
            HTTPException: If signup fails
        """
        # Validate input data
        await self._validate_user_data(user_data)
        
        # Get appropriate repository
        user_repo = self._get_repository_by_user_type(user_data.user_type)
        
        # Check for existing users (may return partial record)
        email = user_data.email.lower()
        existing_partial_user = await self._check_existing_user(user_repo, email, user_data.user_unique_id)
        
        # Prepare user data
        combined_name = f"{user_data.first_name} {user_data.last_name}"
        hashed_password = PasswordHandler.hash_password(user_data.password)
        
        # Create or update user
        try:
            if existing_partial_user:
                # Complete the partial record
                user_pk = (
                    getattr(existing_partial_user, "student_id", None) or
                    getattr(existing_partial_user, "teacher_id", None) or
                    getattr(existing_partial_user, "parent_id", None) or
                    getattr(existing_partial_user, "admin_id", None)
                )
                
                if not user_pk:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to determine user primary key for partial record"
                    )
                
                # Update the partial record with complete information
                updated_user = await user_repo.update(
                    user_pk,
                    email=email,
                    name=combined_name,
                    password_hash=hashed_password,
                    is_verified=False  # Will be verified via email
                )
                
                if not updated_user:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to complete partial user record"
                    )
                
                new_user = updated_user
                signup_type = "partial_record_completed"
                
            else:
                # Create new user (fallback for cases where no partial record exists)
                new_user = await user_repo.create(
                    email=email,
                    name=combined_name,
                    password_hash=hashed_password,
                    unique_id=user_data.user_unique_id
                )
                
                if not new_user:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create user"
                    )
                
                signup_type = "new_user_created"
            
            # Format response
            user_out = self._format_user_response(new_user)
            
            # Queue verification email using Celery
            task_id = self.send_verification_email_async(
                user_email=email,
                user_name=combined_name,
                unique_id=user_data.user_unique_id
            )
            
            return {
                "message": SignalResponse.SIGNUP_SUCCESS.value,
                "user": user_out,
                "verification_email_queued": True,
                "email_task_id": task_id,
                "signup_type": signup_type
            }
            
        except Exception as e:
            logger.error(f"Error during user signup: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process user signup"
            )
    
    async def login_user(self, unique_id: str, password: str) -> Dict[str, Any]:
        """
        Handle user login process.
        
        Args:
            unique_id: User's unique identification
            password: User's password
            
        Returns:
            Success response with tokens and user data
            
        Raises:
            HTTPException: If login fails
        """
        try:
            # Determine user type from unique ID
            user_type = IDGenerationService.get_user_role_from_id(unique_id)
            
            # Get appropriate repository (allow admin for login)
            user_repo = self._get_repository_by_user_type(user_type, allow_admin=True)
            
            # Find user by unique ID
            user = await user_repo.get_by_unique_id(unique_id)
            if not user:
                logger.error(f"User not found: {unique_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Invalid credentials"
                )
            
            # Verify password
            if not PasswordHandler.verify_password(password, user.password_hash):
                logger.error(f"Invalid password for user: {unique_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Invalid credentials"
                )
            
            # Generate tokens
            user_data = self._format_user_response(user)
            access_token = JWTHandler.create_access_token(user_data=user_data)
            refresh_token = JWTHandler.create_access_token(
                user_data=user_data, 
                refresh=True
            )
            
            return {
                "message": "Login successful",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": user_data
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Login failed"
            )
    