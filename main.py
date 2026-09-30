"""
Main application entrypoint module
"""
import asyncio
import uvicorn

from app.api.app_factory import create_app
from app.settings import settings, PSMLogger
from app.managers import PowerMonitorManager, db_manager

PSMLogger.setup_logging(logs_dir=settings.LOGS_DIR, level=settings.LOG_LEVEL)

async def run_power_monitor() -> None:
    """
    Initializes the database and runs the power monitor loop.
    """
    await db_manager.init_db()

    async with db_manager.async_session_maker() as session:
        power_monitor_manager = PowerMonitorManager(
            database_session=session,
            settings_instance=settings
        )
        await power_monitor_manager.run()

async def main() -> None:
    """
    Main entrypoint that runs the background monitor and the HTTP API server concurrently.
    """
    monitor_task = asyncio.create_task(run_power_monitor())

    app = create_app(settings=settings)

    config = uvicorn.Config(
        app=app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.API_LOG_LEVEL
    )
    server = uvicorn.Server(config)

    try:
        await server.serve()
    finally:
        print("API detenida, deteniendo monitor.")
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
