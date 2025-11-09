# Data Reliability SLOs

## Ingestion Freshness
- **Sessions & Participation**
  - Source: GPS / training scheduler
  - SLO: 99% of events ingested within 15 minutes of session end
  - Error budget: 90 minutes per week
- **Wellness Surveys**
  - SLO: 99% data ingested within 5 minutes of submission
  - Alert if backlog > 20 surveys
- **Wearables (HR/HRV/Sleep)**
  - SLO: 95% of nightly data ingested by 07:00 local time
  - Alert if missing >2 days per athlete

## Data Quality
- Great Expectations suites must pass with 100% critical expectations met.
- Allowed warnings:
  - Up to 2% nulls in optional fields (notes, metadata)
  - Up to 1% duplicates (auto-removed) with post-fix audit.

## Feature Computation
- Batch job (daily 05:00) completion SLO: 99% finished < 10 minutes.
- Streaming update: readiness features refresh within 2 minutes of new data.

## Alert Generation
- Alert emission SLO: within 1 minute of risk score > threshold.
- Acknowledgement tracking: 90% alerts acknowledged within 30 minutes (monitored).

## Monitoring & Escalation
- Pager escalation if:
  - Ingestion backlog > SLO for 10 consecutive minutes.
  - Feature job failing twice in 24h.
  - Alert pipeline latency >5 minutes.
# Data & Ingestion SLOs

## 1. Ingestion Latency
- Wellness surveys: <30 min from submission to availability in warehouse.
- Sessions & participation: <60 min post-session end.
- External wearables (HR/HRV): <2 h for nightly batch.

## 2. Freshness Guarantees
- Daily completeness SLA: ≥95 % athletes with at least one wellness entry per day.
- If completeness drops <90 %, raise alert via `alerts` table (`severity=MEDIUM`).

## 3. Data Quality SLO
- Great Expectations suites must pass on ingest (no critical failures).
- Allow warning-level (non-blocking) for missing optional fields; log to monitoring.

## 4. Recovery Objectives
- RPO: 4 h (recover to last successful ingest within 4 h).
- RTO: 2 h (time to restore pipeline after failure).

## 5. Monitoring Hooks
- Track ingestion status in MLflow or Prometheus metrics (`ingest_latency_seconds`).
- Daily summary job writing to `/jobs/monitoring/daily_data_quality.py` (see Team B spec).

