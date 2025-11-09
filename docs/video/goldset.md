# Video Gold-Set Specification

## Purpose
- Maintain high-quality reference dataset for model benchmarking and analyst training.

## Composition
- 20 sessions per tenant (mix of training, match, recovery).
- Include:
  - ≥5 high-load sessions
  - ≥5 low-load sessions
  - ≥5 sessions with injuries/alerts
  - ≥5 recovery-focused sessions
- Ensure representation of all teams (U17, U18) and genders if applicable.

## Annotation Requirements
- Dual-review: two analysts annotate, consensus resolution.
- Capture:
  - Event type, start/end, athletes, intensity tag, outcome.
  - Flag correlation with wellness alerts (Yes/No).
- Store in `/data/video/goldset/` as Parquet + JSON manifest.

## Refresh Cadence
- Quarterly review; add new sessions, retire outdated ones.
- Maintain change log in `data/video/goldset/CHANGELOG.md`.

## Access Control
- Restricted to analysts, data science, medical leads.
- Audit access via logging middleware (tenant-aware).
# Video Gold-Set Specification

## Purpose
- Provide benchmark dataset for model evaluation and analyst training.

## Composition
- 20 matches across two tenants.
- 200 tagged clips per match (balanced across event types).
- Include injury/pre-injury clips (minimum 30).
- Metadata: tenant_id, match_id, athlete_id, event_type, outcome, timestamp.

## Storage
- Store in `data/video/goldset/`.
- Maintain manifest (`manifest.json`) listing files, checksums, permissions.

## Validation
- Run checksum verification before release.
- Validate tagging coverage (≥95 % of high-intensity events tagged).

## Access Control
- Limited to analysts and medical roles.
- Audit downloads via logging pipeline.

