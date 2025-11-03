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

## 🚀 Quick Start (1 Comando)

### Primo Avvio

```bash
# 1. Clona/estrai il progetto
cd football-club-platform

# 2. Crea file .env
cp .env.example .env

# 3. OPZIONALE: Modifica .env (JWT_SECRET, password, etc.)
# notepad .env       # Windows
# nano .env          # macOS/Linux

# 4. Inizializza tutto (build, migrate, seed)
make init
```

**Output atteso:**
```
✓ Initialization complete!
Backend API: http://localhost:8000/docs
Frontend:    http://localhost:3000
```

### Accesso

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Credenziali demo**:
  - Admin: `admin@club1.local` / `admin123`
  - Coach: `coach@club1.local` / `coach123`
  - Player: `player1@club1.local` / `player123`

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
make seed              # Carica dati demo
make db-backup         # Backup database
make db-restore FILE=backup.sql  # Restore

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
