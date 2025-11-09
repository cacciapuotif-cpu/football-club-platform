# Staging Models

- `stg_sessions.sql`: cleans raw session data from operational DB (training sessions).
- `stg_wellness.sql`: maps wellness readings to canonical format.
- `stg_session_participation.sql`: flatten participation with load metrics.

These staging views enforce column naming conventions and basic filters (`tenant_id` scoped).

