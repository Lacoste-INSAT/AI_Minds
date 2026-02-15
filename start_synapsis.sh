#!/bin/bash
# Synapsis Integrated Stack — Startup Script
# ==========================================
# Starts Synapsis backend + Ollama + Qdrant for air-gapped local AI.
#
# Usage:
#   ./start_synapsis.sh              # Start with Docker
#   ./start_synapsis.sh --local      # Start without Docker (dev mode)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN} $1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

print_status() {
    echo -e "  ${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "  ${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "  ${RED}✗${NC} $1"
}

print_info() {
    echo -e "  ${BLUE}→${NC} $1"
}

# Check if Docker is available
check_docker() {
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Start with Docker Compose
start_docker() {
    print_header "Starting Synapsis Stack (Docker)"
    
    if ! check_docker; then
        print_error "Docker not available or not running"
        print_info "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Create required directories
    mkdir -p data/qdrant data/uploads
    
    # Start services
    docker-compose up -d
    
    print_status "Starting Qdrant on :6333"
    print_status "Starting Ollama on :11434"
    print_status "Starting Synapsis backend on :8000"
    
    # Wait for services
    echo -e "\nWaiting for services..."
    sleep 10
    
    # Check health
    echo ""
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "Backend is healthy"
    else
        print_warning "Backend starting (may take 30s)"
    fi
    
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_status "Ollama is running"
        
        # Check if models are available
        MODELS=$(curl -s http://localhost:11434/api/tags | grep -c '"name"' || echo "0")
        if [ "$MODELS" -gt 0 ]; then
            print_status "Models available: $MODELS"
        else
            print_warning "Models downloading in background..."
            print_info "Check progress: docker logs -f synapsis-ollama-init"
        fi
    else
        print_warning "Ollama starting..."
    fi
    
    if curl -s http://localhost:6333/readyz > /dev/null 2>&1; then
        print_status "Qdrant is ready"
    else
        print_warning "Qdrant starting..."
    fi
    
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN} Services Started!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "  Backend API:    http://localhost:8000"
    echo "  API Docs:       http://localhost:8000/docs"
    echo "  OpenAI-Compat:  http://localhost:8000/v1"
    echo "  Ollama:         http://localhost:11434"
    echo "  Qdrant:         http://localhost:6333"
    echo ""
    echo "Next steps:"
    echo "  1. Start frontend: cd frontend/synapsis && npm run dev"
    echo ""
    echo "To stop: docker-compose down"
    echo "Logs:    docker-compose logs -f"
}

# Start without Docker (development mode)
start_local() {
    print_header "Starting Synapsis (Local Dev Mode)"
    
    # Check Ollama
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_error "Ollama not running"
        print_info "Start Ollama: ollama serve"
        exit 1
    fi
    print_status "Ollama is running"
    
    # Check for models
    MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name"' | wc -l)
    if [ "$MODELS" -eq 0 ]; then
        print_warning "No models installed"
        print_info "Pull a model: ollama pull phi4-mini"
        print_info "Or smaller: ollama pull qwen2.5:0.5b"
    else
        print_status "Found $MODELS model(s)"
    fi
    
    # Check Qdrant
    if curl -s http://localhost:6333/readyz > /dev/null 2>&1; then
        print_status "Qdrant is running"
    else
        print_warning "Qdrant not running"
        print_info "Start Qdrant: docker run -d -p 6333:6333 qdrant/qdrant"
    fi
    
    # Start backend
    print_header "Starting Backend"
    
    cd backend
    
    # Check if venv exists
    if [ ! -d ".venv" ]; then
        print_info "Creating virtual environment..."
        python -m venv .venv
    fi
    
    # Activate venv (handle both Unix and Windows/Git Bash)
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
    fi
    
    # Install deps
    print_info "Installing dependencies..."
    pip install -q -r requirements.txt
    
    print_status "Starting FastAPI server..."
    echo ""
    
    # Run uvicorn
    uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
}

# Stop services
stop_services() {
    print_header "Stopping Synapsis Stack"
    docker-compose -f docker-compose.integrated.yml down
    print_status "Services stopped"
}

# Show status
show_status() {
    print_header "Synapsis Stack Status"
    
    echo ""
    echo "Backend:"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "Running on :8000"
    else
        print_error "Not running"
    fi
    
    echo ""
    echo "Ollama:"
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_status "Running on :11434"
        MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//' | head -5)
        for model in $MODELS; do
            print_info "  Model: $model"
        done
    else
        print_error "Not running"
    fi
    
    echo ""
    echo "Qdrant:"
    if curl -s http://localhost:6333/readyz > /dev/null 2>&1; then
        print_status "Running on :6333"
    else
        print_error "Not running"
    fi
}

# Main
case "$1" in
    --local|-l)
        start_local
        ;;
    --stop|-s)
        stop_services
        ;;
    --status)
        show_status
        ;;
    --help|-h)
        echo "Synapsis Stack — Air-gapped Local AI"
        echo ""
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (default)      Start with Docker Compose"
        echo "  --local, -l    Start without Docker (dev mode)"
        echo "  --stop, -s     Stop Docker services"
        echo "  --status       Show service status"
        echo "  --help, -h     Show this help"
        ;;
    *)
        start_docker
        ;;
esac
