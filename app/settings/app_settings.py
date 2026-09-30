"""
Configuración general de la aplicación
"""
import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings.app_version import __version__

class Settings(BaseSettings):
    """
    Clase de gestión de varibles de entorno y configuración.
    """
    # ------------ APP INFO ------------
    APP_NAME: str = "PowerSupplyMonitor"
    APP_VERSION: str =  __version__

    # ------------ Directories and config path ------------
    # Directory and path config
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UI_DIR: Path = Path(__file__).resolve().parent.parent / "ui"
    INSTANCE_DIR: Path = BASE_DIR / "instance"
    LOGS_DIR: Path = BASE_DIR / "logs"
    MAIL_TEMPLATES_DIR: Path = UI_DIR / "emails"

    # ----------- LOGGING -------------
    LOG_LEVEL: str = "INFO"

    # ----------- POWER SYSTEM ------------
    CHECK_INTERVAL: int = 5
    SUPPLY_PATH: Path = Path("/sys/class/power_supply")
    AC_SUPPLY_NAME: str = "AC0"
    FLUCTUATION_NOTIFY_COOLDOWN_SECONDS: int = 600  # 10 minutos

    # ----------- SERVER LOCATION ------------
    LATITUDE: float
    LONGITUDE: float

    # ----------- WEBHOOKS ------------
    NTFY_TOPIC: str
    NTFY_URL: str

    # ----------- DEBOUNCE ------------
    CONFIRMATION_READS: int = 3  # lecturas consecutivas para confirmar un cambio de estado

    # ----------- DATABASE ------------
    DATABASE_URL: str = str(f"sqlite+aiosqlite:///{INSTANCE_DIR / f'{APP_NAME.lower()}_database.db'}")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_PRE_PING: bool = True

    # ----------- API ------------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8095
    API_RELOAD: bool = False
    API_LOG_LEVEL: str = "info"

    # ------------ Mail ------------
    MAIL_HOST: str = "smtp.google.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = "yourmail@gmail.com"
    MAIL_PASSWORD: str = "your-email-password"
    MAIL_USE_TLS: bool = True
    MAIL_USE_SSL: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **values):
        """
        Initialize configuration settings, forcing physical directory verification layout.
        """
        super().__init__(**values)
        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        try:
            self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            self.INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f" CRITICAL ERROR: Could not create directory {dir}. check permissions.")
            print(f"Errors Detail: {e}")
            sys.exit(1)

settings = Settings()
