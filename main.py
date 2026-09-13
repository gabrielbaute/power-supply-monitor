from app.settings import settings, PSMLogger
from app.managers import PowerMonitorManager

PSMLogger.setup_logging(logs_dir=settings.LOGS_DIR, level=settings.LOG_LEVEL)
power_monitor_manager = PowerMonitorManager(settings_instance=settings)

if __name__ == "__main__":
    power_monitor_manager.run()
