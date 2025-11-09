## Decision Log — Wellness vs Sessions Feature Structure

**Date**: 2025‑11‑09  
**Team**: Team 1 – Product & Delivery  
**Participants**: Head of Product, Program Manager, UX Lead, Security/Privacy Lead, Technical Writer  

### Context
The platform must expose both wellness (subjective wellness, psychometrics) and sessions (objective load, attendance, GPS) data for youth players, with specific compliance needs for minors. Team 1 must decide whether to unify these views or maintain separate pages to guide the downstream teams.

### Decision
Maintain **two dedicated sections**:
- `/wellness`: focus on wellness entries, subjective ratings, psychometrics, and compliance badges.
- `/sessions`: focus on training/match sessions, RPE, load metrics, GPS insights.

Both pages will surface cross-linked highlights and share risk indicators from the readiness model, but the primary navigation remains separate.

### Rationale
1. **User Roles**: Coaching staff, S&C, and medical staff consume sessions data differently from wellness/psych profiles. Distinct surfaces prevent overload and support role-based layouts decided by Team 1.
2. **Compliance & Consent**: Wellness/Psychometric data has tighter consent/retention requirements (GDPR Art. 9). Keeping it distinct simplifies privacy disclosures and access control.
3. **Data Contract Alignment**: Team 1 contracts specify separate SLAs and data cadence per source (wellness survey vs session tracking). Unification would increase coupling and complexity for Team 2’s pipelines.
4. **UX Flow**: Player journey expects quick toggles between load vs subjective data. Dedicated tabs with shared summary cards provide clarity without overwhelming a single page.

### Acceptance Criteria (for Teams 2 & 3)
- `/wellness` displays 90‑day longitudinal charts of subjective scores, psychometrics, and alert thresholds; includes consent status and retention indicators.
- `/sessions` displays 90‑day load trends, attendance, session intensity, and cross-link to session detail.
- Both pages expose readiness risk (7/14/28 days) and SHAP explanations consistently, but UI components are tuned for the context (e.g., wellness shows mental/physical wellbeing; sessions shows load vs planned).
- Cross-navigation: quick access between pages (e.g., “View latest session load” on wellness page).
- Data/API acceptance: endpoints must support per-section filters and team-athlete scopes as defined in data contracts.

### Impact on Downstream Teams
- **Team 2**: Schemas, dbt/GE suites, and demo seeds will maintain separate models/tables for wellness vs sessions but share keys for readiness features.
- **Team 3**: Frontend pages and API controllers must match this separation, applying RBAC and compliance controls specific to each domain.

### Follow-up Actions
- UX flows updated in `/docs/ux/flows.md` to reflect the navigation.
- Data contracts in `/docs/data/contracts/wellness.yaml` and `sessions.yaml` reference this decision.
- Compliance pack to highlight additional safeguards for wellness data access.

