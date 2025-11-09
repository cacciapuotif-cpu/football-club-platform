# Return-to-Play Coding Standards

## Injury Classification
- Follow FIFA 11+ taxonomy.
- Required fields: injury_id, athlete_id, tenant_id, diagnosis_code, body_region, severity, onset_date, mechanism.
- Severity scale:
  - **Minor**: 1–3 days lost.
  - **Moderate**: 4–14 days.
  - **Major**: >14 days or surgical.

## RTP Stages
1. **Rehab** — constrained training, monitor with wellness + physio notes.
2. **Modified** — partial team training; limited minutes in sessions.
3. **Full** — cleared for match play; reintroduce into load calculations.

## Data Integration
- Sessions API must exclude athletes not in Full stage from readiness baseline.
- Alerts triggered when stage regresses or remains static > expected recovery window.
- Document stage transitions in audit log.

## Medical Notes
- Store attachments separately (encrypted).
- Track clinician, timestamp, clearance status.

## Compliance
- Align with GDPR: minors require guardian acknowledgement stored in `guardians` table.
- Retention: 10 years medical, purge request protocol documented in `/docs/compliance/data_retention.md`.

