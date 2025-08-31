"""
File validation utilities for lesson uploads.
"""

import os
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from src.Enums.signal_response import SignalResponse
import magic
import io


class FileValidator:
    """Handles file validation for lesson uploads."""
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MIN_FILE_SIZE = 1024  # 1KB
    
    # Allowed file types
    ALLOWED_EXTENSIONS = {'.pdf', '.txt'}
    ALLOWED_MIME_TYPES = {
        'application/pdf', 
        'text/plain', 
        'text/x-script.python',
        'text/x-python', 
        'text/x-script',
        'text/x-c++',
        'text/x-java',
        'text/x-script.sh',
        'text/markdown',
        'text/x-markdown',
        'text/html',
        'text/xml',
        'application/x-empty'  # For very small text files
    }
    
    @classmethod
    async def validate_pdf_file(cls, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded PDF or TXT file.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not file:
                return False, SignalResponse.NO_FILE_UPLOADED.value

            # Check filename
            if not file.filename:
                return False, SignalResponse.NO_FILE_NAME_PROVIDED.value

            # Check file extension
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in cls.ALLOWED_EXTENSIONS:
                return False, f"Invalid file extension. Only {', '.join(cls.ALLOWED_EXTENSIONS)} allowed"
            
            # Read file content for validation
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Check file size
            file_size = len(file_content)
            if file_size < cls.MIN_FILE_SIZE:
                return False, f"File too small. Minimum size: {cls.MIN_FILE_SIZE / 1024:.1f}KB"
            
            if file_size > cls.MAX_FILE_SIZE:
                return False, f"File too large. Maximum size: {cls.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            
            # Check MIME type using python-magic
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
                if mime_type not in cls.ALLOWED_MIME_TYPES:
                    return False, f"Invalid file type. Expected PDF or TXT, got {mime_type}"
            except Exception:
                # Fallback: Check file headers
                if file_ext == '.pdf' and not file_content.startswith(b'%PDF'):
                    return False, "File does not appear to be a valid PDF"
                elif file_ext == '.txt':
                    # For TXT files, try to decode as text
                    try:
                        file_content.decode('utf-8')
                    except UnicodeDecodeError:
                        return False, "File does not appear to be valid UTF-8 text"
            
            # Additional validation based on file type
            if file_ext == '.pdf':
                # Check if PDF is readable (basic validation)
                try:
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    if len(pdf_reader.pages) == 0:
                        return False, "PDF file appears to be empty"
                except Exception as e:
                    return False, f"Invalid PDF file: {str(e)}"
            elif file_ext == '.txt':
                # Check if TXT file has readable content
                try:
                    text_content = file_content.decode('utf-8').strip()
                    if not text_content:
                        return False, "TXT file appears to be empty"
                except UnicodeDecodeError as e:
                    return False, f"Invalid TXT file encoding: {str(e)}"
            
            return True, None
            
        except Exception as e:
            return False, f"File validation error: {str(e)}"
    
    @classmethod
    def generate_lesson_filename(cls, original_filename: str, lesson_id: str) -> str:
        """
        Generate a unique filename for the lesson.
        
        Args:
            original_filename: Original uploaded filename
            lesson_id: Unique lesson identifier
            
        Returns:
            Generated filename
        """
        # Get file extension
        _, ext = os.path.splitext(original_filename)
        
        # Create readable filename
        # Format: lesson_{lesson_id}_{sanitized_original_name}.pdf
        base_name = os.path.splitext(original_filename)[0]
        sanitized_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
        sanitized_name = sanitized_name.replace(' ', '_')[:50]  # Limit length
        
        return f"lesson_{lesson_id}_{sanitized_name}{ext}"
    
    @classmethod
    async def validate_and_prepare_file(
        cls, 
        file: UploadFile, 
        file_content: bytes = None,
        max_size: int = None,
        allowed_extensions: set = None
    ) -> dict:
        """
        Validate file and return validation result as dict.
        
        Args:
            file: FastAPI UploadFile object
            file_content: File content as bytes (optional, will read if not provided)
            max_size: Maximum file size in bytes (optional, uses class default)
            allowed_extensions: Allowed file extensions (optional, uses class default)
            
        Returns:
            Dict with validation result: {'is_valid': bool, 'error': str, 'content': bytes}
        """
        try:
            # Read file content if not provided
            if file_content is None:
                file_content = await file.read()
                await file.seek(0)  # Reset for potential reuse
            
            # Use provided parameters or class defaults
            max_size = max_size or cls.MAX_FILE_SIZE
            allowed_extensions = allowed_extensions or cls.ALLOWED_EXTENSIONS
            
            # Check file size
            if len(file_content) > max_size:
                return {
                    'is_valid': False,
                    'error': f"File too large. Maximum size: {max_size // (1024*1024)}MB",
                    'content': None
                }
            
            if len(file_content) < cls.MIN_FILE_SIZE:
                return {
                    'is_valid': False,
                    'error': f"File too small. Minimum size: {cls.MIN_FILE_SIZE} bytes",
                    'content': None
                }
            
            # Check file extension
            if not file.filename:
                return {
                    'is_valid': False,
                    'error': "No filename provided",
                    'content': None
                }
            
            file_ext = None
            for ext in allowed_extensions:
                if file.filename.lower().endswith(ext.lower()):
                    file_ext = ext.lower()
                    break
            
            if not file_ext:
                return {
                    'is_valid': False,
                    'error': f"File type not allowed. Supported: {', '.join(allowed_extensions)}",
                    'content': None
                }
            
            # Validate specific file types
            is_valid, error = await cls.validate_pdf_file(file)
            if not is_valid:
                return {
                    'is_valid': False,
                    'error': error,
                    'content': None
                }
            
            return {
                'is_valid': True,
                'error': None,
                'content': file_content
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f"File validation error: {str(e)}",
                'content': None
            }


async def validate_lesson_upload(file: UploadFile) -> bytes:
    """
    Convenience function to validate lesson upload and return content.
    Raises HTTPException if validation fails.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        File content as bytes
        
    Raises:
        HTTPException: If validation fails
    """
    is_valid, error, content = await FileValidator.validate_and_prepare_file(file)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File validation failed: {error}"
        )
    
    return content
