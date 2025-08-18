# Database Operations Design Pattern - LearNova

This document explains the Repository and Service pattern implementation for handling database operations in the LearNova project.

## Architecture Overview

### 1. Repository Pattern
The Repository pattern encapsulates data access logic and provides a uniform interface for accessing domain objects.

**Structure:**
```
src/Models/repositories/
├── __init__.py
├── base.py                 # BaseRepository with common CRUD operations
├── user_repository.py      # User-related repositories
├── lesson_repository.py    # Lesson-related repositories
├── exam_repository.py      # Exam-related repositories
└── analytics_repository.py # Analytics-related repositories
```

**Benefits:**
- Centralized data access logic
- Consistent CRUD operations across all models
- Easy to test with mocking
- Type-safe operations with generics

### 2. Service Pattern
Services orchestrate business logic and can use multiple repositories to perform complex operations.

**Structure:**
```
src/Models/services/
├── __init__.py
├── user_service.py     # User authentication, family management
├── lesson_service.py   # Lesson creation, content search
└── exam_service.py     # Exam management, analytics
```

**Benefits:**
- Encapsulates business logic
- Manages transactions across multiple entities
- Provides higher-level abstractions
- Handles complex workflows

## Key Classes

### BaseRepository
Abstract base class providing common CRUD operations:
- `create(**kwargs)` - Create new record
- `get_by_id(id)` - Get record by primary key
- `get_all(offset, limit, filters)` - List records with pagination
- `update(id, **kwargs)` - Update record
- `delete(id)` - Delete record
- `exists(id)` - Check if record exists
- `count(filters)` - Count records

### Specific Repositories
Each model has its own repository class inheriting from BaseRepository:

**StudentRepository:**
- `get_by_email(email)`
- `get_by_parent_id(parent_id)`
- `get_by_rating_range(min_rating, max_rating)`
- `get_verified_students()`

**LessonRepository:**
- `get_by_teacher_id(teacher_id)`
- `get_by_subject_id(subject_id)`
- `get_top_rated_lessons(limit)`

**ExamRepository:**
- `get_upcoming_exams(teacher_id)`
- `get_by_date_range(start_date, end_date)`

### Service Classes

**UserService:**
- `authenticate_user(email, password_hash)` - Cross-user-type authentication
- `get_family_info(parent_id)` - Get parent and children data
- `update_user_verification_status()` - Update verification across user types

**LessonService:**
- `create_lesson_with_chunks()` - Transactional lesson creation
- `get_teacher_lessons_with_stats()` - Lessons with analytics
- `search_lessons_by_content()` - Content-based search

**ExamService:**
- `submit_exam_result()` - Submit result and update ratings
- `get_exam_analytics()` - Comprehensive exam statistics
- `get_student_exam_history()` - Student performance history

## Usage Patterns

### 1. Simple CRUD Operations
```python
# Use repositories directly
async def get_student(student_id: UUID, session: AsyncSession):
    student_repo = StudentRepository(session)
    return await student_repo.get_by_id(student_id)
```

### 2. Complex Business Logic
```python
# Use services for business logic
async def authenticate_user(email: str, password: str, session: AsyncSession):
    user_service = UserService(session)
    return await user_service.authenticate_user(email, password)
```

### 3. FastAPI Integration
```python
@router.post("/exams/{exam_id}/submit")
async def submit_exam(
    exam_id: UUID,
    submission: ExamSubmissionSchema,
    session: AsyncSession = Depends(get_async_session)
):
    exam_service = ExamService(session)
    result = await exam_service.submit_exam_result(
        submission.student_id,
        exam_id,
        submission.score,
        submission.rating
    )
    return result
```

## Best Practices

### 1. When to Use Repositories
- Simple CRUD operations
- Model-specific queries
- Data validation at the model level
- Direct database access needs

### 2. When to Use Services
- Complex business logic involving multiple models
- Operations requiring transactions
- Data aggregation and analytics
- Cross-cutting concerns (authentication, authorization)

### 3. Error Handling
```python
try:
    result = await service.complex_operation()
    return result
except Exception as e:
    await session.rollback()
    raise HTTPException(status_code=500, detail="Operation failed")
```

### 4. Dependency Injection
```python
# Create repositories/services per request
async def endpoint(session: AsyncSession = Depends(get_async_session)):
    student_repo = StudentRepository(session)
    user_service = UserService(session)
    # Use repositories and services
```

## Testing Strategy

### Repository Testing
```python
async def test_student_repository():
    # Mock the database session
    mock_session = AsyncMock()
    student_repo = StudentRepository(mock_session)
    
    # Test repository methods
    result = await student_repo.get_by_email("test@example.com")
    assert result is not None
```

### Service Testing
```python
async def test_user_service():
    # Mock repositories
    mock_session = AsyncMock()
    user_service = UserService(mock_session)
    
    # Test business logic
    auth_result = await user_service.authenticate_user("email", "hash")
    assert auth_result["user_type"] == "student"
```

## Performance Considerations

1. **Lazy Loading:** Use `lazy="select"` in relationships
2. **Pagination:** Always implement offset/limit in list operations
3. **Indexing:** Ensure proper database indexes for common queries
4. **Connection Pooling:** Use async connection pooling
5. **Query Optimization:** Use `selectinload` for eager loading when needed

## Future Extensions

1. **Caching Layer:** Add Redis caching to repositories
2. **Event System:** Add domain events for business logic
3. **Audit Trail:** Add created/updated timestamps and user tracking
4. **Soft Deletes:** Implement soft delete pattern
5. **Multi-tenancy:** Add tenant isolation for schools

This architecture provides a solid foundation for scalable, maintainable database operations while keeping business logic separate from data access concerns.
