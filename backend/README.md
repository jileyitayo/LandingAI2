# SiteSmith Backend API

FastAPI backend for SiteSmith - AI Website Builder for African Entrepreneurs.

## 🚀 Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.12+
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Supabase Auth
- **AI:** OpenAI GPT-4
- **Payments:** Stripe
- **Deployment:** Vercel

## 📋 Prerequisites

- Python 3.12 or higher
- pip or poetry
- Docker (optional)

## 🛠️ Setup Instructions

### 1. Install uv (if not already installed)

```bash
# Install uv - fast Python package installer
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create a virtual environment and install dependencies

```bash
cd backend

# Create virtual environment
uv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate

# Install dependencies with uv
uv pip install -r requirements.txt
```

### 3. Set up environment variables

Copy the `.env.example` file to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Stripe
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Vercel
VERCEL_API_TOKEN=your_vercel_api_token
VERCEL_TEAM_ID=your_vercel_team_id
```

### 4. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🐳 Docker Setup

### Build and run with Docker

```bash
# Build the image
docker build -t sitesmith-backend .

# Run the container
docker run -p 8000:8000 --env-file .env sitesmith-backend
```

### Using Docker Compose (from project root)

```bash
# From the project root directory
docker-compose up backend
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── config.py         # Configuration settings
│   ├── routers/          # API route handlers
│   │   ├── __init__.py
│   │   └── health.py     # Health check endpoints
│   ├── models/           # Database models and schemas
│   │   └── __init__.py
│   ├── services/         # Business logic and external services
│   │   └── __init__.py
│   └── utils/            # Utility functions
│       └── __init__.py
├── tests/                # Test files
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── .env.example         # Environment variables template
└── README.md           # This file
```

## 🔌 API Endpoints

### Health Check

```bash
GET /api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "message": "SiteSmith API is running"
}
```

### Root

```bash
GET /
```

Response:
```json
{
  "message": "Welcome to SiteSmith API",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health"
}
```

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_health.py
```

## 📝 Development Commands

```bash
# Run development server with auto-reload
uvicorn app.main:app --reload

# Run on specific port
uvicorn app.main:app --reload --port 8080

# Format code with black
black app/

# Lint with flake8
flake8 app/

# Type check with mypy
mypy app/
```

## 🚀 Deployment

### Vercel (Serverless)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel
```

### Docker Production

```bash
# Build production image
docker build -t sitesmith-backend:prod .

# Run production container
docker run -d -p 8000:8000 --env-file .env sitesmith-backend:prod
```

## 🔒 Security

- All sensitive data stored in environment variables
- CORS configured for frontend origin
- Rate limiting on API endpoints (coming soon)
- Input validation with Pydantic
- SQL injection prevention with Supabase client

## 📚 API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Run linting and tests
5. Submit a pull request

## 🆘 Troubleshooting

### Port already in use

```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

### Module not found errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Environment variables not loading

Make sure your `.env` file is in the `backend/` directory and properly formatted.

## 📄 License

This project is private and proprietary.

---

Built with ❤️ for African Entrepreneurs

