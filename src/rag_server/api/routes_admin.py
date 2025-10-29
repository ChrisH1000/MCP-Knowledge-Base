"""Admin API routes (health, config)."""

from typing import Any, Dict
from fastapi import APIRouter, Depends

from rag_server.core.config import Settings, get_settings
from rag_server.core.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/config")
async def get_config(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """Get current configuration (with secrets redacted)."""
    return settings.model_dump_safe()
