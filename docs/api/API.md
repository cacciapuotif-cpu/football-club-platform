# Football Club Platform - API Reference

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: JWT Bearer Token (header: `Authorization: Bearer <token>`)

---

## Authentication

### POST /auth/signup

Create new organization + owner user.

**Request**:
```json
{
  "email": "owner@club.local",
  "password": "securepassword123",
  "full_name": "John Doe",
  "organization_name": "FC Example",
  "organization_slug": "fc-example"
}
```

**Response** (201):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "role": "OWNER"
}
```

### POST /auth/login

Login with email and password.

**Request**:
```json
{
  "email": "coach@club.local",
  "password": "password123"
}
```

**Response** (200):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "role": "COACH"
}
```

### GET /auth/me

Get current user profile.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "id": "uuid",
  "email": "coach@club.local",
  "full_name": "Coach Mario",
  "role": "COACH",
  "organization_id": "uuid"
}
```

---

## Machine Learning

### GET /ml/predict

Predict player performance and overload risk.

**Query Params**:
- `player_id` (required): UUID

**Response** (200):
```json
{
  "expected_performance": 72.3,
  "confidence_lower": 68.1,
  "confidence_upper": 76.5,
  "threshold": "neutro",
  "overload_risk": {
    "level": "low",
    "probability": 0.12,
    "confidence_lower": 0.08,
    "confidence_upper": 0.18
  },
  "model_version": "1.0.0",
  "model_health": "OK"
}
```

**Thresholds**:
- `attenzione`: performance < 45
- `neutro`: 45 ≤ performance < 70
- `in_crescita`: performance ≥ 70

### GET /ml/explain

Explain prediction with SHAP contributions.

**Query Params**:
- `player_id` (required): UUID

**Response** (200):
```json
{
  "global_importances": {
    "load_acwr": 0.23,
    "wellness_hrv_avg": 0.18,
    "wellness_sleep_avg": 0.15,
    "wellness_fatigue_avg": 0.12
  },
  "local_contributions": {
    "load_acwr": 5.2,
    "wellness_hrv_avg": -2.1,
    "wellness_sleep_avg": 3.7
  },
  "natural_language": "Performance prevista sopra media grazie a carico allenamento ottimale (ACWR 1.2) e buon recupero (sonno 8.2h avg). Attenzione a HRV in calo (-8% vs baseline)."
}
```

### GET /ml/health

Check ML model health and drift.

**Response** (200):
```json
{
  "status": "OK",
  "model_version": "1.0.0",
  "last_trained": "2025-01-15T03:00:00Z",
  "samples_since_retrain": 245,
  "drift": {
    "psi_carichi": 0.08,
    "psi_wellness": 0.05,
    "psi_kpi_tecnici": 0.12,
    "mae_degrade": 0.03,
    "status": "OK"
  },
  "metrics": {
    "mae": 6.2,
    "rmse": 8.5,
    "r2": 0.78,
    "brier_score": 0.08
  },
  "warnings": []
}
```

---

## Reports

### GET /reports/player/{player_id}

Generate player report (PDF).

**Path Params**:
- `player_id` (required): UUID

**Query Params**:
- `range` (optional): `last_4_weeks`, `last_month`, `season`
- `format` (optional): `pdf`, `html`, `json` (default: `pdf`)

**Response** (200):
- Content-Type: `application/pdf`
- Binary PDF file

### GET /reports/team/{team_id}

Generate team report (PDF).

**Path Params**:
- `team_id` (required): UUID

**Query Params**:
- `range` (optional): `last_week`, `last_month`
- `format` (optional): `pdf`, `html`

**Response** (200):
- Content-Type: `application/pdf`
- Binary PDF file

---

## Sensors

### POST /sensors/import

Import sensor data from CSV.

**Form Data**:
- `file` (required): CSV file
- `mapping` (optional): JSON with column mappings

**Response** (201):
```json
{
  "imported": 42,
  "errors": [],
  "session_ids": ["uuid1", "uuid2"]
}
```

### POST /sensors/webhook

Webhook for real-time sensor data.

**Headers**:
- `X-Sensor-Token`: configured token

**Request**:
```json
{
  "player_id": "uuid",
  "session_id": "uuid",
  "timestamp": "2025-01-15T10:30:00Z",
  "metrics": {
    "distance_m": 5430,
    "hi_runs": 45,
    "sprints": 12,
    "hr_avg": 165,
    "player_load": 342
  }
}
```

**Response** (201):
```json
{
  "status": "accepted",
  "sensor_data_id": "uuid"
}
```

---

## Video

### POST /video/upload

Upload video for processing.

**Form Data**:
- `file` (required): Video file
- `match_id` (optional): UUID
- `session_id` (optional): UUID

**Response** (202):
```json
{
  "video_id": "uuid",
  "status": "UPLOADED",
  "processing_started": true,
  "estimated_duration_sec": 300
}
```

### GET /video/{video_id}/events

Get detected events timeline.

**Response** (200):
```json
{
  "video_id": "uuid",
  "events": [
    {
      "timestamp_sec": 450.2,
      "event_type": "SHOT",
      "player_id": "uuid",
      "confidence": 0.87,
      "x": 0.85,
      "y": 0.42
    }
  ]
}
```

---

## Benchmark

### GET /benchmark/role-age

Anonymous benchmark data for role and age group.

**Query Params**:
- `role` (required): `GK`, `DF`, `MF`, `FW`
- `age_group` (required): `U15`, `U17`, `U19`, `Pro`

**Response** (200):
```json
{
  "role": "MF",
  "age_group": "U17",
  "sample_size": 127,
  "metrics": {
    "distance_km": {"p25": 8.2, "p50": 9.5, "p75": 10.8},
    "sprint_count": {"p25": 12, "p50": 18, "p75": 24},
    "player_load": {"p25": 280, "p50": 340, "p75": 410}
  }
}
```

---

## Health & Metrics

### GET /healthz

Liveness probe.

**Response** (200):
```json
{
  "status": "ok",
  "service": "Football Club Platform API",
  "version": "1.0.0"
}
```

### GET /readyz

Readiness probe (checks DB + Redis).

**Response** (200):
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

---

## Error Responses

All errors follow this format:

**4xx/5xx**:
```json
{
  "detail": "Error message in English or Italian",
  "error_code": "OPTIONAL_CODE",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Common Status Codes**:
- `400` Bad Request
- `401` Unauthorized (invalid/missing token)
- `403` Forbidden (insufficient permissions)
- `404` Not Found
- `422` Validation Error
- `429` Rate Limit Exceeded
- `500` Internal Server Error

---

**Full API Docs**: http://localhost:8000/docs (Swagger UI)
