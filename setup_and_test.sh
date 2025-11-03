#!/bin/bash
# Complete setup and test script for Football Club Platform
# Advanced Analytics System

set -e  # Exit on error

echo "========================================================================"
echo "🚀 FOOTBALL CLUB PLATFORM - ADVANCED ANALYTICS SETUP"
echo "========================================================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo -e "\n${YELLOW}Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# Navigate to backend
cd backend

# Step 1: Start database with Docker Compose
echo -e "\n${YELLOW}Step 1: Starting PostgreSQL database...${NC}"
if docker-compose -f ../infra/docker-compose.yml up -d db; then
    echo -e "${GREEN}✅ PostgreSQL started${NC}"
else
    echo -e "${YELLOW}⚠️  Database might already be running${NC}"
fi

# Wait for database to be ready
echo -e "\n${YELLOW}Waiting for database to be ready...${NC}"
sleep 5

# Step 2: Apply migrations
echo -e "\n${YELLOW}Step 2: Applying database migrations...${NC}"
if alembic upgrade head; then
    echo -e "${GREEN}✅ Migrations applied successfully${NC}"
else
    echo -e "${RED}❌ Migration failed. Check alembic.ini and database connection.${NC}"
    exit 1
fi

# Step 3: Seed database
echo -e "\n${YELLOW}Step 3: Seeding database with demo data...${NC}"
if python scripts/complete_seed_advanced.py; then
    echo -e "${GREEN}✅ Database seeded successfully${NC}"
else
    echo -e "${RED}❌ Seeding failed. Check the error messages above.${NC}"
    exit 1
fi

# Step 4: Start backend (in background)
echo -e "\n${YELLOW}Step 4: Starting backend server...${NC}"
echo "   Starting uvicorn on http://localhost:8000"
echo "   Logs will be in backend.log"

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
else
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"

    # Wait for backend to start
    echo "   Waiting for backend to start..."
    sleep 10

    # Check if backend is responding
    if curl -s http://localhost:8000/healthz > /dev/null; then
        echo -e "${GREEN}✅ Backend started successfully${NC}"
    else
        echo -e "${RED}❌ Backend failed to start. Check backend.log${NC}"
        exit 1
    fi
fi

# Step 5: Run tests
echo -e "\n${YELLOW}Step 5: Running API tests...${NC}"
if python scripts/test_analytics_apis.py; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed. Check the output above.${NC}"
    exit 1
fi

# Summary
echo -e "\n========================================================================"
echo -e "${GREEN}🎉 SETUP COMPLETED SUCCESSFULLY!${NC}"
echo "========================================================================"
echo ""
echo "📊 Your Football Club Platform is now running with:"
echo "   • Advanced ML Analytics"
echo "   • 8 Teams with 176 players"
echo "   • 60+ matches with detailed statistics"
echo "   • Performance Index, xG/xA calculations"
echo "   • Intelligent Scouting System"
echo ""
echo "🌐 Access Points:"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/healthz"
echo "   • Metrics: http://localhost:8000/metrics"
echo ""
echo "🔐 Login Credentials:"
echo "   Email: admin@demo.club"
echo "   Password: admin123"
echo ""
echo "📖 Documentation:"
echo "   • Advanced Analytics Guide: ADVANCED_ANALYTICS_GUIDE.md"
echo "   • Main README: README.md"
echo ""
echo "🛑 To stop the backend:"
echo "   kill \$(lsof -t -i:8000)"
echo ""
echo "========================================================================"
