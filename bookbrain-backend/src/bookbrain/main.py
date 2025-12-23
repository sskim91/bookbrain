"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="BookBrain API",
    description="Personal Knowledge Search System using LLM + RAG",
    version="0.1.0",
)


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
