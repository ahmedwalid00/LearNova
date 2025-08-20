"""
Authentication utilities for JWT token handling.

This module provides utilities for creating, validating, and managing
JWT access and refresh tokens with proper security practices.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
import secrets
import hashlib
import logging
import uuid
import jwt
import bcrypt

from src.Helpers.config import get_settings

settings = get_settings()



class JWTHandler:
    """
    JWT token handler with secure token generation and validation.
    """
    
    # Token types
    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"
    
    @staticmethod
    def create_access_token(
        user_data: dict, expiry: timedelta = None, refresh: bool = False
    ):
        payload = {}

        payload["user"] = user_data
        payload["exp"] = datetime.now() + (
            expiry if expiry is not None else timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload["jti"] = str(uuid.uuid4())

        payload["refresh"] = refresh

        token = jwt.encode(
            payload=payload, key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

        return token
    
    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            token_data = jwt.decode(
                jwt=token, key=settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )

            return token_data

        except jwt.PyJWTError as e:
            logging.exception(e)
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