# Psychometric Assessment Plan

## Scales & Instruments
- **Hooper Index** (sleep, stress, fatigue, muscle soreness; 1–7 Likert)
- **Short Mood Scale** (5 items, 1–5)
- **Wellbeing Questionnaire** weekly (survey app)

## Frequency
- Daily micro-survey (sleep, mood, soreness, stress)
- Weekly deeper questionnaire (Hooper + energy/motivation)
- Monthly mental health check-in (psychologist)

## Privacy-by-Default Rules
- For minors, results shown only to authorized staff (Medical, Psych) with consent status “granted”.
- If consent revoked:
  - Store only aggregated/trend info (anonymized) for risk modeling.
  - Hide raw responses in UI.

## Alerting
- If daily score drops ≥3 points from baseline for two consecutive days → amber alert.
- If Hooper total > 20 → escalate to medical/psych staff.
- Combine with load metrics to adjust readiness.

## Data Handling
- Raw responses stored in `psychometrics` table with pseudonymized `tokenized_identifier`.
- Retention: purge raw responses after 3 years; keep anonymized trends for 5 years.
- Access logs required for each view/download event.
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

