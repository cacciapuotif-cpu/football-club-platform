# 🚀 Quick Start - Advanced Analytics System

## Opzione 1: Setup Automatico (Raccomandato)

### Windows
```batch
setup_and_test.bat
```

### Linux/macOS/Git Bash
```bash
chmod +x setup_and_test.sh
./setup_and_test.sh
```

Questo script automaticamente:
1. ✅ Avvia PostgreSQL con Docker
2. ✅ Applica le migrations del database
3. ✅ Popola il database con dati demo realistici
4. ✅ Avvia il backend FastAPI
5. ✅ Testa tutte le API advanced analytics

---

## Opzione 2: Setup Manuale

### Prerequisiti
- Docker Desktop in esecuzione
- Python 3.11+
- Git Bash (per Windows) o terminale Unix

### Passo 1: Avvia Database
```bash
cd infra
docker-compose up -d db
cd ../backend
```

### Passo 2: Applica Migrations
```bash
alembic upgrade head
```

### Passo 3: Popola Database
```bash
python scripts/complete_seed_advanced.py
```

Questo creerà:
- 1 organizzazione
- 8 squadre (Milan, Inter, Juventus, Roma, Napoli, Lazio, Atalanta, Fiorentina)
- 176 giocatori (22 per squadra: 2 GK, 8 DF, 8 MF, 4 FW)
- 60 partite della stagione 2024-2025
- 800+ statistiche dettagliate con metriche ML calcolate
- Rating, form level e market value aggiornati

### Passo 4: Avvia Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Passo 5: Testa API
In un altro terminale:
```bash
python scripts/test_analytics_apis.py
```

---

## 🌐 Accesso alla Piattaforma

### API Documentation (Swagger)
**URL:** http://localhost:8000/docs

Qui troverai tutti gli endpoint documentati con esempi interattivi.

Cerca la sezione **"Advanced ML Analytics & Scouting"** per testare:
- Player Analysis
- Scouting Recommendations
- Team Analysis
- Performance Trends

### Health Check
**URL:** http://localhost:8000/healthz

### Prometheus Metrics
**URL:** http://localhost:8000/metrics

---

## 🔐 Credenziali di Accesso

**Email:** `admin@demo.club`
**Password:** `admin123`

---

## 📊 Dati Demo Creati

| Tipo | Quantità | Descrizione |
|------|----------|-------------|
| **Organizzazioni** | 1 | Demo Football Club |
| **Squadre** | 8 | Serie A italiana |
| **Giocatori** | 176 | 22 per squadra |
| **Partite** | 60 | Stagione 2024-2025 |
| **Statistiche** | 800+ | Con metriche ML complete |

### Distribuzione Giocatori per Ruolo
- **Portieri (GK):** 16 giocatori
- **Difensori (DF):** 64 giocatori
- **Centrocampisti (MF):** 64 giocatori
- **Attaccanti (FW):** 32 giocatori

---

## 🧪 Test delle API Advanced Analytics

### 1. Analisi Giocatore
```bash
curl "http://localhost:8000/api/v1/advanced-analytics/players/{PLAYER_ID}/analysis?matches=10"
```

**Response includes:**
- Aggregate statistics (goals, assists, shots, passes, etc.)
- Performance Index (0-100)
- Influence Score (0-10)
- Form Prediction (0-10)
- Position Ranking & Percentile
- Strengths & Areas for Improvement

### 2. Scouting Intelligente
```bash
curl "http://localhost:8000/api/v1/advanced-analytics/scouting/teams/{TEAM_ID}/recommendations?position=FW&max_age=28&max_budget=50000000&min_rating=6.5"
```

**Response includes:**
- List of recommended players
- Value Score (rapporto qualità/prezzo)
- Form Prediction
- Recommendation Level (STRONG_BUY, BUY, CONSIDER, HOLD)
- Confidence Score (0-100%)

### 3. Analisi Squadra
```bash
curl "http://localhost:8000/api/v1/advanced-analytics/teams/{TEAM_ID}/analysis"
```

**Response includes:**
- Team composition & distribution
- Average rating per position
- Top performers
- Areas for improvement

