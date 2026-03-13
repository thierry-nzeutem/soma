"""Metrics Middleware — LOT 19.

Middleware Starlette qui mesure le temps de réponse de chaque requête API
et l'enregistre dans un buffer in-memory.

Design :
  - Buffer circulaire limité à 10 000 entrées (deque maxlen).
  - Jamais bloquant : l'enregistrement est synchrone mais trivial (append).
  - Endpoints exclus : /health, /docs, /openapi.json, /redoc (bruit non productif).
  - Le buffer est lu par GET /analytics/performance (analytics_dashboard router).

Usage :
    from app.middleware.metrics_middleware import MetricsMiddleware
    app.add_middleware(MetricsMiddleware)
"""
import time
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# ── Buffer in-memory ──────────────────────────────────────────────────────────

_metrics_buffer: deque = deque(maxlen=10_000)


@dataclass
class MetricRecord:
    """Enregistrement d'une requête API."""
    endpoint: str
    method: str
    response_time_ms: int
    status_code: int
    created_at: datetime


# ── Middleware ────────────────────────────────────────────────────────────────

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware de monitoring des performances API.

    Enregistre endpoint, method, response_time_ms et status_code
    pour chaque requête dans un buffer circulaire thread-safe.
    """

    # Endpoints à exclure du monitoring (bruit ou sensibles)
    _SKIP_PATHS: frozenset[str] = frozenset({
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    })

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Skip les endpoints de monitoring / docs
        if path in self._SKIP_PATHS:
            return await call_next(request)

        start_ms = time.monotonic() * 1000
        status_code = 500  # fallback si exception

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            # Propager l'exception sans la masquer
            raise
        finally:
            elapsed_ms = int(time.monotonic() * 1000 - start_ms)
            _metrics_buffer.append(
                MetricRecord(
                    endpoint=path,
                    method=request.method,
                    response_time_ms=elapsed_ms,
                    status_code=status_code,
                    created_at=datetime.now(timezone.utc),
                )
            )


# ── Accesseurs publics ────────────────────────────────────────────────────────

def get_buffered_metrics() -> list[MetricRecord]:
    """Retourne une copie snapshot du buffer (thread-safe via list())."""
    return list(_metrics_buffer)


def flush_metrics_buffer() -> list[MetricRecord]:
    """Retourne le buffer et le vide atomiquement."""
    records = list(_metrics_buffer)
    _metrics_buffer.clear()
    return records


def get_buffer_size() -> int:
    """Retourne le nombre d'entrées actuellement dans le buffer."""
    return len(_metrics_buffer)
