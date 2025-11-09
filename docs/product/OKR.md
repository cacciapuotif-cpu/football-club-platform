# Product OKR & Roadmap — Football Club Platform

## North-Star Objective (Q1)
Build a trusted, explainable performance & wellness platform for youth players that gives staff timely decisions on readiness, risk, and compliance by the end of the quarter.

### Key Results (Outcomes, not outputs)
1. **Decision Adoption**: ≥80 % of coaching/medical staff report weekly use of the player readiness dashboard and follow ≥2 recommended actions per sprint retrospective.
2. **Alert Precision**: Injury/overload alerts achieve ≥75 % precision and ≤10 % false positives on the demo dataset and first external pilot, backed by Team 2 validation.
3. **Compliance Assurance**: 100 % of minors’ records have consents, pseudonymization, retention flags, and audit trails verified by legal/DPO sign-off before release.

## 12-Week Roadmap (3 × 4-week increments)

| Period | Theme | Outcomes |
| --- | --- | --- |
| Weeks 1–4 | **Foundations & Compliance** | Team 1 specs, GDPR pack, unified data contracts; demo seed baseline with ≥10 players × 10 sessions × 90-day history defined. |
| Weeks 5–8 | **Scientific Validation** | Team 2 thresholds, dbt/GE suites, ML readiness stub with SHAP validated, demo data passes QA; integration contracts validated. |
| Weeks 9–12 | **Implementation & Delivery** | Team 3 UI/API fully implemented, CI+k6 green, release gate passed, demo scenario ready for stakeholders. |

## Capability Priorities
1. **Player Dashboard (Must)** – longitudinal view, risk timelines, explainability, recommendations.
2. **Wellness & Sessions** – Staff need separate drill-downs but unified insights (decision: keep as separate pages, see Decision Log).
3. **Risk & Recommendations** – Explainable inference with 7/14/28 day outlook + safe “what-if” adjustments.
4. **Reports** – Weekly PDF/export with insights and compliance notes.

### Decision Log Snippet
- **Topic**: Wellness vs Sessions page structure  
  **Decision**: Maintain separate pages (`/wellness`, `/sessions`) with cross-links and shared data contracts; acceptance criteria include synchronous filters, 90-day coverage, threshold badges.  
  **Rationale**: Different users (S&C vs Staff Medico) need focused views; unification risks clutter. Documented fully in `/docs/product/DECISION-LOG.md`.

