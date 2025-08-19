# Database Session Usage Guide

## ✅ Correct Usage with get_db_session

### FastAPI Endpoint Pattern

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.Helpers.db_session import get_db_session
from src.Models.repositories import StudentRepository
from src.Models.services import UserService

router = APIRouter()

@router.post("/students")
async def create_student(
    data: StudentSchema, 
    session: AsyncSession = Depends(get_db_session)
):
    # ✅ CORRECT: Use session from dependency
    student_repo = StudentRepository(session)
    user_service = UserService(session)
    
    # All operations use the same session
    # get_db_session handles commit/rollback
    student = await student_repo.create(**data.dict())
    return student

@router.post("/complex-operation")
async def complex_operation(
    data: ComplexSchema,
    session: AsyncSession = Depends(get_db_session)
):
    # ✅ CORRECT: Multiple repos with same session
    lesson_repo = LessonRepository(session)
    chunk_repo = LessonChunkRepository(session)
    user_service = UserService(session)
    
    # All operations are atomic within this request
    lesson = await lesson_repo.create(**data.lesson)
    chunks = await chunk_repo.insert_many_chunks(data.chunks)
    
    return {"lesson": lesson, "chunks": chunks}
```

### Service Pattern

```python
# ✅ CORRECT: Service manages business logic
@router.post("/lesson-with-chunks")
async def create_lesson_with_chunks(
    data: LessonSchema,
    session: AsyncSession = Depends(get_db_session)
):
    lesson_service = LessonService(session)
    
    # Service handles complex operations atomically
    result = await lesson_service.create_lesson_with_chunks(
        data.lesson, data.chunks
    )
    return result
```

## ❌ Anti-Patterns to Avoid

### DON'T: Call commit/rollback in repositories or services

```python
# ❌ WRONG: Don't do this
async def create(self, **kwargs):
    instance = self.model(**kwargs)
    self.session.add(instance)
    await self.session.commit()  # ❌ Conflicts with get_db_session
    return instance

# ❌ WRONG: Don't do this  
async def some_service_method(self):
    try:
        # ... operations
    except Exception:
        await self.session.rollback()  # ❌ Let get_db_session handle this
```

### DON'T: Create your own sessions

```python
# ❌ WRONG: Don't create new sessions
async def bad_endpoint():
    # Don't do this - bypasses get_db_session transaction management
    session = create_async_session()
    repo = StudentRepository(session)
```

## ✅ Exception Handling Best Practices

### Repository Level (Minimal)
- Validate essential inputs (None checks)
- Convert database errors to meaningful ValueError/RuntimeError
- Let exceptions bubble up to get_db_session for rollback

### Service Level (Business Logic)
- Validate business rules
- Coordinate multiple repository operations
- Let get_db_session handle transaction management

### FastAPI Level (User-Facing)
- Catch service exceptions
- Convert to appropriate HTTP status codes
- Log errors for debugging

```python
@router.post("/students")
async def create_student(
    data: StudentSchema,
    session: AsyncSession = Depends(get_db_session)
):
    try:
        user_service = UserService(session)
        student = await user_service.create_student(data.dict())
        return student
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## 🔧 Key Benefits of This Approach

1. **Single Transaction per Request**: Entire request is atomic
2. **Automatic Rollback**: get_db_session handles errors automatically  
3. **Simple & Flexible**: Easy to use multiple repos/services per endpoint
4. **Consistent**: Same session across all operations in a request
5. **Testable**: Easy to mock session for unit tests

## 📝 Quick Checklist

- ✅ Use `session: AsyncSession = Depends(get_db_session)` in endpoints
- ✅ Pass the same session to all repos/services in an endpoint  
- ✅ Use `flush()` in repositories, not `commit()`
- ✅ Let get_db_session handle commit/rollback
- ✅ Add minimal validation at critical entry points
- ✅ Convert database errors to meaningful exceptions
