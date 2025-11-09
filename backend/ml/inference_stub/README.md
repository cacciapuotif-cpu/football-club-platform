# Readiness Inference Stub

Provides lightweight contract tests for the readiness prediction API without
loading the full model.

## Usage
```python
from backend.ml.inference_stub.schemas import ReadinessFeaturePayload, ReadinessPredictionResponse

payload: ReadinessFeaturePayload = {
    "tenant_id": "demo-fc",
    "athlete_id": "uuid-athlete",
    "event_date": date.today(),
    "features": [
        {"name": "acute_chronic_ratio_7_28", "value": 1.2},
        {"name": "sleep_debt_hours_7d", "value": 3.0},
    ],
}
```

Mock outputs for tests are stored in `sample_response.json`.

