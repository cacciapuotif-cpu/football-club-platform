# Parental Consent Framework

## Consent Types
- **Performance & Wellness Monitoring** (Art. 6(1)(a) + Art. 9(2)(a))  
  Scope: wellness surveys, psychometrics, readiness scores.
- **Video & GPS Analytics** (Art. 6(1)(a))  
  Scope: tagged footage, GPS load metrics.
- **Medical Recommendations** (Art. 9(2)(h))  
  Scope: injury logs, return-to-play protocols.

## Collection Process
1. Guardian registration in club portal.
2. Provide consent form per category, with granular opt-in/out.
3. Record timestamp, IP, and tokenized guardian ID.

## Revocation & Updates
- Guardians can revoke consent at any time.
- Revocation triggers masking/purging workflows within 7 days.
- Audit logs capture revocation details.

## Record Keeping
- Store signed digital consent (PDF/JSON) with hash for integrity.
- Link consent status to `consent_status` field in data contracts.
- Retention: keep records until player turns 21 + 2 years.

