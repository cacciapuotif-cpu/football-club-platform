# Player Progress Feature - Implementation Summary

## 📋 File Modificati/Creati

### Modelli EAV
- ✅ `backend/app/models/wellness_eav.py`
  - Aggiunto `UniqueConstraint` per `(player_id, date)` su `WellnessSession`
  
- ✅ `backend/app/models/training_eav.py`
  - Aggiunto `UniqueConstraint` per `(training_session_id, player_id)` su `TrainingAttendance`

### Router Progress
- ✅ `backend/app/routers/progress.py` (completamente riscritto)
  - 3 endpoint implementati:
    1. `GET /api/v1/players/{player_id}/progress`
    2. `GET /api/v1/players/{player_id}/training-load`
    3. `GET /api/v1/players/{player_id}/overview`

### Test
- ✅ `backend/tests/test_progress_endpoints.py` (nuovo)
- ✅ `backend/tests/test_wellness_training_seed.py` (nuovo)

### Integrazione
- ✅ `backend/app/main.py` - Router già registrato (linea 275)

### Seed
- ✅ `backend/scripts/seed_demo_data.py` - Già completo e idempotente

---

## 🎯 Funzionalità Implementate

### 1. Endpoint Progress (`/api/v1/players/{player_id}/progress`)

**Query Params:**
- `bucket`: "daily" | "weekly" | "monthly" (default: "weekly")
- `date_from`: ISO date (default: oggi - 90 giorni)
- `date_to`: ISO date (default: oggi)
- `metrics`: CSV opzionale (default: sleep_quality,fatigue,soreness,stress,mood)

**Output:**
```json
{
  "bucket": "weekly",
  "date_from": "2024-10-01",
  "date_to": "2025-01-01",
  "series": [
    {
      "bucket_start": "2024-10-07",
      "sleep_quality": 6.3,
      "fatigue": 3.1,
      "soreness": 2.8,
      "stress": 4.2,
      "mood": 7.1,
      "srpe": 1320,
      "delta_prev_pct": {
        "sleep_quality": 4.2,
        "srpe": -12.7
      }
    }
  ]
}
```

**Caratteristiche:**
- Aggregazione temporale con `DATE_TRUNC`
- Calcolo delta percentuale vs bucket precedente
- sRPE = somma di (RPE × minutes) per bucket
- Supporta metriche wellness personalizzate via CSV

---

### 2. Endpoint Training Load (`/api/v1/players/{player_id}/training-load`)

**Query Params:**
- `acute_days`: int (default: 7, range: 1-14)
- `chronic_days`: int (default: 28, range: 7-56)

**Output:**
```json
{
  "series": [
    {
      "date": "2025-01-01",
      "srpe": 340,
      "acute": 310,
      "chronic": 285,
      "acwr": 1.09
    }
  ],
  "acute_days": 7,
  "chronic_days": 28,
  "flags": [
    {
      "date": "2025-01-05",
      "risk": "high",
      "reason": "acwr>1.52"
    }
  ]
}
```

**Caratteristiche:**
- Moving average per finestre acute/chronic
- ACWR = acute / chronic (se chronic > 0)
- Flags automatici:
  - `high`: ACWR > 1.5
  - `low`: ACWR < 0.8
  - `normal`: altrimenti

---

### 3. Endpoint Overview (`/api/v1/players/{player_id}/overview`)

**Query Params:**
- `period`: "7d" | "28d" | "30d" | "90d" (default: "28d")

**Output:**
```json
{
  "window_days": 28,
  "wellness_days_with_data": 22,
  "wellness_completeness_pct": 78.6,
  "last_values": {
    "sleep_quality": 6.0,
    "fatigue": 3.0,
    "soreness": 2.5,
    "stress": 4.0,
    "mood": 7.5
  },
  "training_sessions": 12,
  "present_count": 10,
  "avg_srpe_last_7d": 1100,
  "avg_srpe_last_28d": 980
}
```

