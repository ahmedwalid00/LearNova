from src.celery_app import celery_app, get_setup_utils
from src.Helpers.config import get_settings
from src.Helpers.idempotency_manager import IdempotencyManager
from src.email_config import create_message, mail
from src.Api.utils import TokenSerializer
import asyncio
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

@celery_app.task(
    bind=True, 
    name="src.Tasks.sending_email.send_verification_email",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def send_verification_email(self, user_email: str, user_name: str, unique_id: str):
    """
    Celery task to send verification email.
    """
    return asyncio.run(
        _send_verification_email(self, user_email, user_name, unique_id)
    )

@celery_app.task(
    bind=True, 
    name="src.Tasks.sending_email.send_password_reset_email",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60}
)
def send_password_reset_email(self, user_email: str, user_name: str, unique_id: str):
    """
    Celery task to send password reset email.
    """
    return asyncio.run(
        _send_password_reset_email(self, user_email, user_name, unique_id)
    )

async def _send_verification_email(task_instance, user_email: str, user_name: str, unique_id: str):
    """
    Internal async function to handle verification email sending.
    """
    db_engine = None
    
    try:
        # Get database setup
        (db_engine, db_client) = await get_setup_utils()
        
        # Create idempotency manager
        idempotency_manager = IdempotencyManager(db_client, db_engine)
        
        # Define task arguments for idempotency check
        task_args = {
            "user_email": user_email,
            "user_name": user_name,
            "unique_id": unique_id,
            "email_type": "verification"
        }
        
        task_name = "src.Tasks.sending_email.send_verification_email"
        
        # Check if task should execute
        should_execute, existing_task = await idempotency_manager.should_execute_task(
            task_name=task_name,
            task_args=task_args,
            celery_task_id=task_instance.request.id,
            task_time_limit=settings.CELERY_TASK_TIME_LIMIT
        )
        
        if not should_execute:
            logger.info(f"Verification email task already processed for {user_email}")
            return existing_task.result
        
        # Create or update task record
        task_record = None
        if existing_task:
            await idempotency_manager.update_task_status(
                execution_id=existing_task.execution_id,
                status='PENDING'
            )
            task_record = existing_task
        else:
            task_record = await idempotency_manager.create_task_record(
                task_name=task_name,
                task_args=task_args,
                celery_task_id=task_instance.request.id
            )
        
        # Update status to STARTED
        await idempotency_manager.update_task_status(
            execution_id=task_record.execution_id,
            status='STARTED'
        )
        
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
        
        result = {
            "success": True,
            "message": f"Verification email sent to {user_email}",
            "email": user_email
        }
        
        # Update task status to SUCCESS
        await idempotency_manager.update_task_status(
            execution_id=task_record.execution_id,
            status='SUCCESS',
            result=result
        )
        
        logger.info(f"Verification email sent successfully to {user_email}")
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "email": user_email
        }
        
        # Update task status to FAILURE if we have a task record
        if 'task_record' in locals() and task_record:
            await idempotency_manager.update_task_status(
                execution_id=task_record.execution_id,
                status='FAILURE',
                result=error_result
            )
        
        logger.error(f"Failed to send verification email to {user_email}: {str(e)}")
        raise
        
    finally:
        try:
            if db_engine:
                await db_engine.dispose()
        except Exception as e:
            logger.error(f"Task cleanup failed: {str(e)}")

async def _send_password_reset_email(task_instance, user_email: str, user_name: str, unique_id: str):
    """
    Internal async function to handle password reset email sending.
    """
    db_engine = None
    
    try:
        # Get database setup
        (db_engine, db_client) = await get_setup_utils()
        
        # Create idempotency manager
        idempotency_manager = IdempotencyManager(db_client, db_engine)
        
        # Define task arguments for idempotency check
        task_args = {
            "user_email": user_email,
            "user_name": user_name,
            "unique_id": unique_id,
            "email_type": "password_reset"
        }
        
        task_name = "src.Tasks.sending_email.send_password_reset_email"
        
        # Check if task should execute
        should_execute, existing_task = await idempotency_manager.should_execute_task(
            task_name=task_name,
            task_args=task_args,
            celery_task_id=task_instance.request.id,
            task_time_limit=settings.CELERY_TASK_TIME_LIMIT
        )
        
        if not should_execute:
            logger.info(f"Password reset email task already processed for {user_email}")
            return existing_task.result
        
        # Create or update task record
        task_record = None
        if existing_task:
            await idempotency_manager.update_task_status(
                execution_id=existing_task.execution_id,
                status='PENDING'
            )
            task_record = existing_task
        else:
            task_record = await idempotency_manager.create_task_record(
                task_name=task_name,
                task_args=task_args,
                celery_task_id=task_instance.request.id
            )
        
        # Update status to STARTED
        await idempotency_manager.update_task_status(
            execution_id=task_record.execution_id,
            status='STARTED'
        )
        
        # Create reset token
        token_data = {
            "email": user_email,
            "unique_id": unique_id,
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
            <p>Hello {user_name},</p>
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
            recipients=[user_email],
            subject=subject,
            body=html_content
        )
        await mail.send_message(message)
        
        result = {
            "success": True,
            "message": f"Password reset email sent to {user_email}",
            "email": user_email
        }
        
        # Update task status to SUCCESS
        await idempotency_manager.update_task_status(
            execution_id=task_record.execution_id,
            status='SUCCESS',
            result=result
        )
        
        logger.info(f"Password reset email sent successfully to {user_email}")
        return result
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "email": user_email
        }
        
        # Update task status to FAILURE if we have a task record
        if 'task_record' in locals() and task_record:
            await idempotency_manager.update_task_status(
                execution_id=task_record.execution_id,
                status='FAILURE',
                result=error_result
            )
        
        logger.error(f"Failed to send password reset email to {user_email}: {str(e)}")
        raise
        
    finally:
        try:
            if db_engine:
                await db_engine.dispose()
        except Exception as e:
            logger.error(f"Task cleanup failed: {str(e)}")
