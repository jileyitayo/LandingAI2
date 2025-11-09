cd /Users/jileyitayo/Documents/Projects/LandingV2

# Load environment variables from .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Validate required environment variables
if [ -z "$NEXT_PUBLIC_SUPABASE_URL" ]; then
  echo "❌ Error: NEXT_PUBLIC_SUPABASE_URL is not set"
  echo "Please set it in your .env file or export it before running this script"
  exit 1
fi

if [ -z "$NEXT_PUBLIC_SUPABASE_ANON_KEY" ]; then
  echo "❌ Error: NEXT_PUBLIC_SUPABASE_ANON_KEY is not set"
  echo "Please set it in your .env file or export it before running this script"
  exit 1
fi

# Build
docker build \
  --build-arg NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL} \
  --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY} \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  --build-arg NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY} \
  --build-arg NEXT_PUBLIC_UNSPLASH_ACCESS_KEY=${NEXT_PUBLIC_UNSPLASH_ACCESS_KEY} \
  -f Dockerfile.combined \
  -t sitesmith-combined .

# Stop and remove old container if exists
docker rm -f sitesmith-combined 2>/dev/null || true

# Run
docker run -d \
  -p 8000:8000 \
  -p 3000:3000 \
  --env-file .env \
  --name sitesmith-combined \
  sitesmith-combined

echo "✅ Container started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "View logs: docker logs -f sitesmith-combined"

# # Frontend
# docker build --no-cache \
#   --build-arg NEXT_PUBLIC_SUPABASE_URL=https://gshukbgzjrerdwexnmjd.supabase.co \
#   --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdzaHVrYmd6anJlcmR3ZXhubWpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0NTQzMjksImV4cCI6MjA3NTAzMDMyOX0.3woNYTOCPNDE3RTZ5Hbjtce3TdJkVidP6EbGMm0NXTk \
#   --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
#   --build-arg NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY} \
#   -t sitesmith-frontend .

#   # Run the container
# docker run -p 3000:3000 sitesmith-frontend


# # Backend
# docker build -t sitesmith-backend .
# docker run -p 8000:8000 --env-file .env sitesmith-backend