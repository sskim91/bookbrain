"""FastAPI application entry point."""

from fastapi import FastAPI

from bookbrain.api.routes import books, health

app = FastAPI(
    title="BookBrain API",
    description="Personal Knowledge Search System using LLM + RAG",
    version="0.1.0",
)

# Register routers
app.include_router(health.router)
app.include_router(books.router)
