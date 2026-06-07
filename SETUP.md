# AutoAB Platform - Complete Setup Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Windows Machine                       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Docker (Linux Containers)            │  │
│  │  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │  PostgreSQL  │  │    Redis     │             │  │
│  │  │   (port 5432)│  │  (port 6379) │             │  │
│  │  └──────────────┘  └──────────────┘             │  │
│  │                                                   │  │
│  │  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │   FastAPI    │  │Celery Worker │             │  │
│  │  │  (port 8000) │  │  (background)│             │  │
│  │  └──────────────┘  └──────────────┘             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Native Windows Apps                  │  │
│  │                                                   │  │
│  │  React Frontend (npm)      CLI (Python)          │  │
│  │  http://localhost:3000     Terminal commands     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Why This Architecture?

✅ **Backend in Docker**:
- Redis & Celery need Linux → Docker provides Linux containers
- PostgreSQL works better in containers → Easy data persistence
- FastAPI runs anywhere → But Docker keeps environment consistent
- One command starts everything → `docker compose up -d`

✅ **Frontend on Windows**:
- React dev server works perfectly on Windows
- Hot reload and debugging tools work natively
- No performance overhead

✅ **CLI on Windows**:
- Python runs natively on Windows
- Direct access to terminal
- Can connect to Dockerized API

## Prerequisites

1. **Docker Desktop** (required for backend)
   - Download: https://www.docker.com/products/docker-desktop/
   - Make sure WSL2 backend is enabled
   - Start Docker Desktop before running backend

2. **Node.js** (required for frontend)
   - You already have v16.13.2
   - Recommended: Upgrade to v18+ or v20 LTS

3. **Python** (required for CLI)
   - You likely have Python installed
   - Python 3.8+ recommended

## 🚀 Quick Start

### Option 1: PowerShell Script (Easiest)

```powershell
cd "c:\Nandini Kushwah\My\AB Testing and Uplifting Model\autoab"
.\start.ps1
```

### Option 2: Manual Steps

#### 1. Start Backend (Docker)

```powershell
cd "c:\Nandini Kushwah\My\AB Testing and Uplifting Model\autoab"
docker compose up -d
```

Wait ~10 seconds for services to initialize.

#### 2. Verify Backend

```powershell
# Check all containers are running
docker compose ps

# Check API health
curl http://localhost:8000/health

# View logs
docker compose logs -f api
```

#### 3. Start Frontend

```powershell
cd "c:\Nandini Kushwah\My\AB Testing and Uplifting Model\autoab\frontend"
npm start
```

Opens http://localhost:3000

#### 4. Use CLI

```powershell
cd "c:\Nandini Kushwah\My\AB Testing and Uplifting Model\autoab\cli"
pip install -r requirements.txt
python autoab_cli.py health
python autoab_cli.py list
```

## Services Overview

| Service | Port | Purpose | Location |
|---------|------|---------|----------|
| **FastAPI** | 8000 | Backend API | Docker |
| **PostgreSQL** | 5432 | Database | Docker |
| **Redis** | 6379 | Cache & Queue | Docker |
| **Celery** | - | Background tasks | Docker |
| **React** | 3000 | Frontend UI | Windows |
| **CLI** | - | Terminal commands | Windows |

## Common Commands

### Docker Commands

```powershell
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f api
docker compose logs -f celery-worker

# Restart a service
docker compose restart api

# Rebuild containers (after code changes)
docker compose up -d --build

# Check status
docker compose ps

# Shell into API container
docker compose exec api bash

# Database shell
docker compose exec db psql -U autoab -d autoab
```

### Frontend Commands

```powershell
cd frontend

# Install dependencies (first time)
npm install

# Start dev server
npm start

# Build for production
npm run build

# Clear cache
rm -rf node_modules
npm install
```

### CLI Commands

