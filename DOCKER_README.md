# Docker Deployment Guide

This guide explains how to build and run the PDF Summarization System using Docker.

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Set your environment variables
export GOOGLE_API_KEY="your-api-key-here"

# 2. Start the application (in-memory mode - no Qdrant needed)
docker-compose up -d app

# 3. Access the application
# - Frontend: http://localhost:8501
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Option 2: Using Docker Build + Run

```bash
# 1. Build the image
docker build -t pdf-summarizer:latest .

# 2. Run the container
docker run -d \
  --name pdf-summarizer \
  -p 8000:8000 \
  -p 8501:8501 \
  -e GOOGLE_API_KEY="your-api-key-here" \
  -e QDRANT_URL=":memory:" \
  -v $(pwd)/logs:/app/logs \
  pdf-summarizer:latest

# 3. Access the application
# - Frontend: http://localhost:8501
# - Backend API: http://localhost:8000
```

## Architecture Overview

The Docker setup includes:

### Single Container Deployment
- **FastAPI Backend** (Port 8000): REST API for PDF processing and summarization
- **Streamlit Frontend** (Port 8501): Web UI for user interaction
- **In-Memory Vector Store**: No external database needed (default mode)

### Multi-Container Deployment (with Qdrant)
- **Application Container**: FastAPI + Streamlit
- **Qdrant Container**: Vector database for persistent embeddings storage

## Configuration Modes

### 1. In-Memory Mode (Default - No Database)

Perfect for testing, development, or stateless deployments.

```yaml
# docker-compose.yml
environment:
  - QDRANT_URL=:memory:
```

**Pros:**
- No external dependencies
- Fast startup
- Simple deployment

**Cons:**
- Data lost on restart
- Limited scalability

### 2. Persistent Mode (with Qdrant)

For production deployments requiring data persistence.

```yaml
# docker-compose.yml - Uncomment these lines
environment:
  - QDRANT_URL=http://qdrant:6333
  - QDRANT_HOST=qdrant
  - QDRANT_PORT=6333
```

```bash
# Start both app and Qdrant
docker-compose up -d
```

**Pros:**
- Data persists across restarts
- Production-ready
- Scalable

**Cons:**
- Requires Qdrant service
- More resource usage

## Detailed Usage

### Building the Image

```bash
# Build with default tag
docker build -t pdf-summarizer:latest .

# Build with custom tag
docker build -t pdf-summarizer:v1.0.0 .

# Build with no cache (clean build)
docker build --no-cache -t pdf-summarizer:latest .

# View build history
docker history pdf-summarizer:latest
```

### Running the Container

#### Basic Run (In-Memory Mode)

```bash
docker run -d \
  --name pdf-summarizer \
  -p 8000:8000 \
  -p 8501:8501 \
  -e GOOGLE_API_KEY="your-api-key-here" \
  pdf-summarizer:latest
```

#### Advanced Run (with Environment File)

```bash
# Create .env file with your configuration
cat > .env.docker << EOF
GOOGLE_API_KEY=your-api-key-here
API_KEY=your-secure-api-key
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp
QDRANT_URL=:memory:
EOF

# Run with environment file
docker run -d \
  --name pdf-summarizer \
  -p 8000:8000 \
  -p 8501:8501 \
  --env-file .env.docker \
  -v $(pwd)/logs:/app/logs \
  pdf-summarizer:latest
```

#### Run with Persistent Storage

```bash
docker run -d \
  --name pdf-summarizer \
  -p 8000:8000 \
  -p 8501:8501 \
  -e GOOGLE_API_KEY="your-api-key-here" \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/uploads:/app/uploads \
  pdf-summarizer:latest
```

### Docker Compose Commands

```bash
# Start all services in background
docker-compose up -d

# Start only app (in-memory mode)
docker-compose up -d app

# View logs
docker-compose logs -f app

# View logs (last 100 lines)
docker-compose logs --tail=100 app

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build

# Scale services (not applicable for this app)
# docker-compose up -d --scale app=2
```

### Container Management

```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# Stop container
docker stop pdf-summarizer

# Start container
docker start pdf-summarizer

# Restart container
docker restart pdf-summarizer

# Remove container
docker rm pdf-summarizer

# Remove container (force)
docker rm -f pdf-summarizer

# View container logs
docker logs pdf-summarizer

# Follow container logs
docker logs -f pdf-summarizer

# Execute command in container
docker exec -it pdf-summarizer bash

# View container stats
docker stats pdf-summarizer

# Inspect container
docker inspect pdf-summarizer
```

### Health Checks

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' pdf-summarizer

# View health check logs
docker inspect --format='{{json .State.Health}}' pdf-summarizer | jq

# Manual health check
curl http://localhost:8000/health
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google AI API key | `AIzaSy...` |

