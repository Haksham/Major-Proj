"""Prometheus metrics helpers for the SALF backend."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response


REQUEST_COUNT = Counter(
    "salf_backend_http_requests_total",
    "Total backend HTTP requests.",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "salf_backend_http_request_duration_seconds",
    "Backend HTTP request latency in seconds.",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

IN_PROGRESS = Gauge(
    "salf_backend_http_requests_in_progress",
    "Backend HTTP requests currently being processed.",
)

SLOW_REQUESTS = Counter(
    "salf_backend_slow_requests_total",
    "Backend requests slower than the configured p95 threshold.",
    ["path"],
)

EXCEPTION_COUNT = Counter(
    "salf_backend_exceptions_total",
    "Unhandled backend exceptions.",
    ["exception_type"],
)


def metrics_response() -> Response:
    """Render the Prometheus exposition payload."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
