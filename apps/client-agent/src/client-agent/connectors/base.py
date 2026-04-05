# connectors/base.py
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

class BaseConnector(ABC):
    @abstractmethod
    async def connect(self, host: str, user: str, password: str, dbname: str) -> AsyncEngine: ...

    @abstractmethod
    async def fetch_catalog(self) -> list[str]: ...

    @abstractmethod
    async def fetch_tables(self, database: str) -> list[str]: ...

    @abstractmethod
    async def scan_table(self, table: str, schema: str | None = None) -> list[dict[str, object]]: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    def has_engine(self) -> None:
        """Helper method to check if the engine is initialized."""
        if not hasattr(self, 'engine'):
            raise Exception("Not connected to the database. Please call connect() first.")