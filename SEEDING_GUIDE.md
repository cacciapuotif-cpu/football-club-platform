# 🌱 Football Club Platform - Seeding Guide

Comprehensive guide for database seeding with idempotent, ordered, and transaction-safe operations.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Port Configuration](#port-configuration)
- [Quick Start](#quick-start)
- [Datasets](#datasets)
- [Architecture](#architecture)
- [Usage](#usage)
- [Testing](#testing)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The seeding system provides:

- **Idempotent**: Can be run multiple times safely
- **Ordered**: Executes steps in topological order (respecting FK dependencies)
- **Transaction-safe**: Each step is atomic
- **Configurable**: Three datasets (minimal, staging, demo)
- **Port-safe**: Guard-rails prevent conflicts with pythonpro (port 3001)

---

## 🔒 Port Configuration

### Critical: Port 3001 Reserved

**Port 3001 is RESERVED for pythonpro and must NOT be used by Football Club Platform.**

### Football Club Platform Ports

| Service        | Variable         | Default | Notes                               |
|----------------|------------------|---------|-------------------------------------|
| Frontend       | `FCP_WEB_PORT`   | 3000    | **NEVER SET TO 3001**               |
| Backend API    | `FCP_API_PORT`   | 8000    | Main API                            |
| Backend Alt    | `FCP_API_PORT_ALT` | 8001  | Alternative (if needed)             |
| Database       | `FCP_DB_PORT`    | 5434    | PostgreSQL (not 5432 to avoid conflicts) |
| Redis          | `FCP_REDIS_PORT` | 6381    | Cache (not 6379 to avoid conflicts) |

### Configuration Files

Add to `.env`:

```bash
# Football Club Platform Ports
FCP_WEB_PORT=3000
FCP_API_PORT=8000
FCP_API_PORT_ALT=8001
FCP_DB_PORT=5434
FCP_REDIS_PORT=6381

# Reserved - DO NOT USE
PYTHONPRO_WEB_PORT=3001
```

### Port Validation

The seeding system automatically validates ports at startup:

```python
# backend/seeds/config.py validates at import time
if FCP_WEB_PORT == 3001:
    sys.exit("❌ Port 3001 is RESERVED for pythonpro!")
```

---

## 🚀 Quick Start

### 1. Initialize Environment

```bash
# Copy example environment file
cp .env.example .env

# Verify port configuration
make check-ports
```

### 2. Start Services

```bash
# Start Docker containers
make up

# Wait for services to be healthy
docker-compose ps
```

### 3. Run Migrations

```bash
# Apply database migrations
make migrate
```

### 4. Seed Database

```bash
# Minimal dataset (CI/testing)
make seed-minimal

# OR staging dataset
make seed-staging

# OR demo dataset (rich data)
make seed-demo
```

### 5. Verify

```bash
# Check database
make db-shell
# \dt  -- list tables
# SELECT COUNT(*) FROM players;
```

---

## 📦 Datasets

### Minimal (`minimal.yaml`)

**Purpose**: CI/CD, quick testing, development

**Contents**:
- 1 Organization ("Minimal FC")
- 1 Season (2024-2025)
- 1 Team ("Prima Squadra")
- 1 Admin User
- 2 Players (Marco Rossi, Luca Bianchi)

**Use cases**:
- Automated tests
- CI pipelines
- Quick local development

```bash
make seed-minimal
# OR
DATASET=minimal make seed
```

### Staging (`staging.yaml`)

**Purpose**: Staging environment, integration testing

**Contents**:
- 1 Organization ("Staging FC")
- 2 Seasons (2023-2024, 2024-2025)
- 3 Teams (Prima Squadra, Primavera, Giovanissimi)
- 2 Users (Admin, Coach)
- 4 Players (diverse roles and teams)

**Use cases**:
- Staging deployments
- Integration tests
- Pre-production validation

```bash
make seed-staging
```

### Demo (`demo.yaml`)

**Purpose**: Demonstrations, UI development, rich testing

**Contents**:
- 1 Organization ("Demo FC")
- 3 Seasons (2022-2025)
- 4 Teams
- 3 Users (Admin, Coach, Doctor)
- 12 Players (realistic names, varied attributes)
  - **All players have `external_id`** for optimal idempotence
  - 8 Primera Squadra players with professional-level tactical attributes
  - 4 Primavera (U19) youth players with guardian information

**Use cases**:
- Product demos
- UI/UX development
- Frontend testing
- Manual QA

```bash
make seed-demo
```

**Player Natural Keys**:
Players use a **three-tier idempotent strategy**:
1. **external_id** (e.g., `demo-fc-ps-10`) - Primary natural key
2. **(organization_id, team_id, jersey_number)** - Secondary composite key
3. **(organization_id, team_id, last_name, first_name, date_of_birth)** - Fallback identity key

This ensures players can be safely re-seeded without creating duplicates.

---

## 🏗️ Architecture

### Directory Structure

```
backend/seeds/
├── __init__.py                # Package root
├── config.py                  # Configuration + port guard-rails
├── utils.py                   # Transaction & upsert utilities
├── runner.py                  # Main orchestrator
├── datasets/                  # YAML dataset files
│   ├── minimal.yaml
│   ├── staging.yaml
│   └── demo.yaml
└── steps/                     # Seed steps (topological order)
    ├── __init__.py
    ├── 01_organizations.py    # Root entity (no dependencies)
    ├── 02_seasons.py          # FK: organization_id
    ├── 03_teams.py            # FK: organization_id, season_id
    ├── 04_users.py            # FK: organization_id
    ├── 05_players.py          # FK: organization_id, team_id
    └── 99_relations.py        # N-N relationships, late FK bindings
```

### Dependency Graph

```
Organizations (root)
├── Seasons
│   └── Teams
├── Teams
│   └── Players
└── Users
```

**Execution Order**: `01 → 02 → 03 → 04 → 05 → 99`

### Key Components

#### 1. Config (`config.py`)

- Port validation (guard-rails)
- Dataset selection
- Environment configuration
- Production safety checks

#### 2. Utils (`utils.py`)

- `tx()`: Transaction context manager
- `upsert()`: Idempotent create/update/skip
- `bulk_upsert()`: Efficient batch operations
- Validation helpers

#### 3. Runner (`runner.py`)

- Loads YAML dataset
- Executes steps in order
- Reports statistics
- Handles errors

#### 4. Steps (`steps/*.py`)

Each step:
1. Receives session + data
2. Resolves FK dependencies
3. Upserts entities
4. Returns statistics

##### Step 05: Players (`05_players.py`)

**Advanced Idempotent Strategy**:

Players use a robust three-tier natural key approach:

```python
unique_keys = []

# 1. Primary: external_id (if present)
if external_id:
    unique_keys.append(("external_id",))

# 2. Secondary: Composite key with jersey number
if jersey_number:
    unique_keys.append(("organization_id", "team_id", "jersey_number"))

# 3. Fallback: Identity-based key
unique_keys.append((
    "organization_id", "team_id",
    "last_name", "first_name", "date_of_birth"
))
```

**Features**:
- ✅ Safe FK resolution with `_resolve_org()` and `_resolve_team()`
- ✅ Enum parsing: PlayerRole, DominantFoot, DominantArm
- ✅ Minor player support with guardian information
- ✅ Tactical/mental attributes (1-100 scale)
- ✅ Detailed logging: inserted/updated/skipped counts
- ✅ Non-strict error handling (continues on individual failures)

**Example Data**:
```yaml
05-players:
  - external_id: "demo-fc-ps-10"          # Primary natural key
    organization_slug: "demo-fc"
    team_name: "Prima Squadra"
    first_name: "Marco"
    last_name: "Rossi"
    date_of_birth: "2008-05-15"
    nationality: "IT"
    role_primary: "FW"
    role_secondary: "MF"                  # Optional
    dominant_foot: "RIGHT"
    dominant_arm: "RIGHT"
    jersey_number: 10
    height_cm: 178
    weight_kg: 72
    is_minor: false
    tactical_awareness: 75
    positioning: 70
    decision_making: 68
    work_rate: 80
    mental_strength: 72
    leadership: 65
    concentration: 70
    adaptability: 75
```

---

## 💻 Usage

### Command Line

```bash
# Basic usage (minimal dataset)
python -m seeds.runner

# Specify dataset
DATASET=staging python -m seeds.runner

# Verbose mode
SEED_VERBOSE=true python -m seeds.runner

# With arguments
python -m seeds.runner --dataset=demo --verbose
```

### Makefile

```bash
# Seed commands
make seed                    # Default: minimal
make seed DATASET=staging    # Explicit dataset
make seed-minimal            # Shortcut
make seed-staging            # Shortcut
make seed-demo               # Shortcut

# Reseed (reset + migrate + seed)
make reseed                  # With current DATASET
make reseed DATASET=demo     # Explicit dataset
make reseed-minimal          # Shortcut
make reseed-demo             # Shortcut

# Port validation
make check-ports             # Verify no conflicts

# Database operations
make migrate                 # Apply migrations
make migrate-reset           # Reset to base
make db-shell                # PostgreSQL shell

# Combined operations
make quickstart              # up + migrate + seed-minimal
```

### Docker

```bash
# Inside container
docker exec football_club_platform_backend python -m seeds.runner

# With environment variable
docker exec -e DATASET=demo football_club_platform_backend python -m seeds.runner
```

### Windows PowerShell

```powershell
# Set dataset
$env:DATASET="demo"

# Run seeder
docker exec football_club_platform_backend python -m seeds.runner

# Quickstart
make quickstart-win
```

---

## 🧪 Testing

### Run Seed Tests

```bash
# All seed tests
make test-seeds

# Player seed tests (idempotence, FK resolution, enum parsing)
pytest tests/test_seeds_players.py -v

# CORS tests (frontend-backend communication)
pytest tests/test_cors.py -v

# With coverage
pytest tests/test_seeds.py tests/test_seeds_players.py --cov=seeds --cov-report=html

# Specific test
pytest tests/test_seeds_players.py::TestPlayerSeedIdempotence::test_seed_players_idempotent_external_id -v
```

### Test Coverage

Seed tests verify:

- ✅ **Idempotence** (multiple runs = same result)
  - external_id strategy
  - Composite key (org, team, jersey_number)
  - Identity fallback (org, team, name, dob)
- ✅ **FK Resolution** (organization and team lookups)
- ✅ **Enum Parsing** (PlayerRole, DominantFoot, DominantArm)
- ✅ **Cardinality** (correct entity counts)
- ✅ **Foreign key integrity**
- ✅ **No duplicates**
- ✅ **Natural key uniqueness**
- ✅ **Port validation**
- ✅ **Minor player guardian info**

CORS tests verify:

- ✅ **Preflight OPTIONS** requests
- ✅ **Access-Control-Allow-Origin** header
- ✅ **Access-Control-Allow-Credentials** header
- ✅ **Access-Control-Allow-Methods** header
- ✅ **Unauthorized origin blocking**
- ✅ **Multiple allowed origins**
- ✅ **Security headers coexistence**

### Manual Verification

```bash
# Start services
make up

# Run migration + seed
make migrate seed-minimal

# Verify database
make db-shell

# Inside PostgreSQL
\dt                                    -- List tables
SELECT COUNT(*) FROM organizations;    -- Should be 1
SELECT COUNT(*) FROM players;          -- Should be 2
SELECT * FROM players;                 -- View data
\q
```

---

## 🔄 CI/CD Integration

### GitHub Actions

File: `.github/workflows/ci-seeds.yml`

```yaml
name: CI - Seeds

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-seeds:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: changeme
          POSTGRES_DB: football_club_platform
        ports:
          - 5434:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt

      - name: Run migrations
        run: |
          cd backend
          alembic upgrade head

      - name: Seed database (minimal)
        env:
          DATASET: minimal
          DATABASE_URL: postgresql://app:changeme@localhost:5434/football_club_platform
        run: |
          cd backend
          python -m seeds.runner

      - name: Run seed tests
        run: |
          cd backend
          pytest tests/test_seeds.py -v
```

### Deployment Pipeline

```bash
# 1. Build
docker-compose build

# 2. Migrate
make migrate

# 3. Seed (environment-specific)
if [ "$ENV" = "staging" ]; then
  make seed-staging
elif [ "$ENV" = "production" ]; then
  # Optionally seed production (with safety checks)
  SEED_ALLOW_PROD=true make seed-minimal
fi
```

---

## 🛠️ Troubleshooting

### Port Conflicts

**Problem**: Port 3001 already in use

**Solution**:
```bash
# Verify pythonpro is using 3001
netstat -ano | findstr :3001  # Windows
lsof -i :3001                # Unix

# Ensure FCP uses different ports
echo "FCP_WEB_PORT=3000" >> .env
make check-ports
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'seeds'`

**Solution**:
```bash
# Ensure backend is in PYTHONPATH
cd backend
python -m seeds.runner  # Use module syntax

# OR
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
python seeds/runner.py
```

### FK Violations

**Problem**: `ForeignKeyViolationError`

**Solution**:
- Check YAML dataset for correct references
- Verify migration order
- Reset and reseed:

```bash
make reseed-minimal
```

### Duplicate Keys

**Problem**: `UniqueViolationError`

**Solution**:
- Check YAML for duplicate slugs/names
- Natural keys must be unique within dataset
- Fix YAML and re-run (upsert will handle existing records)

### Production Seed Blocked

**Problem**: `❌ BLOCKED: Demo Seed in Production`

**Solution**:
```bash
# Only if intentional (NOT recommended)
SEED_ALLOW_PROD=true DATASET=minimal make seed
```

---

## 📚 References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLModel Guide](https://sqlmodel.tiangolo.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Project README](./README.md)

---

## 🤝 Contributing

When adding new entities:

1. **Create model** in `backend/app/models/`
2. **Add to dependencies** graph
3. **Create seed step** in `backend/seeds/steps/XX_entity.py`
4. **Update datasets** with sample data
5. **Add tests** in `tests/test_seeds.py`
6. **Update this guide**

Example: Adding "Coaches"

```python
# backend/seeds/steps/06_coaches.py
def seed(session, data):
    stats = {"create": 0, "update": 0, "skip": 0}

    for item in data:
        org = get_or_fail(session, Organization, slug=item.pop("organization_slug"))
        keys = {"organization_id": org.id, "email": item["email"]}
        defaults = {k: v for k, v in item.items() if k != "email"}

        _, op = upsert(session, Coach, keys=keys, defaults=defaults)
        stats[op] += 1

    return {"Coaches": stats}
```

---

**Version**: 1.0.0
**Last Updated**: 2025-11-05
**Maintainer**: Football Club Platform Team
