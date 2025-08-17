
# LearNova

LearNova is an intelligent educational platform leveraging AI to deliver personalized content, dynamic assessment tools, and deep analytics for schools. The platform helps improve educational quality and provides actionable insights for students, teachers, and administrators.

## Features
- Personalized learning content
- Dynamic assessments and exams
- AI-powered analytics and reporting
- Role-based access for students, teachers, parents, and admins
- Chatbot with RAG (Retrieval-Augmented Generation) for lesson interaction

## Technologies Used
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Uvicorn
- Docker & Docker Compose
- Pydantic & pydantic-settings
- passlib, python-jose (auth)

## Folder Structure
```
Src/
  Api/
	 Routers/
	 Schemes/
  Authorization/
  Chatbot/
  Utils/
  Database/
  Models/
	 Crud/
Tests/
Dockerfile
docker-compose.yml
requirements.txt
.env
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
6. Run database migrations:
	```bash
	alembic upgrade head
	```
7. Start the application:
	```bash
	uvicorn src.main:app --reload
	```

## Usage
- Access the API at `http://localhost:8000`
- API docs available at `/docs`

## License
This project is licensed under the MIT License.
