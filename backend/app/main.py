"""
Football Club Platform - Main FastAPI Application
Gestionale innovativo per società di calcio.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import init_db

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
request_duration = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown."""
    logger.info("🚀 Starting Football Club Platform API...")

    # Initialize database
    await init_db()

    # Setup and start scheduler
    from app.scheduler import setup_scheduler, start_scheduler, shutdown_scheduler
    scheduler = setup_scheduler()
    start_scheduler(scheduler)

    logger.info("✅ Football Club Platform API started successfully")
    yield

    # Shutdown scheduler
    shutdown_scheduler(scheduler)
    logger.info("🛑 Shutting down Football Club Platform API...")


# Create FastAPI app
app = FastAPI(
    title="Football Club Platform API",
    description="Gestionale innovativo per società di calcio",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json",
    lifespan=lifespan,
)

# Setup observability (must be done before adding other middleware)
if settings.OTEL_ENABLED or settings.SENTRY_DSN:
    from app.observability import setup_telemetry, setup_sentry
    if settings.OTEL_ENABLED:
        logger.info("Setting up OpenTelemetry...")
        setup_telemetry(app)
    if settings.SENTRY_DSN:
        logger.info("Setting up Sentry...")
        setup_sentry(app)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=settings.CORS_MAX_AGE,
)


# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

    return response


# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request metrics."""
    method = request.method
    path = request.url.path

    with request_duration.labels(method=method, endpoint=path).time():
        response = await call_next(request)

    request_count.labels(method=method, endpoint=path, status=response.status_code).inc()
    return response


# ============================================
# HEALTH & METRICS ENDPOINTS
# ============================================


@app.get("/healthz", tags=["Health"])
async def healthz():
    """Health check endpoint."""
    return {"status": "ok", "service": "Football Club Platform API", "version": "1.0.0"}


@app.get("/readyz", tags=["Health"])
async def readyz():
    """Readiness check with real DB and Redis checks."""
    checks = {}
    overall_status = "ready"

    # Check database
    try:
        from sqlalchemy import text
        from app.database import get_session
        async for session in get_session():
            # Simple query to check DB connectivity
            await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
            break
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        checks["database"] = f"error: {str(e)}"
        overall_status = "not_ready"

    # Check Redis
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()
        checks["redis"] = "ok"
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        checks["redis"] = f"error: {str(e)}"
        overall_status = "not_ready"

    # Check migrations status (Alembic)
    try:
        from alembic.config import Config as AlembicConfig
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from app.database import engine

        # Get current revision from database
        async with engine.connect() as conn:
            context = await conn.run_sync(
                lambda sync_conn: MigrationContext.configure(sync_conn)
            )
            current_rev = await conn.run_sync(
                lambda sync_conn: MigrationContext.configure(sync_conn).get_current_revision()
            )

        # Get head revision from migrations
        alembic_cfg = AlembicConfig("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()

        if current_rev == head_rev:
            checks["migrations"] = "ok"
        else:
            checks["migrations"] = f"outdated: current={current_rev}, head={head_rev}"
            overall_status = "not_ready"
    except Exception as e:
        logger.warning(f"Migration check failed (may be normal on first run): {e}")
        checks["migrations"] = f"unknown: {str(e)}"

    status_code = status.HTTP_200_OK if overall_status == "ready" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={"status": overall_status, "checks": checks}
    )


@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.ENABLE_METRICS:
        return JSONResponse({"error": "Metrics disabled"}, status_code=status.HTTP_404_NOT_FOUND)
    return Response(content=generate_latest(), media_type="text/plain")


# ============================================
# API ROUTERS
# ============================================

# Import routers
from app.routers import (
    advanced_analytics,
    advanced_tracking,
    alerts,
    analytics,
    auth,
    matches,
    metrics,
    ml_analytics,
    ml_predict,
    ml_reports,
    performance,
    plans,
    players,
    progress,  # NEW: Player progress tracking
    progress_ml,  # NEW: ML predictions for progress
    quick_input,
    reports,
    sessions,
    teams,
    training,
    wellness,
)
from app.ml.api import endpoints as youth_ml

# API version prefix
api_prefix = f"/api/{settings.API_VERSION}"

# Register routers
app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["Authentication"])
app.include_router(players.router, prefix=f"{api_prefix}/players", tags=["Players"])
app.include_router(sessions.router, prefix=f"{api_prefix}/sessions", tags=["Training Sessions"])
app.include_router(training.router, prefix=f"{api_prefix}/training", tags=["Training & RPE"])
app.include_router(metrics.router, prefix=f"{api_prefix}/metrics", tags=["Metrics & Readiness"])
app.include_router(alerts.router, prefix=f"{api_prefix}/alerts", tags=["Alerts & Notifications"])
app.include_router(wellness.router, prefix=f"{api_prefix}/wellness", tags=["Wellness Data"])
app.include_router(performance.router, prefix=f"{api_prefix}/performance", tags=["Performance Modules"])
app.include_router(analytics.router, prefix=f"{api_prefix}/analytics", tags=["Analytics & Reports"])
app.include_router(ml_analytics.router, prefix=api_prefix, tags=["ML Analytics"])
app.include_router(advanced_analytics.router, prefix=f"{api_prefix}/advanced-analytics", tags=["Advanced ML Analytics & Scouting"])
app.include_router(advanced_tracking.router, prefix=f"{api_prefix}/tracking", tags=["Advanced Tracking"])
app.include_router(ml_predict.router, prefix=f"{api_prefix}/ml", tags=["ML Predictions"])
app.include_router(ml_reports.router)  # ML Reports & Predictions (has its own prefix)
app.include_router(youth_ml.router, prefix=f"{api_prefix}/youth-ml", tags=["Youth ML - Performance & Development"])

# ============================================
# NEW ROUTERS - Player Progress & ML Insights
# ============================================
app.include_router(progress.router, prefix=api_prefix, tags=["Player Progress Tracking"])
app.include_router(progress_ml.router, prefix=f"{api_prefix}/progress-ml", tags=["Progress ML - Risk & Insights"])

# ============================================
# NEW CRITICAL ROUTERS - FULLY IMPLEMENTED
# ============================================
app.include_router(teams.router, prefix=f"{api_prefix}/teams", tags=["Teams & Seasons"])
app.include_router(matches.router, prefix=f"{api_prefix}/matches", tags=["Matches & Attendance"])
app.include_router(plans.router, prefix=f"{api_prefix}/plans", tags=["Training Plans & Adherence"])
app.include_router(reports.router, prefix=f"{api_prefix}/reports", tags=["Reports & PDF Generation"])
app.include_router(quick_input.router, prefix=f"{api_prefix}/quick", tags=["Quick Input - Mobile Optimized"])

# ============================================
# FUTURE ROUTERS (TODO)
# ============================================
# app.include_router(sensors.router, prefix=f"{api_prefix}/sensors", tags=["Sensors"])
# app.include_router(video.router, prefix=f"{api_prefix}/video", tags=["Video"])
# app.include_router(benchmark.router, prefix=f"{api_prefix}/benchmark", tags=["Benchmark"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "service": "Football Club Platform API",
        "tagline": "Gestionale per Società di Calcio",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/healthz",
    }


# ============================================
# GLOBAL EXCEPTION HANDLER
# ============================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc) if settings.DEBUG else "Internal error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
