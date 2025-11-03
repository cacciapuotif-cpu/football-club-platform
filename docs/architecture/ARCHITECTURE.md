# Football Club Platform - Architecture

**Architettura Semplice e Non Ridondante**

---

## Overview

Football Club Platform è un gestionale per società di calcio con architettura a microservizi leggera:

```
┌──────────────────────────────────────────────┐
│         FRONTEND (Next.js 14)                │
│  Mobile-First • Dashboard • Report UI        │
└────────────────┬─────────────────────────────┘
                 │ REST API (JWT)
┌────────────────▼─────────────────────────────┐
│         BACKEND (FastAPI + Python)           │
│  ┌─────────┬─────────┬─────────┬──────────┐ │
│  │Routers  │Services │   ML    │ Reports  │ │
│  └─────────┴─────────┴─────────┴──────────┘ │
└──┬───────┬──────┬──────────┬────────────────┘
   │       │      │          │
   ▼       ▼      ▼          ▼
┌────┐  ┌─────┐ ┌──────┐  ┌────────┐
│ DB │  │Redis│ │Worker│  │Storage │
│(PG)│  │     │ │ (RQ) │  │(FS/S3) │
└────┘  └─────┘ └──────┘  └────────┘
```

---

## Stack Tecnologico

### Backend
- **Framework**: FastAPI 0.109 (async, high-performance)
- **ORM**: SQLModel (Pydantic + SQLAlchemy)
- **DB**: PostgreSQL 15 (relazionale, ACID)
- **Migrazioni**: Alembic
- **Cache**: Redis 7
- **Queue**: RQ (Redis Queue) - per video processing, ML training

### Frontend
- **Framework**: Next.js 14 (React 18, App Router)
- **Styling**: Tailwind CSS 3 + shadcn/ui
- **State**: React hooks (no Redux per semplicità)
- **API Client**: Axios

### ML & Data
- **Models**: LightGBM, XGBoost (interpretabili, CPU-friendly)
- **Explainability**: SHAP / Feature Importances
- **Video**: FFmpeg + OpenCV + MediaPipe (pose tracking)
- **Report**: WeasyPrint (HTML→PDF) + Matplotlib

### Deployment
- **Runtime**: Docker Desktop (Windows/macOS/Linux)
- **Orchestrazione**: Docker Compose v2
- **Profiles**: `dev` (con frontend), `prod` (solo backend+worker)

---

## Database Schema (Semplificato)

### Core Entities

```
organizations (tenant)
├── users (auth + RBAC)
├── teams
│   └── players
│       ├── physical_tests
│       ├── technical_tests
│       ├── wellness_data
│       ├── injuries
│       └── training_plans
├── matches
│   └── attendances
├── training_sessions
├── videos
│   └── video_events
└── sensor_data
```

### ML & Reporting

```
ml_predictions (performance + risk)
ml_model_versions (versioning)
drift_metrics (monitoring)

reports
└── report_caches

benchmark_data (anonymous role/age)

audit_logs (GDPR compliance)
```

**Isolamento Multi-Tenant**: Ogni query filtrata automaticamente per `organization_id`.

---

## API Architecture

### REST Endpoints

**Base URL**: `http://localhost:8000/api/v1`

#### Authentication
- `POST /auth/signup` - Crea organizzazione + owner
- `POST /auth/login` - JWT access + refresh token
- `POST /auth/refresh` - Rinnova token
- `GET /auth/me` - Profilo utente corrente

#### Core Resources
- `/players`, `/teams`, `/matches`, `/sessions`
- CRUD standard con paginazione, filtri, sorting

#### Advanced Features
- `POST /sensors/import` - Import CSV sensori
- `POST /sensors/webhook` - Webhook real-time
- `POST /video/upload` - Upload video → async processing
- `GET /video/{id}/events` - Timeline eventi
- `POST /video/{id}/clip` - Genera clip

#### ML & Predictions
- `GET /ml/predict?player_id=<uuid>` - Performance + overload risk
- `GET /ml/explain?player_id=<uuid>` - SHAP explainability
- `GET /ml/health` - Drift + model health

#### Reports
- `GET /reports/player/{id}?range=last_4_weeks&format=pdf`
- `GET /reports/team/{id}?range=last_week&format=pdf`
- `GET /reports/staff-weekly` - Cron automatico

#### Benchmark
- `GET /benchmark/role-age?role=MF&age_group=U17` - Percentili anonimi

---

## ML Pipeline

### 1. Feature Engineering

**Features estratte** (16 totali):

- **Load** (5): ACWR, monotony, strain, avg_km, trend
- **Wellness** (5): HRV avg/trend, sleep, fatigue, stress
- **Performance** (1): sRPE avg
- **Injury** (3): count_6m, days_out, recurrence
- **Demographic** (2): age, role_encoded

### 2. Training

