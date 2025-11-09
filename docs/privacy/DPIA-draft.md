# DPIA Draft — Football Club Platform (Youth Players)

## Overview
- **Controller**: Football Club Platform operator (club)
- **Processors**: Hosting provider, ML ops platform, integration vendors (Hudl, Wyscout, GPS)
- **Data Subjects**: Youth players (minors), staff
- **Purpose**: Monitor health, performance, wellness, injury risk; operational recommendations

## Data Inventory
- Identification: player_id (UUID), tokenized_identifiers, minimal PII (name, team)
- Special categories (Art. 9): wellness, psychometric, injury/medical data
- Derived data: readiness scores, SHAP explainability, prescriptions
- Video analytics metadata

## Legal Bases
- Art. 6(1)(a) consent for minors (parental/guardian) – wellness, psychometrics
- Art. 6(1)(f) legitimate interest (coaching decisions) with balancing test
- Art. 9(2)(a) explicit consent, Art. 9(2)(h) medical diagnosis/management

## Necessity & Proportionality
- Data minimization: only fields needed for readiness calculation
- Pseudonymization: tokenized IDs, separation of keys in secure vault
- Access control: RBAC, least privilege
- Retention aligned with sports federation guidelines (max 5 years, adjustable via retention policy)

## Risk Assessment
- **Confidentiality**: Unauthorized access to minors’ wellness/medical data → high risk
- **Integrity**: Wrong recommendations due to tampered data → medium risk
- **Availability**: Platform downtime causing missed injury warnings → medium risk
- **Compliance**: Non-compliant cross-border transfers → medium risk

## Mitigations
- Encryption in transit (TLS) & at rest (database encryption)
- Pseudonymization/tokenization; token vault isolated
- Consent management UI, audit trail, parental dashboards
- Vendor due diligence (DPA, Standard Contractual Clauses for non-EU transfers)
- Incident response plan (notify DPO ~72 hours)

## Data Subject Rights
- Access, rectification, erasure (subject to legal obligations)
- Consent withdrawal via guardian portal
- Objection to profiling (must respect and degrade to manual review)

## Residual Risk & Decision
- Residual risk: medium (acceptable with controls)
- Next steps: finalize full DPIA, involve DPO, document in release checklist

