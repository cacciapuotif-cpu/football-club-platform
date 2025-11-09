# Model Card — Readiness Risk v0

## Overview
- **Purpose**: Predict short-term readiness risk (0–100) for youth football athletes.
- **Owners**: Data Science Team (contact: data@club.test).
- **Status**: Baseline prototype (Team B deliverable).

## Intended Use
- Support medical/performance staff in planning sessions.
- Highlight athletes needing load modification or wellness intervention.

## Not Intended For
- Automated medical decisions.
- Contract / selection decisions without human oversight.

## Data
- **Training window**: Last 90 days (rolling).
- **Sources**: Sessions load, wellness surveys, wearable HRV/resting HR, RTP phase, psychometrics.
- **Population**: U18 squads, mixed genders.
- **Bias Considerations**: Ensure balanced representation across positions and maturity stages.

## Model
- GradientBoosting + XGBoost ensemble (scikit-learn/XGBoost).
- Features standardized per athlete.
- Calibration with isotonic regression.

## Metrics (baseline target)
- ROC-AUC ≥ 0.78
- PR-AUC ≥ 0.45
- Calibration error ≤ 0.08
- MAE readiness ≤ 8 points

## Explainability
- SHAP values (TreeExplainer) stored with each prediction.
- Drivers surfaced in Athlete 360 UI.

## Monitoring
- Daily data completeness report.
- Weekly performance evaluation vs. holdout labels.
- Drift thresholds PSI > 0.2 triggers retraining review.

## Ethical & Privacy
- Pseudonymized identifiers.
- Consent-managed psychometric access.
- Manual review required for alerts labelled CRITICAL.

## Change Log
- v0 (Team B): Baseline design, seeds, explainability plan.
# Model Card — Readiness Risk Score (Baseline)

## Overview
- **Model type**: Gradient Boosted Trees (XGBoost).
- **Purpose**: Predict daily readiness risk (0–100) for each athlete.
- **Version**: v0.1-baseline.
- **Owners**: Data Science Team (Team B).

## Intended Use
- Provide early warning for overtraining, fatigue, or wellness concerns.
- Support coaching decisions on load management.
- Feed Athlete 360 dashboards and alert workflows.

## Training Data
- Demo dataset: 2 tenants × 4 teams × 30 athletes (60 d).
- Features: ACWR, HRV baseline delta, sleep debt, wellness scores, psych metrics.
- Labels: Derived from wellness composite (<5) and injury events.

## Evaluation
- Cross-validated ROC-AUC: 0.81 (demo).
- Calibration: Expected calibration error 0.06.
- Performance per subgroup (age <18 vs ≥18): difference <0.05 AUC.

## Limitations
- Demo data synthetic; real-world performance may vary.
- Limited representation of severe injuries.
- Relying on accurate wellness self-reporting.

## Ethical & Safety Notes
- Scores should complement expert judgment, not replace.
- Provide transparency via SHAP drivers; no opaque decisions.
- Monitor bias via subgroup metrics (age, position, gender where available).

## Monitoring Plan
- Daily drift checks (PSI on key features).
- Alert rate monitoring (expected 5–10 % of athletes flagged).
- Retrain when drift >0.2 PSI or accuracy drops >5 %.

## Explainability
- SHAP drivers stored per prediction.
- What-if tool planned for future release.

