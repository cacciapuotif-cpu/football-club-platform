# Seeding Guide - Demo Data for Progress Tracking

This guide explains how to seed the database with realistic demo data for testing the player progress tracking features.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [What Gets Seeded](#what-gets-seeded)
- [Customizing the Seed](#customizing-the-seed)
- [Verifying the Seed](#verifying-the-seed)
- [Troubleshooting](#troubleshooting)

---

## Overview

The `seed_demo_data.py` script creates a complete dataset for development and testing:

- **Organization**: Demo Football Club
- **Season**: 2025/26
- **Team**: U17 (Youth category)
- **Players**: 25 players with realistic profiles
- **Wellness Data**: 90 days of daily wellness metrics per player
- **Training Sessions**: 30 sessions with attendance and GPS metrics
- **Matches**: 8 matches with player statistics
- **Metric Catalog**: Pre-populated with 30+ standard metrics

---

## Quick Start

### Prerequisites

1. **Database Running**: Ensure PostgreSQL is running and accessible
2. **Migrations Applied**: Run Alembic migrations first

```bash
# Apply migrations
cd backend
alembic upgrade head
```

### Run the Seed Script

```bash
# From project root
cd backend
python scripts/seed_demo_data.py
```

**Expected Output**:
```
============================================================
🌱 SEEDING DEMO DATA - EAV Progress Tracking
============================================================
🗂️  Seeding metric catalog...
   ✅ Metric catalog seeded via migration
🏢 Getting organization...
   ✅ Using existing organization: Demo Football Club
⚽ Creating season and team...
   ✅ Created season: 2025/26
   ✅ Created team: U17
👥 Creating players...
   ✅ Created 25 players
😴 Creating wellness data (90 days per player)...
   ✅ Created 2025 wellness sessions with 18225 metrics
🏋️  Creating training sessions with attendance...
   ✅ Created 30 training sessions, 675 attendances, 3375 metrics
⚽ Creating matches with player stats...
   ✅ Created 8 matches, 128 attendances, 896 metrics
============================================================
✅ SEEDING COMPLETE!
============================================================
Organization: Demo Football Club
Season: 2025/26
Team: U17 (25 players)

Next steps:
1. Start the API: make up (or docker compose up)
2. Test endpoints:
   GET /api/v1/players/{player_id}/progress?from=2025-01-01&to=2025-12-31&metrics=sleep_quality,stress,fatigue&groupby=week
   GET /api/v1/players/{player_id}/training-load?from=2025-01-01&to=2025-12-31
   GET /api/v1/players/{player_id}/overview?period=30d
   POST /api/v1/progress-ml/players/{player_id}/predict-risk
============================================================
```

---

## What Gets Seeded

### 1. Metric Catalog (30+ entries)

Pre-populated with standard metrics for wellness, training, and matches. Each metric includes:
- **Key**: Unique identifier (e.g., `sleep_quality`)
- **Area**: wellness, training, or match
- **Description**: Human-readable description
- **Unit**: score, m, km, bpm, etc.
- **Range**: Min/max values for validation
- **Direction**: up_is_better, down_is_better, or neutral

**Example Metrics**:
- Wellness: `sleep_quality`, `stress`, `fatigue`, `doms`, `mood`, `hydration`, `rpe_morning`
- Training: `rpe_post`, `hsr`, `sprint_count`, `total_distance`, `accel_count`, `avg_hr`
- Match: `pass_accuracy`, `sprint_count`, `duels_won`, `touches`, `shots_on_target`

### 2. Organization

Creates or uses existing organization:
- **Name**: Demo Football Club
- **Website**: https://demo.club

### 3. Season & Team

- **Season**: 2025/26 (July 1, 2025 - June 30, 2026)
- **Team**: U17 Youth team
- **Category**: Youth

### 4. Players (25 total)

Realistic player profiles with Italian names:

- **Roles**: Distributed across GK, DF, MF, FW
- **Birth Year**: 2008 (U17 age group)
- **Attributes**: Height (165-190cm), Weight (55-75kg)
- **Jersey Numbers**: 1-25
- **External IDs**: `DEMO_U17_01` through `DEMO_U17_25`

**Example Players**:
- Marco Rossi (GK, #1)
- Luca Bianchi (DF, #2)
- Andrea Verdi (MF, #3)
- Francesco Ferrari (FW, #4)
- ... (21 more)

### 5. Wellness Data (90 days per player)

Creates **~2,000+ wellness sessions** with **~18,000+ metrics**:

**Coverage**: 90 days back from today (with ~10% random missing data)

**Metrics per Session**:
- `sleep_quality` (6.5-8.5 with variation)
- `sleep_hours` (5.5-9.5)
- `stress` (3-6, increases on training days)
- `fatigue` (3-6, spikes after training)
- `doms` (2-5, increases post-training)
- `mood` (6-9)
- `motivation` (6-9)
- `hydration` (6-9)
- `rpe_morning` (2-5)

**Realistic Patterns**:
- Fatigue and DOMS increase on training days (Mon/Wed/Fri pattern)
- Sleep quality varies ±0.5 daily
- Temporal trends simulate real athlete data

### 6. Training Sessions (30 sessions)

Creates **30 training sessions** over 85 days:

**Session Types**: Technical, Tactical, Physical, Recovery

**Duration**: 60-105 minutes

**Intensity**: Low, Medium, High

**Attendance** (~90% participation):
- **Status**: present, absent, injured, sick
- **Minutes**: 45-90 (varies by participation)
- **RPE Post**: 4-8
- **Participation %**: Calculated from minutes/duration

**Metrics per Attendance**:
- `hsr`: High Speed Running (150-800m)
- `total_distance`: 3-9 km
- `accel_count`: 15-100
- `sprint_count`: 5-30
- `avg_hr`: 140-175 bpm

**Total Data**:
- ~675 attendance records
- ~3,375 training metrics

### 7. Matches (8 matches)

Creates **8 league matches** over 80 days:

**Opponents**: Juventus U17, Milan U17, Inter U17, Roma U17, Napoli U17, Lazio U17, Fiorentina U17, Atalanta U17

**Results**: Random distribution of WIN/DRAW/LOSS

**Lineup** (per match):
- 11 starters (60-90 minutes)
- 5 bench players (0-45 minutes)

**Attendance Data**:
- `is_starter`: True/False
- `minutes_played`: 0-90
- `goals`, `assists`: Realistic distribution
- `coach_rating`: 5.5-8.5

**Metrics per Player**:
- `sprint_count`: 8-35
- `hsr`: 200-1200m
- `total_distance`: 5-12 km
- `pass_accuracy`: 65-95%
- `pass_completed`: 15-80
- `duels_won`: 3-20
- `touches`: 30-100

**Positions**: Assigned based on player role (GK, CB, RB, LB, CM, CDM, CAM, ST, LW, RW)

**Total Data**:
- 8 matches
- ~128 attendance records
- ~896 match metrics

---

## Customizing the Seed

### Adjust Number of Players

Edit `seed_demo_data.py`:

```python
# Change from 25 to your desired count
for i in range(50):  # Create 50 players instead
    ...
```

### Adjust Wellness Days

```python
# Change from 90 to your desired count
for day_offset in range(180):  # 180 days instead
    ...
```

### Adjust Training Sessions

```python
# Change from 30 to your desired count
for i in range(60):  # 60 training sessions instead
    ...
```

### Adjust Matches

```python
# Change from 8 to your desired count
for i in range(15):  # 15 matches instead
    ...
```

### Customize Metric Values

Adjust the base values and ranges:

```python
# Make players more fatigued
base_fatigue = random.uniform(5.0, 8.0)  # Higher fatigue

# Make sleep quality lower
base_sleep = random.uniform(5.0, 7.0)  # Lower sleep quality
```

---

## Verifying the Seed

### 1. Check Database Counts

```sql
-- Wellness
SELECT COUNT(*) FROM wellness_sessions;  -- Should be ~2000+
SELECT COUNT(*) FROM wellness_metrics;   -- Should be ~18000+

-- Training
SELECT COUNT(*) FROM training_attendance;  -- Should be ~675
SELECT COUNT(*) FROM training_metrics;     -- Should be ~3375

-- Matches
SELECT COUNT(*) FROM matches;         -- Should be 8
SELECT COUNT(*) FROM attendances;     -- Should be ~128
SELECT COUNT(*) FROM match_metrics;   -- Should be ~896

-- Players
SELECT COUNT(*) FROM players WHERE team_id IS NOT NULL;  -- Should be 25
```

### 2. Test API Endpoints

Get a player ID:
```bash
curl "http://localhost:8000/api/v1/players" | jq '.[0].id'
```

Test endpoints (replace `{player_id}` with actual UUID):

```bash
# Progress
curl "http://localhost:8000/api/v1/players/{player_id}/progress?from=2025-01-01&to=2025-12-31&metrics=sleep_quality,stress&groupby=week"

# Training Load
curl "http://localhost:8000/api/v1/players/{player_id}/training-load?from=2025-01-01&to=2025-12-31"

# Overview
curl "http://localhost:8000/api/v1/players/{player_id}/overview?period=30d"

# ML Risk Prediction
curl -X POST "http://localhost:8000/api/v1/progress-ml/players/{player_id}/predict-risk"
```

### 3. Verify Data Quality

```sql
-- Check for duplicates
SELECT player_id, date, COUNT(*)
FROM wellness_sessions
GROUP BY player_id, date
HAVING COUNT(*) > 1;

-- Check metric validity
SELECT validity, COUNT(*)
FROM wellness_metrics
GROUP BY validity;

-- Check ACWR calculation
SELECT * FROM mv_training_load LIMIT 10;
```

---

## Troubleshooting

### Error: "No organization found"

**Solution**: Create an organization manually or ensure migrations are applied.

```python
# Or create via SQL
INSERT INTO organizations (id, name, website)
VALUES (gen_random_uuid(), 'Demo Football Club', 'https://demo.club');
```

### Error: "Table does not exist"

**Solution**: Run Alembic migrations first.

```bash
cd backend
alembic upgrade head
```

### Error: "Duplicate key violation"

**Solution**: The seed script is idempotent. It checks for existing data and skips if already seeded. To re-seed, delete existing data first:

```sql
-- ⚠️ WARNING: This deletes ALL data!
DELETE FROM wellness_metrics;
DELETE FROM wellness_sessions;
DELETE FROM training_metrics;
DELETE FROM training_attendance;
DELETE FROM match_metrics;
DELETE FROM match_player_positions;
DELETE FROM attendances;
DELETE FROM matches;
DELETE FROM players WHERE external_id LIKE 'DEMO_U17_%';
DELETE FROM teams WHERE name = 'U17';
DELETE FROM seasons WHERE name = '2025/26';
```

### Performance Issues

For large datasets:

1. **Increase batch size**: Commit less frequently
2. **Disable indexes temporarily**: Drop indexes before seeding, recreate after
3. **Use COPY**: For CSV imports, use PostgreSQL COPY command

---

## Next Steps

After seeding:

1. **Explore the API**: See `API_USAGE.md` for endpoint documentation
2. **Build ML Models**: Use the seeded data to train injury prediction models
3. **Create Dashboards**: Visualize player progress and trends
4. **Test Workflows**: Simulate real-world coach/analyst workflows

---

## Support

For issues or questions:
- Check logs: `backend/logs/` (if configured)
- GitHub Issues: https://github.com/your-org/football-club-platform/issues
- Documentation: See `README.md` and `API_USAGE.md`

---

**Last Updated**: 2025-11-05
