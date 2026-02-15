# Synapsis Integrated Stack — Startup Script (Windows)
# =====================================================
# Starts Synapsis backend + Ollama + Qdrant for air-gapped local AI.
#
# Usage:
#   .\start_synapsis.ps1              # Start with Docker
#   .\start_synapsis.ps1 -Local       # Start without Docker (dev mode)
#   .\start_synapsis.ps1 -Status      # Check service status

param(
    [switch]$Local,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Help
)

# Colors for output
function Write-Success { param($Message) Write-Host "  ✓ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "  ⚠ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "  ✗ $Message" -ForegroundColor Red }
function Write-Info { param($Message) Write-Host "  → $Message" -ForegroundColor Cyan }

function Write-Header {
    param($Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " $Title" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
}

function Test-ServiceHealth {
    param($Url, $Timeout = 5)
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $Timeout -UseBasicParsing -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Start-Docker {
    Write-Header "Starting Synapsis Stack (Docker)"
    
    # Check Docker
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker not running or not installed"
        Write-Info "Install Docker Desktop: https://docs.docker.com/desktop/windows/install/"
        exit 1
    }
    
    # Create required directories
    New-Item -ItemType Directory -Force -Path "data/qdrant" | Out-Null
    New-Item -ItemType Directory -Force -Path "data/uploads" | Out-Null
    
    # Start services
    docker-compose up -d
    
    Write-Success "Starting Qdrant on :6333"
    Write-Success "Starting Ollama on :11434"
    Write-Success "Starting Synapsis backend on :8000"
    
    Write-Host "`nWaiting for services..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Check health
    Write-Host ""
    if (Test-ServiceHealth "http://localhost:8000/health") {
        Write-Success "Backend is healthy"
    } else {
        Write-Warning "Backend starting (may take 30s)"
    }
    
    if (Test-ServiceHealth "http://localhost:11434/api/tags") {
        Write-Success "Ollama is running"
    } else {
        Write-Warning "Ollama starting..."
    }
    
    if (Test-ServiceHealth "http://localhost:6333/readyz") {
        Write-Success "Qdrant is ready"
    } else {
        Write-Warning "Qdrant starting..."
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " Services Started!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Backend API:    http://localhost:8000"
    Write-Host "  API Docs:       http://localhost:8000/docs"
    Write-Host "  OpenAI-Compat:  http://localhost:8000/v1"
    Write-Host "  Ollama:         http://localhost:11434"
    Write-Host "  Qdrant:         http://localhost:6333"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Start frontend: cd frontend\synapsis; npm run dev"
    Write-Host ""
    Write-Host "To stop: docker-compose down"
}

function Start-Local {
    Write-Header "Starting Synapsis (Local Dev Mode)"
    
    # Check Ollama
    if (-not (Test-ServiceHealth "http://localhost:11434/api/tags")) {
        Write-Error "Ollama not running"
        Write-Info "Start Ollama: ollama serve"
        exit 1
    }
    Write-Success "Ollama is running"
    
    # Check Qdrant
    if (Test-ServiceHealth "http://localhost:6333/readyz") {
        Write-Success "Qdrant is running"
    } else {
        Write-Warning "Qdrant not running"
        Write-Info "Start Qdrant: docker run -d -p 6333:6333 qdrant/qdrant"
    }
    
    # Start backend
    Write-Header "Starting Backend"
    
    Push-Location backend
    
    # Create venv if needed
    if (-not (Test-Path ".venv")) {
        Write-Info "Creating virtual environment..."
        python -m venv .venv
    }
    
    # Activate venv
    & .\.venv\Scripts\Activate.ps1
    
    # Install deps
    Write-Info "Installing dependencies..."
    pip install -q -r requirements.txt
    
    Write-Success "Starting FastAPI server..."
    Write-Host ""
    
    # Run uvicorn
    uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
    
    Pop-Location
}

function Stop-Services {
    Write-Header "Stopping Synapsis Stack"
    docker-compose down
    Write-Success "Services stopped"
}

function Show-Status {
    Write-Header "Synapsis Stack Status"
    
    Write-Host "`nBackend:" -ForegroundColor Cyan
    if (Test-ServiceHealth "http://localhost:8000/health") {
        Write-Success "Running on :8000"
    } else {
        Write-Error "Not running"
    }
    
    Write-Host "`nOllama:" -ForegroundColor Cyan
    if (Test-ServiceHealth "http://localhost:11434/api/tags") {
        Write-Success "Running on :11434"
        try {
            $models = (Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing).Content | ConvertFrom-Json
            foreach ($model in $models.models) {
                Write-Info "  Model: $($model.name)"
            }
        } catch {}
    } else {
        Write-Error "Not running"
    }
    
    Write-Host "`nQdrant:" -ForegroundColor Cyan
    if (Test-ServiceHealth "http://localhost:6333/readyz") {
        Write-Success "Running on :6333"
    } else {
        Write-Error "Not running"
    }
}

function Show-Help {
    Write-Host "Synapsis Stack — Air-gapped Local AI" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\start_synapsis.ps1 [option]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  (default)   Start with Docker Compose"
    Write-Host "  -Local      Start without Docker (dev mode)"
    Write-Host "  -Stop       Stop Docker services"
    Write-Host "  -Status     Show service status"
    Write-Host "  -Help       Show this help"
}

# Main
if ($Help) {
    Show-Help
} elseif ($Status) {
    Show-Status
} elseif ($Stop) {
    Stop-Services
} elseif ($Local) {
    Start-Local
} else {
    Start-Docker
}
