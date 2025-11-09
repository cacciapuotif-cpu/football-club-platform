# Architecture Note — Tenancy & Sessions/Wellness APIs

## Multi-Tenancy & RLS
- FastAPI dependencies (`get_current_user`) decode JWT / OIDC, map `org_id → tenant_id`, and populate Postgres GUCs via `set_rls_context`.
- All new domain tables (`athletes`, `sessions`, `session_participation`, `wellness_readings`, `features`, `predictions`, `alerts`) include a `tenant_id` column with enforced Row Level Security (policy `*_tenant_isolation`).
- `SKIP_AUTH=true` (development/tests) injects a synthetic admin user and still applies tenant scoping.

## Sessions API (`/api/v1/sessions`)
- `GET /v1/sessions`  
  Paginates tenant-scoped sessions with filters for `teamId`, `type`, `from`, `to`, returning `SessionsPage`.
- `GET /v1/sessions/{sessionId}`  
  Returns session metadata plus participation (`SessionDetail`).
- `GET /v1/sessions/{sessionId}/wellness_snapshot?window_days=2`  
  Aggregates wellness readings, predictions, and alerts in a ±N day window around the session for participating athletes (`SessionWellnessSnapshot`).

## Readiness ML API (`/api/v1/ml`)
- `POST /ml/readiness/predict`  
  Wraps the scikit-learn readiness pipeline (RandomForest baseline) for on-demand scoring. Requires feature payload with `age_years`, `position_code`, `session_load`, `wellness_score`. Returns expected performance, confidence bounds, overload probability/level, threshold classification and feature importances.
- `GET /ml/readiness/{playerId}`  
  Returns the latest prediction stored in `ml_predictions` for the given player (seeded during `08_ml_predictions` step).

## Schemas & Enums
- `SessionListItem`, `SessionDetail`, `SessionWellnessSnapshot` and related DTOs live in `app/schemas/sessions_wellness.py`.
- Session types enumerate `{training, match, recovery, other}`; participation statuses cover `{completed, partial, missed, excused}`; alerts reuse severity from predictions.

## Testing & Guardrails
- Unit tests (`backend/tests/test_sessions_router.py`) cover pagination logic, detail retrieval, snapshot aggregation, and error paths with mocked `AsyncSession`.
- Unit tests (`backend/tests/test_readiness_api.py`) validate the readiness endpoint and ensure the scikit-learn pipeline is reachable.
- Dataset regression (`test_demo_dataset_players_are_minors`) enforces that the demo seed players (`05-players` in `backend/seeds/datasets/demo.yaml`) remain under 18 and flagged as minors.

## Next Steps
- Extend integration coverage once async DB fixtures are available (end-to-end with seeded demo tenant).
- Expose additional filters (playerId, load thresholds) as the data pipeline (Team B) matures.

