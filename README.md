
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
		schemas/
		Schemes/
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
	uv pip install -r requirements.txt
	```
5. Copy `.env.example` to `.env` and update environment variables as needed.
6. Start the PostgreSQL database using Docker Compose:
	```bash
	cd Docker
	docker-compose up -d db
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

## Usage
- Access the API at `http://localhost:8000`
- API docs available at `/docs`
- All models, relationships, and indexes are implemented as per the provided schema.

## License
This project is licensed under the MIT License.
