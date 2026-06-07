#!/bin/bash

# Startup script for AutoAB Platform

echo "🚀 Starting AutoAB Platform..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Start backend services with Docker Compose
echo "📦 Starting backend services (PostgreSQL, Redis, FastAPI, Celery)..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service health
echo ""
echo "🔍 Checking service status..."
docker compose ps

echo ""
echo "=" * 80
echo "✅ AutoAB Platform is starting!"
echo "=" * 80
echo ""
echo "Backend API:      http://localhost:8000"
echo "API Docs:         http://localhost:8000/docs"
echo "PostgreSQL:       localhost:5432"
echo "Redis:            localhost:6379"
echo ""
echo "To start the frontend:"
echo "  cd frontend"
echo "  npm start"
echo ""
echo "To use the CLI:"
echo "  cd cli"
echo "  python autoab_cli.py list"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop all services:"
echo "  docker compose down"
echo ""
