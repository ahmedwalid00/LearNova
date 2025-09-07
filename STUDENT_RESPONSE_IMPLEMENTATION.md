# Student Response System Documentation

## Overview

The Student Response System enables students to answer practice questions and exams from their enrolled classrooms, with automatic performance tracking and rating calculations.

## Features Implemented

### 1. Students can answer practice questions created by their teacher in the same enrolled class

- Students can only answer practice questions from classrooms they are enrolled in
- Prevents duplicate responses (one answer per question per student)
- Tracks correctness, response time, and timestamps
- Automatically updates student ratings based on performance

### 2. Students can answer exams created by their teacher for the subject in the same enrolled class

- Students can only answer exam questions from classrooms they are enrolled in
- Prevents duplicate responses (one answer per question per student)
- Tracks correctness, response time, and timestamps
- Links responses to specific exams for comprehensive tracking

### 3. Student Rating Logic

- **Practice Performance**: Tracks accuracy rate, total questions answered, and total correct
- **Exam Performance**: Tracks exams taken, total scores, and average scores
- **Overall Rating**: Weighted combination (60% exam performance, 40% practice performance)
- **Term-based**: Ratings are calculated per academic term

## Database Schema

### New Tables

#### `practice_question_responses`
- Tracks student responses to practice questions
- Unique constraint on (student_id, practice_id)
- Includes correctness and timing data

#### `exam_question_responses`
- Tracks student responses to exam questions
- Unique constraint on (student_id, question_id)
- Links to both exam and question for context

#### `student_ratings`
- Stores calculated performance metrics per student per term
- Includes practice accuracy, exam averages, and overall rating
- Automatically updated when students answer questions

## API Endpoints

### Student Endpoints

#### Answer Practice Question
```
POST /api/v1/student/responses/practice/answer
```
**Request Body:**
```json
{
  "practice_id": "uuid",
  "answer_id": "uuid",
  "time_taken_seconds": 45
}
```

#### Answer Exam Question
```
POST /api/v1/student/responses/exam/answer
```
**Request Body:**
```json
{
  "exam_id": "uuid",
  "question_id": "uuid", 
  "answer_id": "uuid",
  "time_taken_seconds": 120
}
```

#### Get Practice Responses
```
GET /api/v1/student/responses/practice?classroom_id=uuid&limit=50&offset=0
```

#### Get Exam Responses
```
GET /api/v1/student/responses/exam?exam_id=uuid&classroom_id=uuid&limit=50&offset=0
```

#### Get Performance Summary
```
GET /api/v1/student/responses/performance
```

### Admin Endpoints

#### Get Student Practice Responses
```
GET /api/v1/student/responses/admin/student/{student_id}/practice
```

#### Get Student Exam Responses
```
GET /api/v1/student/responses/admin/student/{student_id}/exam
```

#### Get Student Performance Summary
```
GET /api/v1/student/responses/admin/student/{student_id}/performance
```

## Security Features

### Authentication & Authorization
- All endpoints require authentication
- Students can only access their own data
- Admin users can access any student's data
- Classroom enrollment verification for question access

### Validation
- Prevents students from answering questions from non-enrolled classrooms
- Validates question-exam relationships for exam questions
- Prevents duplicate responses per student per question

## Rating Calculation Logic

### Practice Rating
- Based on accuracy rate (correct answers / total answers)
- Converted to percentage (0-100)

### Exam Rating  
- Based on average exam score across all exams
- Calculated as percentage (0-100)

### Overall Rating
- Weighted average: (Exam Rating × 0.6) + (Practice Rating × 0.4)
- Updated automatically when students answer questions
- Stored per academic term for historical tracking

## Usage Examples

### Student answering a practice question:
1. Student logs in and navigates to practice questions
2. System shows only questions from enrolled classrooms
3. Student selects an answer and submits
4. System records response and updates rating
5. Student receives immediate feedback

### Student taking an exam:
1. Student accesses exam from enrolled classroom
2. System tracks responses per question
3. Prevents re-answering the same question
4. Updates performance metrics upon completion

### Viewing performance:
1. Student can view comprehensive performance summary
2. Includes practice accuracy, exam averages, and overall rating
3. Historical data preserved per academic term

## Deployment Steps

1. **Run Database Migration:**
   ```bash
   alembic upgrade head
   ```

2. **Start FastAPI Server:**
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

3. **Test Endpoints:**
   - Use Postman collection or API testing tool
   - Authenticate as student user
   - Test answering questions and viewing performance

## File Structure

```
src/
├── Models/
│   ├── DBSchemes/Schemes/
│   │   └── student_response_models.py      # Database models
│   └── repositories/
│       └── student_response_repository.py  # Data access layer
├── Services/
│   └── student_response_service.py         # Business logic
├── Controllers/
│   └── student_response_controller.py      # HTTP request handling
├── Api/
│   ├── Schemes/
│   │   └── student_response_schemes.py     # Request/response schemas
│   └── routers/StudentRoutes/
│       └── student_response_router.py      # API routes
```

## Error Handling

- **400 Bad Request**: Invalid input data or business rule violations
- **403 Forbidden**: Student not enrolled in classroom
- **404 Not Found**: Question, exam, or student not found
- **500 Internal Server Error**: System errors with detailed logging

## Performance Considerations

- Indexed database fields for fast lookups
- Pagination support for large result sets
- Efficient relationship loading to prevent N+1 queries
- Atomic operations for rating calculations

## Future Enhancements

1. **Time-based Exams**: Add exam duration limits
2. **Question Difficulty**: Weight ratings based on question difficulty
3. **Progress Tracking**: Visual progress indicators for students
4. **Analytics Dashboard**: Advanced performance analytics for teachers
5. **Gamification**: Achievement system based on performance milestones
