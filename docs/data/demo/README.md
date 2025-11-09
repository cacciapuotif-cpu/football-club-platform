# Demo Dataset (Sessions & Wellness)

## Overview
- **Tenants**: `demo-fc`, `aurora-academy`
- **Teams per tenant**: 4 (U16–U19)
- **Athletes per tenant**: 32 (8 per team, all U16–U19)
- **Time span**: 90 days ending today
- **Data types**:
  - Sessions (training, match, recovery)
  - Session participation (RPE, load)
  - Wellness readings (sleep, HRV, resting HR, fatigue, soreness, mood)
  - Feature store entries (ACR, HRV baseline, sleep debt, readiness)
  - Predictions with SHAP-like drivers
  - Alerts (≥12 per tenant, varying severities)

## Generation Script
- `poetry run python backend/seeds/seed_wellness_sessions.py`
  - Automatically creates organizations/teams if missing.
  - Idempotent via deterministic UUIDs.
  - Applies RLS context for each tenant.

## Scenarios Included
- Weekly load cycles (overreaching weeks every 3rd micro-cycle).
- Travel fatigue spikes on alternating away weeks.
- Minor illness pockets (partial sleep/hrv deterioration).
- Alerts fired for high risk or excessive load.

## Validation
- Run Great Expectations checkpoint:
  ```bash
  GE_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/football_club \
  poetry run great_expectations --config-file great_expectations/great_expectations.yml \
    checkpoint run ingest_contract
  ```
- Execute dbt tests:
  ```bash
  cd dbt
  dbt deps
  dbt seed --profiles-dir .
  dbt run --profiles-dir .
  dbt test --profiles-dir .
  ```

