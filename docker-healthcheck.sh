#!/bin/bash
# ============================================================================
# Docker Health Check Script
# ============================================================================
# This script verifies that the application is running correctly
# It checks both the backend API and frontend services
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:8501}"
MAX_RETRIES=30
RETRY_DELAY=2

echo "=========================================="
echo "Docker Health Check"
echo "=========================================="
echo ""

# Function to check if a service is responding
check_service() {
    local url=$1
    local service_name=$2
    local retries=0

    echo -n "Checking ${service_name}... "

    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s -f "${url}" > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
            return 0
        fi
        retries=$((retries + 1))
        sleep $RETRY_DELAY
    done

    echo -e "${RED}FAILED${NC}"
    return 1
}

# Check Backend API
if ! check_service "${BACKEND_URL}/health" "Backend API"; then
    echo -e "${RED}Backend API is not responding${NC}"
    echo "URL: ${BACKEND_URL}/health"
    exit 1
fi

# Check Frontend (basic connectivity)
if ! check_service "${FRONTEND_URL}" "Frontend"; then
    echo -e "${YELLOW}Warning: Frontend is not responding (this may be normal if Streamlit is still starting)${NC}"
    # Don't exit on frontend failure, as it may take longer to start
fi

echo ""
echo -e "${GREEN}Health check passed!${NC}"
echo ""
echo "Application endpoints:"
echo "  Backend API:  ${BACKEND_URL}"
echo "  API Docs:     ${BACKEND_URL}/docs"
echo "  Frontend UI:  ${FRONTEND_URL}"
echo ""

exit 0