### Optional Variables (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `dev-key-12345` | API authentication key |
| `LLM_PROVIDER` | `gemini` | LLM provider (gemini/ollama) |
| `GEMINI_MODEL` | `gemini-2.0-flash-exp` | Gemini model name |
| `EMBEDDING_MODEL` | `models/text-embedding-004` | Embedding model |
| `QDRANT_URL` | `:memory:` | Vector DB URL (:memory: or http://host:port) |
| `CHUNK_SIZE` | `1000` | Text chunk size |
| `CHUNK_OVERLAP` | `200` | Text chunk overlap |
| `TOP_K_CHUNKS` | `5` | Number of chunks to retrieve |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Debug mode |
| `ENVIRONMENT` | `production` | Environment (development/production) |

## Volume Mounts

### Recommended Volumes

```bash
# Logs (recommended for debugging)
-v $(pwd)/logs:/app/logs

# Data (for persistent document storage)
-v $(pwd)/data:/app/data

# Uploads (for temporary file uploads)
-v $(pwd)/uploads:/app/uploads
```

### Creating Directories

```bash
# Create necessary directories on host
mkdir -p logs data uploads
chmod 755 logs data uploads
```

## Networking

### Port Mappings

| Container Port | Host Port | Service |
|----------------|-----------|---------|
| 8000 | 8000 | FastAPI Backend API |
| 8501 | 8501 | Streamlit Frontend |
| 6333 | 6333 | Qdrant REST API (optional) |
| 6334 | 6334 | Qdrant gRPC API (optional) |

### Custom Port Mapping

```bash
# Map to different host ports
docker run -d \
  --name pdf-summarizer \
  -p 9000:8000 \
  -p 9501:8501 \
  -e GOOGLE_API_KEY="your-api-key-here" \
  pdf-summarizer:latest

# Access at:
# - Backend: http://localhost:9000
# - Frontend: http://localhost:9501
```

## Troubleshooting

### Container Won't Start

```bash
# Check container logs
docker logs pdf-summarizer

# Check container status
docker ps -a | grep pdf-summarizer

# Inspect container
docker inspect pdf-summarizer

# Try running interactively
docker run -it --rm \
  -e GOOGLE_API_KEY="your-api-key-here" \
  pdf-summarizer:latest bash
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different ports
docker run -p 9000:8000 -p 9501:8501 ...
```

### Permission Issues

```bash
# Ensure directories are writable
chmod 755 logs data uploads

# Check container user
docker exec pdf-summarizer whoami
# Should output: appuser
```

### Health Check Failing

```bash
# Check backend directly
curl http://localhost:8000/health

# Check from inside container
docker exec pdf-summarizer curl http://localhost:8000/health

# View health check logs
docker inspect --format='{{json .State.Health}}' pdf-summarizer | jq
```

### Memory Issues

```bash
# Run with memory limits
docker run -d \
  --name pdf-summarizer \
  --memory="2g" \
  --memory-swap="2g" \
  -p 8000:8000 \
  -p 8501:8501 \
  pdf-summarizer:latest
```

### Build Issues

```bash
# Clean build with no cache
docker build --no-cache -t pdf-summarizer:latest .

# Check build logs
docker build -t pdf-summarizer:latest . 2>&1 | tee build.log

# Prune Docker system
docker system prune -a
```

## Production Deployment

### Security Best Practices

1. **Use secrets for sensitive data:**
```bash
# Docker Swarm secrets
echo "your-api-key" | docker secret create google_api_key -
```

2. **Run behind reverse proxy:**
```nginx
# Nginx configuration
location /api/ {
    proxy_pass http://localhost:8000/;
}

location / {
    proxy_pass http://localhost:8501/;
}
```

3. **Use specific image tags:**
```bash
docker build -t pdf-summarizer:v1.0.0 .
```

4. **Enable HTTPS:**
```bash
# Use Traefik, Nginx, or Caddy for SSL termination
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### High Availability

```bash
# Use Docker Swarm or Kubernetes for HA
docker stack deploy -c docker-compose.yml pdf-summarizer
```

## Monitoring

### Container Metrics

```bash
# View resource usage
docker stats pdf-summarizer

# Export metrics
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Application Logs

```bash
# Follow logs
docker-compose logs -f app

# Export logs
docker logs pdf-summarizer > app.log 2>&1
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build

# Restart with new image
docker-compose up -d
```

### Backups

```bash
# Backup volumes
docker run --rm \
  -v pdf-summarizer-qdrant-data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/qdrant-backup-$(date +%Y%m%d).tar.gz /data

# Restore volumes
docker run --rm \
  -v pdf-summarizer-qdrant-data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/qdrant-backup-20231130.tar.gz -C /
```

### Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full system cleanup
docker system prune -a --volumes
```

## Testing

```bash
# Test build
docker build -t pdf-summarizer:test .

# Test run
docker run --rm -it \
  -e GOOGLE_API_KEY="test-key" \
  pdf-summarizer:test

# Run tests inside container
docker exec pdf-summarizer pytest /app/tests
```

## Support

For issues or questions:
1. Check logs: `docker logs pdf-summarizer`
2. Check health: `curl http://localhost:8000/health`
3. Review environment variables
4. Verify API key is valid
5. Ensure ports are not in use

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
