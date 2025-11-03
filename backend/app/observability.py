"""
OpenTelemetry instrumentation for FastAPI.
Production-ready observability with traces, metrics, and logging.
"""

import logging

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

from app.config import settings

logger = logging.getLogger(__name__)


def setup_telemetry(app):
    """
    Setup OpenTelemetry instrumentation for FastAPI app.
    Instruments: FastAPI, SQLAlchemy, Redis, HTTPx
    """
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry disabled")
        return

    # Resource (service identification)
    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": "1.0.0",
            "deployment.environment": settings.APP_ENV,
        }
    )

    # Traces
    if settings.OTEL_TRACES_EXPORTER == "otlp":
        trace_provider = TracerProvider(resource=resource)
        otlp_trace_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
        trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
        trace.set_tracer_provider(trace_provider)
        logger.info(f"OpenTelemetry traces enabled → {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")

    # Metrics
    if settings.OTEL_METRICS_EXPORTER == "otlp":
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True),
            export_interval_millis=60000,
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)
        logger.info("OpenTelemetry metrics enabled")

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument SQLAlchemy (engine must be set later)
    try:
        from app.database import engine
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        logger.info("SQLAlchemy instrumented")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    # Instrument Redis
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumented")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")

    # Instrument HTTPx
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPx instrumented")
    except Exception as e:
        logger.warning(f"Failed to instrument HTTPx: {e}")

    logger.info("✅ OpenTelemetry setup complete")


def setup_sentry(app):
    """Setup Sentry error tracking."""
    if not settings.SENTRY_DSN:
        logger.info("Sentry disabled (no DSN)")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,
        )
        logger.info("✅ Sentry initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
