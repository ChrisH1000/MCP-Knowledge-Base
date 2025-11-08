"""Main entry point for the RAG server."""

from rag_server.server import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "rag_server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
