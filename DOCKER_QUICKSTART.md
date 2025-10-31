# Docker Quick Start Guide

This is a condensed quick reference for running the PDF Summarization System with Docker.

## Prerequisites

- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)
- Google API Key for Gemini

## Fastest Way to Run

### Method 1: Using Make (Recommended)

```bash
# 1. Set your API key
export GOOGLE_API_KEY="your-api-key-here"

# 2. Quick start (builds, initializes, and runs everything)
make quickstart

# That's it! Application is running at:
# - Frontend: http://localhost:8501
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Method 2: Using Docker Compose

```bash
# 1. Set your API key
export GOOGLE_API_KEY="your-api-key-here"

# 2. Start the application
docker-compose up -d app

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f app
```

### Method 3: Using Docker CLI

```bash
# 1. Build image
docker build -t pdf-summarizer:latest .

# 2. Run container
docker run -d \
  --name pdf-summarizer \
  -p 8000:8000 \
  -p 8501:8501 \
  -e GOOGLE_API_KEY="your-api-key-here" \
  -e QDRANT_URL=":memory:" \
  pdf-summarizer:latest

# 3. Check logs
docker logs -f pdf-summarizer
```

## Common Commands

### Using Make

```bash
make build          # Build Docker image
make run            # Run container
make stop           # Stop container
make logs           # View logs
make health         # Check health
make shell          # Open shell in container
make clean          # Remove container and image
```

### Using Docker Compose

```bash
docker-compose up -d           # Start services
docker-compose down            # Stop services
docker-compose logs -f app     # View logs
docker-compose restart app     # Restart app
docker-compose ps              # List services
```

### Using Docker CLI

```bash
docker ps                      # List running containers
docker logs -f pdf-summarizer  # View logs
docker stop pdf-summarizer     # Stop container
docker start pdf-summarizer    # Start container
docker exec -it pdf-summarizer bash  # Shell access
```

## Verification

### Check Application Health

```bash
# Using make
make health

# Using curl
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","timestamp":"..."}
```

### Test Upload (using curl)

```bash
# Upload a PDF
curl -X POST "http://localhost:8000/upload-pdf" \
  -H "X-API-Key: dev-key-12345" \
  -F "file=@/path/to/document.pdf"

# Get documents list
curl -X GET "http://localhost:8000/documents" \
  -H "X-API-Key: dev-key-12345"
```

## Configuration Modes

### In-Memory Mode (Default - No Database)

```bash
# Set in docker-compose.yml or environment
QDRANT_URL=:memory:

# Pros: Simple, fast, no dependencies
# Cons: Data lost on restart
```

### Persistent Mode (with Qdrant)

```bash
# Start both app and Qdrant
docker-compose up -d

# In docker-compose.yml, set:
QDRANT_URL=http://qdrant:6333

# Pros: Data persists
# Cons: Requires Qdrant service
```

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use different ports
docker run -p 9000:8000 -p 9501:8501 ...
```

### Container Won't Start

```bash
# Check logs
docker logs pdf-summarizer

# Or with docker-compose
docker-compose logs app

# Check environment
docker exec pdf-summarizer env | grep GOOGLE_API_KEY
```

### API Key Issues

```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Check in container
docker exec pdf-summarizer printenv | grep GOOGLE_API_KEY
```

### Permission Issues

```bash
# Create directories with correct permissions
mkdir -p logs data uploads
chmod 755 logs data uploads
```

## Stopping the Application

### Using Make

```bash
make stop
```

### Using Docker Compose

```bash
docker-compose down

# Remove volumes too
docker-compose down -v
```

### Using Docker CLI

```bash
docker stop pdf-summarizer
docker rm pdf-summarizer
```

## Access Points

Once running, access the application at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:8501 | Streamlit UI for uploading and summarizing PDFs |
| Backend | http://localhost:8000 | FastAPI REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Health | http://localhost:8000/health | Health check endpoint |

## Environment Variables

Minimum required:

```bash
GOOGLE_API_KEY=your-api-key-here
```

Optional (with sensible defaults):

```bash
API_KEY=dev-key-12345              # API authentication
QDRANT_URL=:memory:                # Vector DB mode
LLM_PROVIDER=gemini                # LLM provider
GEMINI_MODEL=gemini-2.0-flash-exp  # Model name
LOG_LEVEL=INFO                     # Logging level
```

## Quick Commands Reference

```bash
# Start application
make quickstart                    # All-in-one start
docker-compose up -d app           # Docker Compose start
docker run -d ... pdf-summarizer   # Docker CLI start

# Monitor
make logs                          # View logs
make health                        # Check health
docker stats pdf-summarizer        # Resource usage

# Manage
make stop                          # Stop application
make restart                       # Restart application
make clean                         # Remove everything

# Debug
make shell                         # Shell access
docker logs -f pdf-summarizer      # Follow logs
docker inspect pdf-summarizer      # Detailed info
```

## Production Deployment

For production use:

1. **Copy production environment template:**
```bash
cp .env.production .env.prod
# Edit .env.prod with your credentials
```

2. **Run with production config:**
```bash
docker-compose --env-file .env.prod up -d
```

3. **Enable HTTPS with reverse proxy** (Nginx, Traefik, Caddy)

4. **Set up monitoring** (Prometheus, Grafana)

5. **Configure backups:**
```bash
make backup  # Backup Qdrant data
```

## Next Steps

1. Start the application (see methods above)
2. Open http://localhost:8501 in your browser
3. Upload a PDF document
4. Generate a summary (brief or detailed)
5. View results with page references

## Getting Help

- Full documentation: See `DOCKER_README.md`
- Application docs: See `START_APP.md`
- Make commands: Run `make help`
- Docker Compose help: Run `docker-compose --help`

## Additional Resources

- **Application**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Logs**: `docker-compose logs -f app`
