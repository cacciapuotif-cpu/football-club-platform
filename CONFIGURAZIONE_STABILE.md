# ⚙️ Configurazione Stabile - Football Club Platform

**Data:** 2025-11-07
**Revisione:** Team di 3 Programmatori Fullstack
**Modalità:** Development (Opzione A)

---

## 🎯 Architettura Finale

### Backend (Docker)
- **Porta:** `8000`
- **Container:** `football_club_platform_backend`
- **Network:** `football_club_platform_network`
- **URL Base:** `http://localhost:8000`
- **API Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/healthz`

### Frontend (NPM Dev Mode)
- **Porta:** `3002`
- **Modalità:** Development (hot reload)
- **URL:** `http://localhost:3002`
- **Comando:** `cd frontend && npm run dev -- -p 3002`

### Database & Servizi
- **PostgreSQL:** `5432` (container: `football_club_platform_db`)
- **Redis:** `6379` (container: `football_club_platform_redis`)
- **MinIO:** `9000` (container: `football_club_platform_minio`)

---

## 📁 Pagine Frontend (6 pagine principali)

Tutte le pagine sono presenti e funzionanti:

1. ✅ **Home** - `/` - `frontend/app/page.tsx`
2. ✅ **Giocatori** - `/players` - `frontend/app/players/page.tsx`
3. ✅ **Sessioni** - `/sessions` - `frontend/app/sessions/page.tsx`
4. ✅ **Wellness** - `/wellness` - `frontend/app/wellness/page.tsx`
5. ✅ **Report** - `/report` - `frontend/app/report/page.tsx`
6. ✅ **ML Predittivo** - `/ml-predictive` - `frontend/app/ml-predictive/page.tsx`

### Navbar
File: `frontend/components/Navbar.tsx`

Contiene tutti i link alle 6 pagine principali in questo ordine:
- Home
- Giocatori
- Sessioni
- Wellness
- Report
- ML Predittivo

---

## 🚀 Come Avviare il Sistema

### 1. Avvio Backend (Docker)

```bash
# Dalla root del progetto
docker-compose -f docker-compose.prod.yml up -d db redis minio backend

# Oppure usando il Makefile (usa automaticamente docker-compose.prod.yml)
make up
```

**Verifica che sia avviato:**
```bash
curl http://localhost:8000/healthz
# Risposta attesa: {"status":"ok","service":"Football Club Platform API","version":"1.0.0"}
```

### 2. Avvio Frontend (Dev Mode)

```bash
# Dalla directory frontend
cd frontend
npm run dev -- -p 3002
```

**Oppure dalla root:**
```bash
cd frontend && npm run dev -- -p 3002
```

Il frontend sarà disponibile su: **http://localhost:3002**

### 3. (Opzionale) Seed Database

Se il database è vuoto, popolare con dati demo:

```bash
docker exec football_club_platform_backend python -m seeds.runner
```

---

## 🔧 Configurazioni Principali

### File `.env`
- **Backend URL:** `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- **CORS Origins:** `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000`
- **Database:** `DATABASE_URL=postgresql+asyncpg://app:changeme@db:5432/football_club_platform`

### File `frontend/next.config.js`
```javascript
env: {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'Football Club Platform',
}
```

### File `frontend/lib/api.ts`
```typescript
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
```

### File `Makefile`
Il Makefile usa automaticamente `docker-compose.prod.yml`:
```makefile
COMPOSE_FILE := docker-compose.prod.yml
COMPOSE := docker-compose -f $(COMPOSE_FILE)
```

---

## 📝 Pulizia Effettuata

### File Eliminati (obsoleti/temporanei)
- ❌ `TROUBLESHOOTING_ERR_EMPTY_RESPONSE.md`
- ❌ `SOLUZIONE_DEFINITIVA.md`
- ❌ `ANALISI_COMPLETA_SISTEMA.md`
- ❌ `COME_AVVIARE_BACKEND.md`
- ❌ `AVVIA_BACKEND.md`
- ❌ `DATABASE_SETUP_COMPLETED.md`
- ❌ `LEGGIMI_PRIMA.txt`
- ❌ `start_backend.ps1`
- ❌ `start_all.ps1`
- ❌ `RIAVVIA_TUTTO.ps1`
- ❌ `AVVIA_TUTTO_ORA.ps1`
- ❌ `package.json` (root)
- ❌ `package-lock.json` (root)
- ❌ `frontend/FORZA_REBUILD.ps1`
- ❌ `frontend/RIBUILDA_NAVBAR.ps1`
- ❌ `frontend/REBUILD_COMPLETO.md`
- ❌ `frontend/VERIFICA_NAVBAR.md`
- ❌ `backend/scripts/check_backend.py`
- ❌ `backend/scripts/setup_database.py`
- ❌ `backend/scripts/quick_setup_db.*`
- ❌ `backend/SETUP_DATABASE.md`
- ❌ `artifacts/` (intera directory)
- ❌ `IMPLEMENTATION_REPORT_60-100.md`
- ❌ `MANUAL_SETUP_COMMANDS.md`
- ❌ `QUICK_START_COMPLETE.md`
- ❌ `SEEDS_PR_SUMMARY.md`
- ❌ `COMPLETE_PLATFORM_SETUP.md`

