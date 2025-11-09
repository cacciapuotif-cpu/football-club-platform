# Data Validation Playbook

## Tooling
- **Great Expectations** for schema, distribution, and reference checks.
- **dbt tests** for key constraints, not-null, relationships.
- **Custom ML drift monitors** in `/backend/jobs/monitoring/`.

## Execution Flow
1. Ingest raw data into landing tables.
2. Run GE checkpoint `ge.checkpoint.run "ingest_contract"`.
3. On success, load into staging tables (`dbt run --select staging`).
4. Execute dbt tests (`dbt test`).
5. If all green, promote to mart tables (`dbt run --select marts`).

## Contract Coverage
- **Schema**: field presence, type checks (`expect_table_columns_to_match_set`).
- **Freshness**: `expect_column_max_to_be_between` on timestamps.
- **PII**: `expect_column_values_to_match_regex` for tokenized identifiers.
- **Metrics**:
  - HRV values 20–200 ms.
  - Resting HR 35–100 bpm.
  - Sleep hours 3–12.
- **Load**:
  - `load` between 0 and 1500 AU.
  - ACWR 0–3.0.

## Automation
- CI job `data-contracts`:
  ```bash
  poetry run great_expectations --config-file great_expectations.yml checkpoint run ingest_contract
  dbt deps
  dbt seed --profiles-dir .
  dbt run --profiles-dir .
  dbt test --profiles-dir .
  ```

## Incident Response
- Failure triggers Slack webhook `#data-quality`.
- Engineers must update incident doc with root cause & resolution.
# Data Validation Playbook

## Tools
- **Great Expectations**: contract validation suites.
- **dbt tests**: schema and relationship checks in warehouse.
- **Custom Python checks**: anomaly detection for feature drift.

## Execution Flow
1. Ingest raw data into staging tables (`stg_*`).
2. Run Great Expectations checkpoint `ingest_checkpoint`:
   - Confirm required columns not null.
   - Validate enum values (session type, wellness metric).
   - Check ranges (RPE 1–10, wellness 1–10).
3. On success, trigger dbt `run + test` to build marts.
4. Persist validation summary to `data_quality_reports` table and push metrics to monitoring.

## Commands
```bash
poetry run python scripts/run_ge_checkpoint.py ingest_checkpoint
poetry run dbt run --project-dir dbt
poetry run dbt test --project-dir dbt
```

## Failure Handling
- Critical failure: abort pipeline, send alert to #data-ops.
- Warning: log issue, mark row for quarantine (`quality_score < 0.7`).
- Automatic retries: 3 attempts with exponential backoff.

## Reporting
- Daily digest in `/data/demo/README.md`.
- Long-term metrics visualized in Grafana (pipeline latency, GE pass rate).

