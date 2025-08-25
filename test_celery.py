#!/usr/bin/env python3
"""
Simple test script to verify Celery setup and email tasks.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Tasks.sending_email import send_verification_email, send_password_reset_email

def test_celery_tasks():
    """Test that Celery tasks can be queued."""
    print("Testing Celery email tasks...")
    
    try:
        # Test verification email task
        print("Queuing verification email task...")
        task1 = send_verification_email.delay(
            user_email="test@example.com",
            user_name="Test User",
            unique_id="22001"
        )
        print(f"Verification email task queued: {task1.id}")
        
        # Test password reset email task
        print("Queuing password reset email task...")
        task2 = send_password_reset_email.delay(
            user_email="test@example.com",
            user_name="Test User",
            unique_id="22001"
        )
        print(f"Password reset email task queued: {task2.id}")
        
        print("Tasks queued successfully!")
        print("Check Flower dashboard at http://localhost:5555 to monitor tasks")
        
    except Exception as e:
        print(f"Error testing Celery tasks: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_celery_tasks()
