"""
FastAPI Application Factory module
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import Settings
from app.api.include_routes import include_routers

def create_app(settings: Settings) -> FastAPI:
    """
    Creates and setup the FastAPI application.

    Args:
        config (Config): GFeneral config application.

    Returns:
        app (FastAPI): the FastAPI application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=f"{settings.APP_NAME} API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    include_routers(app, prefix="/api/v1")

    return app
