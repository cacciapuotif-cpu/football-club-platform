@echo off
REM Complete Football Platform Setup Script for Windows
REM This script sets up the complete platform with 50+ players and ML algorithms

echo ================================================================================
echo   FOOTBALL CLUB PLATFORM - COMPLETE SETUP
echo ================================================================================
echo.

REM Step 1: Check prerequisites
echo.
echo Step 1/6: Checking prerequisites...
echo --------------------------------------------------------------------------------

REM Check for Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker not found! Please install Docker Desktop first.
    pause
    exit /b 1
)
echo OK: Docker found

REM Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found! Please install Python 3.9+ first.
    pause
    exit /b 1
)
echo OK: Python found

REM Step 2: Start database
echo.
echo Step 2/6: Starting database services...
echo --------------------------------------------------------------------------------

echo Starting Docker containers...
docker-compose up -d postgres

echo Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

docker ps | findstr postgres >nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to start PostgreSQL
    pause
    exit /b 1
)
echo OK: PostgreSQL is running

REM Step 3: Install Python dependencies
echo.
echo Step 3/6: Installing Python dependencies...
echo --------------------------------------------------------------------------------

cd backend

if exist requirements.txt (
    echo Installing requirements...
    pip install -r requirements.txt --quiet
    echo OK: Dependencies installed
) else (
    echo WARNING: requirements.txt not found, skipping...
)

cd ..

REM Step 4: Run database migrations
echo.
echo Step 4/6: Running database migrations...
echo --------------------------------------------------------------------------------

cd backend

echo Applying all migrations...
alembic upgrade head

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to apply migrations
    cd ..
    pause
    exit /b 1
)
echo OK: Migrations applied successfully

cd ..

REM Step 5: Seed database with complete data
echo.
echo Step 5/6: Seeding database with 50+ players and training data...
echo --------------------------------------------------------------------------------

echo Running complete data seed script...
python scripts\complete_data_seed.py

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to seed database
    pause
    exit /b 1
)
echo OK: Database seeded successfully

REM Step 6: Verify data
echo.
echo Step 6/6: Verifying data...
echo --------------------------------------------------------------------------------

echo Running verification script...
python scripts\verify_complete_data.py

if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Verification completed with warnings
) else (
    echo OK: Data verification completed
)

REM Final summary
echo.
echo ================================================================================
echo   SETUP COMPLETE!
echo ================================================================================
echo.
echo OK: Platform setup completed successfully!
echo.
echo What was created:
echo    - 50+ players with complete profiles (physical, tactical, psychological)
echo    - 10 training sessions with detailed statistics
echo    - 550+ individual training performance records
echo    - Advanced ML algorithms ready to use
echo.
echo Next steps:
echo.
echo    1. Start the backend server:
echo       cd backend ^&^& uvicorn app.main:app --reload
echo.
echo    2. Access API documentation:
echo       http://localhost:8000/docs
echo.
echo    3. Test ML algorithms:
echo       python scripts\test_ml_algorithms.py
echo.
echo    4. View exported data:
echo       type artifacts\complete_data_export.json
echo.
echo Documentation:
echo    - Complete setup guide: COMPLETE_PLATFORM_SETUP.md
echo    - API endpoints: http://localhost:8000/docs
echo.
echo ================================================================================

pause
