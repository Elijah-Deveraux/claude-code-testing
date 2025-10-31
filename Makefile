# ============================================================================
# Makefile for PDF Summarization System
# ============================================================================
# Convenient commands for building, running, and managing the application
#
# Usage:
#   make help           Show this help message
#   make build          Build Docker image
#   make run            Run container in detached mode
#   make up             Start with docker-compose
#   make down           Stop docker-compose services
#   make logs           View application logs
#   make test           Run tests
# ============================================================================

.PHONY: help build run stop clean logs shell test up down restart

# Default target
.DEFAULT_GOAL := help

# Variables
IMAGE_NAME := pdf-summarizer
IMAGE_TAG := latest
CONTAINER_NAME := pdf-summarizer-app
DOCKER_COMPOSE := docker-compose

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "$(GREEN)PDF Summarization System - Makefile Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================================================
# Docker Build
# ============================================================================

build: ## Build Docker image
	@echo "$(GREEN)Building Docker image: $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "$(GREEN)Build complete!$(NC)"

build-no-cache: ## Build Docker image without cache
	@echo "$(GREEN)Building Docker image (no cache): $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"
	docker build --no-cache -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "$(GREEN)Build complete!$(NC)"

# ============================================================================
# Docker Run
# ============================================================================

run: ## Run container in detached mode (in-memory mode)
	@echo "$(GREEN)Starting container: $(CONTAINER_NAME)$(NC)"
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p 8000:8000 \
		-p 8501:8501 \
		-e GOOGLE_API_KEY=$(GOOGLE_API_KEY) \
		-e QDRANT_URL=:memory: \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/data:/app/data \
		$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)Container started!$(NC)"
	@echo "$(YELLOW)Access:$(NC)"
	@echo "  Frontend: http://localhost:8501"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

run-dev: ## Run container in interactive mode (for development)
	@echo "$(GREEN)Starting container in interactive mode$(NC)"
	docker run -it --rm \
		--name $(CONTAINER_NAME) \
		-p 8000:8000 \
		-p 8501:8501 \
		-e GOOGLE_API_KEY=$(GOOGLE_API_KEY) \
		-e DEBUG=true \
		-e LOG_LEVEL=DEBUG \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/src:/app/src \
		-v $(PWD)/frontend:/app/frontend \
		$(IMAGE_NAME):$(IMAGE_TAG)

stop: ## Stop and remove container
	@echo "$(YELLOW)Stopping container: $(CONTAINER_NAME)$(NC)"
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	@echo "$(GREEN)Container stopped and removed$(NC)"

restart: stop run ## Restart container

# ============================================================================
# Docker Compose
# ============================================================================

up: ## Start services with docker-compose (in-memory mode)
	@echo "$(GREEN)Starting services with docker-compose$(NC)"
	$(DOCKER_COMPOSE) up -d app
	@echo "$(GREEN)Services started!$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(YELLOW)Access:$(NC)"
	@echo "  Frontend: http://localhost:8501"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

up-all: ## Start all services including Qdrant
	@echo "$(GREEN)Starting all services (app + Qdrant)$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)All services started!$(NC)"
	@$(DOCKER_COMPOSE) ps

down: ## Stop docker-compose services
	@echo "$(YELLOW)Stopping docker-compose services$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Services stopped$(NC)"

down-volumes: ## Stop services and remove volumes
	@echo "$(YELLOW)Stopping services and removing volumes$(NC)"
	$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)Services stopped and volumes removed$(NC)"

restart-compose: down up ## Restart docker-compose services

# ============================================================================
# Logs and Monitoring
# ============================================================================

logs: ## View application logs
	@echo "$(GREEN)Viewing application logs (Ctrl+C to exit)$(NC)"
	$(DOCKER_COMPOSE) logs -f app

logs-tail: ## View last 100 lines of logs
	@echo "$(GREEN)Last 100 lines of application logs$(NC)"
	$(DOCKER_COMPOSE) logs --tail=100 app

logs-container: ## View logs from standalone container
	@echo "$(GREEN)Viewing container logs (Ctrl+C to exit)$(NC)"
	docker logs -f $(CONTAINER_NAME)

stats: ## View container resource usage
	@echo "$(GREEN)Container resource usage$(NC)"
	docker stats $(CONTAINER_NAME)

ps: ## List running containers
	@echo "$(GREEN)Running containers:$(NC)"
	@$(DOCKER_COMPOSE) ps

# ============================================================================
# Shell Access
# ============================================================================

shell: ## Open shell in container
	@echo "$(GREEN)Opening shell in container$(NC)"
	docker exec -it $(CONTAINER_NAME) bash

