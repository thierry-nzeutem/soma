"""
Structured logging configuration for SOMA.

Features:
- JSON formatter for production (machine-readable, ELK/CloudWatch compatible).
- Human-readable formatter for development.
- request_id support (set per-request via middleware).
- Log level from settings.LOG_LEVEL.

Usage:
    from app.observability.logging_config import setup_logging
    setup_logging()  # call once at app startup
"""
from __future__ import annotations

import logging
import logging.config
import sys
from typing import Optional


# ── Formatters ────────────────────────────────────────────────────────────────

class DevFormatter(logging.Formatter):
    """
    Human-readable formatter for development.
    Format: [LEVEL] logger_name: message
    """
    _COLORS = {
        "DEBUG": "\033[36m",    # cyan
        "INFO": "\033[32m",     # green
        "WARNING": "\033[33m",  # yellow
        "ERROR": "\033[31m",    # red
        "CRITICAL": "\033[35m", # magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self._COLORS.get(record.levelname, "")
        reset = self._COLORS["RESET"]
        msg = super().format(record)
        return f"{color}[{record.levelname}]{reset} {record.name}: {record.getMessage()}"


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for production.
    Each log line is a JSON object (one per line).
    """
    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Include any extra fields set via LogRecord
        for key, val in record.__dict__.items():
            if key.startswith("soma_") or key == "request_id":
                payload[key] = val
        return json.dumps(payload, default=str)


# ── Setup ─────────────────────────────────────────────────────────────────────

def setup_logging(log_level: Optional[str] = None, json_mode: bool = False) -> None:
    """
    Configure root logger and per-module levels.

    Args:
        log_level: Override log level (e.g., "DEBUG", "INFO"). Defaults to settings.LOG_LEVEL.
        json_mode: If True, use JSON formatter (set automatically in production).
    """
    try:
        from app.core.config import settings
        level_str = log_level or getattr(settings, "LOG_LEVEL", "INFO")
        env = getattr(settings, "APP_ENV", "development")
        use_json = json_mode or env == "production"
    except Exception:
        level_str = log_level or "INFO"
        use_json = json_mode

    level = getattr(logging, level_str.upper(), logging.INFO)
    formatter: logging.Formatter = JsonFormatter() if use_json else DevFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging configured: level=%s, json=%s", level_str, use_json
    )
