import asyncio
from app.settings import settings, PSMLogger
from app.managers import PowerMonitorManager, db_manager

PSMLogger.setup_logging(logs_dir=settings.LOGS_DIR, level=settings.LOG_LEVEL)

async def main():
    await db_manager.init_db()

    async with db_manager.async_session_maker() as session:
        power_monitor_manager = PowerMonitorManager(
            database_session=session,
            settings_instance=settings
        )
        await power_monitor_manager.run()

if __name__ == "__main__":
    asyncio.run(main())