shell-compose: ## Open shell in docker-compose container
	@echo "$(GREEN)Opening shell in docker-compose container$(NC)"
	$(DOCKER_COMPOSE) exec app bash

# ============================================================================
# Health and Testing
# ============================================================================

health: ## Check application health
	@echo "$(GREEN)Checking application health$(NC)"
	@curl -s http://localhost:8000/health | jq || echo "$(RED)Health check failed$(NC)"

test: ## Run tests inside container
	@echo "$(GREEN)Running tests$(NC)"
	docker exec $(CONTAINER_NAME) pytest /app/tests -v

test-local: ## Run tests locally (requires venv)
	@echo "$(GREEN)Running tests locally$(NC)"
	. venv/bin/activate && pytest tests/ -v

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove container and image
	@echo "$(YELLOW)Cleaning up container and image$(NC)"
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-all: ## Deep clean (containers, images, volumes)
	@echo "$(RED)WARNING: This will remove all stopped containers, unused images, and volumes$(NC)"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	docker container prune -f
	docker image prune -a -f
	docker volume prune -f
	@echo "$(GREEN)Deep cleanup complete$(NC)"

# ============================================================================
# Development
# ============================================================================

init: ## Initialize project (create directories)
	@echo "$(GREEN)Initializing project directories$(NC)"
	mkdir -p logs data uploads
	chmod 755 logs data uploads
	@echo "$(GREEN)Directories created$(NC)"

check-env: ## Check if required environment variables are set
	@echo "$(GREEN)Checking environment variables$(NC)"
	@if [ -z "$(GOOGLE_API_KEY)" ]; then \
		echo "$(RED)ERROR: GOOGLE_API_KEY is not set$(NC)"; \
		echo "$(YELLOW)Set it with: export GOOGLE_API_KEY=your-key-here$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)GOOGLE_API_KEY is set$(NC)"; \
	fi

# ============================================================================
# Quick Start
# ============================================================================

quickstart: check-env init build run ## Quick start (check env, init, build, run)
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)Application is running!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(YELLOW)Access points:$(NC)"
	@echo "  Frontend: http://localhost:8501"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "$(YELLOW)Useful commands:$(NC)"
	@echo "  make logs     - View logs"
	@echo "  make health   - Check health"
	@echo "  make stop     - Stop container"
	@echo ""

# ============================================================================
# Image Management
# ============================================================================

push: ## Push image to registry (requires DOCKER_REGISTRY env var)
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "$(RED)ERROR: DOCKER_REGISTRY is not set$(NC)"; \
		exit 1; \
	fi
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)Image pushed to registry$(NC)"

pull: ## Pull image from registry
	@if [ -z "$(DOCKER_REGISTRY)" ]; then \
		echo "$(RED)ERROR: DOCKER_REGISTRY is not set$(NC)"; \
		exit 1; \
	fi
	docker pull $(DOCKER_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)Image pulled from registry$(NC)"

# ============================================================================
# Backup and Restore
# ============================================================================

backup: ## Backup Qdrant data volume
	@echo "$(GREEN)Backing up Qdrant data$(NC)"
	mkdir -p backups
	docker run --rm \
		-v pdf-summarizer-qdrant-data:/data \
		-v $(PWD)/backups:/backup \
		ubuntu tar czf /backup/qdrant-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz /data
	@echo "$(GREEN)Backup complete$(NC)"

restore: ## Restore Qdrant data volume (requires BACKUP_FILE env var)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)ERROR: BACKUP_FILE is not set$(NC)"; \
		echo "$(YELLOW)Usage: make restore BACKUP_FILE=backups/qdrant-backup-20231130.tar.gz$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Restoring Qdrant data from $(BACKUP_FILE)$(NC)"
	docker run --rm \
		-v pdf-summarizer-qdrant-data:/data \
		-v $(PWD)/backups:/backup \
		ubuntu tar xzf /backup/$(notdir $(BACKUP_FILE)) -C /
	@echo "$(GREEN)Restore complete$(NC)"

# ============================================================================
# Production
# ============================================================================

deploy: build push ## Build and push to registry
	@echo "$(GREEN)Deployment complete$(NC)"

prod-run: ## Run in production mode
	@echo "$(GREEN)Starting in production mode$(NC)"
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p 8000:8000 \
		-p 8501:8501 \
		--env-file .env.production \
		--restart unless-stopped \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/data:/app/data \
		$(IMAGE_NAME):$(IMAGE_TAG)
	@echo "$(GREEN)Production container started$(NC)"
