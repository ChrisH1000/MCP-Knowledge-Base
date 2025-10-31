"""FastAPI application factory."""

from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from rag_server.api import routes_admin, routes_index, routes_query
from rag_server.core.config import Settings, get_settings
from rag_server.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


def api_key_guard(
    x_api_key: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> bool:
    """Validate API key from header.

    Args:
        x_api_key: API key from header
        settings: Application settings

    Returns:
        True if valid

    Raises:
        HTTPException: If API key is invalid
    """
    if settings.RAG_API_KEY and x_api_key != settings.RAG_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app
    """
    # Configure logging
    configure_logging()

    # Log LangSmith configuration
    settings = get_settings()
    if settings.LANGSMITH_TRACING.lower() == "true":
        logger.info(
            "langsmith_enabled",
            project=settings.LANGCHAIN_PROJECT,
            tracing=True
        )

    # Create app
    app = FastAPI(
        title="RAG Server",
        version="0.1.0",
        description="Code-Knowledge RAG Server - Retrieval-Augmented Generation for codebases",
    )

    # Add exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Include routers
    app.include_router(
        routes_admin.router,
        prefix="",
        tags=["admin"],
    )

    app.include_router(
        routes_index.router,
        prefix="/index",
        tags=["index"],
        dependencies=[Depends(api_key_guard)],
    )

    app.include_router(
        routes_query.router,
        prefix="",
        tags=["query"],
        dependencies=[Depends(api_key_guard)],
    )

    logger.info("app_created")
    return app
