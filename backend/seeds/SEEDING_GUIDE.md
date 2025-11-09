# Seeding Guide — Sessions & Wellness

## Prerequisites
- Postgres running (`docker compose up -d db`)
- `.env` configured with matching credentials.
- Poetry environment installed.

## Base Seed (Structural)
```bash
poetry run alembic -c backend/alembic.ini upgrade head
poetry run python backend/seeds/seed_all.py --dataset demo
```

## Sessions & Wellness Enrichment
```bash
# Generates 2 tenants × 4 teams each × 90 days of data
poetry run python backend/seeds/seed_wellness_sessions.py
```

### What It Creates
- Ensures tenants `demo-fc` and `aurora-academy`.
- Adds ~32 athletes per tenant (minors, guardian info).
- Populates 90 days of:
  - Sessions (training, match, recovery patterns)
  - Participation (RPE, load)
  - Wellness (sleep, HRV, fatigue, mood...)
  - Feature store metrics (ACR, HRV baseline, sleep debt, readiness)
  - Predictions with drivers
  - ≥12 alerts per tenant across severities

### Idempotency Rules
- Deterministic UUIDs (`uuid5`) for sessions, wellness, features, alerts.
- Upserts by composite keys on features and predictions.
- Safe to run multiple times; updates in-place.

## Validation Steps
1. **Great Expectations** (contract checks)
   ```bash
   GE_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/football_club \
   poetry run great_expectations --config-file great_expectations/great_expectations.yml \
     checkpoint run ingest_contract
   ```
2. **dbt build**
   ```bash
   cd dbt
   dbt deps
   dbt run --profiles-dir .
   dbt test --profiles-dir .
   ```
3. **Smoke tests**
   - `/api/v1/sessions`
   - `/api/v1/wellness/teams/{teamId}/heatmap`
   - `/api/v1/wellness/athletes/{athleteId}/readiness`

## Troubleshooting
- **RLS errors**: ensure script runs with environment variable `SKIP_AUTH=true` or rely on `set_rls_context` (already invoked).
- **Duplicate players**: script checks `external_id`; delete conflicting rows manually if overrides were made.
- **Performance**: script uses batches but may take ~20–30 seconds for full dataset.

