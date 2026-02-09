# Pull and run VideoTeaching from GitHub Container Registry
# PowerShell version

param(
    [string]$ImageTag = "latest",
    [string]$ContainerName = "videoteaching-app"
)

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "======================================" "Blue"
Write-ColorOutput "VideoTeaching - Pull & Run Script" "Blue"
Write-ColorOutput "======================================" "Blue"

# Configuration
$Registry = "ghcr.io"
$Repo = "cong-ty-tnnh-q-tech/createvideo-website"
$FullImage = "${Registry}/${Repo}:${ImageTag}"

# Check if GEMINI_API_KEY is set
if (-not $env:GEMINI_API_KEY) {
    Write-ColorOutput "Error: GEMINI_API_KEY environment variable is not set" "Red"
    Write-Host "Please set it with: `$env:GEMINI_API_KEY = 'your_api_key'"
    exit 1
}

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-ColorOutput "Error: Docker is not installed" "Red"
    exit 1
}

# Check if NVIDIA Docker is available (for GPU support)
$GpuFlag = ""
try {
    docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✓ NVIDIA GPU detected" "Green"
        $GpuFlag = "--gpus all"
    }
} catch {
    Write-ColorOutput "ℹ No GPU detected, running in CPU mode" "Cyan"
}

Write-Host ""
Write-ColorOutput "Step 1: Pulling image from GHCR..." "Blue"
docker pull $FullImage

Write-Host ""
Write-ColorOutput "Step 2: Stopping existing container (if any)..." "Blue"
docker stop $ContainerName 2>$null | Out-Null
docker rm $ContainerName 2>$null | Out-Null

Write-Host ""
Write-ColorOutput "Step 3: Creating necessary directories..." "Blue"
$directories = @(
    "data",
    "static\uploads\presentations",
    "static\results",
    "app\SadTalker\checkpoints",
    "app\SadTalker\gfpgan\weights"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host ""
Write-ColorOutput "Step 4: Starting new container..." "Blue"

# Get current directory for volume mounting
$CurrentDir = (Get-Location).Path

# Build docker run command
$dockerCmd = @(
    "run", "-d",
    "--name", $ContainerName
)

if ($GpuFlag) {
    $dockerCmd += $GpuFlag
}

$dockerCmd += @(
    "-p", "5000:5000",
    "-e", "GEMINI_API_KEY=$env:GEMINI_API_KEY",
    "-e", "FLASK_APP=run.py",
    "-e", "FLASK_ENV=production",
    "-e", "PYTHONUNBUFFERED=1",
    "-v", "${CurrentDir}\data:/app/data",
    "-v", "${CurrentDir}\static\uploads:/app/static/uploads",
    "-v", "${CurrentDir}\static\results:/app/static/results",
    "-v", "${CurrentDir}\app\SadTalker\checkpoints:/app/app/SadTalker/checkpoints",
    "-v", "${CurrentDir}\app\SadTalker\gfpgan\weights:/app/app/SadTalker/gfpgan/weights",
    "--restart", "unless-stopped",
    $FullImage
)

& docker @dockerCmd

Write-Host ""
Write-ColorOutput "✓ Container started successfully!" "Green"
Write-Host ""
Write-Host "Container name: $ContainerName"
Write-Host "Image: $FullImage"
Write-Host ""
Write-ColorOutput "Waiting for application to be ready..." "Blue"
Start-Sleep -Seconds 10

# Check if container is running
$containerStatus = docker ps --filter "name=$ContainerName" --format "{{.Names}}"
if ($containerStatus -eq $ContainerName) {
    Write-ColorOutput "✓ Container is running" "Green"
    Write-Host ""
    Write-Host "View logs: docker logs -f $ContainerName"
    Write-Host "Stop: docker stop $ContainerName"
    Write-Host "Access app: http://localhost:5000"
} else {
    Write-ColorOutput "✗ Container failed to start" "Red"
    Write-Host "View logs: docker logs $ContainerName"
    exit 1
}

Write-Host ""
Write-ColorOutput "======================================" "Green"
Write-ColorOutput "Setup Complete!" "Green"
Write-ColorOutput "======================================" "Green"
