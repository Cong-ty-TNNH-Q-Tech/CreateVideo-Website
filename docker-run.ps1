# VideoTeaching Docker Helper Script (PowerShell)
# Windows version of docker-run.sh

param(
    [Parameter(Position=0)]
    [ValidateSet('build', 'start', 'dev', 'stop', 'logs', 'clean', 'help')]
    [string]$Command = 'help',
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Color functions
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Check for NVIDIA Docker runtime
function Test-GPU {
    try {
        $null = nvidia-smi 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning-Custom "NVIDIA GPU not detected. Running in CPU mode."
            $env:CUDA_VISIBLE_DEVICES = ""
            return $false
        }
        
        Write-Success "GPU support enabled"
        return $true
    }
    catch {
        Write-Warning-Custom "NVIDIA drivers not found. Running in CPU mode."
        return $false
    }
}

# Check for required files
function Test-Requirements {
    if (-not (Test-Path ".env")) {
        Write-Warning-Custom ".env file not found. Creating from .env.example..."
        Copy-Item .env.example .env
        Write-Warning-Custom "Please edit .env and add your GEMINI_API_KEY"
    }
    
    if (-not (Test-Path "app\SadTalker\checkpoints")) {
        Write-Warning-Custom "SadTalker checkpoints not found."
        Write-Warning-Custom "Please download models using: python download_models.py"
    }
}

# Build Docker image
function Invoke-Build {
    Write-Success "Building Docker image..."
    docker-compose build --no-cache
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Build complete"
    } else {
        Write-Error-Custom "Build failed"
        exit 1
    }
}

# Start services
function Start-Services {
    Test-Requirements
    Test-GPU
    
    Write-Success "Starting VideoTeaching..."
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Application started at http://localhost:5000"
        docker-compose logs -f
    } else {
        Write-Error-Custom "Failed to start services"
        exit 1
    }
}

# Start in development mode
function Start-Development {
    Test-Requirements
    Test-GPU
    
    Write-Success "Starting VideoTeaching in development mode..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
}

# Stop services
function Stop-Services {
    Write-Success "Stopping VideoTeaching..."
    docker-compose down
    Write-Success "Services stopped"
}

# View logs
function Show-Logs {
    if ($Arguments) {
        docker-compose logs -f $Arguments
    } else {
        docker-compose logs -f
    }
}

# Clean up
function Invoke-Clean {
    Write-Warning-Custom "This will remove all containers, volumes, and images."
    $response = Read-Host "Continue? (y/N)"
    
    if ($response -match '^[yY]') {
        docker-compose down -v --rmi all
        Write-Success "Cleanup complete"
    } else {
        Write-Warning-Custom "Cleanup cancelled"
    }
}

# Show usage
function Show-Usage {
    @"
VideoTeaching Docker Management (PowerShell)

Usage: .\docker-run.ps1 [command] [arguments]

Commands:
    build       Build Docker image
    start       Start services in production mode
    dev         Start services in development mode
    stop        Stop all services
    logs        View logs (optional: service name)
    clean       Remove all containers, volumes, and images
    help        Show this help message

Examples:
    .\docker-run.ps1 build
    .\docker-run.ps1 start
    .\docker-run.ps1 dev
    .\docker-run.ps1 logs videoteaching
    .\docker-run.ps1 stop

"@
}

# Main execution
switch ($Command) {
    'build' { Invoke-Build }
    'start' { Start-Services }
    'dev' { Start-Development }
    'stop' { Stop-Services }
    'logs' { Show-Logs }
    'clean' { Invoke-Clean }
    'help' { Show-Usage }
    default { Show-Usage }
}
