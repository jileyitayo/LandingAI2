# SiteSmith Frontend

AI Website Builder for African Entrepreneurs - Built with Next.js 15, TypeScript, and Tailwind CSS.

## 🚀 Tech Stack

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Authentication:** Supabase Auth
- **Database:** Supabase (PostgreSQL)
- **Payments:** Stripe
- **Deployment:** Vercel

## 📋 Prerequisites

- Node.js 20.x or higher
- npm or yarn package manager
- Docker (optional, for containerized development)

## 🛠️ Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd LandingV2
```

### 2. Install dependencies

```bash
cd frontend
npm install
# or
yarn install
```

### 3. Set up environment variables

Copy the `.env.example` file to `.env.local` and fill in your values:

```bash
cp .env.example .env.local
```

Edit `.env.local` with your actual values:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Stripe Configuration
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key_here
```

### 4. Run the development server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to see the result.

## 🐳 Docker Setup

### Build and run with Docker Compose

```bash
# Build the image
docker-compose build

# Run the container
docker-compose up

# Run in detached mode
docker-compose up -d

# Stop the container
docker-compose down
```

### Build Docker image manually

```bash
# Build the image
docker build -t sitesmith-frontend .

# Run the container
docker run -p 3000:3000 sitesmith-frontend
```

## 📁 Project Structure

```
src/
├── app/              # Next.js App Router pages
│   ├── layout.tsx    # Root layout
│   ├── page.tsx      # Home page
│   └── globals.css   # Global styles
├── components/       # Reusable React components
├── hooks/           # Custom React hooks
├── lib/             # Utility functions and configurations
└── types/           # TypeScript type definitions
```

## 🎨 Tailwind Configuration

Custom theme colors are configured in `tailwind.config.ts`:

- **Primary:** #6366f1 (Indigo)
- **Secondary:** #8b5cf6 (Purple)

Both colors include full shade ranges (50-950) for flexibility.

## 🧹 Code Quality

### Run ESLint

```bash
npm run lint
```

### Format code with Prettier

```bash
# Check formatting
npm run format:check

# Format all files
npm run format
```

## 📦 Build for Production

```bash
npm run build
npm run start
```

## 🚀 Deployment

This project is optimized for deployment on Vercel:

1. Push your code to GitHub
2. Import the project in Vercel
3. Add environment variables in Vercel dashboard
4. Deploy!

For other platforms, use the Docker setup or standard Node.js deployment.

## 📝 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run linting and formatting
4. Submit a pull request

## 📄 License

This project is private and proprietary.

## 🆘 Support

For questions or issues, please contact the development team.

---

Built with ❤️ for African Entrepreneurs

