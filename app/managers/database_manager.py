"""
Módulo de gestión de la base de datos asíncrona utilizando SQLAlchemy y SQLModel.
Este módulo define la clase `DatabaseManager`, que implementa un patrón singleton para gestionar la conexión a la base de datos y la creación de sesiones asíncronas. Proporciona métodos para inicializar la base de datos, obtener sesiones y configurar parámetros específicos de SQLite para mejorar el rendimiento y la concurrencia.
El `DatabaseManager` asegura que solo exista una instancia del motor de base de datos y del generador de sesiones, facilitando la gestión de la base de datos en toda la aplicación.
"""
import logging
from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.settings.app_settings import Settings, settings

class DatabaseManager:
    """
    Conexión y gestión de la base de datos asíncrona utilizando SQLAlchemy y SQLModel.
    Esta clase implementa como un singleton para asegurar que solo exista una instancia del motor de base de datos y del generador de sesiones.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Implementa un patrón singleton para asegurar que solo exista una instancia de DatabaseManager.

        Returns:
            DatabaseManager: Instancia única del DatabaseManager
        """
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, settings: Settings):
        """
        Inicializa el motor asíncrono de la base de datos y el generador de sesiones.

        Args:
            settings (Settings): Ajustes de configuración que contienen la URL de la base de datos y otros parámetros.
        """
        if self._initialized:
            return

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Initializing engine at: {settings.DATABASE_URL}")

        self.engine = create_async_engine(
            url=settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
            connect_args={"check_same_thread": False}
        )

        event.listen(
            self.engine.sync_engine,
            "connect",
            self._set_sqlite_pragma
        )

        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self._initialized = True

    @staticmethod
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        """
        Configura los parámetros PRAGMA de SQLite para mejorar el rendimiento y la concurrencia.

        Args:
            dbapi_connection: La conexión DBAPI subyacente (por ejemplo, sqlite3.Connection).
            _connection_record: El objeto de registro de conexión interno de SQLAlchemy.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    async def init_db(self) -> None:
        """
        Crea todas las tablas definidas en los modelos SQLModel en la base de datos.

        Raises:
            Exception: Si la inicialización de la base de datos falla, se lanza una excepción con el error correspondiente.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            self.logger.info("Base de datos inicializada correctamente.")
        except Exception as e:
            self.logger.error(f"Error inicializando la base de datos: {e}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provee una sesión asíncrona de la base de datos para operaciones CRUD.

        Yields:
            AsyncSession: Sesión activa vinculada al motor asíncrono.
        """
        async with self.async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()


db_manager = DatabaseManager(settings=settings)
