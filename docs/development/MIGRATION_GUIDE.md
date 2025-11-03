# Guida Migrazione - Moduli Performance

## Panoramica

Questa migrazione aggiunge 4 nuovi moduli per la valutazione completa dei giocatori:

1. **TechnicalStats** - Statistiche tecniche (passaggi, tiri, dribbling, etc.)
2. **TacticalCognitive** - Valutazione tattica e cognitiva
3. **PsychologicalProfile** - Profilo psicologico (motivazione, resilienza, etc.)
4. **HealthMonitoring** - Monitoraggio salute e rischio infortuni

Inoltre estende i modelli esistenti con nuovi campi (NON distruttivo).

## Modifiche al Database

### Nuove Tabelle

#### `technical_stats`
```sql
- id (UUID, PK)
- player_id (UUID, FK)
- date (DATE)
- pass_accuracy_pct (FLOAT, 0-100)
- shots_total, shots_on_target, goals, assists (INT)
- conversion_rate_pct (FLOAT, auto-calcolato)
- dribbles_won, dribbles_attempted (INT)
- duels_won, duels_lost (INT)
- crosses_successful, crosses_attempted (INT)
- unforced_errors, turnovers (INT)
- weak_foot_usage_pct (FLOAT, 0-100)
- decision_time_ms (FLOAT)
- heatmap_json (TEXT, opzionale)
- organization_id (UUID, FK)
- created_at (TIMESTAMP)
```

#### `tactical_cognitive`
```sql
- id (UUID, PK)
- player_id (UUID, FK)
- date (DATE)
- involvement_pct (FLOAT, 0-100)
- reaction_time_ms (FLOAT)
- correct_decisions_pct (FLOAT, 0-100)
- anticipations_pct (FLOAT, 0-100)
- pressing_timing_ms (FLOAT)
- cognitive_errors (INT)
- centroid_x_pct, centroid_y_pct (FLOAT, 0-100)
- organization_id (UUID, FK)
- created_at (TIMESTAMP)
```

#### `psychological_profile`
```sql
- id (UUID, PK)
- player_id (UUID, FK)
- date (DATE)
- motivation_1_5, self_esteem_1_5, leadership_1_5 (INT, 1-5)
- resilience_1_5, stress_mgmt_1_5, mental_fatigue_1_5 (INT, 1-5)
- coach_note (VARCHAR(500))
- organization_id (UUID, FK)
- created_at (TIMESTAMP)
```

#### `health_monitoring`
```sql
- id (UUID, PK)
- player_id (UUID, FK)
- week_start_date (DATE)
- status (ENUM: HEALTHY, INJURED, RECOVERING, ILLNESS)
- injury_type (VARCHAR(255))
- injury_start, injury_end (DATE)
- weekly_load_AU (FLOAT)
- injury_risk_0_1 (FLOAT, 0-1)
- avg_sleep_quality_1_5 (FLOAT, 1-5)
- nutrition_hydration_1_5 (INT, 1-5)
- pain_1_10 (INT, 1-10)
- organization_id (UUID, FK)
- created_at (TIMESTAMP)
```

### Estensioni Tabelle Esistenti (NON distruttive)

#### `players` - Aggiunte:
```sql
- medical_clearance (BOOLEAN, default FALSE)
- medical_clearance_expiry (DATE, nullable)
```

#### `training_sessions` - Aggiunte:
```sql
- distance_m (FLOAT, >=0)
- hi_distance_m (FLOAT, >=0, distanza alta intensità >20 km/h)
- sprints_count (INT, >=0)
- top_speed_ms (FLOAT, 0-12 m/s)
- max_acc_ms2 (FLOAT, 0-12 m/s²)
- hr_avg_bpm (INT, 30-220)
- hr_max_bpm (INT, 30-220)
- fatigue_note (VARCHAR(500))
```

#### `wellness_data` - Aggiunte:
```sql
- sleep_start_hhmm (VARCHAR(5), formato HH:MM)
- wake_time_hhmm (VARCHAR(5), formato HH:MM)
- body_weight_kg (FLOAT, >=0)
- hydration_pct (FLOAT, 0-100)
```

## Esecuzione Migrazione

### 1. Backup Database (OBBLIGATORIO)
```bash
# PostgreSQL
pg_dump -U postgres football_club_platform > backup_before_migration.sql

# MySQL
mysqldump -u root -p football_club_platform > backup_before_migration.sql
```

### 2. Genera Migrazione
```bash
cd backend
alembic revision --autogenerate -m "add performance modules"
```

