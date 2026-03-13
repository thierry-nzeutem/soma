"""
SOMA — Personal Health Operating System
Backend API (FastAPI)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.api.v1.router import api_router
from app.services.scheduler_service import create_scheduler
from app.observability.logging_config import setup_logging
from app.cache.cache_service import init_cache, close_cache
from app.middleware.metrics_middleware import MetricsMiddleware  # LOT 19
from app.middleware.locale_middleware import LocaleMiddleware  # BATCH 7 i18n

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle. Démarre le scheduler APScheduler et le cache Redis."""
    setup_logging(
        log_level=getattr(settings, "LOG_LEVEL", "INFO"),
        json_mode=not getattr(settings, "DEBUG", True),
    )
    logger.info("SOMA API starting", env=settings.APP_ENV)

    # Init Redis cache
    await init_cache()

    scheduler = create_scheduler()
    scheduler.start()
    logger.info(
        "Scheduler started",
        jobs=[j.id for j in scheduler.get_jobs()],
        next_run=str(scheduler.get_jobs()[0].next_run_time) if scheduler.get_jobs() else "N/A",
    )
    yield
    scheduler.shutdown(wait=False)
    await close_cache()
    logger.info("SOMA API shutting down")


app = FastAPI(
    title="SOMA — Personal Health OS",
    description="Backend API for SOMA Personal Health Operating System",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS (mobile app locale en dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://soma.local"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LOT 19 : Metrics middleware (buffer in-memory, non bloquant)
app.add_middleware(MetricsMiddleware)

# BATCH 7 : Locale middleware (Accept-Language → request.state.locale)
app.add_middleware(LocaleMiddleware)


# Handler d'erreur global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback; tb = traceback.format_exc()
    logger.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )


# Routes
app.include_router(api_router)


@app.get("/health")
async def healthcheck():
    return {"status": "ok", "app": "SOMA", "version": "0.1.0"}
