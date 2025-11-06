# API Usage Guide - Player Progress Tracking

This guide covers the new EAV (Entity-Attribute-Value) endpoints for flexible player progress tracking.

## Table of Contents

- [Overview](#overview)
- [Progress Endpoints](#progress-endpoints)
- [Training Load Endpoints](#training-load-endpoints)
- [ML Prediction Endpoints](#ml-prediction-endpoints)
- [Training Attendance Batch Upload](#training-attendance-batch-upload)
- [Examples](#examples)

---

## Overview

The new EAV architecture allows flexible metric storage without schema changes. Key features:

- **Wellness metrics**: Sleep, stress, fatigue, DOMS, mood, etc.
- **Training metrics**: RPE, HSR, distance, accelerations, HR, etc.
- **Match metrics**: Pass accuracy, sprints, duels, touches, etc.
- **Flexible aggregations**: Day/week/month bucketing
- **ACWR calculation**: Acute:Chronic Workload Ratio
- **ML predictions**: Injury risk with SHAP-like explanations

---

## Progress Endpoints

### 1. Get Player Progress (Time-series)

**Endpoint**: `GET /api/v1/players/{player_id}/progress`

**Query Parameters**:
- `from` (required): Start date (YYYY-MM-DD)
- `to` (required): End date (YYYY-MM-DD)
- `metrics` (required): Comma-separated metric keys (e.g., `stress,doms,sleep_quality`)
- `groupby` (optional): Bucketing granularity - `day`, `week`, or `month` (default: `week`)

**Response**:
```json
[
  {
    "bucket": "2025-01-06",
    "metric_key": "sleep_quality",
    "avg_value": 7.2,
    "min_value": 6.0,
    "max_value": 8.5,
    "count": 7
  },
  {
    "bucket": "2025-01-06",
    "metric_key": "stress",
    "avg_value": 4.5,
    "min_value": 3.0,
    "max_value": 6.0,
    "count": 7
  }
]
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/players/{player_id}/progress?from=2025-01-01&to=2025-03-31&metrics=sleep_quality,stress,fatigue,doms&groupby=week"
```

---

### 2. Get Player Overview (KPIs)

**Endpoint**: `GET /api/v1/players/{player_id}/overview`

**Query Parameters**:
- `period` (optional): Time period - `7d`, `30d`, `90d`, or `season` (default: `30d`)
- `metrics` (optional): List of metrics to summarize (default: sleep_quality, stress, fatigue, doms, mood)

**Response**:
```json
{
  "player_id": "uuid",
  "period_days": 30,
  "wellness_entries": 28,
  "training_sessions": 12,
  "matches": 4,
  "wellness_completeness_pct": 93.3,
  "training_completeness_pct": 100.0,
  "metric_summaries": [
    {
      "metric_key": "sleep_quality",
      "current_value": 7.5,
      "avg_value": 7.2,
      "trend_pct": 5.8,
      "variance": 0.8,
      "min_value": 6.0,
      "max_value": 8.5,
      "completeness_pct": 93.3
    }
  ],
  "data_quality_issues": 2
}
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/players/{player_id}/overview?period=30d&metrics=sleep_quality,stress,fatigue"
```

---

## Training Load Endpoints

### 3. Get Training Load (sRPE & ACWR)

**Endpoint**: `GET /api/v1/players/{player_id}/training-load`

**Query Parameters**:
- `from` (required): Start date (YYYY-MM-DD)
- `to` (required): End date (YYYY-MM-DD)

**Response**:
```json
[
  {
    "date": "2025-01-15",
    "minutes": 75.0,
    "rpe_post": 6.0,
    "hsr": 450.0,
    "total_distance": 6.5,
    "srpe": 450.0,
    "acute_7d": 420.0,
    "chronic_28d": 380.0,
    "acwr_7_28": 1.11
  }
]
```

**ACWR Interpretation**:
- **< 0.8**: Low load (detraining risk)
- **0.8 - 1.3**: Optimal range (sweet spot)
- **> 1.5**: High spike (injury risk)

**Example**:
```bash
curl "http://localhost:8000/api/v1/players/{player_id}/training-load?from=2025-01-01&to=2025-03-31"
```

---

## ML Prediction Endpoints

### 4. Predict Injury Risk

**Endpoint**: `POST /api/v1/progress-ml/players/{player_id}/predict-risk`

**Response**:
```json
{
  "player_id": "uuid",
  "prediction_date": "2025-01-20",
  "risk_score": 0.42,
  "risk_level": "Medium",
  "top_features": [
    {
      "feature_name": "acwr_7_28",
      "value": 1.6,
      "contribution": 0.18
    },
    {
      "feature_name": "doms_7d",
      "value": 7.2,
      "contribution": 0.12
    },
    {
      "feature_name": "sleep_quality_7d",
      "value": 5.8,
      "contribution": 0.08
    }
  ],
  "recommendations": [
    "⚠️ Reduce training load by 20-30% for 48-72 hours",
    "😴 Improve sleep quality - aim for 8+ hours",
    "💆 Active recovery - massage, stretching, ice bath"
  ]
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/progress-ml/players/{player_id}/predict-risk"
```

---

### 5. Get Performance Trends

**Endpoint**: `GET /api/v1/progress-ml/players/{player_id}/performance-trends`

**Query Parameters**:
- `metrics` (optional): List of metrics (default: sleep_quality, stress, fatigue, doms, mood)

**Response**:
```json
[
  {
    "player_id": "uuid",
    "metric_key": "stress",
    "current_value": 6.5,
    "trend_7d": 15.2,
    "trend_28d": 8.3,
    "zscore": 2.4,
    "anomaly": true
  }
]
```

**Anomaly Detection**: `zscore > 2` indicates significant deviation (potential issue)

**Example**:
```bash
curl "http://localhost:8000/api/v1/progress-ml/players/{player_id}/performance-trends?metrics=sleep_quality,stress,fatigue,doms"
```

---

## Training Attendance Batch Upload

### 6. Batch Upsert Training Attendance

**Endpoint**: `POST /api/v1/training/sessions/{session_id}/attendance:batch-upsert`

**Request Body**:
```json
[
  {
    "player_id": "uuid",
    "status": "present",
    "minutes": 75,
    "participation_pct": 100,
    "rpe_post": 7,
    "metrics": [
      {
        "metric_key": "hsr",
        "metric_value": 650.0,
        "unit": "m"
      },
      {
        "metric_key": "total_distance",
        "metric_value": 7.2,
        "unit": "km"
      },
      {
        "metric_key": "sprint_count",
        "metric_value": 18.0,
        "unit": "#"
      },
      {
        "metric_key": "accel_count",
        "metric_value": 45.0,
        "unit": "#"
      },
      {
        "metric_key": "avg_hr",
        "metric_value": 165.0,
        "unit": "bpm"
      }
    ]
  }
]
```

**Response**:
```json
{
  "training_session_id": "uuid",
  "updated_count": 0,
  "created_count": 1
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/training/sessions/{session_id}/attendance:batch-upsert" \
  -H "Content-Type: application/json" \
  -d '[{"player_id":"uuid","status":"present","minutes":75,"rpe_post":7,"metrics":[{"metric_key":"hsr","metric_value":650,"unit":"m"}]}]'
```

---

## Examples

### Complete Workflow Example

```bash
# 1. Get player overview
curl "http://localhost:8000/api/v1/players/{player_id}/overview?period=30d"

# 2. Get wellness progress (weekly)
curl "http://localhost:8000/api/v1/players/{player_id}/progress?from=2025-01-01&to=2025-03-31&metrics=sleep_quality,stress,fatigue,doms&groupby=week"

# 3. Get training load with ACWR
curl "http://localhost:8000/api/v1/players/{player_id}/training-load?from=2025-01-01&to=2025-03-31"

# 4. Predict injury risk
curl -X POST "http://localhost:8000/api/v1/progress-ml/players/{player_id}/predict-risk"

# 5. Check performance trends
curl "http://localhost:8000/api/v1/progress-ml/players/{player_id}/performance-trends"
```

---

## Metric Catalog

### Wellness Metrics
- `sleep_quality` (1-10): Sleep quality score
- `sleep_hours` (0-24): Hours of sleep
- `stress` (1-10): Stress level (lower is better)
- `fatigue` (1-10): Fatigue level (lower is better)
- `doms` (1-10): Delayed Onset Muscle Soreness (lower is better)
- `mood` (1-10): Mood score (higher is better)
- `motivation` (1-10): Motivation level
- `hydration` (1-10): Hydration status
- `rpe_morning` (1-10): Morning RPE
- `body_weight_kg`: Body weight in kg
- `resting_hr_bpm`: Resting heart rate
- `hrv_ms`: Heart rate variability

### Training Metrics
- `rpe_post` (1-10): Session RPE
- `hsr` (m): High Speed Running distance
- `sprint_count` (#): Number of sprints
- `total_distance` (km): Total distance covered
- `accel_count` (#): Acceleration count
- `decel_count` (#): Deceleration count
- `top_speed` (km/h): Maximum speed
- `avg_hr` (bpm): Average heart rate
- `max_hr` (bpm): Maximum heart rate
- `player_load` (AU): Arbitrary units

### Match Metrics
- `pass_accuracy` (%): Pass completion percentage
- `pass_completed` (#): Passes completed
- `duels_won` (#): Duels won
- `touches` (#): Number of touches
- `dribbles_success` (#): Successful dribbles
- `interceptions` (#): Interceptions
- `tackles` (#): Tackles
- `shots_on_target` (#): Shots on target

---

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid parameters
- **404 Not Found**: Player/session not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

**Error Response Format**:
```json
{
  "detail": "Player not found"
}
```

---

## Rate Limiting

The API has rate limiting configured (check `settings.RATE_LIMIT_PER_MINUTE`).

**Default**: 60 requests/minute per IP

---

## Pagination

For large datasets, consider using date ranges to limit response size.

**Best Practices**:
- Use `groupby=week` or `groupby=month` for long periods
- Request specific metrics rather than all metrics
- Use appropriate date ranges (7d, 30d, 90d)

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/football-club-platform/issues
- Documentation: See `README.md` and `SEEDING_GUIDE.md`

---

## Readiness Index Endpoint

### 7. Get Player Readiness

**Endpoint**: `GET /api/v1/players/{player_id}/readiness`

**Query Parameters**:
- `date_from` (optional): Start date (YYYY-MM-DD, default: 90 days ago)
- `date_to` (optional): End date (YYYY-MM-DD, default: today)

**Response**:
```json
{
  "player_id": "uuid",
  "date_from": "2025-01-01",
  "date_to": "2025-03-31",
  "series": [
    {
      "date": "2025-01-15",
      "readiness": 72.5
    },
    {
      "date": "2025-01-16",
      "readiness": 68.3
    }
  ],
  "latest_value": 68.3,
  "avg_7d": 70.1
}
```

**Readiness Index (0-100)**:
- **0-40**: Low readiness (high fatigue risk)
- **40-60**: Moderate readiness
- **60-80**: Good readiness
- **80-100**: Excellent readiness

**Calculation**: Composite index using z-scores of:
- HRV (positive), Resting HR (negative), Sleep Quality (positive)
- Soreness (negative), Stress (negative), Mood (positive)
- Body Weight (negative, mild)

**Example**:
```bash
curl "http://localhost:8000/api/v1/players/{player_id}/readiness?date_from=2025-01-01&date_to=2025-03-31"
```

---

## Alerts Endpoint

### 8. Get Player Alerts

**Endpoint**: `GET /api/v1/players/{player_id}/alerts`

**Query Parameters**:
- `date_from` (optional): Start date (YYYY-MM-DD, default: 90 days ago)
- `date_to` (optional): End date (YYYY-MM-DD, default: today)

**Response**:
```json
{
  "player_id": "uuid",
  "date_from": "2025-01-01",
  "date_to": "2025-03-31",
  "alerts": [
    {
      "type": "risk_load",
      "metric": "acwr",
      "date": "2025-01-20",
      "value": 1.65,
      "threshold": "> 1.5 (high spike, injury risk)",
      "severity": "error"
    },
    {
      "type": "risk_fatigue",
      "metric": "readiness",
      "date": "2025-02-15",
      "value": 38.5,
      "threshold": "< 40 for 3 days",
      "severity": "error"
    },
    {
      "type": "risk_outlier",
      "metric": "resting_hr_bpm",
      "date": "2025-03-10",
      "value": 75.0,
      "threshold": "|z-score| >= 2.0 (high)",
      "severity": "warning"
    }
  ]
}
```

**Alert Types**:
- **risk_load**: ACWR outside [0.8, 1.5] range
- **risk_fatigue**: Readiness < 40 for 3+ consecutive days
- **risk_outlier**: |z-score| >= 2 for resting_hr_bpm, hrv_ms, soreness, mood

**Severity Levels**:
- **warning**: Moderate risk
- **error**: High risk requiring attention

**Example**:
```bash
curl "http://localhost:8000/api/v1/players/{player_id}/alerts?date_from=2025-01-01&date_to=2025-03-31"
```

---

## Training Load Extended Metrics

### Updated Training Load Response

The `GET /api/v1/players/{player_id}/training-load` endpoint now includes:

**New Fields**:
- `acwr_latest`: Latest ACWR value
- `acwr_series`: Full ACWR time series
- `monotony_weekly`: Weekly Monotony values (mean / std)
- `strain_weekly`: Weekly Strain values (total_load × monotony)

**Example Response**:
```json
{
  "series": [...],
  "window_short": 7,
  "window_long": 28,
  "acwr_latest": 1.12,
  "acwr_series": [
    {"date": "2025-01-15", "value": 1.08},
    {"date": "2025-01-16", "value": 1.12}
  ],
  "monotony_weekly": [
    {"week_start": "2025-01-13", "value": 2.3},
    {"week_start": "2025-01-20", "value": 2.1}
  ],
  "strain_weekly": [
    {"week_start": "2025-01-13", "value": 2100.5},
    {"week_start": "2025-01-20", "value": 1950.2}
  ],
  "flags": [...]
}
```

**Monotony Interpretation**:
- **< 1.5**: Low monotony (good variability)
- **1.5-2.0**: Moderate monotony
- **> 2.0**: High monotony (low variability, injury risk)

**Strain Interpretation**:
- Higher values indicate higher training stress
- Monitor in combination with ACWR and Readiness

---

**Last Updated**: 2025-11-06