### 4. Trend Prestazioni
```bash
curl "http://localhost:8000/api/v1/advanced-analytics/players/{PLAYER_ID}/trend?period_days=60"
```

**Response includes:**
- Performance data over time
- Trend direction (improving/declining/stable)
- Consistency score
- Average performance

---

## 🧠 Algoritmi ML Implementati

### 1. Performance Index (0-100)
Calcola prestazione complessiva basata su:
- **Offensive Impact (30%):** Goals, assists, tiri, dribbling
- **Defensive Impact (25%):** Tackle, intercetti, duelli aerei
- **Creativity (20%):** Passaggi chiave, through balls, precisione
- **Physical Impact (15%):** Distanza, sprint, efficienza fisica
- **Discipline (10%):** Cartellini, falli, fuorigioco

Pesi dinamici per posizione (GK, DF, MF, FW).

### 2. Influence Score (0-10)
Misura impatto sulla partita con formula ponderata e normalizzazione sigmoid.

### 3. Expected Goals (xG)
Calcola gol attesi basandosi su:
- Qualità dei tiri (on target ratio)
- Posizione del giocatore (moltiplicatore)
- Tasso di conversione storico

### 4. Expected Assists (xA)
Calcola assist attesi da:
- Key passes
- Through balls
- Cross accuracy

### 5. Form Prediction (0-10)
Predice forma attuale con media ponderata delle ultime 5-10 partite e bias di recency.

### 6. Scouting Intelligente
Algoritmo multi-fattoriale che considera:
- Performance recenti
- Età e potenziale
- Valore di mercato (value score)
- Forma attuale
- Confidence score basato su dati disponibili

---

## 📁 File Creati

### Script di Seed
- `backend/scripts/complete_seed_advanced.py` - Popolamento database completo con dati realistici

### Script di Test
- `backend/scripts/test_analytics_apis.py` - Test automatico di tutte le API

### Script di Setup
- `setup_and_test.sh` - Setup automatico (Linux/macOS/Git Bash)
- `setup_and_test.bat` - Setup automatico (Windows)

### Documentazione
- `ADVANCED_ANALYTICS_GUIDE.md` - Guida completa con esempi e best practices
- `QUICK_START.md` - Questa guida rapida

---

## 🔧 Troubleshooting

### Database connection error
```
❌ asyncpg.exceptions.InvalidPasswordError
```
**Soluzione:** Verifica che PostgreSQL sia in esecuzione con Docker e che le credenziali in `.env` siano corrette.

```bash
docker-compose -f infra/docker-compose.yml up -d db
```

### Migration error
```
❌ alembic.util.exc.CommandError
```
**Soluzione:** Assicurati di essere nella directory `backend`:
```bash
cd backend
alembic upgrade head
```

### Port 8000 already in use
**Soluzione Windows:**
```batch
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Soluzione Linux/macOS:**
```bash
lsof -ti:8000 | xargs kill -9
```

### No data found after seeding
**Soluzione:** Riesegui lo script di seed:
```bash
python scripts/complete_seed_advanced.py
```

---

## 📖 Prossimi Passi

1. ✅ Esplora la API documentation su http://localhost:8000/docs
2. ✅ Testa gli endpoint interattivamente
3. ✅ Leggi `ADVANCED_ANALYTICS_GUIDE.md` per esempi dettagliati
4. ✅ Integra le API nel tuo frontend
5. ✅ Personalizza gli algoritmi ML per le tue esigenze

---

## 🎯 Obiettivi Raggiunti

✅ Database strutturato con 60+ metriche per giocatore
✅ Algoritmi ML avanzati (Performance Index, xG/xA, Form Prediction)
✅ Sistema scouting intelligente con AI
✅ API RESTful complete e documentate
✅ 800+ statistiche con metriche calcolate
✅ Script di test automatici
✅ Setup completamente automatizzato

---

**🎉 La tua piattaforma Advanced Analytics è pronta all'uso!**

Per domande o supporto, consulta `ADVANCED_ANALYTICS_GUIDE.md` o la documentazione API.
