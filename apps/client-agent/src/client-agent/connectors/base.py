# connectors/base.py
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def fetch_tables(self) -> list[str]: ...

    @abstractmethod
    async def scan_table(self, table: str) -> list[dict]: ...

    @abstractmethod
    async def disconnect(self) -> None: ...