"""
Módulo de carga de rutas de la API
"""
from fastapi import FastAPI

from app.api.routes.electric_event_routes import router as electric_events_router
from app.api.routes.health_routes import router as health_router

def include_routers(app: FastAPI, prefix: str = ""):
    """
    Incluye y carga las rutas en la aplicación de FastAPI
    """
    app.include_router(electric_events_router, prefix=prefix)
    app.include_router(health_router, prefix=prefix)
