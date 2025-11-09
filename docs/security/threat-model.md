# Threat Model v1 — Football Club Platform

## Scope
- FastAPI backend, Next.js frontend
- PostgreSQL + Redis infrastructure
- External integrations (Hudl, Wyscout, GPS vendors)
- ML readiness inference stub
- Data: minors’ performance, wellness, medical notes

## Architecture Summary
- Client (Next.js) → API Gateway (FastAPI) → Postgres/Redis/ML services
- Background jobs for ingestion and alerting
- External integrations via secured connectors

## Assets
1. Player PII + wellness/medical data (high sensitivity)
2. Credentials (JWT secrets, vendor API keys)
3. Model artifacts (risk predictions, SHAP explanations)
4. Audit logs & consents

## Adversaries & Motivation
- External attackers seeking PII/medical info (GDPR fines)
- Insider misuse (unauthorized staff access)
- Vendor compromise causing tampered data
- Availability attacks (DoS) impacting decision support

## Threat Enumeration (STRIDE)

### Spoofing
- Fake JWT tokens → unauthorized API access  
  *Mitigation*: JWT signed with strong secret, RBAC enforced, audience checks.
- Vendor data spoofing  
  *Mitigation*: Validate signatures / API keys, ingest integrity checks.

### Tampering
- API payload manipulation  
  *Mitigation*: Input validation, hashing of audit logs, row-level security.
- Model artifact tampering  
  *Mitigation*: Store models with checksums, MLflow versioning.

### Repudiation
- Users deny actions (e.g., altering recommendations)  
  *Mitigation*: Audit logs (append-only), correlation IDs, signed reports.

### Information Disclosure
- Exposed wellness/medical data  
  *Mitigation*: Pseudonymization, consent flags, RBAC, TLS, field-level masking.
- Misconfigured S3/MinIO buckets  
  *Mitigation*: Private buckets, signed URLs, secrets vault-managed.

### Denial of Service
- API overload (k6-tested but still risk)  
  *Mitigation*: Rate limiting (SlowAPI), autoscaling (future), monitoring.
- DB saturation  
  *Mitigation*: Connection pooling, alerts, read replicas (future consideration).

### Elevation of Privilege
- Compromised viewer turning into admin  
  *Mitigation*: Strict RBAC, separation of roles, least privilege, secrets rotation.

## Secrets Management Policy
- Store secrets (JWT_SECRET, vendor keys) in .env only for dev; production uses vault/secret manager.
- Rotation policy: every 90 days or upon incident.
- Access limited to DevOps/security.

## RBAC Roles
- **Coach**: Read/write player plans, read wellness/sessions; limited access to psychometrics.
- **Staff Medico**: Full medical data, can log injuries/prescriptions.
- **Direzione**: Read aggregated insights, limited individual details.
- **Viewer**: Masked/pseudonymized data only.
- System role for integrations (no UI access).

## Residual Risks & Mitigations
- Vendor breach → Data pollution  
  *Follow-up*: Team 2 validation, anomaly detection.
- Manual processes for consent revocation  
  *Follow-up*: Build automated revocation workflow in Team 3.

## References
- Compliance artifacts in `/docs/privacy/*`
- Integrations roadmap `/docs/integrations/roadmap.md`