### File Mantenuti (utili)
- ✅ `README.md` - Documentazione principale
- ✅ `README_DEV_NOTES.md` - Note per sviluppatori
- ✅ `QUICK_START.md` - Guida rapida
- ✅ `SEEDING_GUIDE.md` - Guida seeding
- ✅ `ADVANCED_ANALYTICS_GUIDE.md` - Guida analytics avanzati

---

## ⚠️ Problemi Risolti

### 1. ❌ Reti Docker Incompatibili
**Problema:** Backend e DB su reti diverse (`football-club-platform_net` vs `football-club-platform_default`)
**Soluzione:** Rimossi tutti i container, riavviati con `docker-compose.prod.yml` che crea una singola rete `football_club_platform_network`

### 2. ❌ URL Backend Errato
**Problema:** `frontend/next.config.js` e `frontend/lib/api.ts` puntavano a `http://localhost:8012`
**Soluzione:** Aggiornati a `http://localhost:8000/api/v1`

### 3. ❌ Navbar Incompleta
**Problema:** Mancava il link a `/sessions` (Sessioni di Allenamento)
**Soluzione:** Aggiunto alla `frontend/components/Navbar.tsx`

### 4. ❌ File Docker Compose Duplicati
**Problema:** `docker-compose.yml` (minimal) vs `docker-compose.prod.yml` (full stack)
**Soluzione:** Configurato Makefile per usare sempre `docker-compose.prod.yml`

### 5. ❌ Credenziali Database Sbagliate
**Problema:** DB con credenziali vecchie (postgres/postgres) vs backend che si aspetta (app/changeme)
**Soluzione:** Rimossi volumi, ricreato DB pulito con credenziali corrette

---

## 🧪 Test di Verifica

### Test Backend
```bash
# Health check
curl http://localhost:8000/healthz

# API Documentation
curl http://localhost:8000/docs

# Readiness (DB, Redis, Migrations)
curl http://localhost:8000/readyz
```

### Test Frontend
```bash
# Homepage
curl http://localhost:3002

# Verifica che Next.js sia pronto
# Output atteso: "Ready in Xs"
```

### Verifica Container
```bash
docker ps --filter "name=football_club_platform"

# Output atteso:
# - football_club_platform_backend (healthy)
# - football_club_platform_db (healthy)
# - football_club_platform_redis (healthy)
# - football_club_platform_minio (healthy)
```

---

## 🛠️ Comandi Utili

### Makefile
```bash
make up          # Avvia tutti i servizi
make down        # Ferma tutti i servizi
make logs        # Visualizza logs (SERVICE=nome per servizio specifico)
make ps          # Lista container
make build       # Builda immagini
make migrate     # Applica migrazioni
make seed        # Seed database
```

### Docker Compose Manuale
```bash
# Avvio
docker-compose -f docker-compose.prod.yml up -d

# Stop
docker-compose -f docker-compose.prod.yml down

# Logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Rebuild
docker-compose -f docker-compose.prod.yml build backend
```

### Frontend
```bash
cd frontend
npm install          # Installa dipendenze
npm run dev -- -p 3002   # Dev mode porta 3002
npm run build        # Build production
npm run start        # Start production
```

---

## 📊 Stack Tecnologico

### Backend
- **Framework:** FastAPI
- **Database:** PostgreSQL 16
- **ORM:** SQLAlchemy (async)
- **Cache:** Redis
- **Storage:** MinIO (S3-compatible)
- **ML:** PyTorch, scikit-learn, MLflow
- **Observability:** OpenTelemetry, Prometheus, Grafana

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **UI:** Tailwind CSS, Radix UI
- **Charts:** Recharts
- **HTTP Client:** Axios

---

## ✅ Checklist di Verifica Pre-Sviluppo

Prima di continuare lo sviluppo, verifica:

- [ ] Backend risponde su `http://localhost:8000/healthz`
- [ ] Frontend risponde su `http://localhost:3002`
- [ ] Database è raggiungibile (verifica `/readyz`)
- [ ] Tutte le 6 pagine sono visibili nella navbar
- [ ] Hot reload funziona (modifica un file frontend e verifica che si ricarichi)
- [ ] API docs accessibili su `http://localhost:8000/docs`

---

## 🎓 Note Finali

### Modalità Development vs Production

**Development (ATTUALE - Opzione A):**
- Backend: Docker (porta 8000)
- Frontend: NPM dev (porta 3002) - **hot reload, debugging**
- Migliore per sviluppo continuo

**Production (Opzione B):**
- Backend: Docker (porta 8000)
- Frontend: Docker (porta 3000)
- Migliore per testing/deploy

### Prossimi Passi
1. Seed database con dati demo
2. Test delle API principali
3. Verificare tutte le pagine frontend
4. Continuare sviluppo nuove features

---

**Data Ultima Modifica:** 2025-11-07
**Autore:** Team di 3 Programmatori Fullstack
**Versione:** 1.0 - Configurazione Stabile
