import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.router import api_router
from app.config import settings
from app.middleware.request_id import RequestIDMiddleware


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
        handlers=[logging.StreamHandler()],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logging.getLogger(__name__).info("FFE Backend starting up")
    yield
    logging.getLogger(__name__).info("FFE Backend shutting down")


app = FastAPI(
    title="Financial Forensics Engine",
    description="Money muling detection via graph theory — RIFT 2026",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
# Note: FastAPI applies middleware in reverse registration order.
# RequestIDMiddleware is registered last so it runs first (outermost layer).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestIDMiddleware)

# ── Global exception handler ──────────────────────────────────────────────────
# Catches any unhandled exception. Never leaks stack traces to the client.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger = logging.getLogger(__name__)
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error("[%s] Unhandled error: %s", req_id, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": req_id},
    )


# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(health_router)               # GET /health
app.include_router(api_router, prefix="/api")   # GET /api/results, POST /api/analyze
