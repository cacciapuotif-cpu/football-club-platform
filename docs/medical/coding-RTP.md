# Return-to-Play (RTP) Coding & Protocols

## Injury Classification
- Use FIFA 11+ categories:
  - Soft-tissue: hamstring, quadriceps, calf, groin, hip
  - Joint: ankle sprain, knee sprain, shoulder
  - Overuse: stress fracture, tendinopathy
  - Illness: respiratory, gastrointestinal
- Severity codes:
  - MINOR (1–3 days lost)
  - MODERATE (4–7 days)
  - MAJOR (8–28 days)
  - LONG_TERM (>28 days)

## RTP Phases
1. **Phase 0 – Diagnosis**
   - Medical assessment, imaging if required.
2. **Phase 1 – Controlled Rehab**
   - Individual PT work, no team drills.
   - Load capped at 40% of baseline.
3. **Phase 2 – Partial Return**
   - Non-contact team training, limited minutes.
   - Load target 60–80% baseline.
4. **Phase 3 – Full Return**
   - Full participation, monitor for 14 days.

## Coding
- `injury_events` table:
  - `injury_id`, `athlete_id`, `tenant_id`
  - `injury_type`, `body_region`, `severity`, `injury_date`
  - `diagnosis_notes`, `treatment_plan`
- `rtp_progress` table:
  - `entry_id`, `injury_id`
  - `phase`, `start_date`, `end_date`
  - `clearance_by` (medical staff)

## Alerts & Overrides
- Phase transitions require clearance from medical staff role.
- Automatic red alert if load plan exceeds phase threshold.
- Combine RTP phase with wellness to adjust readiness scores.

## Documentation
- Medical staff must upload clearance note per phase.
- Audit trail of edits required (tie into audit logging).
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

