# Agentic AI Project Management Assistant

Complete implementation of an AI-powered project management system with FastAPI backend and React frontend.

## 🌟 Overview

This project transforms the existing BOTMEDICAL Flask application into a comprehensive AI-driven project management assistant featuring:

- **FastAPI Backend** with AI integration
- **React + Vite Frontend** with modern UI
- **Local LLM Support** via Ollama
- **Real-time Collaboration** features
- **Analytics & Reporting** capabilities
- **Free Deployment** ready configuration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Supabase)    │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • REST API      │    │ • PostgreSQL    │
│ • Task Mgmt     │    │ • AI Services   │    │ • Redis Cache   │
│ • AI Chat       │    │ • WebSockets    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   AI Services   │              │
         │              │                 │              │
         └──────────────►│ • Ollama (LLM) │◄─────────────┘
                        │ • Hugging Face  │
                        │ • NLP Pipeline  │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python run_server.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📋 Features Implemented

### ✅ Backend (FastAPI)

- [x] **Core Configuration** - Environment-based settings with Pydantic
- [x] **Database Models** - SQLAlchemy models for User, Project, Task, Notification
- [x] **Authentication API** - JWT-based auth with GitHub OAuth support
- [x] **Projects API** - CRUD operations with permissions
- [x] **Tasks API** - Task management with dependencies and comments
- [x] **AI Agent API** - Natural language processing and command execution
- [x] **Analytics API** - Comprehensive reporting and metrics
- [x] **Security** - Password hashing, JWT tokens, role-based access
- [x] **AI Service** - Ollama integration with Hugging Face fallback

### ✅ Frontend (React + Vite)

- [x] **Authentication** - Login/register with context management
- [x] **Layout System** - Responsive sidebar and header
- [x] **Dashboard** - Overview with metrics and AI insights
- [x] **Routing** - Protected routes with React Router
- [x] **API Integration** - Axios-based service layer
- [x] **UI Components** - Tailwind CSS styling system
- [x] **State Management** - React Query for server state

### 🔄 In Progress

- [ ] **Task Management UI** - Drag-and-drop boards
- [ ] **AI Chat Interface** - Real-time chat with AI assistant
- [ ] **Analytics Charts** - Chart.js visualizations
- [ ] **Real-time Updates** - WebSocket integration
- [ ] **File Uploads** - Document attachment system

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM with PostgreSQL/SQLite support
- **Pydantic** - Data validation and settings
- **Ollama** - Local LLM integration
- **JWT** - Secure authentication
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **React Router** - Client-side routing
- **React Query** - Server state management
- **Axios** - HTTP client

### Infrastructure
- **Supabase** - PostgreSQL database
- **Railway** - Backend deployment
- **Netlify** - Frontend deployment
- **GitHub OAuth** - Authentication provider

## 📁 Project Structure

```
BOTMEDICAL/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Configuration and security
│   │   ├── models/         # Database models
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt
│   ├── run_server.py       # Development server
│   └── README.md
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── store/          # State management
│   │   └── App.jsx         # Main application
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
└── README.md               # This file
```

## 🤖 AI Features

### Natural Language Processing
- Intent classification for user commands
- Entity extraction for tasks and projects
- Command execution and automation

### Intelligent Assistance
- Task prioritization recommendations
- Risk analysis and early warnings
- Project timeline optimization
- Resource allocation suggestions

### Supported Commands
- "Create task 'Setup database' in project 'Website'"
- "What's the status of my projects?"
- "Show me overdue tasks"
- "Analyze project risks"

## 🔐 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control
- Input validation and sanitization
- CORS configuration
- Rate limiting support

## 📊 Analytics & Reporting

- Project completion metrics
- Task productivity analysis
- Team performance insights
- Timeline and deadline tracking
- Resource utilization reports

## 🚀 Deployment

### Backend (Railway)
1. Connect GitHub repository to Railway
2. Set environment variables
3. Deploy automatically on push

### Frontend (Netlify)
1. Connect GitHub repository to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Configure environment variables

### Local Development
```bash
# Backend
cd backend && python run_server.py

# Frontend (new terminal)
cd frontend && npm run dev
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python test_setup.py
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 📝 Environment Configuration

### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@host:5432/db
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
OLLAMA_BASE_URL=http://localhost:11434
SECRET_KEY=your-secret-key
```

### Frontend (.env.local)
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_GITHUB_CLIENT_ID=your-github-client-id
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- 📚 **Documentation**: Check the README files in backend/ and frontend/
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discussions**: Use GitHub Discussions for questions

---

**Built with ❤️ using 100% free tools and services**