from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """
    Root base class for all data-source connectors.

    Connectors are responsible solely for data access: establishing connections,
    enumerating structure (catalogs, schemas, tables, columns), and fetching
    raw data rows.  PII detection and analysis is handled at the agent layer.
    """

    @abstractmethod
    async def disconnect(self) -> None:
        """Tear down the connection and release resources."""
        ...

    def has_engine(self) -> None:
        """Raise if the underlying engine/connection has not been initialised."""
        if not getattr(self, "engine", None):
            raise RuntimeError(
                "Not connected to the data source. Call connect() first."
            )
