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

from src.Models.repositories.user_repository import StudentRepository, TeacherRepository, ParentRepository
from src.Enums.signal_response import SignalResponse
from src.Enums.user_type_enums import UserTypeEnum
from src.Models.services.id_generation_service import IDGenerationService
from src.Api.utils import PasswordHandler, JWTHandler, TokenSerializer
from src.Api.Schemes.auth_schemes import UserSignUpModel
from src.email import create_message, mail
from src.Helpers.config import get_settings

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
    
    def _get_repository_by_user_type(self, user_type: str):
        """
        Get the appropriate repository based on user type.
        
        Args:
            user_type: The type of user (student, teacher, parent)
            
        Returns:
            Repository instance for the specified user type
            
        Raises:
            HTTPException: If user type is invalid or not allowed
        """
        # Accept either the enum or its string value
        if isinstance(user_type, UserTypeEnum):
            user_type = user_type.value

        if user_type == UserTypeEnum.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Admin accounts cannot self-register"
            )
        
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
    
    async def _check_existing_user(self, user_repo, email: str, unique_id: str) -> None:
        """
        Check if user already exists by email or unique ID.
        
        Args:
            user_repo: Repository instance
            email: User email to check
            unique_id: User unique ID to check
            
        Raises:
            HTTPException: If user already exists
        """
        # Check email
        existing_email = await user_repo.get_by_email(email)
        if existing_email:
            logger.error(f"Email already registered: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=SignalResponse.EMAIL_ALREADY_REGISTERED.value
            )
        
        # Check unique ID
        existing_unique_id = await user_repo.get_by_unique_id(unique_id)
        if existing_unique_id:
            logger.error(f"Unique ID already registered: {unique_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=SignalResponse.UNIQUE_ID_ALREADY_REGISTERED.value
            )
    
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
    
    async def send_verification_email(self, user_email: str, user_name: str, unique_id: str) -> None:
        """
        Send verification email to the user.
        
        Args:
            user_email: User's email address
            user_name: User's name
            unique_id: User's unique identifier
        """
        try:
            # Create verification token
            token_data = {
                "email": user_email,
                "unique_id": unique_id,
                "purpose": "email_verification"
            }
            verification_token = TokenSerializer.create_url_safe_token(token_data)
            
            # Create verification URL
            verification_url = f"{settings.DOMAIN}/api/v1/auth/verify-email?token={verification_token}"
            
            # Create email content
            subject = "Verify Your Email - LearNova"
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to LearNova, {user_name}!</h2>
                <p>Thank you for signing up. Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p>{verification_url}</p>
                <p>This verification link will expire in 24 hours.</p>
                <p>Best regards,<br>LearNova Team</p>
            </body>
            </html>
            """
            
            # Send email
            message = create_message(
                recipients=[user_email],
                subject=subject,
                body=html_content
            )
            await mail.send_message(message)
            logger.info(f"Verification email sent to {user_email}")
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user_email}: {str(e)}")
            # Don't raise exception - email failure shouldn't block signup

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
            
            # Update verification status
            await user_repo.update(user, {"is_verified": True})
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
            
            # Create reset token
            token_data = {
                "email": email,
                "unique_id": user.unique_id,
                "purpose": "password_reset"
            }
            reset_token = TokenSerializer.create_url_safe_token(token_data)
            
            # Create reset URL
            reset_url = f"{settings.DOMAIN}/api/v1/auth/confirm-password-reset?token={reset_token}"
            
            # Create email content
            subject = "Reset Your Password - LearNova"
            html_content = f"""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hello {user.name},</p>
                <p>You requested to reset your password. Click the link below to set a new password:</p>
                <p><a href="{reset_url}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p>{reset_url}</p>
                <p>This reset link will expire in 1 hour.</p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <p>Best regards,<br>LearNova Team</p>
            </body>
            </html>
            """
            
            # Send email
            message = create_message(
                recipients=[email],
                subject=subject,
                body=html_content
            )
            await mail.send_message(message)
            logger.info(f"Password reset email sent to {email}")
            
            return {
                "message": "Password reset email sent successfully",
                "email": email
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
            
            # Update password
            await user_repo.update(user, {"password_hash": hashed_password})
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
        
        # Check for existing users
        email = user_data.email.lower()
        await self._check_existing_user(user_repo, email, user_data.user_unique_id)
        
        # Prepare user data
        combined_name = f"{user_data.first_name} {user_data.last_name}"
        hashed_password = PasswordHandler.hash_password(user_data.password)
        
        # Create user
        try:
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
            
            # Format response
            user_out = self._format_user_response(new_user)
            
            # Send verification email
            await self._send_verification_email(
                user_email=email,
                user_name=combined_name,
                unique_id=user_data.user_unique_id
            )
            
            return {
                "message": SignalResponse.SIGNUP_SUCCESS.value,
                "user": user_out,
                "verification_email_sent": True
            }
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to create user"
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
            
            # Get appropriate repository
            user_repo = self._get_repository_by_user_type(user_type)
            
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
    