```python
# ml/train.py
- Carica dati ultimi 6 mesi
- Feature engineering
- Train/test split temporale (80/20)
- Train LightGBM (performance) + XGBoost (overload)
- Calibra probabilità (Isotonic Regression)
- Salva model + metrics
```

### 3. Prediction

```python
# ml/predict.py
- Estrae features da player_data
- Predict performance (0-100) + confidence band
- Predict overload risk (low/med/high) + prob
- Fallback a regole se model unavailable
```

### 4. Explainability

```python
# ml/predict.py::explain()
- Global: feature importances
- Local: contributi per predizione corrente
- Natural Language: testo italiano operativo
```

### 5. Drift Monitoring

```python
# ml/drift.py (TODO)
- PSI (Population Stability Index) per feature groups
- MAE degradation check
- Status: OK / WARN / ALERT
- Auto-retrain se drift > threshold
```

---

## Security & GDPR

### Authentication
- **JWT** (access 30min, refresh 7 giorni)
- **Password**: bcrypt, 12 rounds
- **RBAC**: 8 ruoli (Owner, Admin, Coach, Analyst, Physio, Doctor, Player, Parent)

### Multi-Tenancy
- Query filtrate per `organization_id` via middleware
- Isolamento STRICT

### Rate Limiting
- 60 req/min per IP (burst 100)
- Via `slowapi`

### GDPR
- **Consensi**: flag + timestamp obbligatori
- **Audit Log**: ogni accesso dati sensibili (retention 7 anni)
- **Export**: `/privacy/export/{player_id}` → ZIP pseudonimizzato
- **Retention**: 3 anni configurabile, anonimizzazione automatica

---

## Observability

### Health Checks
- `/healthz` - Liveness probe
- `/readyz` - Readiness (DB + Redis check)
- `/ml/health` - ML model health + drift

### Metrics
- `/metrics` - Prometheus format
- Custom: `http_requests_total`, `http_request_duration_seconds`

### Logging
- Structured JSON (via `structlog`)
- Levels: DEBUG, INFO, WARN, ERROR

---

## Deployment su Docker Desktop

### Risorse Minime
- **CPU**: 4 vCPU
- **RAM**: 6-8 GB
- **Disk**: 20+ GB

### Comandi

```bash
# Inizializza progetto
make init

# Start services
make up              # dev profile (frontend + backend + worker)
make up-prod         # prod profile (solo backend + worker)

# Database
make migrate         # Alembic migrations
make seed            # Carica dati demo

# Monitoring
make logs            # Tutti i logs
make logs-backend    # Solo backend
make health          # Health checks

# ML
make ml-train        # Training modelli
make ml-health       # Drift check

# Backup
make db-backup       # Backup DB
make db-restore FILE=backup.sql.gz

# Cleanup
make clean           # Rimuovi volumi
make reset           # Full reset (clean + init)
```

### GPU Support (Opzionale)

Windows WSL2 + NVIDIA:

```bash
# .env
ENABLE_GPU=true

# Verifica
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## Scalabilità

### Verticale
- Backend: aumenta workers Gunicorn (`WORKERS=8`)
- DB: aumenta pool (`DB_POOL_SIZE=50`)
- Redis: aumenta max connections

### Orizzontale
- **Backend**: multiple replicas dietro load balancer (Nginx/Traefik)
- **Worker**: multiple istanze RQ per code differenti
- **DB**: Read replicas per query heavy

### Cloud (Opzionale)
- Push images a registry (Docker Hub, GCR, ECR)
- Deploy su Cloud Run, ECS, Azure Container Instances
- DB gestito (RDS, Cloud SQL, Azure Database)
- Storage S3-compatible (AWS S3, GCS, Azure Blob)

---

## Differenziatori Chiave

1. **Ibrido Regole + ML**: fallback automatico, zero downtime
2. **Explainability Operativa**: testo italiano, non solo chart
3. **CPU-First**: funziona senza GPU, ottimizzato per low-cost
4. **Architettura Semplice**: no microservizi ridondanti, monolith modulare
5. **GDPR Native**: audit, consent, export, retention integrati
6. **Benchmark Anonimo**: opt-in multi-club per confronti role/age

---

## Prossimi Sviluppi

### Short-term
- [ ] Calibrazione automatica modelli (Platt + Isotonic)
- [ ] Drift monitoring completo con alert
- [ ] Frontend dashboard completa
- [ ] Router completi per tutti gli endpoint

### Medium-term
- [ ] Training automatico schedulato (cron)
- [ ] Video tracking YOLO-pose (alternativa a MediaPipe)
- [ ] Report cover A4 con template personalizzabili
- [ ] Integrazione Sentry per error tracking

### Long-term
- [ ] Mobile app (React Native)
- [ ] Integrazione wearables (Garmin, Apple Watch, Polar)
- [ ] Multi-language support (EN, ES, FR)
- [ ] Kubernetes Helm chart

---

**Architettura = Semplice, Efficace, Production-Ready** ✅
