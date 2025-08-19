"""
Authentication utilities for JWT token handling.

This module provides utilities for creating, validating, and managing
JWT access and refresh tokens with proper security practices.
"""

import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
import secrets
import hashlib

from src.Helpers.config import get_settings

settings = get_settings()


class JWTHandler:
    """
    JWT token handler with secure token generation and validation.
    """
    
    # Token types
    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"
    
    # Default expiry times
    ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days
    
    @staticmethod
    def create_access_token(user_id: str, user_type: str, additional_claims: Optional[Dict] = None) -> str:
        """
        Create a new access token.
        
        Args:
            user_id: User's unique identifier
            user_type: Type of user (student, teacher, parent, admin)
            additional_claims: Optional additional claims to include
            
        Returns:
            JWT access token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=JWTHandler.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "user_type": user_type,
            "token_type": JWTHandler.ACCESS_TOKEN,
            "iat": now,  # Issued at
            "exp": expire,  # Expiry
            "jti": secrets.token_urlsafe(16),  # JWT ID for token revocation
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str, user_type: str) -> str:
        """
        Create a new refresh token.
        
        Args:
            user_id: User's unique identifier
            user_type: Type of user
            
        Returns:
            JWT refresh token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=JWTHandler.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": str(user_id),
            "user_type": user_type,
            "token_type": JWTHandler.REFRESH_TOKEN,
            "iat": now,
            "exp": expire,
            "jti": secrets.token_urlsafe(16),
        }
        
        return jwt.encode(payload, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str, token_type: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            token_type: Expected token type (access or refresh)
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            # Choose the correct secret key based on token type
            secret_key = (
                settings.JWT_SECRET_KEY if token_type == JWTHandler.ACCESS_TOKEN
                else settings.JWT_REFRESH_SECRET_KEY
            )
            
            payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
            
            # Verify token type matches expected
            if payload.get("token_type") != token_type:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None  # Token has expired
        except jwt.InvalidTokenError:
            return None  # Token is invalid
    
    @staticmethod
    def get_token_expiry(token: str) -> Optional[datetime]:
        """
        Get the expiry time of a token without verification.
        
        Args:
            token: JWT token string
            
        Returns:
            Token expiry datetime or None if invalid
        """
        try:
            # Decode without verification to get expiry
            payload = jwt.decode(token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            return None
        except Exception:
            return None


class PasswordHandler:
    """
    Secure password hashing and verification using bcrypt.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            hashed_password: Previously hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        if not password or not hashed_password:
            return False
        
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False


class SecurityUtils:
    """
    Additional security utilities.
    """
    
    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate a secure random token for email verification.
        
        Returns:
            URL-safe random token string
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate a secure random token for password reset.
        
        Returns:
            URL-safe random token string
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_reset_token(token: str) -> str:
        """
        Hash a reset token for secure storage.
        
        Args:
            token: Plain reset token
            
        Returns:
            SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def verify_reset_token(token: str, hashed_token: str) -> bool:
        """
        Verify a reset token against its hash.
        
        Args:
            token: Plain reset token
            hashed_token: Previously hashed token
            
        Returns:
            True if token matches, False otherwise
        """
        return hashlib.sha256(token.encode()).hexdigest() == hashed_token


# Convenience functions for common operations
def create_token_pair(user_id: str, user_type: str) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User's unique identifier
        user_type: Type of user
        
    Returns:
        Dictionary containing access_token and refresh_token
    """
    access_token = JWTHandler.create_access_token(user_id, user_type)
    refresh_token = JWTHandler.create_refresh_token(user_id, user_type)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": JWTHandler.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    }


def hash_password(password: str) -> str:
    """Convenience function for password hashing."""
    return PasswordHandler.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Convenience function for password verification."""
    return PasswordHandler.verify_password(password, hashed_password)