"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bookbrain.api.routes import books, health, search
from bookbrain.core.database import close_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager for resource cleanup."""
    # Startup: nothing to do (pool is lazy-initialized)
    yield
    # Shutdown: close the connection pool
    await close_pool()


app = FastAPI(
    title="BookBrain API",
    description="Personal Knowledge Search System using LLM + RAG",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(books.router)
app.include_router(search.router)
