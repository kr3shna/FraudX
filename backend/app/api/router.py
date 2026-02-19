from fastapi import APIRouter

from app.api import analyze, results

api_router = APIRouter()
api_router.include_router(analyze.router, tags=["analyze"])
api_router.include_router(results.router, tags=["results"])
