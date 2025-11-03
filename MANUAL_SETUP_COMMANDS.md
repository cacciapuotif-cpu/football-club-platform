# Manual Setup Commands - Step by Step

## Prerequisites Check

```bash
# Check Docker is running
docker --version
docker info

# Check Python version (need 3.11+)
python --version

# Check if required packages are installed
pip list | grep -E "fastapi|sqlalchemy|alembic|asyncpg"
```

---

## Step 1: Start PostgreSQL Database

```bash
# From project root
cd infra
docker-compose up -d db

# Wait for database to be ready (check logs)
docker-compose logs -f db

# Verify database is running
docker ps | grep postgres

# Test connection
docker exec -it football-club-platform-db-1 psql -U app -d nextgoal -c "SELECT version();"
```

**Expected output:** PostgreSQL version info

---

## Step 2: Configure Environment

```bash
cd ../backend

# Check .env file exists and has correct DATABASE_URL
cat .env | grep DATABASE_URL

# Example DATABASE_URL:
# DATABASE_URL=postgresql+asyncpg://app:changeme@localhost:5432/nextgoal
```

---

## Step 3: Apply Database Migrations

```bash
# Make sure you're in backend directory
pwd  # Should show: /path/to/football-club-platform/backend

# Check alembic.ini is configured
cat alembic.ini | grep sqlalchemy.url

# Run migrations
alembic upgrade head

# Verify current migration version
alembic current

# Check tables were created
docker exec -it football-club-platform-db-1 psql -U app -d nextgoal -c "\dt"
```

**Expected output:** List of tables including `players`, `player_stats`, `teams`, `matches`, etc.

---

## Step 4: Seed Database with Demo Data

```bash
# From backend directory
python scripts/complete_seed_advanced.py
```

**Expected output:**
```
🚀 Starting complete database seeding...
✅ Organization created: Demo Football Club
✅ Admin user created: admin@demo.club / admin123
✅ Season created: 2024-2025
✅ Created 8 teams
✅ Created 176 players across all teams
✅ Created 60 matches
🎯 Generating player statistics with ML metrics...
✅ Created 800+ player statistics with ML metrics
📊 Updating player ratings...
✅ Player ratings and market values updated

🎉 DATABASE SEEDING COMPLETED SUCCESSFULLY!
```

---

## Step 5: Verify Data Was Created

```bash
# Count records in database
docker exec -it football-club-platform-db-1 psql -U app -d nextgoal << EOF
SELECT 'Teams' as table_name, COUNT(*) as count FROM teams
UNION ALL
SELECT 'Players', COUNT(*) FROM players
UNION ALL
SELECT 'Matches', COUNT(*) FROM matches
UNION ALL
SELECT 'Player Stats', COUNT(*) FROM player_stats;
EOF
```

**Expected output:**
```
  table_name   | count
---------------+-------
 Teams         |     8
 Players       |   176
 Matches       |    60
 Player Stats  |   800+
```

---

## Step 6: Start Backend Server

```bash
# From backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [PID]
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
🚀 Starting Football Club Platform API...
✅ Football Club Platform API started successfully
INFO:     Application startup complete.
```

**Keep this terminal open** - the backend is now running.

---

## Step 7: Test Health Endpoint (New Terminal)

```bash
# Open a new terminal window
curl http://localhost:8000/healthz
```

**Expected output:**
```json
{
  "status": "ok",
  "service": "Football Club Platform API",
  "version": "1.0.0"
}
```

---

## Step 8: Test Advanced Analytics APIs

```bash
# From backend directory (in new terminal)
python scripts/test_analytics_apis.py
```

**Expected output:**
```
======================================================================
🧪 ADVANCED ANALYTICS API TEST SUITE
======================================================================

✅ Backend is running

📋 Fetching sample data...
   Using player ID: <uuid>
   Using team ID: <uuid>

📊 TEST 1: Player Analysis API
   ✅ SUCCESS
   Player: Marco Rossi
   Position: MF
   Overall Rating: 7.25
   Performance Index: 72.50
   Form Prediction: 7.80
   ...

🔍 TEST 2: Scouting Recommendations API
   ✅ SUCCESS
   Total Recommendations: 15
   Strong Buys: 3
   ...

🏆 TEST 3: Team Analysis API
   ✅ SUCCESS
   Total Players: 22
   Average Rating: 7.15
   ...

📈 TEST 4: Performance Trend API
   ✅ SUCCESS
   Period: 60 days
   ...

======================================================================
📊 TEST SUMMARY
======================================================================
   Passed: 4/4
   Failed: 0/4

   ✅ ALL TESTS PASSED! 🎉
```

