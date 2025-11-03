#!/bin/bash

# Complete Football Platform Setup Script
# This script sets up the complete platform with 50+ players and ML algorithms

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════════════════════"
echo "  🚀 FOOTBALL CLUB PLATFORM - COMPLETE SETUP                                    "
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Check prerequisites
echo ""
print_info "Step 1/6: Checking prerequisites..."
echo "────────────────────────────────────────────────────────────────────────────────"

# Check for Docker
if command -v docker &> /dev/null; then
    print_success "Docker found: $(docker --version)"
else
    print_error "Docker not found! Please install Docker first."
    exit 1
fi

# Check for Docker Compose
if command -v docker-compose &> /dev/null; then
    print_success "Docker Compose found: $(docker-compose --version)"
else
    print_error "Docker Compose not found! Please install Docker Compose first."
    exit 1
fi

# Check for Python
if command -v python &> /dev/null; then
    print_success "Python found: $(python --version)"
else
    print_error "Python not found! Please install Python 3.9+ first."
    exit 1
fi

# Step 2: Start database
echo ""
print_info "Step 2/6: Starting database services..."
echo "────────────────────────────────────────────────────────────────────────────────"

print_info "Starting Docker containers..."
docker-compose up -d postgres

# Wait for postgres to be ready
print_info "Waiting for PostgreSQL to be ready..."
sleep 5

# Check if postgres is running
if docker ps | grep -q postgres; then
    print_success "PostgreSQL is running"
else
    print_error "Failed to start PostgreSQL"
    exit 1
fi

# Step 3: Install Python dependencies
echo ""
print_info "Step 3/6: Installing Python dependencies..."
echo "────────────────────────────────────────────────────────────────────────────────"

cd backend

if [ -f "requirements.txt" ]; then
    print_info "Installing requirements..."
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
else
    print_warning "requirements.txt not found, skipping..."
fi

cd ..

# Step 4: Run database migrations
echo ""
print_info "Step 4/6: Running database migrations..."
echo "────────────────────────────────────────────────────────────────────────────────"

cd backend

print_info "Applying all migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    print_success "Migrations applied successfully"
else
    print_error "Failed to apply migrations"
    cd ..
    exit 1
fi

cd ..

# Step 5: Seed database with complete data
echo ""
print_info "Step 5/6: Seeding database with 50+ players and training data..."
echo "────────────────────────────────────────────────────────────────────────────────"

print_info "Running complete data seed script..."
python scripts/complete_data_seed.py

if [ $? -eq 0 ]; then
    print_success "Database seeded successfully"
else
    print_error "Failed to seed database"
    exit 1
fi

# Step 6: Verify data
echo ""
print_info "Step 6/6: Verifying data..."
echo "────────────────────────────────────────────────────────────────────────────────"

print_info "Running verification script..."
python scripts/verify_complete_data.py

if [ $? -eq 0 ]; then
    print_success "Data verification completed"
else
    print_warning "Verification completed with warnings"
fi

# Final summary
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "  ✅ SETUP COMPLETE!                                                             "
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
print_success "Platform setup completed successfully!"
echo ""
echo "📊 What was created:"
echo "   • 50+ players with complete profiles (physical, tactical, psychological)"
echo "   • 10 training sessions with detailed statistics"
echo "   • 550+ individual training performance records"
echo "   • Advanced ML algorithms ready to use"
echo ""
echo "🚀 Next steps:"
echo ""
echo "   1. Start the backend server:"
echo "      ${GREEN}cd backend && uvicorn app.main:app --reload${NC}"
echo ""
echo "   2. Access API documentation:"
echo "      ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "   3. Test ML algorithms:"
echo "      ${GREEN}python scripts/test_ml_algorithms.py${NC}"
echo ""
echo "   4. View exported data:"
echo "      ${GREEN}cat artifacts/complete_data_export.json | python -m json.tool | head -50${NC}"
echo ""
echo "   5. Query sample players:"
echo "      ${BLUE}curl http://localhost:8000/api/players | python -m json.tool${NC}"
echo ""
echo "📚 Documentation:"
echo "   • Complete setup guide: ${BLUE}COMPLETE_PLATFORM_SETUP.md${NC}"
echo "   • API endpoints: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
