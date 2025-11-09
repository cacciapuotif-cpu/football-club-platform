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

