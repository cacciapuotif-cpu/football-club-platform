# Data Retention Policy

| Data Category | Retention Period | Notes |
| --- | --- | --- |
| Player Wellness/Psychometrics | 5 years from capture or 2 years after player leaves program (whichever earlier) | Masked when consent revoked. |
| Session Load/GPS | 5 years | Aggregated statistics kept, granular data purged after retention window. |
| Medical/Injury Logs | 7 years | In line with medical obligations; pseudonymized after 3 years. |
| Video Analytics | 3 years | Clips tokenized; delete raw footage 30 days after tagging unless legal hold. |
| Consents & Audit Logs | 10 years | Proof for compliance. |

## Implementation Notes
- Scheduled purge job (Team 3) must enforce retention flags.
- Reports exported externally must inherit same retention rules.

