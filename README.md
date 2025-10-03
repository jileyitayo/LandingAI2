# SiteSmith - AI Website Builder

AI Website Builder for African Entrepreneurs. Create professional websites in minutes using natural language.

## 🏗️ Project Structure

```
LandingV2/
├── frontend/          # Next.js 15 frontend application
├── backend/           # FastAPI backend API (coming soon)
├── prd.md            # Product Requirements Document
└── README.md         # This file
```

## 🚀 Tech Stack

### Frontend
- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Deployment:** Vercel

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** Supabase (PostgreSQL)
- **Authentication:** Supabase Auth
- **Payments:** Stripe

## 📋 Prerequisites

- Node.js 20.x or higher
- Python 3.11 or higher
- Docker (optional)
- npm or yarn

## 🛠️ Quick Start

### Frontend Development

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your credentials
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)

### Backend Development (Coming Soon)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend API will be available at [http://localhost:8000](http://localhost:8000)

## 🐳 Docker Setup

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop all services
docker-compose down
```

## 📖 Documentation

- [Frontend README](./frontend/README.md) - Frontend setup and development
- [Product Requirements](./prd.md) - Complete product specification
- [Backend README](./backend/README.md) - Backend setup (coming soon)

## 🎯 MVP Features

- ✅ User authentication (Supabase)
- ✅ AI website generation (OpenAI)
- ✅ Live preview system
- ✅ Basic content editing
- ✅ One-click publishing
- ✅ Subscription management (Stripe)
- ✅ WhatsApp integration

## 📝 Development Phases

### Phase 1: Foundation ✅ (In Progress)
- [x] Frontend project setup
- [ ] Backend project setup
- [ ] Supabase configuration
- [ ] Database schema

### Phase 2: Authentication (Next)
- [ ] Login/Signup UI
- [ ] Auth API endpoints
- [ ] Protected routes
- [ ] Profile management

See [prd.md](./prd.md) for complete development roadmap.

## 🤝 Contributing

This is a private project. For questions or contributions, contact the development team.

## 📄 License

This project is private and proprietary.

---

Built with ❤️ for African Entrepreneurs
