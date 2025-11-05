"""
CORS (Cross-Origin Resource Sharing) Tests

Tests CORS configuration for frontend-backend communication.
Validates preflight OPTIONS requests and CORS headers on actual requests.
"""

import pytest
from fastapi import status
from httpx import AsyncClient

from app.config import settings


class TestCORSConfiguration:
    """Test CORS middleware configuration."""

    @pytest.mark.asyncio
    async def test_cors_preflight_options(self, client: AsyncClient):
        """Test CORS preflight OPTIONS request."""
        origin = "http://localhost:3000"

        response = await client.options(
            "/api/v1/players",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "GET" in response.headers["access-control-allow-methods"]
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "authorization" in response.headers["access-control-allow-headers"].lower()

    @pytest.mark.asyncio
    async def test_cors_get_request(self, client: AsyncClient):
        """Test CORS headers on GET request."""
        origin = "http://localhost:3000"

        response = await client.get(
            "/api/v1/players",
            headers={"Origin": origin},
        )

        # Should return CORS headers even if authentication fails
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers.get("access-control-allow-credentials") == "true"

    @pytest.mark.asyncio
    async def test_cors_post_request(self, client: AsyncClient):
        """Test CORS headers on POST request."""
        origin = "http://localhost:3000"

        response = await client.post(
            "/api/v1/players",
            headers={
                "Origin": origin,
                "Content-Type": "application/json",
            },
            json={"first_name": "Test", "last_name": "Player"},
        )

        # Should return CORS headers even if validation/authentication fails
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == origin

    @pytest.mark.asyncio
    async def test_cors_health_endpoint(self, client: AsyncClient):
        """Test CORS on health check endpoint."""
        origin = "http://localhost:3000"

        response = await client.get(
            "/healthz",
            headers={"Origin": origin},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["access-control-allow-origin"] == origin
        assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_cors_unauthorized_origin_blocked(self, client: AsyncClient):
        """Test that unauthorized origins are handled correctly."""
        # Origin not in ALLOWED_ORIGINS
        unauthorized_origin = "http://malicious-site.com"

        response = await client.get(
            "/healthz",
            headers={"Origin": unauthorized_origin},
        )

        # FastAPI's CORS middleware doesn't add headers for disallowed origins
        # The request still succeeds but CORS headers are missing
        assert response.status_code == status.HTTP_200_OK
        # Access-Control-Allow-Origin should NOT be set for unauthorized origins
        # (or it should not match the unauthorized origin)
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] != unauthorized_origin

    @pytest.mark.asyncio
    async def test_cors_multiple_allowed_origins(self, client: AsyncClient):
        """Test CORS with multiple allowed origins from config."""
        # Test each origin in ALLOWED_ORIGINS
        for origin in settings.ALLOWED_ORIGINS:
            response = await client.get(
                "/healthz",
                headers={"Origin": origin},
            )

            assert response.status_code == status.HTTP_200_OK
            assert response.headers["access-control-allow-origin"] == origin
            assert response.headers.get("access-control-allow-credentials") == "true"

    @pytest.mark.asyncio
    async def test_cors_no_origin_header(self, client: AsyncClient):
        """Test request without Origin header (same-origin request)."""
        response = await client.get("/healthz")

        assert response.status_code == status.HTTP_200_OK
        # No CORS headers should be present for same-origin requests
        # (this is normal behavior)

    @pytest.mark.asyncio
    async def test_cors_credentials_flag(self, client: AsyncClient):
        """Test that credentials flag is properly set."""
        origin = "http://localhost:3000"

        response = await client.get(
            "/api/v1/players",
            headers={"Origin": origin},
        )

        # Verify credentials flag matches configuration
        assert response.headers.get("access-control-allow-credentials") == str(
            settings.CORS_ALLOW_CREDENTIALS
        ).lower()


class TestCORSPlayerEndpoints:
    """Test CORS specifically for player endpoints."""

    @pytest.mark.asyncio
    async def test_cors_players_list_endpoint(self, client: AsyncClient):
        """Test CORS on GET /api/v1/players."""
        origin = "http://localhost:3000"

        response = await client.get(
            "/api/v1/players",
            headers={"Origin": origin},
        )

        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == origin

    @pytest.mark.asyncio
    async def test_cors_players_create_preflight(self, client: AsyncClient):
        """Test CORS preflight for POST /api/v1/players."""
        origin = "http://localhost:3000"

        response = await client.options(
            "/api/v1/players",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "content-type" in response.headers["access-control-allow-headers"].lower()

    @pytest.mark.asyncio
    async def test_cors_players_get_by_id(self, client: AsyncClient):
        """Test CORS on GET /api/v1/players/{id}."""
        origin = "http://localhost:3000"
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.get(
            f"/api/v1/players/{fake_uuid}",
            headers={"Origin": origin},
        )

        # Should have CORS headers even if player not found
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == origin

    @pytest.mark.asyncio
    async def test_cors_players_update_preflight(self, client: AsyncClient):
        """Test CORS preflight for PUT /api/v1/players/{id}."""
        origin = "http://localhost:3000"
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.options(
            f"/api/v1/players/{fake_uuid}",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "PUT" in response.headers["access-control-allow-methods"]

    @pytest.mark.asyncio
    async def test_cors_players_delete_preflight(self, client: AsyncClient):
        """Test CORS preflight for DELETE /api/v1/players/{id}."""
        origin = "http://localhost:3000"
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = await client.options(
            f"/api/v1/players/{fake_uuid}",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "authorization",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert "DELETE" in response.headers["access-control-allow-methods"]


class TestCORSSecurityHeaders:
    """Test that CORS and security headers coexist properly."""

    @pytest.mark.asyncio
    async def test_cors_with_security_headers(self, client: AsyncClient):
        """Test that CORS headers don't interfere with security headers."""
        origin = "http://localhost:3000"

        response = await client.get(
            "/healthz",
            headers={"Origin": origin},
        )

        # Should have both CORS and security headers
        assert "access-control-allow-origin" in response.headers
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers

    @pytest.mark.asyncio
    async def test_cors_max_age_header(self, client: AsyncClient):
        """Test that max-age header is set correctly in preflight."""
        origin = "http://localhost:3000"

        response = await client.options(
            "/api/v1/players",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        # max-age should match CORS_MAX_AGE from settings
        if "access-control-max-age" in response.headers:
            max_age = int(response.headers["access-control-max-age"])
            assert max_age == settings.CORS_MAX_AGE
