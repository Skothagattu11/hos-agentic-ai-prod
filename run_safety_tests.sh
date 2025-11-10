#!/bin/bash

# Safety Test Runner Script
# Runs safety validation tests within the .venv virtual environment
#
# Usage:
#   ./run_safety_tests.sh unit             # Run unit tests only
#   ./run_safety_tests.sh quick            # Run quick integration test (1 plan)
#   ./run_safety_tests.sh full             # Run full integration test (15 plans)
#   ./run_safety_tests.sh archetype NAME   # Test specific archetype
#   ./run_safety_tests.sh all              # Run all tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: .venv virtual environment not found${NC}"
    echo "Please create it first:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate

# Check if httpx is installed (required for integration tests)
if ! python -c "import httpx" 2>/dev/null; then
    echo -e "${YELLOW}Installing httpx (required for integration tests)...${NC}"
    pip install httpx
fi

# Function to run unit tests
run_unit_tests() {
    echo -e "\n${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}  UNIT TESTS - Safety Validator Logic${NC}"
    echo -e "${BLUE}=================================================================================${NC}\n"

    python testing/test_safety_validation.py

    echo -e "\n${GREEN}✅ Unit tests complete${NC}\n"
}

# Function to run quick integration test
run_quick_test() {
    echo -e "\n${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}  QUICK INTEGRATION TEST - Single Plan Generation${NC}"
    echo -e "${BLUE}=================================================================================${NC}\n"

    echo -e "${YELLOW}⚠️  Make sure the server is running on http://localhost:8002${NC}"
    echo -e "${YELLOW}   Start with: python start_openai.py${NC}\n"

    read -p "Press Enter to continue or Ctrl+C to cancel..."

    python testing/test_safety_integration_endpoint.py --quick

    echo -e "\n${GREEN}✅ Quick test complete${NC}\n"
}

# Function to run full integration test
run_full_test() {
    echo -e "\n${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}  FULL INTEGRATION TEST - Multiple Archetypes & Iterations${NC}"
    echo -e "${BLUE}=================================================================================${NC}\n"

    echo -e "${YELLOW}⚠️  Make sure the server is running on http://localhost:8002${NC}"
    echo -e "${YELLOW}   Start with: python start_openai.py${NC}\n"
    echo -e "${YELLOW}⏱  This will generate 15 plans (5 archetypes × 3 iterations)${NC}"
    echo -e "${YELLOW}   Estimated time: 5-10 minutes${NC}\n"

    read -p "Press Enter to continue or Ctrl+C to cancel..."

    python testing/test_safety_integration_endpoint.py

    echo -e "\n${GREEN}✅ Full test complete${NC}"
    echo -e "${GREEN}📄 Report saved to: testing/safety_test_report.json${NC}\n"
}

# Function to test specific archetype
run_archetype_test() {
    local archetype="$1"

    echo -e "\n${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}  ARCHETYPE TEST - ${archetype}${NC}"
    echo -e "${BLUE}=================================================================================${NC}\n"

    echo -e "${YELLOW}⚠️  Make sure the server is running on http://localhost:8002${NC}"
    echo -e "${YELLOW}   Start with: python start_openai.py${NC}\n"

    read -p "Press Enter to continue or Ctrl+C to cancel..."

    python testing/test_safety_integration_endpoint.py --archetype "$archetype"

    echo -e "\n${GREEN}✅ Archetype test complete${NC}\n"
}

# Function to run all tests
run_all_tests() {
    run_unit_tests

    echo -e "\n${YELLOW}Starting integration tests...${NC}"
    echo -e "${YELLOW}⚠️  Make sure the server is running on http://localhost:8002${NC}\n"

    read -p "Press Enter to continue or Ctrl+C to cancel..."

    run_quick_test
    run_full_test

    echo -e "\n${GREEN}🎉 All tests complete!${NC}\n"
}

# Parse command line arguments
case "${1:-}" in
    unit)
        run_unit_tests
        ;;
    quick)
        run_quick_test
        ;;
    full)
        run_full_test
        ;;
    archetype)
        if [ -z "${2:-}" ]; then
            echo -e "${RED}Error: Please specify archetype name${NC}"
            echo "Usage: ./run_safety_tests.sh archetype \"Foundation Builder\""
            exit 1
        fi
        run_archetype_test "$2"
        ;;
    all)
        run_all_tests
        ;;
    *)
        echo -e "${BLUE}Safety Test Runner${NC}"
        echo ""
        echo "Usage:"
        echo "  ${GREEN}./run_safety_tests.sh unit${NC}             # Run unit tests only"
        echo "  ${GREEN}./run_safety_tests.sh quick${NC}            # Run quick integration test (1 plan)"
        echo "  ${GREEN}./run_safety_tests.sh full${NC}             # Run full integration test (15 plans)"
        echo "  ${GREEN}./run_safety_tests.sh archetype NAME${NC}   # Test specific archetype"
        echo "  ${GREEN}./run_safety_tests.sh all${NC}              # Run all tests"
        echo ""
        echo "Examples:"
        echo "  ${YELLOW}./run_safety_tests.sh unit${NC}"
        echo "  ${YELLOW}./run_safety_tests.sh quick${NC}"
        echo "  ${YELLOW}./run_safety_tests.sh archetype \"Peak Performer\"${NC}"
        echo ""
        exit 1
        ;;
esac

# Deactivate virtual environment
deactivate 2>/dev/null || true
