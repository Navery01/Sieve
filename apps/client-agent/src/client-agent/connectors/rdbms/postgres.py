from ..base import BaseConnector
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text

class PostgresConnector(BaseConnector):
    def __init__(self):
        super().__init__()
        

    async def connect(self, host: str, user: str, password: str, dbname: str = "postgres") -> AsyncEngine:
        connection_string = f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}"
        self.engine = create_async_engine(connection_string)
        return self.engine

    async def fetch_catalog(self) -> list[str]:
        self.has_engine()

        query = text ('''SELECT datname FROM pg_database WHERE datistemplate = false;''')

        async with self.engine.connect() as conn:
            result = await conn.execute(query)
            databases = [row[0] for row in result.fetchall()]

        return databases

    async def fetch_tables(self, database: str) -> list[str]:
        self.has_engine()

        query = text(f'''SELECT CONCAT(table_schema, '.', table_name) FROM information_schema.tables WHERE table_schema = 'public' AND table_catalog = :database;''')

        async with self.engine.connect() as conn:
            result = await conn.execute(query, {"database": database})
            tables = [row[0] for row in result.fetchall()]

        return tables

    async def scan_table(self, table: str, schema: str | None = None) -> list[dict[str, object]]:
        self.has_engine()
        query = text(f'''SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = :table AND table_schema = :schema;''')

        async with self.engine.connect() as conn:
            result = await conn.execute(query, {"table": table, "schema": schema})
            columns = [dict(row) for row in result.fetchall()]

        return columns

    async def disconnect(self) -> None:
        self.has_engine()
        await self.engine.dispose()