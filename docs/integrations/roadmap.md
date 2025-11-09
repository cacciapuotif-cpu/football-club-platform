# Integrations Roadmap

## Vendors & Priorities
1. **Hudl** (Sessions + Video Tagging)
   - Phase: MVP
   - Contract: `/docs/data/contracts/hudl.yaml`
   - Auth: OAuth2 client credentials
   - Notes: Requires DPA + youth consent handling; daily session sync.
2. **Wyscout** (Match Analytics)
   - Phase: Phase 2
   - Contract: `/docs/data/contracts/wyscout.yaml`
   - Auth: API key
   - Notes: Post-match events, map to internal session IDs.
3. **GPS Provider (Catapult/Playermaker)** (Load Metrics)
   - Phase: MVP (if hardware already deployed)
   - Contract: `/docs/data/contracts/gps.yaml`
   - Auth: OAuth2 client credentials
   - Notes: Hourly load ingestion for readiness features.

## Timeline (Indicative)
- **Weeks 1–4**: finalize contracts, legal review, test sandbox credentials.
- **Weeks 5–8**: implement connectors, mock ingestion, validate GE suites.
- **Weeks 9–12**: production integration, monitoring, rate-limiting guardrails.

## Authentication & Secrets
- All vendor credentials stored in secrets manager (no plain .env in production).
- Rotate keys every 90 days or per vendor contract.

## Quotas & Monitoring
- Hudl: 1000 calls/day (apply pre-ingest caching to avoid chokepoints).
- Wyscout: 5000 calls/day; throttle to respect fairness.
- GPS: 500 requests/hour; degrade gracefully if exceeding quota.

## Dependencies
- Consent framework (parental).
- Tokenization strategy (IDs exchanged must map via token vault).
- Compliance review before go-live (DPO).

