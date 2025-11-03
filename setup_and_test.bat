@echo off
REM Complete setup and test script for Football Club Platform
REM Advanced Analytics System (Windows)

echo ========================================================================
echo FOOTBALL CLUB PLATFORM - ADVANCED ANALYTICS SETUP
echo ========================================================================

REM Check if Docker is running
echo.
echo Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)
echo [OK] Docker is running

REM Navigate to backend
cd backend

REM Step 1: Start database
echo.
echo Step 1: Starting PostgreSQL database...
docker-compose -f ../infra/docker-compose.yml up -d db
if errorlevel 1 (
    echo [WARNING] Database might already be running
)
echo [OK] PostgreSQL started

REM Wait for database
echo.
echo Waiting for database to be ready...
timeout /t 5 /nobreak >nul

REM Step 2: Apply migrations
echo.
echo Step 2: Applying database migrations...
alembic upgrade head
if errorlevel 1 (
    echo [ERROR] Migration failed. Check alembic.ini and database connection.
    pause
    exit /b 1
)
echo [OK] Migrations applied

REM Step 3: Seed database
echo.
echo Step 3: Seeding database with demo data...
python scripts\complete_seed_advanced.py
if errorlevel 1 (
    echo [ERROR] Seeding failed. Check the error messages above.
    pause
    exit /b 1
)
echo [OK] Database seeded

REM Step 4: Start backend
echo.
echo Step 4: Starting backend server...
echo    Starting uvicorn on http://localhost:8000
echo    Press Ctrl+C to stop the server later

REM Check if port is already in use
netstat -ano | findstr :8000 >nul
if not errorlevel 1 (
    echo [WARNING] Backend already running on port 8000
    echo    Skipping backend start...
) else (
    REM Start backend in a new window
    start "Football Club Platform Backend" cmd /c "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

    REM Wait for backend to start
    echo    Waiting for backend to start...
    timeout /t 10 /nobreak >nul

    REM Check if backend is responding
    curl -s http://localhost:8000/healthz >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Backend failed to start
        pause
        exit /b 1
    )
    echo [OK] Backend started
)

REM Step 5: Run tests
echo.
echo Step 5: Running API tests...
python scripts\test_analytics_apis.py
if errorlevel 1 (
    echo [ERROR] Some tests failed
    pause
    exit /b 1
)
echo [OK] All tests passed

REM Summary
echo.
echo ========================================================================
echo SETUP COMPLETED SUCCESSFULLY!
echo ========================================================================
echo.
echo Your Football Club Platform is now running with:
echo    • Advanced ML Analytics
echo    • 8 Teams with 176 players
echo    • 60+ matches with detailed statistics
echo    • Performance Index, xG/xA calculations
echo    • Intelligent Scouting System
echo.
echo Access Points:
echo    • API Documentation: http://localhost:8000/docs
echo    • Health Check: http://localhost:8000/healthz
echo    • Metrics: http://localhost:8000/metrics
echo.
echo Login Credentials:
echo    Email: admin@demo.club
echo    Password: admin123
echo.
echo Documentation:
echo    • Advanced Analytics Guide: ADVANCED_ANALYTICS_GUIDE.md
echo    • Main README: README.md
echo.
echo ========================================================================
echo.
pause
