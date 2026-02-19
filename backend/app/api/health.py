from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.store.memory_store import MemoryStore, get_store

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check(store: MemoryStore = Depends(get_store)) -> JSONResponse:
    """
    Readiness probe endpoint.
    Verifies the process is alive AND the result store is operational.
    Returns 200 (healthy) or 503 (unhealthy) for load balancer health checks.
    """
    try:
        store.get("__health__")   # lightweight read — touches eviction logic
        return JSONResponse(status_code=200, content={"status": "ok"})
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unhealthy"})