```powershell
cd cli

# Install dependencies (first time)
pip install -r requirements.txt

# List experiments
python autoab_cli.py list

# Show experiment details
python autoab_cli.py show 1

# Create experiment
python autoab_cli.py create \
  --name "Button Test" \
  --url-a "http://localhost:3001" \
  --url-b "http://localhost:3002"

# Start experiment
python autoab_cli.py start 1

# View results
python autoab_cli.py results 1

# Generate AI report
python autoab_cli.py report 1

# Stop experiment
python autoab_cli.py stop 1

# Check API health
python autoab_cli.py health
```

## Troubleshooting

### Docker Issues

**Docker not running:**
```powershell
# Start Docker Desktop manually
# Wait for "Docker Desktop is running" in system tray
```

**Port already in use:**
```powershell
# Check what's using the port
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

**Services not starting:**
```powershell
# View detailed logs
docker compose logs

# Restart services
docker compose down
docker compose up -d
```

**Database connection errors:**
```powershell
# Check PostgreSQL is running
docker compose ps

# View database logs
docker compose logs db

# Reset database
docker compose down -v
docker compose up -d
```

### Frontend Issues

**Port 3000 in use:**
```powershell
# Kill process on port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Cannot connect to backend:**
- Ensure Docker services are running: `docker compose ps`
- Check API responds: `curl http://localhost:8000/health`
- Frontend proxy is configured in package.json

### CLI Issues

**Module not found:**
```powershell
cd cli
pip install -r requirements.txt
```

**Connection refused:**
- Make sure backend is running in Docker
- Try: `python autoab_cli.py --api-url http://localhost:8000 health`

## Development Workflow

### Making Backend Changes

1. Edit Python files in `backend/`
2. Rebuild container:
   ```powershell
   docker compose up -d --build api
   ```
3. View logs:
   ```powershell
   docker compose logs -f api
   ```

### Making Frontend Changes

1. Edit files in `frontend/src/`
2. Hot reload happens automatically
3. Refresh browser if needed

### Database Migrations

```powershell
# Access database shell
docker compose exec db psql -U autoab -d autoab

# Or run migrations (if using Alembic)
docker compose exec api alembic upgrade head
```

## Data Persistence

- **PostgreSQL data**: Persisted in Docker volume `postgres_data`
- **Redis data**: Ephemeral (lost on restart)

To completely reset:
```powershell
docker compose down -v  # -v removes volumes
docker compose up -d
```

## Production Deployment

For production, consider:

1. **Backend**: Deploy Docker Compose to cloud VM (AWS EC2, DigitalOcean, etc.)
2. **Frontend**: Build and deploy to Vercel/Netlify:
   ```powershell
   cd frontend
   npm run build
   # Deploy 'build' folder
   ```
3. **Database**: Use managed PostgreSQL (AWS RDS, Supabase, etc.)
4. **Redis**: Use managed Redis (Redis Cloud, AWS ElastiCache)

## Alternative: Pure WSL2 Setup

If you prefer running everything in WSL2 instead of Docker:

1. Install WSL2:
   ```powershell
   wsl --install
   ```

2. Inside WSL2 Ubuntu:
   ```bash
   # Install Redis & PostgreSQL
   sudo apt update
   sudo apt install redis-server postgresql postgresql-contrib python3-pip

   # Start services
   sudo service redis-server start
   sudo service postgresql start

   # Run backend
   cd /mnt/c/Nandini\ Kushwah/My/AB\ Testing\ and\ Uplifting\ Model/autoab/backend
   pip3 install -r requirements.txt
   uvicorn app:app --reload

   # Run Celery
   celery -A app.celery_app worker --loglevel=info
   ```

3. Frontend & CLI still run on Windows

**Verdict**: Docker is simpler! One command vs. managing multiple services.

## Summary

✅ **Use Docker for backend** → Handles Redis, PostgreSQL, Celery, FastAPI
✅ **Use Windows for frontend** → npm start works great
✅ **Use Windows for CLI** → Direct Python execution

This gives you:
- Linux environment for services that need it (Redis, Celery)
- Native Windows performance for development tools
- Easy one-command startup
- Production-ready containerization