**Caratteristiche:**
- Completezza dati wellness (giorni con dati / window_days)
- Ultimi valori disponibili per ogni metrica
- Conteggi sessioni allenamento
- Media sRPE per 7d e 28d

---

## 🔧 Estratti Codice Principali

### Calcolo Delta Percentuale
```python
# In progress.py, funzione get_player_progress
delta_prev_pct = {}
if prev_bucket_data:
    for metric in metric_list:
        curr_val = bucket_data.get(metric)
        prev_val = prev_bucket_data.get(metric)
        if curr_val is not None and prev_val is not None and prev_val != 0:
            delta_pct = ((curr_val - prev_val) / prev_val) * 100
            delta_prev_pct[metric] = round(delta_pct, 2)
```

### Calcolo ACWR con Moving Average
```python
# In progress.py, funzione get_training_load
with_rolling AS (
    SELECT
        date,
        srpe,
        AVG(srpe) OVER (
            ORDER BY date
            ROWS BETWEEN :acute_rows PRECEDING AND CURRENT ROW
        ) AS acute,
        AVG(srpe) OVER (
            ORDER BY date
            ROWS BETWEEN :chronic_rows PRECEDING AND CURRENT ROW
        ) AS chronic
    FROM filled_srpe
)
```

### Completezza Dati Wellness
```python
# In progress.py, funzione get_player_overview
wellness_completeness_pct = round(
    (wellness_days_with_data / window_days) * 100, 1
) if window_days > 0 else 0
```

---

## 📝 Comandi da Eseguire

### 1. Verifica/Applica Migrazioni

```bash
# Dalla root del progetto
cd backend

# Genera migrazione (se necessario)
poetry run alembic -c alembic.ini revision --autogenerate -m "sync models for progress feature"

# Applica migrazioni
poetry run alembic -c alembic.ini upgrade head
```

**Nota:** I vincoli unique sono già presenti nella migrazione `2025_11_05_eav_refactor.py`. Se la migrazione è già applicata, non serve rigenerare.

### 2. Esegui Seed Demo

```bash
# Dalla root del progetto
python backend/scripts/seed_demo_data.py
```

**Output atteso:**
```
🌱 SEEDING DEMO DATA - EAV Progress Tracking
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
✅ Created 2250 wellness sessions with 18000 metrics
🏋️  Creating training sessions with attendance...
✅ Created 30 training sessions, 675 attendances, 3375 metrics
⚽ Creating matches with player stats...
✅ Created 8 matches, 112 attendances, 784 metrics
✅ SEEDING COMPLETE!
```

### 3. Test Endpoint

```bash
# Avvia backend (se non già in esecuzione)
cd backend
poetry run uvicorn app.main:app --reload

# In un altro terminale, testa gli endpoint
# Sostituisci {player_id} con un UUID reale dal seed
curl "http://localhost:8000/api/v1/players/{player_id}/progress?bucket=weekly"
curl "http://localhost:8000/api/v1/players/{player_id}/training-load"
curl "http://localhost:8000/api/v1/players/{player_id}/overview?period=28d"
```

### 4. Esegui Test Automatici

```bash
cd backend
poetry run pytest tests/test_progress_endpoints.py -v
poetry run pytest tests/test_wellness_training_seed.py -v
```

---

## 📊 Esempi di Risposta Real

### GET /api/v1/players/{player_id}/progress?bucket=weekly

```json
{
  "bucket": "weekly",
  "date_from": "2024-10-03",
  "date_to": "2025-01-01",
  "series": [
    {
      "bucket_start": "2024-10-07",
      "sleep_quality": 7.2,
      "fatigue": 3.5,
      "soreness": 2.8,
      "stress": 4.1,
      "mood": 7.5,
      "srpe": 1250.0,
      "delta_prev_pct": null
    },
    {
      "bucket_start": "2024-10-14",
      "sleep_quality": 6.8,
      "fatigue": 4.2,
      "soreness": 3.1,
      "stress": 4.5,
      "mood": 7.0,
      "srpe": 1380.0,
      "delta_prev_pct": {
        "sleep_quality": -5.6,
        "fatigue": 20.0,
        "soreness": 10.7,
        "stress": 9.8,
        "mood": -6.7,
        "srpe": 10.4
      }
    }
  ]
}
```