---

## Step 9: Access API Documentation

Open in browser: **http://localhost:8000/docs**

Navigate to section **"Advanced ML Analytics & Scouting"**

Try these endpoints:
1. `GET /api/v1/advanced-analytics/players/{player_id}/analysis`
2. `GET /api/v1/advanced-analytics/scouting/teams/{team_id}/recommendations`
3. `GET /api/v1/advanced-analytics/teams/{team_id}/analysis`
4. `GET /api/v1/advanced-analytics/players/{player_id}/trend`

---

## Manual API Testing with curl

### Get All Players (to find IDs)
```bash
curl http://localhost:8000/api/v1/players?limit=5
```

Copy a `player_id` and `team_id` from the response.

### Test Player Analysis
```bash
PLAYER_ID="<paste-uuid-here>"

curl "http://localhost:8000/api/v1/advanced-analytics/players/$PLAYER_ID/analysis?matches=10" | python -m json.tool
```

### Test Scouting
```bash
TEAM_ID="<paste-uuid-here>"

curl "http://localhost:8000/api/v1/advanced-analytics/scouting/teams/$TEAM_ID/recommendations?position=FW&max_age=28&max_budget=50000000&min_rating=6.5" | python -m json.tool
```

### Test Team Analysis
```bash
TEAM_ID="<paste-uuid-here>"

curl "http://localhost:8000/api/v1/advanced-analytics/teams/$TEAM_ID/analysis" | python -m json.tool
```

### Test Performance Trend
```bash
PLAYER_ID="<paste-uuid-here>"

curl "http://localhost:8000/api/v1/advanced-analytics/players/$PLAYER_ID/trend?period_days=60" | python -m json.tool
```

---

## Stopping Services

### Stop Backend
In the terminal where backend is running:
```
Press CTRL+C
```

### Stop Database
```bash
cd infra
docker-compose down
```

Or to remove volumes (delete data):
```bash
docker-compose down -v
```

---

## Re-seeding Database

If you need to reset and re-seed:

```bash
# Drop all tables
cd backend
alembic downgrade base

# Re-apply migrations
alembic upgrade head

# Re-seed
python scripts/complete_seed_advanced.py
```

---

## Troubleshooting Commands

### Check if port 8000 is in use
```bash
# Linux/macOS
lsof -i :8000

# Windows (Git Bash)
netstat -ano | grep 8000

# Windows (CMD)
netstat -ano | findstr :8000
```

### Kill process on port 8000
```bash
# Linux/macOS
lsof -ti:8000 | xargs kill -9

# Windows
# Find PID from netstat above, then:
taskkill /PID <PID> /F
```

### Check database connection
```bash
docker exec -it football-club-platform-db-1 psql -U app -d nextgoal -c "SELECT 1;"
```

### View database logs
```bash
cd infra
docker-compose logs -f db
```

### View backend logs (if running in background)
```bash
cd backend
tail -f backend.log
```

### Reset alembic migrations
```bash
cd backend

# Check current version
alembic current

# Downgrade to base
alembic downgrade base

# Upgrade to head
alembic upgrade head
```

---

## Quick Verification Checklist

- [ ] Docker is running
- [ ] PostgreSQL container is running (`docker ps`)
- [ ] Backend can connect to database (check `alembic current`)
- [ ] Migrations applied (`player_stats` table exists)
- [ ] Data seeded (800+ player_stats records)
- [ ] Backend running on port 8000
- [ ] Health check returns 200 OK
- [ ] API documentation accessible at /docs
- [ ] All 4 tests pass

---

**If all checks pass, your Advanced Analytics system is fully operational! 🎉**

For detailed API usage and examples, see `ADVANCED_ANALYTICS_GUIDE.md`.
