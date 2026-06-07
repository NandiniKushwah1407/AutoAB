# PowerShell startup script for AutoAB Platform

Write-Host "🚀 Starting AutoAB Platform..." -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Start backend services with Docker Compose
Write-Host "📦 Starting backend services (PostgreSQL, Redis, FastAPI, Celery)..." -ForegroundColor Yellow
docker compose up -d

Write-Host ""
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check service health
Write-Host ""
Write-Host "🔍 Checking service status..." -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "✅ AutoAB Platform is running!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""
Write-Host "Backend API:      http://localhost:8000" -ForegroundColor White
Write-Host "API Docs:         http://localhost:8000/docs" -ForegroundColor White
Write-Host "PostgreSQL:       localhost:5432" -ForegroundColor White
Write-Host "Redis:            localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "To start the frontend:" -ForegroundColor Cyan
Write-Host "  cd frontend" -ForegroundColor Gray
Write-Host "  npm start" -ForegroundColor Gray
Write-Host ""
Write-Host "To use the CLI:" -ForegroundColor Cyan
Write-Host "  cd cli" -ForegroundColor Gray
Write-Host "  python autoab_cli.py list" -ForegroundColor Gray
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  docker compose logs -f" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Cyan
Write-Host "  docker compose down" -ForegroundColor Gray
Write-Host ""
