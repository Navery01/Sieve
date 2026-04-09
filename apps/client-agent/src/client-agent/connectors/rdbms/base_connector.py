from abc import abstractmethod
from ..base_connector import BaseConnector


class RDBMSBaseConnector(BaseConnector):
    """
    Base class for relational database connectors.

    Extends BaseConnector with the full set of methods a structured crawler
    needs to enumerate and read from an RDBMS: catalog listing, schema/table
    discovery, column introspection, and row sampling.

    All methods assume connect() has already been called successfully.
    """

    @abstractmethod
    async def connect(
        self,
        host: str,
        user: str,
        password: str,
        dbname: str,
        port: int = 5432,
    ) -> None:
        """Connect to the given database instance."""
        ...


    @abstractmethod
    async def fetch_catalog(self) -> list[str]:
        """Return the names of all user databases on this server."""
        ...

    @abstractmethod
    async def fetch_schemas(self) -> list[str]:
        """Return the names of all non-system schemas in the current database."""
        ...

    @abstractmethod
    async def fetch_tables(self, schema: str) -> list[str]:
        """Return unqualified table names for the given schema."""
        ...

    @abstractmethod
    async def fetch_columns(self, table: str, schema: str) -> list[dict[str, str]]:
        """
        Return column-level metadata for the given table.

        Each dict contains at minimum:
            column_name : str
            data_type   : str
        """
        ...

    @abstractmethod
    def is_valid_identifier(self, identifier: str) -> bool:
        """Return True when *identifier* is safe/valid for this SQL dialect."""
        ...

    @abstractmethod
    def quote_identifier(self, identifier: str) -> str:
        """Return a safely quoted identifier for this SQL dialect."""
        ...

    # ------------------------------------------------------------------
    # Data access — used by agents after crawlers identify targets
    # ------------------------------------------------------------------

    @abstractmethod
    async def fetch_sample_data(
        self,
        table: str,
        schema: str,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        """
        Return up to *limit* rows from the given table as a list of dicts.

        Callers (typically agents) use this to analyse actual data for PII.
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None: ...
