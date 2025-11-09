# Psychometrics & Wellness Protocol

## Scales & Frequency
- **Wellness Survey (1–10 scale)**: daily, covering sleep, soreness, stress, mood.
- **Commitment/Motivation Scale**: weekly, 5-point Likert.
- **Psych Watchlist**: flag if combined wellness score <4 for 3 days OR commitment drops by ≥20 %.

## Administration
- Delivered via mobile app; responses stored per contract `/docs/data/contracts/wellness.yaml`.
- Reminders at 08:00 local time; cutoff at 18:00.
- Guardian consent required; results masked for viewer role.

## Interpretation
- Combine with load data to contextualize risk.
- Provide “Action prompts” to staff (check-in, rest recommendations).
- Escalate severe cases to sport psychologist with audit trail.

## Privacy Guardrails
- Store psychometrics with pseudonymized identifiers.
- Access limited to Staff Medico/Psych (RBAC).
- Retention: 5 years or until program exit (see retention policy).

