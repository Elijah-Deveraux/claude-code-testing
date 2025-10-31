#!/bin/bash
# ============================================================================
# Docker Setup Verification Script
# ============================================================================
# This script verifies that your Docker setup is complete and ready to use
# Run this before building: ./verify-docker-setup.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Docker Setup Verification"
echo -e "==========================================${NC}"
echo ""

# Track overall status
ERRORS=0
WARNINGS=0

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    local status=$1
    local message=$2

    if [ "$status" = "OK" ]; then
        echo -e "[${GREEN}✓${NC}] $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "[${YELLOW}!${NC}] $message"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "[${RED}✗${NC}] $message"
        ERRORS=$((ERRORS + 1))
    fi
}

echo -e "${BLUE}1. Checking Prerequisites${NC}"
echo "----------------------------"

# Check Docker
if command_exists docker; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | tr -d ',')
    print_status "OK" "Docker installed (version: $DOCKER_VERSION)"
else
    print_status "ERROR" "Docker is not installed"
fi

# Check Docker Compose
if command_exists docker-compose; then
    COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f4 | tr -d ',')
    print_status "OK" "Docker Compose installed (version: $COMPOSE_VERSION)"
else
    print_status "WARN" "Docker Compose not found (optional, can use 'docker compose' instead)"
fi

# Check if Docker daemon is running
if docker info >/dev/null 2>&1; then
    print_status "OK" "Docker daemon is running"
else
    print_status "ERROR" "Docker daemon is not running"
fi

echo ""
echo -e "${BLUE}2. Checking Required Files${NC}"
echo "----------------------------"

# Check Dockerfile
if [ -f "Dockerfile" ]; then
    print_status "OK" "Dockerfile exists"
else
    print_status "ERROR" "Dockerfile not found"
fi

# Check .dockerignore
if [ -f ".dockerignore" ]; then
    print_status "OK" ".dockerignore exists"
else
    print_status "WARN" ".dockerignore not found (optional)"
fi

# Check docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    print_status "OK" "docker-compose.yml exists"
else
    print_status "WARN" "docker-compose.yml not found (optional)"
fi

# Check Makefile
if [ -f "Makefile" ]; then
    print_status "OK" "Makefile exists"
else
    print_status "WARN" "Makefile not found (optional)"
fi

# Check requirements.txt
if [ -f "requirements.txt" ]; then
    print_status "OK" "requirements.txt exists"
else
    print_status "ERROR" "requirements.txt not found"
fi

echo ""
echo -e "${BLUE}3. Checking Application Structure${NC}"
echo "-----------------------------------"

# Check src directory
if [ -d "src" ]; then
    print_status "OK" "src/ directory exists"
else
    print_status "ERROR" "src/ directory not found"
fi

# Check frontend directory
if [ -d "frontend" ]; then
    print_status "OK" "frontend/ directory exists"
else
    print_status "ERROR" "frontend/ directory not found"
fi

# Check main.py
if [ -f "src/api/main.py" ]; then
    print_status "OK" "src/api/main.py exists"
else
    print_status "ERROR" "src/api/main.py not found"
fi

# Check frontend app.py
if [ -f "frontend/app.py" ]; then
    print_status "OK" "frontend/app.py exists"
else
    print_status "ERROR" "frontend/app.py not found"
fi

echo ""
echo -e "${BLUE}4. Checking Environment Configuration${NC}"
echo "---------------------------------------"

# Check GOOGLE_API_KEY environment variable
if [ -n "$GOOGLE_API_KEY" ]; then
    print_status "OK" "GOOGLE_API_KEY is set (length: ${#GOOGLE_API_KEY} chars)"
else
    print_status "WARN" "GOOGLE_API_KEY not set in environment"
fi

# Check .env file
if [ -f ".env" ]; then
    print_status "OK" ".env file exists"

    # Check if GOOGLE_API_KEY is in .env
    if grep -q "GOOGLE_API_KEY=" .env; then
        print_status "OK" "GOOGLE_API_KEY found in .env"
    else
        print_status "WARN" "GOOGLE_API_KEY not found in .env"
    fi
else
    print_status "WARN" ".env file not found (can use environment variables instead)"
fi

# Check .env.production
if [ -f ".env.production" ]; then
    print_status "OK" ".env.production template exists"
else
    print_status "WARN" ".env.production not found (optional)"
fi

echo ""
echo -e "${BLUE}5. Checking Docker Configuration${NC}"
echo "----------------------------------"

# Validate Dockerfile syntax (basic check)
if [ -f "Dockerfile" ]; then
    if grep -q "FROM" Dockerfile && grep -q "WORKDIR" Dockerfile; then
        print_status "OK" "Dockerfile has valid syntax"
    else
        print_status "ERROR" "Dockerfile may have syntax errors"
    fi
fi

# Validate docker-compose.yml (if docker-compose is available)
if [ -f "docker-compose.yml" ] && command_exists docker-compose; then
    if docker-compose config >/dev/null 2>&1; then
        print_status "OK" "docker-compose.yml is valid"
    else
        print_status "ERROR" "docker-compose.yml has syntax errors"
    fi
fi

echo ""
echo -e "${BLUE}6. Checking Permissions${NC}"
echo "------------------------"

# Check if user has Docker permissions
if groups | grep -q docker; then
    print_status "OK" "User is in docker group"
elif [ "$EUID" -eq 0 ]; then
    print_status "OK" "Running as root (has Docker access)"
else
    print_status "WARN" "User may need to be added to docker group"
fi

# Check script permissions
if [ -x "docker-healthcheck.sh" ]; then
    print_status "OK" "docker-healthcheck.sh is executable"
else
    if [ -f "docker-healthcheck.sh" ]; then
        print_status "WARN" "docker-healthcheck.sh exists but not executable"
        echo "         Run: chmod +x docker-healthcheck.sh"
    fi
fi

echo ""
echo -e "${BLUE}7. Checking Ports${NC}"
echo "------------------"

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_status "WARN" "Port 8000 is in use (backend will fail to start)"
else
    print_status "OK" "Port 8000 is available"
fi

# Check if port 8501 is available
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_status "WARN" "Port 8501 is in use (frontend will fail to start)"
else
    print_status "OK" "Port 8501 is available"
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Summary"
echo -e "==========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Your Docker setup is ready.${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Set your API key:"
    echo "   export GOOGLE_API_KEY=\"your-api-key-here\""
    echo ""
    echo "2. Build and run:"
    echo "   make quickstart"
    echo "   or"
    echo "   docker-compose up -d app"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}! Setup complete with $WARNINGS warning(s)${NC}"
    echo ""
    echo -e "${YELLOW}Warnings can usually be ignored, but review them to ensure"
    echo -e "everything is configured as expected.${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Found $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo -e "${RED}Please fix the errors before building the Docker image.${NC}"
    echo ""
    exit 1
fi
