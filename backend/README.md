# Agentic AI Project Management Assistant - Backend

A FastAPI-based backend for an AI-powered project management system.

## Features

- **FastAPI** for high-performance API development
- **SQLAlchemy** with support for PostgreSQL and SQLite
- **JWT Authentication** with GitHub OAuth integration
- **AI Integration** with Ollama (local LLM) and Hugging Face
- **Real-time features** with WebSocket support
- **Comprehensive API** for project and task management
- **Analytics and reporting** capabilities

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL (for production) or SQLite (for development)
- Redis (for caching)
- Ollama (for local AI features)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize the database:
```bash
# The database will be created automatically when you run the app
```

4. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key settings:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: For session security
- `GITHUB_CLIENT_ID` & `GITHUB_CLIENT_SECRET`: For OAuth
- `OLLAMA_BASE_URL`: Local LLM endpoint
- `HUGGING_FACE_API_KEY`: Fallback AI service

### Database Setup

#### Development (SQLite)
```bash
DATABASE_URL=sqlite:///./project_management.db
```

#### Production (Supabase)
```bash
DATABASE_URL=postgresql://user:password@db.host:5432/database_name
```

## AI Integration

### Ollama (Local LLM)

1. Install Ollama:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

2. Pull a model:
```bash
ollama pull llama2
```

3. The AI service will automatically use Ollama for natural language processing.

### Hugging Face (Fallback)

Set your Hugging Face API key in the environment:
```bash
HUGGING_FACE_API_KEY=your-api-key
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/github-oauth` - GitHub OAuth login
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Tasks
- `GET /api/tasks` - List tasks
- `POST /api/tasks` - Create task
- `GET /api/tasks/{id}` - Get task details
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### AI Assistant
- `POST /api/ai/chat` - Send message to AI
- `GET /api/ai/sessions` - Get chat sessions
- `POST /api/ai/analyze-project/{id}` - Analyze project
- `POST /api/ai/suggest-priorities` - Get priority suggestions

### Analytics
- `GET /api/analytics/overview` - Overview analytics
- `GET /api/analytics/project/{id}/analytics` - Project analytics
- `GET /api/analytics/reports/productivity` - Productivity reports

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
flake8 .
```

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── core/                # Core functionality
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── security.py      # Authentication
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── task.py
│   │   └── notification.py
│   ├── api/                 # API endpoints
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   ├── users.py
│   │   ├── ai_agent.py
│   │   └── analytics.py
│   └── services/            # Business logic
│       ├── ai_service.py
│       ├── task_service.py
│       └── notification_service.py
├── requirements.txt
├── .env.example
└── README.md
```

## Deployment

### Railway (Recommended)

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

### Docker

```bash
# Build image
docker build -t project-management-api .

# Run container
docker run -p 8000:8000 project-management-api
```

### Manual Deployment

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Security

- JWT tokens with configurable expiration
- Password hashing with bcrypt
- Rate limiting support
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy

## License

MIT License