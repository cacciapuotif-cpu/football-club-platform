## UX Flows — Player Monitoring & Decision Support

### 1. Player Overview (Coach / Medical Staff)
1. Global navigation → “Players” list.
2. Select athlete → Player Detail page:
   - Summary card: readiness score (7/14/28-day), latest alert status, consent flag.
   - Tabs: Overview (summary), Wellness, Sessions, Tests, Recommendations.

Acceptance Criteria:
- Overview tab must show last 7 days readings, upcoming prescriptions, compliance icons.
- From Overview, deep links to `/wellness` and `/sessions`.

### 2. Wellness Flow (Psych / Medical)
1. From Player detail → “Wellness” tab (`/wellness` page).
2. Select date range (default 90 days).
3. View charts: subjective wellness, sleep, soreness, mood.
4. Alerts panel: highlight breaches, explanation (SHAP snippet describing feature contribution).
5. What-if prompt: “Adjust rest day plan” → propose safe adjustments.

Acceptance Criteria:
- Charts support zoom/pan, thresholds, baseline bands per Team 2 thresholds.
- Alerts include severity, recommended action, compliance consent tags.
- If consent is revoked, hide detailed fields and show anonymized token.

### 3. Sessions Flow (Coach / S&C)
1. From Player detail → “Sessions” tab (`/sessions` page).
2. View calendar/list with filters (session type, intensity).
3. Select session → detail modal/page with load metrics, attendance, GPS info.
4. Compare planned vs actual load; readiness score overlay.

Acceptance Criteria:
- 90-day trendline of cumulative load vs target.
- Session detail includes recommended modifications (e.g., lighten load if high risk).
- Quick switch to team-level view (Team 2 contract, aggregated queries).

### 4. Thresholds & Alerts (Expert Mode)
1. Access Alerts board (global navigation) or Alerts section inside player detail.
2. Filter by severity, role, alert type (injury risk, workload, psych).
3. Inspect alert detail with SHAP explanation, historical context, compliance note.

Acceptance Criteria:
- Each alert shows reason (top 3 features with contributions).
- Provides action log: last actions taken, responsible staff.
- Respect RBAC: viewer role sees masked data.

### 5. Explainability & What-if
1. From readiness card → “Explain” to view SHAP summary breakdown.
2. “What-if” toggle: adjust parameters (e.g., reduce load tomorrow) within safe bounds.
3. System shows predicted change in readiness and recommended plan.

Acceptance Criteria:
- Inputs bounded by Team 2 prescriptions rules.
- Display disclaimer that adjustments must be medically approved.
- Log scenario in audit trail.

### 6. Reports & Export
1. From player or team, click “Generate Report”.
2. Choose period (week/month) and recipients.
3. Report includes summary metrics, alerts, wellness/sessions highlights, compliance statements.

Acceptance Criteria:
- Report generation logs in audit, respects consent.
- Export available in PDF/CSV (future phases) with pseudonymization.

### Navigation Summary
- Global nav: Players, Wellness, Sessions, Alerts, Reports, Admin (RBAC).
- Player Quick Actions: Send recommendation, log medical note, adjust plan.

### Accessibility & Internationalization
- Ensure keyboard navigation, screen-reader labels.
- Localize to Italian/English; date/time in local timezone (Europe/Rome).

### Hand-off Notes
- UI wireframes per flow attached in design system (tracked separately).
- Team 3 must adhere to contracts defined in `/docs/data/contracts/*.yaml`.