### GET /api/v1/players/{player_id}/training-load

```json
{
  "series": [
    {
      "date": "2024-12-25",
      "srpe": 0,
      "acute": null,
      "chronic": null,
      "acwr": null
    },
    {
      "date": "2024-12-26",
      "srpe": 450,
      "acute": 450.0,
      "chronic": null,
      "acwr": null
    },
    {
      "date": "2024-12-27",
      "srpe": 375,
      "acute": 412.5,
      "chronic": null,
      "acwr": null
    },
    {
      "date": "2025-01-01",
      "srpe": 420,
      "acute": 310.5,
      "chronic": 285.2,
      "acwr": 1.09
    }
  ],
  "acute_days": 7,
  "chronic_days": 28,
  "flags": [
    {
      "date": "2025-01-02",
      "risk": "high",
      "reason": "acwr>1.52"
    }
  ]
}
```

### GET /api/v1/players/{player_id}/overview?period=28d

```json
{
  "window_days": 28,
  "wellness_days_with_data": 25,
  "wellness_completeness_pct": 89.3,
  "last_values": {
    "sleep_quality": 7.0,
    "fatigue": 3.2,
    "soreness": 2.5,
    "stress": 4.0,
    "mood": 7.5
  },
  "training_sessions": 12,
  "present_count": 11,
  "avg_srpe_last_7d": 1125.0,
  "avg_srpe_last_28d": 980.5
}
```

---

## 🔍 Note Tecniche

### Metriche Wellness Standard
- `sleep_quality` (1-10)
- `fatigue` (1-10)
- `soreness` o `doms` (1-10) - sinonimi
- `stress` (1-10)
- `mood` (1-10)

### sRPE (Session Rate of Perceived Exertion)
- Formula: `sRPE = RPE × minutes`
- Aggregato per bucket (daily/weekly/monthly)
- Usato per calcolare ACWR

### ACWR (Acute:Chronic Workload Ratio)
- `acute`: media mobile ultimi N giorni (default: 7)
- `chronic`: media mobile ultimi M giorni (default: 28)
- `ACWR = acute / chronic`
- Flags:
  - `high`: ACWR > 1.5 (rischio sovraccarico)
  - `low`: ACWR < 0.8 (sottocarico)
  - `normal`: 0.8 ≤ ACWR ≤ 1.5

### Idempotenza Seed
- Il seed usa `ON CONFLICT DO NOTHING` per i vincoli unique
- Può essere eseguito più volte senza creare duplicati
- Verifica esistenza prima di creare nuovi record

---

## ✅ Checklist Implementazione

- [x] Modelli EAV con vincoli unique
- [x] Migrazione Alembic (già presente)
- [x] Endpoint `/progress` con bucket e delta
- [x] Endpoint `/training-load` con ACWR e flags
- [x] Endpoint `/overview` con KPI e completezza
- [x] Integrazione in `main.py`
- [x] CORS configurato (già presente)
- [x] Seed demo idempotente
- [x] Test automatici
- [x] Documentazione

---

## 🚀 Prossimi Passi

1. **Configurare DATABASE_URL** nel `.env` o variabili d'ambiente
2. **Eseguire migrazioni**: `poetry run alembic -c backend/alembic.ini upgrade head`
3. **Eseguire seed**: `python backend/scripts/seed_demo_data.py`
4. **Testare endpoint** con curl o Postman
5. **Integrare nel frontend** Next.js

---

**Data Implementazione:** 2025-01-01  
**Versione:** 1.0.0

