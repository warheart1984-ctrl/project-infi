"""Optional OpenTelemetry export to Firetiger for AAIS runtime surfaces."""

from __future__ import annotations

import os
from typing import Any


def is_firetiger_export_configured() -> bool:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    return bool(endpoint)


def firetiger_export_status() -> dict[str, Any]:
    configured = is_firetiger_export_configured()
    return {
        "configured": configured,
        "endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip() or None,
        "service_name": os.getenv("OTEL_SERVICE_NAME", "aais-workflow-shell").strip(),
        "headers_set": bool(os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "").strip()),
    }


def init_firetiger_otel(
    *,
    service_name: str = "aais-workflow-shell",
    fastapi_app: Any | None = None,
    flask_app: Any | None = None,
) -> bool:
    """Initialize OTEL export when Firetiger env vars are present.

    Returns True when instrumentation started, False when skipped or unavailable.
    """
    if not is_firetiger_export_configured():
        return False

    os.environ.setdefault("OTEL_SERVICE_NAME", service_name)

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.semconv.resource import ResourceAttributes
    except ImportError:
        return False

    headers_raw = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    headers = {}
    for part in headers_raw.split(","):
        piece = part.strip()
        if "=" in piece:
            key, value = piece.split("=", 1)
            headers[key.strip()] = value.strip()

    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: os.environ["OTEL_SERVICE_NAME"],
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv(
                "OTEL_DEPLOYMENT_ENVIRONMENT", "development"
            ),
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"],
                headers=headers or None,
            )
        )
    )
    trace.set_tracer_provider(provider)

    if fastapi_app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(fastapi_app)
        except ImportError:
            pass

    if flask_app is not None:
        try:
            from opentelemetry.instrumentation.flask import FlaskInstrumentor

            FlaskInstrumentor().instrument_app(flask_app)
        except ImportError:
            pass

    return True
