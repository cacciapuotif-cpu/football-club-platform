# Performance & Wellness Threshold Framework

## Load Metrics
- **Session RPE x Duration (sRPE)**  
  - Baseline per role/age:
    - GK: 250–400 AU/session
    - DF: 300–500 AU/session
    - MF: 350–550 AU/session
    - FW: 320–520 AU/session
  - Alert thresholds:
    - High acute load: > 120% of rolling 7-day average
    - Low load: < 60% of planned weekly target

- **Acute:Chronic Workload Ratio (ACWR)**  
  - Safe band: 0.8 – 1.3
  - Watch band: 1.31 – 1.50 → flag amber
  - Danger band: > 1.50 or < 0.7 → flag red

## Wellness Metrics (Self-Reported)
- Subjective wellness score (1–10):
  - Green: ≥7
  - Amber: 5–6
  - Red: ≤4
- Sleep Hours:
  - Age 15–17: target 8–10 h, red if <7 h 2 consecutive days.
- Soreness/Stress/Mood (1–10):
  - Alert if drop ≥3 points from personal baseline.

## Tests & Screens
- CMJ (Countermovement Jump):
  - Age 15–17: 35–45 cm expected; drop >10% from baseline triggers check.
- YoYo IR2:
  - Age 16–17 MF: 1000+ m high; <800 m red.
- VO2max estimates:
  - Age 15–17: 52–60 ml/kg/min (role dependent); drop >5 ml/kg/min flagged.

## Psychometrics
- Mood (Likert 1–5 or 1–10):
  - Consistent scores ≤3 for 3 days triggers psych review.
- Readiness questionnaires:
  - If total score <60% of baseline → escalate.

## Injury & RTP
- Medical coding aligned to FIFA 11+ categories.
- RTP phases:  
  - Phase 0: Diagnosis  
  - Phase 1: Controlled training  
  - Phase 2: Partial return  
  - Phase 3: Full return  
  - Automatic alerts if load > planned in Phase 2.

## Alert Logic Summary
- Combine load violations + wellness red flags → High priority alert.
- Combine psych drop + high ACWR → medium priority, requires check.
- Use readiness score from ML to adjust thresholds ±10%.
# Scientific Thresholds & Protocols — Football Club Platform

## 1. Load & RPE Thresholds
### Acute:Chronic Workload Ratio (ACWR)
- Window: 7-day acute vs 28-day chronic load.
- Alert thresholds:
  - **High Risk**: ACWR > 1.5 (trigger overload alert).
  - **Moderate Risk**: 1.2 < ACWR ≤ 1.5 (monitor, recommend reduced load).
  - **Low Risk**: 0.8 ≤ ACWR ≤ 1.2 (optimal).
  - **Undercooked**: ACWR < 0.8 (consider ramp-up recommendations).
- Load units from Team 1 data contract (`sessions.yaml`, `actual_load`).

### RPE (Rate of Perceived Exertion)
- Scale 1–10.
- Daily check-in; alert if >8 for 3 consecutive days OR spike ≥2 points vs baseline.
- Age adjustment: players <16 flagged faster (lower tolerance).

## 2. Wellness Survey Thresholds
- Fields: sleep quality, soreness, stress, mood (1–10 scale).
- Rolling baseline: 14-day moving average.
- Alert when any metric deviates by ≥2 points below baseline for two consecutive entries.
- Composite wellness score = weighted average (sleep 30 %, soreness 30 %, stress 20 %, mood 20 %).
  - Thresholds:
    - <6 → amber alert (check-in).
    - <4 → red alert (medical review).

## 3. Psychometrics
- Team commitment scale (Likert): alert if drop of ≥20 % from baseline.
- Frequency: weekly for senior squads; bi-weekly for younger age groups.
- Privacy: results masked to viewer role; medical staff receives full view.

## 4. Testing Batteries
| Test | Frequency | Thresholds | Notes |
| --- | --- | --- | --- |
| CMJ (cm) | Monthly | Drop >10 % vs baseline triggers neuromuscular fatigue alert. | Compare to age/role percentiles. |
| Yo-Yo IR2 (m) | Quarterly | Percentile <25 % for role triggers conditioning block. | Use percentile to adjust training plan. |
| Sprint 30 m (s) | Quarterly | Degradation >5 % triggers sprint mechanics session. | |

## 5. Injury Coding & RTP
- Injury classification: FIFA 11+ categories (e.g., muscle strain, ligament tear).
- RTP stages: Full, Modified, Rehab (documented in `/docs/medical/coding-RTP.md`).
- Exclusion criteria: remove from readiness calculation when injury status != Full.

## 6. Alert Logic Summary
- Combine load (ACWR), wellness, psychometrics, test thresholds.
- Alert severity matrix:
  - **Red**: Any red-level threshold OR combination of two amber alerts.
  - **Amber**: Single amber threshold.
  - **Green**: No thresholds triggered.
- All alerts require SHAP explanation referencing top contributing features.

## 7. Role/Age Adjustments
- Younger players (U15-U17) have lower tolerance: reduce load thresholds by 10 %, tighten wellness thresholds.
- Position codes (from Team 1 contracts):
  - GK → focus on reaction drills, moderate load adjustments.
  - DF/MF/FW → apply general thresholds described above.

