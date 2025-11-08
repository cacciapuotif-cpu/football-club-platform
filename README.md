# Football Club Platform ⚽

**Gestionale innovativo, semplice e production-ready per società di calcio dilettantistiche, settori giovanili e Serie C.**

Sistema completo per monitoraggio atleti, analisi video, ML predittivo, piani personalizzati e reportistica automatica - ottimizzato per **Docker Desktop** e funzionante su CPU (GPU opzionale).

**Colori brand**: Blu (#2563eb) e Giallo Ocra (#eab308)

---

## 🎯 Caratteristiche Principali

- **Multi-Tenant** con isolamento dati completo e RBAC granulare
- **Mobile-First UI** semplice e rapida per inserimento dati
- **6 Aree di Miglioramento**: Tecnico, Tattico/Cognitivo, Fisico, Psicologico/Mentale, Lifestyle/Recupero, Medico/Prevenzione
- **Pipeline Video** con tracking automatico, heatmap, eventi e clip generator
- **Sensori GPS/IMU/BLE** via REST, webhook e import CSV
- **ML Predittivo** con explainability operativa, calibrazione e drift monitoring
- **Report PDF** automatici (atleta, squadra, staff weekly) con cover professionali
- **Benchmark Anonimo** role/age per confronto multi-club (opt-in)
- **GDPR Compliant** con consensi, audit log, export e pseudonimizzazione

### ⚡ NEW: Player Progress Tracking (EAV Architecture)

- **Flexible Metrics**: EAV (Entity-Attribute-Value) structure for wellness, training, and match metrics
- **Time-series Analysis**: Day/week/month aggregations with trend detection
- **ACWR Monitoring**: Acute:Chronic Workload Ratio with injury risk alerts
- **ML Risk Prediction**: Baseline injury prediction with SHAP-like feature explanations
- **Data Quality**: Automated validation, outlier detection, and completeness tracking
- **Progress API**: RESTful endpoints for player overview, training load, and performance trends

**Key Endpoints**:
- `GET /api/v1/players/{id}/progress` - Time-series metrics with flexible bucketing
- `GET /api/v1/players/{id}/training-load` - sRPE & ACWR calculation
- `GET /api/v1/players/{id}/overview` - KPIs with data completeness
- `POST /api/v1/progress-ml/players/{id}/predict-risk` - Injury risk with recommendations

📖 **Documentation**: See [`API_USAGE.md`](backend/API_USAGE.md) and [`SEEDING_GUIDE.md`](backend/SEEDING_GUIDE.md)

---

## 📋 Prerequisiti

### Docker Desktop (OBBLIGATORIO)

Questa piattaforma è progettata per girare su **Docker Desktop** per Windows, macOS e Linux.

#### Windows
1. Installa **Docker Desktop for Windows** da [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Abilita WSL2 backend**:
   - Settings → General → "Use the WSL 2 based engine" ✓
3. **Configura risorse** (Settings → Resources):
   - CPU: **minimo 4 vCPU** (consigliato 6+)
   - Memory: **minimo 6 GB** (consigliato 8-12 GB)
   - Disk: **minimo 20 GB** disponibili
   - Swap: 2 GB

#### macOS
1. Installa **Docker Desktop for Mac** da [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Configura risorse** (Settings → Resources):
   - CPU: **minimo 4 CPU** (consigliato 6+)
   - Memory: **minimo 6 GB** (consigliato 8-12 GB)
   - Disk: **minimo 20 GB**

#### Linux
1. Installa **Docker Desktop for Linux** o Docker Engine + Docker Compose v2
2. Minimo 4 CPU, 6 GB RAM, 20 GB disco

#### GPU (Opzionale - Windows WSL2)
Se hai una GPU NVIDIA:
1. Installa [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) su WSL2
2. Verifica: `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`
3. Nel file `.env` imposta: `ENABLE_GPU=true`

---

## 🚀 Quickstart DEV (3 Step)

### STEP 1 — Infra (DB + MLflow)

```bash
# Crea file .env
cp .env.example .env

# Avvia database e MLflow
docker compose pull
docker compose up -d db mlflow
```

### STEP 2 — Backend (migrate + seed DEMO_10×10 + API)

**PowerShell (Windows):**
```powershell
# Installa dipendenze
poetry install

# Imposta profilo seed
$env:SEED_PROFILE="DEMO_10x10"
# O persistente: setx SEED_PROFILE "DEMO_10x10"

# Esegui migrazioni
poetry run alembic -c backend/alembic.ini upgrade head

# Carica dati DEMO_10x10 (10 giocatori × 10+ sessioni + predictions + prescriptions)
poetry run python backend/seeds/seed_all.py

# Avvia API
poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Bash/Unix:**
```bash
# Installa dipendenze
poetry install

# Imposta profilo seed
export SEED_PROFILE=DEMO_10x10

# Esegui migrazioni
poetry run alembic -c backend/alembic.ini upgrade head

# Carica dati DEMO_10x10
poetry run python backend/seeds/seed_all.py

# Avvia API
poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### STEP 3 — Frontend (dev su porta 3000)

```bash
cd frontend
npm install
npm run dev -- -p 3000
```

### ✅ Verifica DEMO_10x10

**PowerShell:**
```powershell
.\scripts\verify_demo_10x10.ps1
```

**Bash:**
```bash
./scripts/verify_demo_10x10.sh
```

### Accesso

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Health**: [http://localhost:8000/healthz](http://localhost:8000/healthz)
- **Backend Readyz**: [http://localhost:8000/readyz](http://localhost:8000/readyz)
- **MLflow UI**: [http://localhost:5000](http://localhost:5000)

---

## 🏭 Quickstart PROD (Compose)

### Avvio Produzione

```bash
# Build immagini
docker compose -f docker-compose.prod.yml build

# Avvia tutto (DB, Redis, MinIO, MLflow, OTEL, Prometheus, Grafana, Backend, Frontend, NGINX)
docker compose -f docker-compose.prod.yml up -d

# Verifica health
curl -sf http://localhost/api/healthz
curl -sf http://localhost/api/readyz
```

### k6 Smoke Test (Verifica DEMO_10x10)

**Bash:**
```bash
BASE_URL="http://localhost/api/v1" \
HEALTH_URL="http://localhost/api/healthz" \
READY_URL="http://localhost/api/readyz" \
./tests/k6/run_smoke.sh
```

**PowerShell:**
```powershell
.\tests\k6\run_smoke.ps1 -BaseUrl "http://localhost/api/v1"
```

### Accesso Produzione

- **Frontend (via NGINX)**: [http://localhost](http://localhost)
- **Backend API (via NGINX)**: [http://localhost/api](http://localhost/api)
- **Grafana**: [http://localhost:3003](http://localhost:3003) (admin/admin)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **MinIO Console**: [http://localhost:9001](http://localhost:9001)

### Cleanup

```bash
# Dev
docker compose down

# Prod
docker compose -f docker-compose.prod.yml down

# Volumi (ATTENZIONE: perdita dati)
docker volume rm fcp_pgdata fcp_mlruns || true
docker container prune -f && docker volume prune -f && docker network prune -f
```

---

## 📦 Comandi Makefile

```bash
make help              # Mostra tutti i comandi disponibili

# Servizi
make up                # Avvia servizi (dev)
make down              # Ferma servizi
make restart           # Riavvia servizi
make logs              # Mostra logs
make ps                # Stato containers

# Database
make migrate           # Esegui migrazioni
make seed              # Carica dati demo (legacy)
make db-backup         # Backup database
make db-restore FILE=backup.sql  # Restore

# Progress Tracking (NEW)
python backend/scripts/seed_demo_data.py  # Seed EAV progress data (90 days, 25 players)

# Sviluppo
make test              # Test backend
make fmt               # Formatta codice
make lint              # Linting
make shell-backend     # Shell container backend

# ML
make ml-train          # Addestra modelli
make ml-health         # Controlla stato modelli

# Utilities
make health            # Check salute servizi
make clean             # Rimuovi volumi
make reset             # Reset completo
```

---

## 🏗️ Architettura

```
┌─────────────────────────────────────────────────┐
│          FRONTEND (Next.js + React)             │
│  Dashboard • Players • Match • Planner • UI     │
└────────────────┬────────────────────────────────┘
                 │ REST API (JWT)
┌────────────────▼────────────────────────────────┐
│            BACKEND (FastAPI)                    │
│  ┌────────┬────────┬────────┬────────────────┐ │
│  │Routers │Services│   ML   │Report Generator│ │
│  └────────┴────────┴────────┴────────────────┘ │
└──┬──────┬──────┬──────────┬──────────────────┘
   │      │      │          │
   ▼      ▼      ▼          ▼
┌────┐ ┌─────┐ ┌──────┐ ┌────────┐
│ DB │ │Redis│ │Worker│ │Storage │
│(PG)│ │     │ │ (RQ) │ │(FS/S3) │
└────┘ └─────┘ └──────┘ └────────┘
```

**Stack:**
- Backend: Python 3.11, FastAPI, SQLModel, Pydantic v2
- DB: PostgreSQL 16 + RLS (Row Level Security) + Alembic
- Cache/Queue: Redis + RQ worker
- Storage: S3-compatible (MinIO/AWS S3)
- ML: LightGBM/XGBoost + SHAP + MLflow
- Video: FFmpeg + OpenCV + MediaPipe → HLS streaming
- Report: WeasyPrint + Matplotlib
- Observability: OpenTelemetry + Prometheus + Grafana + Tempo
- Frontend: Next.js 14 + Tailwind + shadcn/ui

---

## 🏢 Production-Ready Features

### 🔒 Multi-Tenant Row Level Security (RLS)

**Isolamento dati a livello database** con Postgres RLS:
- Policy automatiche su tutte le tabelle tenant-scoped
- `SET app.tenant_id` per ogni richiesta autenticata
- Zero leak cross-tenant garantito
- Test automatici di isolamento: `make bench-rls-test`

```sql
-- Esempio policy RLS
CREATE POLICY tenant_isolation ON players
  USING (organization_id = current_setting('app.tenant_id')::uuid);
```

### ☁️ S3 Storage By Default

**Storage file/video production-ready**:
- **Development**: MinIO locale (S3-compatible)
- **Production**: AWS S3, Google Cloud Storage, Azure Blob
- Presigned URLs con scadenza
- Retry automatico con backoff esponenziale
- Configurazione: `STORAGE_BACKEND=s3` in `.env`

```bash
# MinIO locale (dev)
S3_ENDPOINT_URL=http://minio:9000
S3_BUCKET=football-media

# AWS S3 (prod)
S3_ENDPOINT_URL=https://s3.eu-south-1.amazonaws.com
S3_BUCKET=football_club_platform-prod
```

### 🎬 HLS Video Pipeline Scalabile

**Streaming video ottimizzato**:
- Transcode H.264 → segmenti HLS (6-10s)
- Upload parallelo segmenti + playlist su S3
- Job chunked con RQ per parallelizzazione
- Idempotenza e resume su fallimenti
- Metriche per step (fps, durata, throughput)

```bash
# Processing automatico
POST /api/v1/video/upload → HLS segments → S3
GET  /api/v1/video/{id}/playlist.m3u8
```

### 📊 Observability Stack Completo

**Monitoring e troubleshooting**:
- **OpenTelemetry**: traces distribuiti FastAPI + SQLAlchemy + Redis
- **Prometheus**: metriche custom + default
- **Grafana**: dashboard API latency p50/p95/p99, error rate, queue lag
- **Tempo**: distributed tracing storage
- **Sentry**: error tracking e alerting

Dashboard key:
- API Overview: http://localhost:3001
- Prometheus: http://localhost:9090
- Tempo traces: integrato in Grafana

### 🤖 ML Production-Grade

**MLflow + Data Quality + Canary Deployment**:
- **MLflow**: experiment tracking + model registry
- **Feature Store**: tabella features con timestamp
- **Great Expectations**: data quality checks su train/inference
- **Canary Deployment**: 10% traffico su nuovo modello
- **Rollback automatico**: se degradazione metrica > soglia
- **SHAP caching**: risultati explainability cachati

```bash
# MLflow UI
http://localhost:5000

# Model registry
POST /api/v1/ml/register
GET  /api/v1/ml/models/production
```

### 🛡️ Security Hardening

**Produzione-grade security**:
- **2FA TOTP**: per OWNER/ADMIN
- **JWT Refresh Tokens**: rotazione e revoca server-side
- **Rate Limiting**: 60 req/min (configurabile)
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **CORS**: domini espliciti (no wildcard)
- **Upload Whitelist**: MIME type + estensione + size limit
- **ClamAV**: antivirus opzionale su upload

### 🔐 GDPR Operativo

**Conformità privacy**:
- Export dati completo (Article 15 - Right of Access)
- Pseudonimizzazione PII (Right to Erasure)
- Flusso minori con tutore e consenso
- Audit log 7 anni retention
- Bozza DPA (Data Processing Agreement) in `docs/ACC_DPA.md`

```bash
# Export dati utente
GET /api/v1/gdpr/export/{user_id}

# Anonimizzazione
POST /api/v1/gdpr/anonymize/{user_id}
```

### 🚀 CI/CD & Supply Chain Security

**GitHub Actions pipeline**:
- Lint (black, ruff, isort, mypy)
- Test (unit + integration) con coverage >80%
- Build immagini multi-arch
- **SBOM** generation (syft)
- **Vulnerability scan** (grype, trivy)
- **Image signing** (cosign)
- Migrations safe (dry-run + backup)
- Deploy automatico su main

```bash
# Pre-commit hooks locali
cd backend && pre-commit install
make pre-commit
```

### ⚠️ Limitazioni Demo

**Questa versione include**:
- Storage locale/MinIO (no S3 reale configurato)
- Dati seed demo (disabilitare con `SEED_DEMO=false`)
- Certificati self-signed (usare Let's Encrypt in prod)
- SMTP mock (configurare server reale)
- Backup manuali (automatizzare con cron)
- Single-node deployment (scalare con Kubernetes)

---

## 📊 Funzionalità Dettagliate

### 1. Acquisizione Dati

#### A. Inserimento Manuale (Mobile-First)
- **Wizard onboarding** atleta (4 step)
- **Quick add** post-sessione: sRPE, minuti, umore, sonno
- Form responsive con validazioni inline

#### B. Import CSV Sensori
```bash
curl -O http://localhost:8000/api/v1/sensors/template
curl -X POST http://localhost:8000/api/v1/sensors/import \
  -H "Authorization: Bearer <token>" \
  -F "file=@session.csv"
```

#### C. Webhook Sensori
```bash
POST /api/v1/sensors/webhook
{
  "player_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2025-01-15T10:30:00Z",
  "metrics": {
    "distance_m": 5430,
    "hr_avg": 165,
    "sprints": 12
  }
}
```

### 2. Pipeline Video

#### Upload
```bash
curl -X POST http://localhost:8000/api/v1/video/upload \
  -F "file=@match.mp4" \
  -F "match_id=<uuid>"
```

#### Processing Automatico
1. Transcode H.264
2. Keyframes ogni N sec
3. Pose tracking (MediaPipe/YOLO)
4. Event detection (tiro, passaggio)
5. Heatmap coordinate normalizzate
6. Timeline eventi

#### Clip Generator
```bash
POST /api/v1/video/{id}/clip
{"timestamp_sec":450,"duration_before":8,"duration_after":8}
```

### 3. Piani Personalizzati

```bash
POST /api/v1/plans/generate
{
  "player_id": "uuid",
  "week_start": "2025-01-20",
  "target_areas": ["Fisico", "Tecnico"]
}
```

Motore: Regole + ML → micro-obiettivi SMART settimanali

### 4. ML Predittivo & Explainability

#### Predizione Performance
```bash
GET /api/v1/ml/predict?player_id=<uuid>
```

Response:
```json
{
  "expected_performance": 72.3,
  "confidence_band": [68.1, 76.5],
  "threshold": "neutro",
  "overload_risk": {
    "level": "low",
    "probability": 0.12
  }
}
```

**Soglie**:
- `<45`: Attenzione
- `45–70`: Neutro
- `>70`: In crescita

#### Explainability (SHAP)
```bash
GET /api/v1/ml/explain?player_id=<uuid>
```

Response con global/local importances + testo naturale.

#### Model Health
```bash
GET /api/v1/ml/health
```

Monitoraggio drift (PSI), degradazione performance, status OK/WARN/ALERT.

### 5. Report PDF Automatici

#### Report Atleta
```bash
GET /api/v1/reports/player/{id}?range=last_4_weeks&format=pdf
```

**Contenuto** (8-12 pagine):
1. Cover A4 professionale
2. KPI chiave + performance attesa
3. Trend carichi 4 settimane
4. Wellness & recupero
5. KPI tecnici ultimi match
6. Heatmap posizionamento
7. Piano settimanale + aderenza
8. Explainability waterfall
9. Benchmark role/age (opt-in)
10. Note staff

#### Report Squadra
```bash
GET /api/v1/reports/team/{id}?range=last_week
```

Semaforo rischio, distribuzioni carichi, KPI collettivi.

#### Weekly Staff Brief (Automatico)
Cron lunedì 08:00:
- 5 Takeaway
- 3 Alert
- Calendario micro-cycles
- Appendici KPI/trend

### 6. Benchmark Anonimo

Opt-in multi-club:
```bash
GET /api/v1/benchmark/role-age?role=MF&age_group=U17
```

P25/P50/P75 per ruolo e età. Privacy: aggregati anonimi min 10 sample.

---

## 🔐 Sicurezza & GDPR

### Multi-Tenancy & RBAC
**Ruoli**: OWNER, ADMIN, COACH, ANALYST, PHYSIO, DOCTOR, PLAYER, PARENT

### Consensi & Minori
- Consenso GDPR obbligatorio
- Minori: campo tutore
- Ruolo PARENT readonly figli

### Audit Log
Ogni accesso dati sensibili loggato (retention 7 anni).

### Export & Portabilità
```bash
GET /api/v1/privacy/export/{player_id}
```

ZIP con JSON + PDF pseudonimizzati.

### Sicurezza
- Rate limiting 60 req/min
- Security headers (HSTS, CSP)
- Upload max 500MB
- Bcrypt password hashing

---

## 🛠️ Operazioni

### Backup Database
```bash
make db-backup
# → ./backups/football_dev_2025-01-15_103000.sql.gz
```

### Restore
```bash
make db-restore FILE=./backups/backup.sql.gz
```

### Migrazioni
```bash
make migration MSG="add wellness table"
make migrate
make downgrade
```

### Training ML
```bash
make ml-train  # Manuale
# Schedulato: lunedì 03:00
```

### Logs & Debug
```bash
make logs
make logs-backend
make shell-backend
make health
make ml-health
```

---

## 🤖 Analytics & ML Setup

### Overview

Il sistema include una pipeline completa di **ML Analytics** per analisi avanzate dei giocatori con:
- **2 modelli sklearn**: LogisticRegression (injury risk) + LinearRegression (performance)
- **6 nuove tabelle**: matches, training_sessions, player_match_stats, player_training_load, player_features_daily, player_predictions
- **4 nuovi endpoint** REST API per summary, predictions, retrain, ingest
- **3 componenti React**: PlayerRadar, PlayerTrend, SquadTable (con recharts)

### Setup Rapido

```bash
# 1. Esegui migrazione Alembic (crea le 6 tabelle analytics)
cd backend
alembic upgrade head

# 2. Popola dati sintetici + train modelli + genera predictions
python scripts/seed_ml_analytics.py
```

**Output atteso:**
```
Found 24 players...
Created 17 matches
Created 68 training sessions
Created 408 player match stats
Created 1632 training load records
Created 2928 daily feature records
Training result: {'injury_auc': 0.82, 'perf_r2': 0.65, 'model_version': '1.0.0'}
Generated 48 predictions
```

### Endpoint API

#### 1. Player ML Summary
```bash
GET /api/v1/advanced-analytics/ml/player/{player_id}/summary
```
Response:
```json
{
  "player_id": "uuid",
  "last_10_matches": 10,
  "avg_xg": 0.35,
  "avg_key_passes": 2.4,
  "avg_duels_won": 5.2,
  "trend_form_last_10": 0.08
}
```

#### 2. Player Predictions
```bash
GET /api/v1/advanced-analytics/ml/player/{player_id}/predictions
```
Genera e ritorna predizioni **injury_risk** (proba) e **performance_index** (valore stimato).

#### 3. Retrain Models
```bash
POST /api/v1/advanced-analytics/ml/retrain
```
Riaddestra i 2 modelli sklearn su dati correnti. Ritorna metriche AUC e R².

#### 4. Ingest Data
```bash
POST /api/v1/advanced-analytics/ml/ingest
```
Placeholder per future ingestion CSV/JSON (match stats, training load).

### Componenti React

I componenti sono in `frontend/components/analytics/`:

#### PlayerRadar
Radar chart con 4 metriche: xG, Key Passes, Duels Won, Form Trend.
```tsx
import PlayerRadar from "@/components/analytics/PlayerRadar";

<PlayerRadar playerId="uuid" apiUrl="http://localhost:8000" />
```

#### PlayerTrend
Line chart con trend xG e Key Passes ultimi 10 match.
```tsx
import PlayerTrend from "@/components/analytics/PlayerTrend";

<PlayerTrend playerId="uuid" />
```

#### SquadTable
Tabella comparativa squadra (primi 20 giocatori per performance).
```tsx
import SquadTable from "@/components/analytics/SquadTable";

<SquadTable />
```

**Nota**: Installa `recharts` se mancante:
```bash
cd frontend
npm install recharts
```

### Modelli ML

I modelli sklearn vengono salvati in `backend/ml/models/`:
- `injury_risk_logreg.joblib`: LogisticRegression per rischio infortunio
- `performance_linreg.joblib`: LinearRegression per performance index

**Features injury model**:
- `load_acute`, `load_chronic`, `monotony`, `strain`

**Features performance model**:
- `rolling_7d_load`, `rolling_21d_load`

### Tabelle Database

| Tabella | Descrizione |
|---------|-------------|
| `matches` | Partite con date, avversari, competizione |
| `training_sessions` | Sedute di allenamento con tipo, durata, RPE |
| `player_match_stats` | Stats giocatore per match (xG, key passes, duels, sprints, etc.) |
| `player_training_load` | Carichi allenamento (acute, chronic, ACWR, monotony, strain) |
| `player_features_daily` | Features giornaliere per ML (rolling loads, form score) |
| `player_predictions` | Predizioni salvate (injury_risk, performance_index) |

### Test Manuale

```bash
# 1. Avvia backend (porta 8000 libera)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Test endpoint
curl http://localhost:8000/api/v1/advanced-analytics/ml/player/{player_id}/summary
curl http://localhost:8000/api/v1/advanced-analytics/ml/player/{player_id}/predictions
curl -X POST http://localhost:8000/api/v1/advanced-analytics/ml/retrain

# 3. Frontend: importa componenti in una pagina player detail
```

### Note Importanti

- **NON usare porte 3000/3001**: Il backend di default è su 8000. Per test su altra porta: `PORT=8012 uvicorn app.main:app`
- **UUID vs Integer**: Il progetto usa UUID per player_id, non integer come negli esempi generici
- **Async/SQLModel**: Tutti i servizi ML usano async SQLAlchemy + SQLModel
- **Multi-tenancy**: Tutte le tabelle includono `organization_id` per isolamento tenant

---

## 📊 Player Dashboard

### Overview

La **Player Dashboard** è una dashboard completa e interattiva per il monitoraggio delle performance dei giocatori, con 5 tab dedicate a diverse aree di analisi:

1. **Overview**: KPI principali, Readiness Index, Alert recenti, e completezza dati
2. **Wellness**: Time-series delle metriche di benessere con selezione multi-metrica
3. **Allenamento**: Carichi di allenamento, ACWR, Monotony, e Strain
4. **Partite**: Aggregati e trend delle metriche di match
5. **Tattico**: Visualizzazione delle metriche tattiche (pressures, recoveries, progressive passes, etc.)

### Accesso

La dashboard è accessibile dalla lista giocatori:
- Naviga su **Giocatori** → clicca **Dashboard** per un giocatore
- URL: `http://localhost:3000/players/{player_id}/dashboard`

### Funzionalità

#### Filtri Persistenti

Tutti i filtri sono sincronizzati con l'URL (querystring) per permettere:
- Condivisione di link con filtri pre-impostati
- Navigazione browser (back/forward) con stato preservato
- Refresh pagina senza perdere le selezioni

**Filtri disponibili**:
- **Date Range**: `date_from` e `date_to` (default: ultimi 90 giorni)
- **Raggruppamento**: `grouping` (day/week/month, default: week)
- **Tab attiva**: `tab` (overview/wellness/allenamento/partite/tattico)

#### Tab Overview

**KPI Cards**:
- **Readiness**: Ultimo valore e media 7 giorni (0-100, baseline 50)
- **ACWR**: Ultimo valore Acute:Chronic Workload Ratio
- **Carico 7d**: sRPE totale ultimi 7 giorni
- **Monotony**: Valore settimana corrente
- **Strain**: Valore settimana corrente

**Alert Banner**:
- Mostra gli ultimi 5 alert degli ultimi 7 giorni
- Tipi di alert: `risk_load`, `risk_fatigue`, `risk_outlier`
- Severità: `warning` (giallo) o `error` (rosso)

**Readiness Index Chart**:
- Line chart con serie temporale del Readiness Index
- Linea di riferimento a 50 (baseline)
- Tooltip interattivo con valori precisi

**Completezza Dati**:
- Percentuale di completezza per famiglia (wellness, training, match)
- Giorni con dati vs giorni totali nel periodo

#### Tab Wellness

**Selezione Metriche**:
- Toggle multi-select per mostrare/nascondere metriche
- Metriche disponibili:
  - Ore Sonno, Qualità Sonno
  - Fatica, Indolenzimento, Stress
  - Umore, Motivazione
  - FC Riposo, HRV

**Time-Series Chart**:
- Line chart interattivo con tutte le metriche selezionate
- Legenda cliccabile per mostrare/nascondere singole metriche
- Tooltip con valori precisi per ogni punto
- Formattazione date in italiano

#### Tab Allenamento

**ACWR Chart**:
- Area chart con ACWR (Acute:Chronic Workload Ratio)
- Linee di riferimento a 0.8 (min) e 1.5 (max)
- Range ideale evidenziato visivamente

**Monotony & Strain**:
- Bar chart settimanale per Monotony
- Bar chart settimanale per Strain
- Side-by-side per confronto rapido

**Training Metrics Chart**:
- Line chart con metriche selezionate (RPE, Distanza, HSR, Sprint, FC Media)
- Selezione multi-metrica con toggle

#### Tab Partite

**Aggregati Periodo**:
- Cards con statistiche aggregate:
  - Partite totali
  - Minuti medi
  - Precisione passaggi media
  - Passaggi totali
  - Duel vinti totali
  - Tocchi totali

**Trend Metriche**:
- Line chart con trend delle metriche di match selezionate
- Metriche disponibili: Precisione Passaggi, Passaggi Completati, Duel Vinti, Tocchi, Tiri in Porta

**Tabella Dettaglio Partite**:
- Tabella completa con tutte le partite del periodo
- Colonne: Data, Avversario (🏠/✈️), Minuti, Passaggi (completati + %), Duel, Tocchi

#### Tab Tattico

**Metriche Tattiche**:
- Line chart con metriche tattiche:
  - Pressures
  - Recoveries Defensive Third
  - Progressive Passes
  - xThreat Contribution
- Placeholder per future metriche avanzate

### Export CSV

**Funzionalità**:
- Bottone **Export CSV** nella barra filtri
- Esporta i dati della tab corrente:
  - **Wellness**: Serie time-series con tutte le metriche
  - **Allenamento**: Serie sRPE e ACWR
  - **Partite**: Dettaglio completo partite

**Formato**:
- File CSV con header
- Nome file: `{tab}_{player_id}_{date_from}_{date_to}.csv`
- Encoding UTF-8

### Screenshots

#### Overview Tab
```
┌─────────────────────────────────────────────────┐
│  [Readiness: 72.3] [ACWR: 1.12] [Carico 7d: 450] │
│  [Monotony: 2.1] [Strain: 980]                  │
├─────────────────────────────────────────────────┤
│  ⚠️ Alert Recenti                               │
│  • risk_load: acwr > 1.5 (2025-01-15)          │
├─────────────────────────────────────────────────┤
│  Readiness Index Chart                          │
│  [Line chart con trend 0-100]                   │
├─────────────────────────────────────────────────┤
│  Completezza Dati                               │
│  Wellness: 85% | Training: 90% | Match: 75%   │
└─────────────────────────────────────────────────┘
```

#### Wellness Tab
```
┌─────────────────────────────────────────────────┐
│  ☑ Qualità Sonno ☑ Fatica ☑ Umore ☐ Stress   │
├─────────────────────────────────────────────────┤
│  Trend Wellness                                 │
│  [Line chart multi-metrica interattivo]         │
└─────────────────────────────────────────────────┘
```

#### Allenamento Tab
```
┌─────────────────────────────────────────────────┐
│  ACWR Chart                                     │
│  [Area chart con linee 0.8/1.5]                 │
├─────────────────────────────────────────────────┤
│  [Monotony Bar] [Strain Bar]                    │
├─────────────────────────────────────────────────┤
│  Training Metrics                               │
│  [Line chart RPE, Distanza, HSR, etc.]          │
└─────────────────────────────────────────────────┘
```

### API Endpoints Utilizzati

La dashboard utilizza i seguenti endpoint backend:

- `GET /api/v1/players/{id}/overview` - KPI e completezza dati
- `GET /api/v1/players/{id}/progress` - Time-series metriche per famiglia
- `GET /api/v1/players/{id}/training-load` - sRPE, ACWR, Monotony, Strain
- `GET /api/v1/players/{id}/match-summary` - Aggregati partite
- `GET /api/v1/players/{id}/readiness` - Readiness Index serie
- `GET /api/v1/players/{id}/alerts` - Alert recenti

### Istruzioni d'Uso

1. **Accedi alla Dashboard**:
   - Vai su **Giocatori** → clicca **Dashboard** per un giocatore

2. **Naviga tra le Tab**:
   - Clicca su Overview, Wellness, Allenamento, Partite, o Tattico

3. **Modifica Filtri**:
   - Cambia date, raggruppamento, o seleziona metriche
   - I filtri si aggiornano automaticamente nell'URL

4. **Interagisci con i Grafici**:
   - Hover per vedere valori precisi
   - Clicca sulla legenda per mostrare/nascondere metriche
   - Zoom e pan (se abilitato)

5. **Esporta Dati**:
   - Clicca **Export CSV** per scaricare i dati della tab corrente

6. **Monitora Alert**:
   - Controlla il banner alert nella tab Overview
   - Alert automatici per ACWR fuori range, Readiness bassa, outlier

### Note Tecniche

- **Librerie**: Recharts per grafici, Radix UI per tabs
- **State Management**: React hooks con URL sync
- **Responsive**: Mobile-first design con breakpoints Tailwind
- **Performance**: Lazy loading dati per tab, memoization grafici
- **Accessibilità**: ARIA labels, keyboard navigation, focus management

---

## 🧪 Testing

```bash
make test
# Coverage >80%
```

Test inclusi:
- `test_auth.py`: JWT, RBAC
- `test_plans.py`: generazione piani
- `test_ml.py`: predict, explain, drift
- `test_sensors.py`: CSV parsing
- `test_reports.py`: PDF generation
- `test_video.py`: processing (mocked)

---

## 🚨 Troubleshooting

### Porte occupate
```bash
netstat -ano | findstr :8000  # Windows
lsof -ti:8000 | xargs kill    # macOS/Linux
```

### Volumi permessi (Linux)
```bash
sudo chown -R 1000:1000 ./data
```

### Database non raggiungibile
```bash
docker compose -f infra/docker-compose.yml exec db pg_isready -U app
```

### Worker non processa
```bash
make logs-worker
make shell-redis
> LLEN rq:queue:default
```

### Out of Memory
Aumenta RAM in Docker Desktop Settings → Resources.

Windows WSL2: crea `.wslconfig`:
```
[wsl2]
memory=8GB
processors=4
```

### GPU non rilevata
```bash
wsl -d Ubuntu
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## 📚 Documentazione Completa

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Diagrammi, stack, flussi
- **[API.md](docs/API.md)**: Reference endpoint
- **[ML.md](docs/ML.md)**: Features, modelli, calibrazione, drift
- **[GDPR.md](docs/GDPR.md)**: Conformità, consensi, audit
- **[OPERATIONS.md](docs/OPERATIONS.md)**: Deploy, monitoring, backup

---

## 🎨 UI/UX

### Mobile-First
- Breakpoints: 320px, 768px, 1024px, 1440px
- Touch targets: min 44×44px
- Offline-ready (service worker opzionale)

### Accessibilità
- WCAG AA contrasti
- Focus visibile
- ARIA labels
- Navigazione tastiera

### Quick Add
Form 30 secondi post-sessione: tap 1-5 per sRPE, umore, sonno.

---

## 🚀 Deploy Produzione

### Checklist
- [ ] Cambia `JWT_SECRET`, password in `.env`
- [ ] Abilita HTTPS (Traefik/Nginx + Let's Encrypt)
- [ ] Configura SMTP reale
- [ ] Backup automatici DB
- [ ] Sentry (`SENTRY_DSN`)
- [ ] Prometheus + Grafana
- [ ] `APP_ENV=production`, `DEBUG=false`
- [ ] Rate limiting API pubbliche
- [ ] Firewall: esponi 80/443, blocca 5432/6379

---

## 📄 Licenza

**Proprietaria** - © 2025 Football Club Platform.

---

**Buon lavoro!** ⚽🚀

Support: support@footballclubplatform.com
