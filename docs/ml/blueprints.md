# Sessions & Wellness ML Blueprints

## Objectives
- **Primary**: Predict athlete readiness risk (0–100 risk score).
- **Secondary**: Flag sessions requiring medical review, recommend load adjustments.

## Targets
- Binary risk label derived from medical incidents / alerts next 7 days.
- Regression target (readiness score) scaled 0–100.
- Multi-task approach: logistic (risk) + regression (readiness).

## Features
- Acute/Chronic load (`acr_7_28`, `session_load_3d`, `session_count_7d`).
- Wellness metrics (sleep, fatigue, soreness, mood).
- Physiological (HRV baseline, resting HR delta).
- Contextual:
  - Travel distance last 7 days.
  - Match minutes & opposition strength.
  - RTP phase.
- Psychological: mood z-score, psychometric responses.

## Data Hygiene
- Leakage guard:
  - Only use data prior to prediction timestamp.
  - Remove post-event medical notes.
- Imputation:
  - Forward fill up to 2 days.
  - Median per athlete for longer gaps.
- Scaling:
  - RobustScaler for load metrics.
  - StandardScaler for z-scores.

## Model Stack
- Baseline: Logistic Regression + Gradient Boosting (scikit-learn).
- Advanced: XGBoost with monotonic constraints.
- Calibrate with isotonic regression.
- Ensemble average (weighted 0.6 XGBoost, 0.4 GradientBoosting).

## Explainability
- Use SHAP TreeExplainer for XGBoost.
- Persist top 5 drivers per prediction.
- Provide “what-if” table adjusting load/sleep deltas ±10%.

## Operational Plan
- Training cadence: weekly batch job (Sunday 22:00 CET).
- Evaluation metrics:
  - ROC-AUC (target ≥0.78)
  - PR-AUC
  - Brier score
  - Calibration curve
- Drift monitoring:
  - PSI on key features monthly.
  - Alert if PSI > 0.2.

## Deployment
- Register models in MLflow (staging/production).
- Promote via CI after tests + evaluation thresholds.
- Serve with FastAPI inference service (Team B deliverable).
# Readiness Risk Modeling Blueprint

## 1. Problem Definition
- Objective: Predict readiness risk score (0–100) per athlete per day.
- Target variable: inverse wellness readiness (higher = higher risk).
- Use cases: drive alerts, prioritize interventions, power Athlete 360 dashboards.

## 2. Data Inputs
- Sessions load metrics (ACWR, RPE, session count).
- Wellness surveys (sleep, soreness, mood, stress).
- HR/HRV features (baseline vs acute).
- Sleep duration/debt metrics.
- Injury status & RTP stage (exclude Rehab from training risk).
- Behavioral/test data (psychometrics, CMJ).

## 3. Feature Engineering
- Rolling windows (7, 14, 28 d) with exponential smoothing.
- Normalization: z-scores vs athlete baseline (28 d).
- Leakage controls:
  - Use only data up to prediction timestamp.
  - For future events (e.g., injuries), shift labels 1 day forward.

## 4. Model Candidates
- Gradient Boosted Trees (XGBoost) baseline.
- Logistic regression for interpretable baseline.
- Future: Time-series transformer with rolling forecast.

## 5. Training Strategy
- Train per tenant with global warm start (transfer learning).
- Cross-validation: grouped by athlete to prevent leakage.
- Metrics: ROC-AUC, PR-AUC, calibration error, Brier score.

## 6. Explainability
- SHAP TreeExplainer for XGBoost.
- Store top 3 drivers per prediction in `predictions.drivers`.
- Provide “what-if” analysis: recompute prediction with adjusted load/sleep.

## 7. Prescriptive Layer
- Rules engine:
  - ACWR >1.5 → recommendation “deload”.
  - Sleep debt >6 h over 7 d → “sleep intervention”.
  - Psych score drop >20 % → “psych consult”.
- Attach to alerts table as `recommendations` JSON (future extension).

## 8. Deployment Plan
- Batch scoring daily at 06:00 local time.
- Near real-time option triggered post-session ingest.
- Model registry in MLflow; stage `Staging` → `Production` on QA approval.
- Canary release per tenant (10 % sample) before full rollout.

