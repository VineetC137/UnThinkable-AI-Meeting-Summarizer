# Meeting Summarizer Enterprise

A complete enterprise-grade AI-powered meeting transcription and summarization platform built with FastAPI, React, and modern AI technologies.

## 🚀 Overview

The Meeting Summarizer Enterprise transforms audio recordings into intelligent summaries using cutting-edge AI technology. Built with a clean architecture and modern technologies, it provides:

- **Multi-Provider AI Pipeline**: Support for Whisper.cpp, OpenAI Whisper, Faster-Whisper for transcription and Ollama, OpenAI GPT, Gemini, Claude for summarization
- **Speaker Diarization**: Identify and separate different speakers using pyannote.audio
- **Structured Analysis**: Generate executive summaries, key decisions, action items, risks, and open questions
- **Enterprise Features**: JWT authentication, role-based access, background processing, monitoring, and more
- **Modern Tech Stack**: FastAPI backend, React TypeScript frontend, PostgreSQL, Redis, Celery

![Meeting Summarizer Interface](https://github.com/user-attachments/assets/5b93cfed-c853-4ebb-8d90-bbda58354192)

## ✨ Key Features

### AI & Processing
- 🎯 **Multiple ASR Providers**: Whisper.cpp (local), OpenAI Whisper API, Faster-Whisper
- 🤖 **Multiple LLM Providers**: Ollama (local), OpenAI GPT, Google Gemini, Anthropic Claude
- 🎭 **Speaker Diarization**: Automatic speaker identification and separation
- 📊 **Structured Output**: Executive summaries, detailed summaries, action items, key decisions, risks, open questions, keywords
- 🔄 **Background Processing**: Non-blocking audio processing with real-time status updates

### Enterprise Features
- 🔐 **JWT Authentication**: Secure token-based authentication with refresh tokens
- 👥 **Role-Based Access**: Admin, User, and Viewer roles with appropriate permissions
- 🗂️ **Meeting Management**: Upload, organize, search, and manage meeting recordings
- 📈 **Analytics & Insights**: Comprehensive analytics and reporting dashboard
- 📤 **Export Options**: PDF, DOCX, Markdown, and JSON export formats
- 🔍 **Advanced Search**: Full-text search across meetings with filters and tags

### User Interface
- 💻 **Modern React UI**: Clean, responsive interface built with TypeScript and Tailwind CSS
- 🌙 **Dark Mode Support**: System-aware theme switching
- 📱 **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- 🔔 **Real-time Updates**: Live processing status and notifications
- 🎨 **Accessible Design**: WCAG compliant with keyboard navigation and screen reader support

### DevOps & Production
- 🐳 **Containerized**: Full Docker setup with docker-compose
- 📊 **Monitoring**: Prometheus metrics and Grafana dashboards
- 🏗️ **CI/CD Ready**: GitHub Actions workflows for automated testing and deployment
- 🔒 **Security**: Rate limiting, CORS, input validation, and secure file uploads
- 📋 **Health Checks**: Comprehensive health monitoring for all services

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI with Pydantic validation
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with refresh tokens
- **Background Tasks**: Celery with Redis broker
- **AI Integration**: Multiple provider support (Whisper, OpenAI, Ollama, etc.)
- **File Processing**: FFmpeg for audio preprocessing
- **Monitoring**: Prometheus metrics

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom component library
- **State Management**: Zustand for global state
- **API Client**: React Query for data fetching and caching
- **Forms**: React Hook Form with validation
- **File Upload**: React Dropzone with progress tracking
- **Charts**: Recharts for analytics visualization

### Infrastructure
- **Containerization**: Docker and Docker Compose
- **Reverse Proxy**: Nginx with SSL termination
- **Databases**: PostgreSQL for data, Redis for caching/queues
- **Monitoring**: Prometheus + Grafana stack
- **CI/CD**: GitHub Actions workflows

## 📋 Prerequisites

Before installation, ensure you have:

- **Docker** and **Docker Compose** installed
- **Python 3.11+** (for local development)
- **Node.js 18+** and **npm** (for frontend development)
- **PostgreSQL** (if running without Docker)
- **Redis** (if running without Docker)
- **FFmpeg** for audio processing

### AI Service Prerequisites
- **Ollama** installed locally (for local LLM processing)
- **API Keys** for external providers:
  - OpenAI API key (for GPT and Whisper API)
  - Google API key (for Gemini)
  - Anthropic API key (for Claude)
  - HuggingFace token (for speaker diarization)

## 🚀 Quick Start

### 🔒 Security Setup (Important!)

Before running the application, you must configure environment variables to secure your installation:

1. **Backend Configuration**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and replace all placeholder values:
   # - SECRET_KEY: Generate a secure 32+ character secret key
   # - Database credentials if using external database
   # - API keys for external AI services (OpenAI, Gemini, Claude, etc.)
   ```

2. **Docker Configuration**
   ```bash
   cp .env.docker.example .env.docker
   # Edit .env.docker and update:
   # - POSTGRES_PASSWORD: Use a strong password
   # - SECRET_KEY: Same as backend/.env
   # - GF_SECURITY_ADMIN_PASSWORD: Secure Grafana admin password
   ```

3. **Verify Security**
   ```bash
   # Ensure sensitive files are not tracked by Git
   git status
   # .env files should NOT appear in untracked files
   ```

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/VineetC137/UnThinkable-AI-Meeting-Summarizer.git
   cd UnThinkable-AI-Meeting-Summarizer
   ```

2. **Configure environment (REQUIRED - See Security Setup above)**
   ```bash
   cp backend/.env.example backend/.env
   cp .env.docker.example .env.docker
   # Edit both files with secure values
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Flower (Celery monitoring): http://localhost:5555
   - Grafana (monitoring): http://localhost:3001

### Option 2: Local Development

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Setup database
   alembic upgrade head
   
   # Start backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Start supporting services**
   ```bash
   # PostgreSQL, Redis, and Ollama must be running
   # Start Celery worker
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

## 📊 API Documentation

The API is fully documented with OpenAPI/Swagger. Access the interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

#### Meetings
- `GET /api/v1/meetings` - List meetings with pagination
- `POST /api/v1/meetings` - Upload new meeting
- `GET /api/v1/meetings/{id}` - Get meeting details
- `POST /api/v1/meetings/{id}/process` - Start processing
- `POST /api/v1/meetings/{id}/export` - Export meeting

#### Health & Monitoring
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed system status
- `GET /api/v1/health/providers` - AI provider status

## 🔧 Configuration

### Environment Variables

Key configuration options in `backend/.env`:

```env
# Application
APP_NAME="Meeting Summarizer Enterprise"
DEBUG=False
SECRET_KEY="your-secret-key-here"

# Database
DATABASE_URL="postgresql://user:pass@localhost:5432/meeting_summarizer"

# Redis
REDIS_URL="redis://localhost:6379/0"

# AI Services
OLLAMA_SERVER_URL="http://localhost:11434"
OPENAI_API_KEY="your-openai-key"
GOOGLE_API_KEY="your-google-key"
ANTHROPIC_API_KEY="your-anthropic-key"
HUGGINGFACE_TOKEN="your-hf-token"

# File Upload
MAX_FILE_SIZE=104857600  # 100MB
UPLOAD_DIR="./uploads"
```

### AI Provider Setup

#### Local Providers
1. **Whisper.cpp**: Automatically built during Docker setup
2. **Ollama**: Install locally and download models:
   ```bash
   ollama pull llama2
   ollama pull codellama
   ```

#### Cloud Providers
1. **OpenAI**: Get API key from https://platform.openai.com/
2. **Google Gemini**: Get API key from https://makersuite.google.com/
3. **Anthropic Claude**: Get API key from https://console.anthropic.com/

## 🏗️ Architecture

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   FastAPI       │    │   PostgreSQL    │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         └──────────────┤   (Cache/Queue) ├──────────────┘
                        └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Celery Workers │
                        │ (Background     │
                        │  Processing)    │
                        └─────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────────┐
                    │      AI Services            │
                    │  ┌─────────┬─────────┐      │
                    │  │Whisper  │ Ollama  │      │
                    │  │ (ASR)   │ (LLM)   │      │
                    │  └─────────┴─────────┘      │
                    └─────────────────────────────┘
```

### Clean Architecture Layers

```
┌──────────────────────────────────────┐
│             Presentation             │  ← React Components, API Routes
├──────────────────────────────────────┤
│             Application              │  ← Use Cases, Services
├──────────────────────────────────────┤
│              Domain                  │  ← Entities, Business Logic
├──────────────────────────────────────┤
│            Infrastructure            │  ← Database, External APIs
└──────────────────────────────────────┘
```

## 🔐 Security Features

### Authentication & Authorization
- JWT tokens with refresh mechanism
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Session management

### API Security
- Rate limiting (60 requests/minute default)
- CORS configuration
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy ORM
- File upload validation and sanitization

### Infrastructure Security
- Security headers (CSP, HSTS, X-Frame-Options)
- Non-root Docker containers
- Environment variable management
- SSL/TLS support with Let's Encrypt

## 📊 Monitoring & Observability

### Metrics & Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **Health Checks**: Application and dependency monitoring
- **Structured Logging**: JSON logs with correlation IDs

### Key Metrics Tracked
- Request latency and throughput
- Processing queue length
- AI provider response times
- Error rates and types
- Resource utilization

### Logging
- Structured JSON logging with correlation IDs
- Log levels: DEBUG, INFO, WARN, ERROR
- Request/response logging
- Performance metrics

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Testing
```bash
cd frontend
npm run test
npm run test:coverage
```

### API Testing
```bash
# Test with curl
curl -X GET http://localhost:8000/health

# Load testing with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health
```

## 🚀 Deployment

### Production Deployment with Docker

1. **Configure production environment**
   ```bash
   cp backend/.env.example backend/.env.production
   # Update with production values
   ```

2. **Build and deploy**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Setup SSL certificates**
   ```bash
   # Using Let's Encrypt
   docker run --rm -v ./nginx/ssl:/etc/letsencrypt \
     certbot/certbot certonly --webroot -w /var/www/certbot \
     -d yourdomain.com
   ```

### Kubernetes Deployment
See `k8s/` directory for Kubernetes manifests and Helm charts.

### CI/CD Pipeline
GitHub Actions workflows are provided for:
- Automated testing on PRs
- Docker image building and publishing
- Deployment to staging/production environments

## 📚 Usage Guide

### 1. User Registration & Login
1. Navigate to the application
2. Click "Register" to create a new account
3. Verify email (if email service is configured)
4. Login with credentials

### 2. Upload Meeting
1. Go to "Upload" page
2. Drag & drop audio file or click to browse
3. Fill in meeting details (title, description, context)
4. Select AI processing providers
5. Click "Upload & Process"

### 3. View Results
1. Monitor processing status on meeting detail page
2. View transcript, summary, and structured analysis when complete
3. Export results in various formats (PDF, DOCX, etc.)

### 4. Meeting Management
1. Browse meetings in the "Meetings" page
2. Use search and filters to find specific recordings
3. View analytics and insights in the dashboard

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- Python: Follow PEP 8, use Black for formatting
- TypeScript: Use ESLint and Prettier
- Commits: Use conventional commit messages
- Documentation: Update docs for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **whisper.cpp** by Georgi Gerganov for efficient local speech recognition
- **Ollama** for accessible local language models
- **FastAPI** team for the excellent web framework
- **React** team for the robust frontend framework
- **pyannote.audio** for speaker diarization capabilities
- **OpenAI** for Whisper and GPT models

## 📞 Support

- **Documentation**: Check this README and API docs
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Community**: Join our Discord/Slack community

## 🗺️ Roadmap

### v1.1 (Next Release)
- [ ] Real-time transcription for live meetings
- [ ] Integration with video conferencing platforms
- [ ] Advanced speaker recognition and profiles
- [ ] Custom prompt templates

### v1.2 (Future)
- [ ] Mobile application (React Native)
- [ ] Advanced analytics and reporting
- [ ] Integration with calendar systems
- [ ] Multi-language support

### v2.0 (Long-term)
- [ ] AI-powered meeting insights and recommendations
- [ ] Integration with project management tools
- [ ] Advanced security features (SAML, LDAP)
- [ ] Enterprise deployment options

---

**Built with ❤️ by [VineetC137](https://github.com/VineetC137)**

*Transform your meetings into actionable insights with UnThinkable AI!*