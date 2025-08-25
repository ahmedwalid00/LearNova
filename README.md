# LearNova

LearNova is an intelligent educational platform leveraging AI to deliver personalized content, dynamic assessment tools, and deep analytics for schools. The platform helps improve educational quality and provides actionable insights for students, teachers, and administrators.

## Features
- Personalized learning content and lesson management
- Dynamic assessments, MCQ questions, and exams
- AI-powered analytics and weekly/term reporting
- Role-based access for students, teachers, parents, and admins
- Chatbot with RAG (Retrieval-Augmented Generation) for lesson interaction
- Classroom management (students, teachers, subjects association)

## Technologies Used
- FastAPI
- SQLAlchemy (async)
- PostgreSQL + PGVector
- Alembic (migrations)
- Uvicorn
- Docker & Docker Compose
- Redis (caching)
- Celery (background jobs)
- Pydantic & pydantic-settings
- passlib, python-jose (auth)

## Folder Structure
```
src/
    Api/
        routers/
        utils.py
        dependencies.py
        Controllers/
            auth_controller.py
        Schemes/
            token.py
            user.py
    Authorization/
    Chatbot/
    Controllers/
    Helpers/
    Models/
        crud/
        DBSchemes/
            Schemes/
                academic_term.py
                term_week.py
                user_models.py
                subject.py
                lesson.py
                question_models.py
                exam_models.py
                analytics.py
                associations.py
    Tests/
    utils/
Docker/
    docker-compose.yml
    Dockerfile
requirements.txt
.env
README.md
```

## Setup Instructions
1. Clone the repository:
	```bash
	git clone <repo-url>
	cd LearNova
	```
2. Install [UV](https://github.com/astral-sh/uv) (recommended for Python dependency management):
	```bash
	curl -Ls https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh | bash
	export PATH="$HOME/.local/bin:$PATH"
	```
3. Create and activate a virtual environment (optional):
	```bash
	uv venv
	source .venv/bin/activate
	```
4. Install dependencies:
    ```bash
    # If running locally (not Docker), install from src/requirements.txt
    uv pip install -r src/requirements.txt
    ```
5. Copy `.env.example` to `.env` and update environment variables as needed.
6. Start the PostgreSQL database using Docker Compose:
	```bash
	cd Docker
    docker-compose up -d db redis
	```
7. Run Alembic migrations to initialize the database tables:
	```bash
	cd .. # Go back to project root if needed
	alembic upgrade head
	```
	If you encounter errors about missing tables, ensure all models are imported in `env.py` and that your database is running.
8. Start the application:
	```bash
	uvicorn src.main:app --reload
	```

### Run with Docker Compose (API + Celery)

For a full local stack (API, DB, Redis, Celery worker/beat, Flower):

1. Create `.env.docker` at repo root (see your existing `.env` as a guide). Ensure these are set at minimum:
    - POSTGRES_*, REDIS_* variables
    - CELERY_BROKER_URL, CELERY_RESULT_BACKEND (e.g., redis URLs)
    - MAIL_* and DOMAIN if you plan to send emails
2. From the `Docker` folder, start services:
    ```bash
    docker-compose up -d --build
    ```
3. Services:
    - API: http://localhost:8000
    - Flower (Celery dashboard): http://localhost:5555

See CELERY_SETUP.md for details about queues, idempotency, and troubleshooting.

Additional notes
- Redis: We use Redis for caching and token blocklisting. When running with Docker Compose the service name is `redis` and the app expects `REDIS_HOST=redis` in the `.env` file. If you run the app locally (not in compose), use `REDIS_HOST=localhost`.
- Email: The project uses an aiosmtplib-based sender. Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, and `MAIL_FROM` in your `.env` to enable sending verification and reset emails.
- Celery: Email tasks are executed via Celery. The worker listens on `default,email_queue`. If running locally without Docker, start a worker: `celery -A src.celery_app worker --loglevel=info --queues=default,email_queue`. More in CELERY_SETUP.md.

## Usage
- Access the API at `http://localhost:8000`
- API docs available at `/docs`
- All models, relationships, and indexes are implemented as per the provided schema.

### Authentication & Authorization
- Endpoints: `/api/v1/auth/sign-up`, `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/auth/verify-email`, `/api/v1/auth/request-password-reset`, `/api/v1/auth/confirm-password-reset`, `/api/v1/auth/refresh_token`
- JWT-based access and refresh tokens (see `src/Api/utils.py`)
- Security handled via `TokenBearer` (see `src/Api/dependencies.py`)
- Passwords hashed with bcrypt/argon2
- Repository/Service/Controller pattern for clean separation:
  - Repositories: direct DB operations
  - Services: business logic (auth, token generation, validation)
  - Controllers: orchestrate logic between services & routes
- Email verification and password reset are prototyped for future async integration (Celery)

### Unique IDs & Parent Flow
- Users have human-readable, role-based `unique_id` values stored on user tables (e.g., students `22xxx`, teachers `11xxx`, parents `P22xxx`, admins `ADMINxxx`).
- Admins generate/assign student and teacher IDs. Parents register using a temporary admin-provided access code and are linked to students via the `parent_student_links` table.
- See `src/Models/DBSchemes/Schemes/user_models.py` and `src/Models/DBSchemes/Schemes/parent_student_association.py` for schema details.

## License
This project is licensed under the MIT License.