### 3. Verifica Script Migrazione
Controlla il file generato in `backend/alembic/versions/`. Verifica che:
- Le nuove tabelle siano create correttamente
- Le colonne esistenti NON siano modificate
- I vincoli e indici siano presenti

### 4. Applica Migrazione
```bash
alembic upgrade head
```

### 5. Verifica Migrazione
```bash
# Verifica tabelle create
alembic current

# Test API
curl http://localhost:8000/api/v1/performance/technical
curl http://localhost:8000/api/v1/performance/tactical
curl http://localhost:8000/api/v1/performance/psychological
curl http://localhost:8000/api/v1/performance/health
```

## Nuovi Endpoint API

### Performance Modules
- `POST /api/v1/performance/technical` - Crea stats tecniche
- `GET /api/v1/performance/technical?player_id={uuid}` - Lista stats
- `POST /api/v1/performance/tactical` - Crea valutazione tattica
- `GET /api/v1/performance/tactical?player_id={uuid}` - Lista valutazioni
- `POST /api/v1/performance/psychological` - Crea profilo psicologico
- `GET /api/v1/performance/psychological?player_id={uuid}` - Lista profili
- `POST /api/v1/performance/health` - Crea monitoraggio salute
- `GET /api/v1/performance/health?player_id={uuid}` - Lista monitoraggio

### Analytics Avanzati
- `GET /api/v1/analytics/players/{id}/injury-risk` - Calcola rischio infortunio (0-1)
  - Formula: `0.25·HRV + 0.20·FC + 0.25·Carico + 0.15·DOMS + 0.15·Sonno`
  - Livelli: low (<0.33), moderate (0.33-0.66), high (>0.66)

- `GET /api/v1/analytics/players/{id}/evolution-index` - Indice evoluzione (0-100)
  - Pesi: Fisico 30%, Tecnico 25%, Tattico 15%, Psicologico 15%, Salute 15%

## Calcoli Automatici

### Conversion Rate (%)
```python
conversion_rate = (goals / max(shots_on_target, 1)) * 100
```

### Weekly Load (AU)
```python
weekly_load = sum(RPE × duration for each session in week)
```

### Injury Risk (0-1)
Normalizzazione z-score su medie 7 giorni:
```python
risk = 0.25·z(HRV↓) + 0.20·z(FC_riposo↑) + 0.25·z(Carico↑) + 0.15·z(DOMS↑) + 0.15·z(Sonno↓)
```

### Evolution Index (0-100)
```python
evolution = (
    0.30 × physical_score +
    0.25 × technical_score +
    0.15 × tactical_score +
    0.15 × psychological_score +
    0.15 × health_score
)
```

## Rollback (se necessario)

```bash
# Torna alla versione precedente
alembic downgrade -1

# Ripristina da backup
psql -U postgres football_club_platform < backup_before_migration.sql
```

## Seed Data (Esempio)

```python
# Esempio inserimento Technical Stats
POST /api/v1/performance/technical
{
  "player_id": "uuid-del-giocatore",
  "date": "2025-01-15",
  "pass_accuracy_pct": 87.5,
  "shots_total": 5,
  "shots_on_target": 3,
  "goals": 1,
  "assists": 2,
  "dribbles_won": 4,
  "dribbles_attempted": 6
}

# Esempio Psychological Profile
POST /api/v1/performance/psychological
{
  "player_id": "uuid-del-giocatore",
  "date": "2025-01-15",
  "motivation_1_5": 5,
  "self_esteem_1_5": 4,
  "leadership_1_5": 4,
  "resilience_1_5": 5,
  "stress_mgmt_1_5": 3,
  "mental_fatigue_1_5": 2,
  "coach_note": "Ottima settimana, molto motivato"
}
```

## Test

```bash
# Unit tests per calcoli
cd backend
pytest tests/test_analytics.py -v

# Test specifici
pytest tests/test_analytics.py::test_conversion_rate
pytest tests/test_analytics.py::test_injury_risk
pytest tests/test_analytics.py::test_evolution_index
```

## Note Importanti

1. ⚠️ **Backup obbligatorio** prima della migrazione
2. ✅ **Nessuna modifica ai campi esistenti** - solo aggiunte
3. 📊 **Indici automatici** su player_id, date, organization_id
4. 🔒 **Validazioni range** implementate a livello DB e API
5. 🎯 **Multi-tenancy** garantito su tutti i nuovi moduli

## Supporto

Per problemi con la migrazione:
1. Controlla i log Alembic: `backend/alembic/versions/*.py`
2. Verifica vincoli FK: tutti i `player_id` devono esistere
3. Test endpoint: usa Swagger UI su `/docs`
