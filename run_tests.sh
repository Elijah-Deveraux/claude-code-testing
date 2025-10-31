#!/bin/bash

# Test Runner Script for PDF Summarization System
# This script provides convenient ways to run different test suites

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PDF Summarization System - Test Runner${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install it with: pip install pytest pytest-cov pytest-asyncio"
    exit 1
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"

case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running unit tests only...${NC}"
        pytest tests/unit/ -v --tb=short
        ;;

    integration)
        echo -e "${YELLOW}Running integration tests...${NC}"
        echo -e "${YELLOW}Note: Integration tests require configured API keys and services${NC}"
        pytest tests/integration/ -v --tb=short -m integration
        ;;

    api)
        echo -e "${YELLOW}Running API endpoint tests...${NC}"
        pytest tests/unit/test_api_endpoints.py -v --tb=short
        ;;

    agents)
        echo -e "${YELLOW}Running agent tests...${NC}"
        pytest tests/unit/test_retrieval_agent.py tests/unit/test_summarizer_agent.py -v --tb=short
        ;;

    coverage)
        echo -e "${YELLOW}Running all tests with coverage report...${NC}"
        pytest tests/ --cov=src --cov-report=html --cov-report=term -v
        echo ""
        echo -e "${GREEN}Coverage report generated at: htmlcov/index.html${NC}"
        ;;

    fast)
        echo -e "${YELLOW}Running fast tests only (excludes integration and slow tests)...${NC}"
        pytest tests/unit/ -v --tb=short -m "not slow"
        ;;

    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        pytest tests/ -v --tb=short
        ;;

    help)
        echo "Usage: ./run_tests.sh [TEST_TYPE]"
        echo ""
        echo "Available test types:"
        echo "  unit         - Run unit tests only (fast, isolated)"
        echo "  integration  - Run integration tests (requires services)"
        echo "  api          - Run API endpoint tests only"
        echo "  agents       - Run agent tests only"
        echo "  coverage     - Run all tests with coverage report"
        echo "  fast         - Run fast tests only (no integration/slow)"
        echo "  all          - Run all tests (default)"
        echo "  help         - Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh              # Run all tests"
        echo "  ./run_tests.sh unit         # Run unit tests only"
        echo "  ./run_tests.sh coverage     # Generate coverage report"
        exit 0
        ;;

    *)
        echo -e "${RED}Error: Unknown test type '${TEST_TYPE}'${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Tests completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Tests failed!${NC}"
    exit 1
fi
