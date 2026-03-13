"""SOMA Locale Middleware — Reads Accept-Language header and sets request.state.locale.

Usage in endpoints :
    @router.get("/endpoint")
    async def handler(request: Request):
        locale = getattr(request.state, "locale", "fr")
        label = t("readiness.excellent", locale=locale)

Supports : fr (default), en.
Parses standard Accept-Language header format :
    Accept-Language: en-US,en;q=0.9,fr;q=0.8
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.i18n import get_supported_locales

_SUPPORTED = set(get_supported_locales())
_DEFAULT = "fr"


def _parse_accept_language(header: str) -> str:
    """Parse Accept-Language header and return best matching locale.

    Examples:
        "en-US,en;q=0.9,fr;q=0.8" → "en"
        "fr-FR,fr;q=0.9"          → "fr"
        "de"                       → "fr" (fallback)
        ""                         → "fr"
    """
    if not header:
        return _DEFAULT

    # Split by comma, parse each entry
    entries: list[tuple[float, str]] = []
    for part in header.split(","):
        part = part.strip()
        if not part:
            continue
        if ";q=" in part:
            lang_part, q_part = part.split(";q=", 1)
            try:
                q = float(q_part.strip())
            except ValueError:
                q = 0.0
        else:
            lang_part = part
            q = 1.0

        lang = lang_part.strip().split("-")[0].lower()
        entries.append((q, lang))

    # Sort by quality descending, find first supported
    entries.sort(key=lambda x: -x[0])
    for _, lang in entries:
        if lang in _SUPPORTED:
            return lang

    return _DEFAULT


class LocaleMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts locale from Accept-Language header."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        accept_lang = request.headers.get("accept-language", "")
        locale = _parse_accept_language(accept_lang)
        request.state.locale = locale
        response = await call_next(request)
        return response
