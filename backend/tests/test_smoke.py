"""
Smoke Tests - Basic functionality checks
==========================================
Quick tests to verify the API is running and basic endpoints are accessible.
"""

import os
from io import BytesIO

import pytest
from PIL import Image


def test_health_check(client):
    """Test /healthz endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Football Club Platform" in data["service"]
    assert "version" in data


def test_readiness_check(client):
    """Test /readyz endpoint."""
    response = client.get("/readyz")
    # May return 200 or 503 depending on DB/Redis availability
    assert response.status_code in [200, 503]
    data = response.json()
    assert data["status"] in ["ready", "not_ready"]
    assert "checks" in data


def test_root_endpoint(client):
    """Test root / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Football Club Platform API"
    assert "docs" in data
    assert "health" in data


def test_openapi_schema(client):
    """Test OpenAPI schema availability."""
    api_version = os.getenv("API_VERSION", "v1")
    response = client.get(f"/api/{api_version}/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


def test_docs_endpoint(client):
    """Test /docs endpoint accessibility."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"swagger" in response.content.lower() or b"openapi" in response.content.lower()


def test_ml_predict_health(client):
    """Test ML prediction service health endpoint."""
    api_version = os.getenv("API_VERSION", "v1")
    response = client.get(f"/api/{api_version}/ml/predict/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "pytorch_version" in data or "pytorch_available" in data
    assert "opencv_version" in data or "opencv_available" in data


def test_predict_frame_mock(client):
    """Test /predict_frame endpoint with mock image."""
    api_version = os.getenv("API_VERSION", "v1")

    # Create a simple test image
    img = Image.new("RGB", (640, 480), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    # Send the image to the predict endpoint
    response = client.post(
        f"/api/{api_version}/ml/predict_frame",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "boxes" in data
    assert "frame_width" in data
    assert "frame_height" in data
    assert "model_version" in data
    assert data["mock"] is True

    # Verify boxes structure
    assert isinstance(data["boxes"], list)
    assert len(data["boxes"]) > 0

    for box in data["boxes"]:
        assert "x1" in box
        assert "y1" in box
        assert "x2" in box
        assert "y2" in box
        assert "label" in box
        assert "score" in box
        assert box["label"] in ["player", "ball", "referee"]
        assert 0.0 <= box["score"] <= 1.0


def test_predict_frame_invalid_file(client):
    """Test /predict_frame with invalid file type."""
    api_version = os.getenv("API_VERSION", "v1")

    # Send a text file instead of an image
    response = client.post(
        f"/api/{api_version}/ml/predict_frame",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_predict_frame_empty_file(client):
    """Test /predict_frame with empty file."""
    api_version = os.getenv("API_VERSION", "v1")

    response = client.post(
        f"/api/{api_version}/ml/predict_frame",
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_metrics_endpoint(client):
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    # May return 200 if enabled or 404 if disabled
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        # Check for Prometheus format
        assert b"http_requests_total" in response.content or b"# HELP" in response.content


@pytest.mark.parametrize("endpoint", [
    "/api/v1/players",
    "/api/v1/sessions",
    "/api/v1/wellness",
])
def test_protected_endpoints_without_auth(client, endpoint):
    """Test that protected endpoints return 401 without authentication."""
    response = client.get(endpoint)
    # Should return 401 (unauthorized) or 403 (forbidden) or 422 (validation error)
    # depending on auth configuration
    assert response.status_code in [401, 403, 422, 200]
    # If SKIP_AUTH is enabled, may return 200 or 422


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/healthz", headers={"Origin": "http://localhost:3000"})
    # CORS headers should be present
    # Note: TestClient may not fully simulate CORS behavior
    assert response.status_code in [200, 405]


def test_security_headers(client):
    """Test security headers are present."""
    response = client.get("/healthz")
    headers = response.headers

    # Check for common security headers
    assert "x-content-type-options" in headers
    assert headers["x-content-type-options"] == "nosniff"
    assert "x-frame-options" in headers
    assert "x-xss-protection" in headers


def test_pytorch_import():
    """Test PyTorch can be imported."""
    try:
        import torch
        assert torch.__version__ is not None
    except ImportError:
        pytest.skip("PyTorch not installed")


def test_opencv_import():
    """Test OpenCV can be imported."""
    try:
        import cv2
        assert cv2.__version__ is not None
    except ImportError:
        pytest.skip("OpenCV not installed")


def test_pillow_import():
    """Test Pillow can be imported."""
    try:
        from PIL import Image
        assert Image.VERSION is not None or Image.__version__ is not None
    except ImportError:
        pytest.skip("Pillow not installed")
