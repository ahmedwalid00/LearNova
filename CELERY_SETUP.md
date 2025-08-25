# Celery Setup and Email Tasks

## Overview

This project uses Celery for background task processing, specifically for sending emails (verification emails and password reset emails). The setup follows best practices with:

- Redis as both broker and result backend
- Idempotency management to prevent duplicate tasks
- Proper error handling and retry mechanisms
- Flower dashboard for monitoring tasks

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│      Redis      │────│ Celery Workers  │
│                 │    │   (Broker +     │    │                 │
│ Queue email     │    │    Backend)     │    │ Process email   │
│ tasks           │    │                 │    │ tasks           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                          ┌─────────────────┐
                          │  Flower Dashboard│
                          │  (Monitoring)    │
                          │  localhost:5555  │
                          └─────────────────┘
```

## Services

### 1. Celery Worker
- Processes background tasks
- Handles email sending with retry logic
- Uses IdempotencyManager to prevent duplicate emails

### 2. Celery Beat (Scheduler)
- Runs scheduled tasks (cleanup, maintenance)
- Runs daily cleanup of old task records

### 3. Flower Dashboard
- Web-based monitoring tool
- Available at http://localhost:5555
- Shows task status, worker health, etc.

## Environment Variables

Add these to your `.env` file:

```bash
# Celery Configuration
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"
CELERY_TASK_SERIALIZER="json"
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_ACKS_LATE=false
CELERY_WORKER_CONCURRENCY=2
```

## Running the Services

### Using Docker Compose (Recommended)

```bash
# Start all services including Celery
docker-compose up -d

# View logs
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
```

### Manual Setup (Development)

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A src.celery_app worker --loglevel=info --concurrency=4

# Terminal 3: Start Celery Beat (optional, for scheduled tasks)
celery -A src.celery_app beat --loglevel=info

# Terminal 4: Start Flower Dashboard (optional)
celery -A src.celery_app flower --port=5555

# Terminal 5: Start FastAPI App
uvicorn src.main:app --reload
```

## Email Tasks

### 1. Verification Email
- **Task**: `src.Tasks.sending_email.send_verification_email`
- **Queue**: `email_queue`
- **Triggers**: User signup
- **Idempotency**: Prevents duplicate verification emails

### 2. Password Reset Email
- **Task**: `src.Tasks.sending_email.send_password_reset_email`  
- **Queue**: `email_queue`
- **Triggers**: Password reset request
- **Idempotency**: Prevents duplicate reset emails

## Usage in Controllers

```python
# In auth_controller.py

# Queue verification email (non-blocking)
task_id = self.send_verification_email_async(
    user_email=email,
    user_name=name,
    unique_id=unique_id
)

# Queue password reset email (non-blocking)  
task_id = self.send_password_reset_email_async(
    user_email=email,
    user_name=name,
    unique_id=unique_id
)
```

## Monitoring and Debugging

### Flower Dashboard
1. Open http://localhost:5555
2. View active/completed tasks
3. Monitor worker status
4. Check task results and errors

### Task Status
Tasks can have these statuses:
- `PENDING`: Task queued but not started
- `STARTED`: Task is being processed
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed (will be retried)
- `RETRY`: Task is being retried

### Logs
```bash
# View worker logs
docker-compose logs -f celery-worker

# View beat logs  
docker-compose logs -f celery-beat

# View flower logs
docker-compose logs -f flower
```

## Task Idempotency

The system uses `IdempotencyManager` to prevent duplicate tasks:

- Tasks are identified by name + arguments hash
- Duplicate tasks within time limit are skipped
- Stuck tasks (running longer than time limit) can be re-executed
- Old task records are cleaned up daily

## Testing

```bash
# Test task queueing
python test_celery.py

# Test actual email sending (requires SMTP configuration)
# Use the API endpoints after starting all services
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   # Check Redis is running
   redis-cli ping
   ```

2. **Import Errors**
   ```bash
   # Ensure PYTHONPATH is set
   export PYTHONPATH=/path/to/project
   ```

3. **Email Not Sending**
   - Check SMTP credentials in `.env`
   - Verify Gmail app password if using Gmail
   - Check worker logs for email errors

4. **Tasks Not Processing**
   - Verify worker is running and connected
   - Check Flower dashboard for worker status
   - Ensure correct queue routing

### Performance Tuning

- Adjust `CELERY_WORKER_CONCURRENCY` based on your needs
- Monitor memory usage with multiple workers
- Scale workers horizontally for high load
- Use separate Redis instances for broker/backend in production

## Production Considerations

1. **Security**: Use Redis AUTH and SSL in production
2. **Monitoring**: Set up proper logging and alerts
3. **Scaling**: Use multiple worker instances
4. **Persistence**: Configure Redis persistence
5. **Error Handling**: Set up dead letter queues for failed tasks
