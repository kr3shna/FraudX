from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """
    Liveness probe endpoint.
    Used by EC2 load balancer health checks and uptime monitors.
    Returns 200 as long as the process is alive.
    """
    return {"status": "ok"}
