# TODO (Production Hardening):
#
# Security:
#   - Use sqlalchemy.engine.URL.create() instead of a raw f-string DSN to prevent
#     password exposure in SQLAlchemy debug logs (connect(), line ~59).
#   - Add SSL/TLS support via connect_args={"ssl": ...} in create_async_engine().
#
# Reliability:
#   - Verify the connection in connect() with a SELECT 1 probe; create_async_engine()
#     is lazy and won't fail on bad credentials/host until first use.
#   - Tune connection pool settings (pool_size, max_overflow, pool_recycle, pool_timeout).
#   - Add query timeouts via connect_args={"command_timeout": N} or SET statement_timeout
#     to prevent runaway SELECT * queries from hanging indefinitely.
#
# Performance:
#   - Cap the enrichment loop in fetch_sample_data() — a table with many all-NULL columns
#     fires one query per column with no upper bound.
#   - Replace the `candidate_row in rows` linear scan with a set of row fingerprints
#     (e.g. frozenset of items) to avoid quadratic dict comparisons on large rows.
#
# Usability:
#   - Implement __aenter__ / __aexit__ so callers can use `async with` and avoid
#     leaking connections when disconnect() is forgotten.
#   - Filter pg_temp_* schemas in fetch_schemas() to exclude temporary schemas from
#     other sessions.

from .base_connector import RDBMSBaseConnector
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


class PostgresConnector(RDBMSBaseConnector):
    """PostgreSQL connector backed by SQLAlchemy's async engine (asyncpg driver).

    Implements the full :class:`RDBMSBaseConnector` interface for PostgreSQL,
    covering connection lifecycle, catalog/schema/table discovery, column
    introspection, and row sampling.

    Typical usage::

        connector = PostgresConnector()
        await connector.connect(host="localhost", user="app", password="secret")
        schemas = await connector.fetch_schemas()
        tables  = await connector.fetch_tables(schemas[0])
        columns = await connector.fetch_columns(tables[0], schemas[0])
        rows    = await connector.fetch_sample_data(tables[0], schemas[0])
        await connector.disconnect()
    """

    def __init__(self):
        super().__init__()

    def is_valid_identifier(self, identifier: str) -> bool:
        """Validate identifier according to PostgreSQL naming constraints.

        We treat inputs as raw identifier names (not pre-quoted SQL snippets).
        PostgreSQL identifiers must be non-empty, cannot contain a NULL byte,
        and are effectively limited to 63 bytes by default.
        """
        if not identifier or "\x00" in identifier:
            return False
        return len(identifier.encode("utf-8")) <= 63

    def quote_identifier(self, identifier: str) -> str:
        """Return a safely quoted PostgreSQL identifier."""
        return '"' + identifier.replace('"', '""') + '"'

    async def connect(
        self,
        host: str,
        user: str,
        password: str,
        dbname: str = "postgres",
        port: int = 5432,
    ) -> None:
        """Create an async engine connected to the given PostgreSQL instance.

        Args:
            host:     Hostname or IP of the PostgreSQL server.
            user:     Database user name.
            password: Password for the database user.
            dbname:   Target database name. Defaults to ``"postgres"``.
            port:     Server port. Defaults to ``5432``.
        """
        connection_string = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"
        self.engine = create_async_engine(connection_string)

    async def fetch_catalog(self) -> list[str]:
        """Return the names of all user databases on this server.

        System template databases (``template0``, ``template1``) are excluded.
        """
        self.has_engine()
        query = text("SELECT datname FROM pg_database WHERE datistemplate = false")
        async with self.engine.connect() as conn:
            result = await conn.execute(query)
            return [row[0] for row in result.fetchall()]

    async def fetch_schemas(self) -> list[str]:
        """Return non-system schema names in the connected database, sorted alphabetically.

        Excludes ``pg_catalog``, ``information_schema``, and internal
        ``pg_toast*`` schemas.
        """
        self.has_engine()
        query = text(
            "SELECT schema_name FROM information_schema.schemata"
            " WHERE schema_name NOT IN ('pg_catalog', 'information_schema')"
            " AND schema_name NOT LIKE 'pg_toast%'"
            " ORDER BY schema_name"
        )
        async with self.engine.connect() as conn:
            result = await conn.execute(query)
            return [row[0] for row in result.fetchall()]

    async def fetch_tables(self, schema: str) -> list[str]:
        """Return unqualified base-table names for the given schema, sorted alphabetically.

        Args:
            schema: Schema to list tables from (e.g. ``"public"``).
        """
        self.has_engine()
        query = text(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema = :schema AND table_type = 'BASE TABLE'"
            " ORDER BY table_name"
        )
        async with self.engine.connect() as conn:
            result = await conn.execute(query, {"schema": schema})
            return [row[0] for row in result.fetchall()]

    async def fetch_columns(self, table: str, schema: str) -> list[dict[str, str]]:
        """Return column metadata for the given table, ordered by ordinal position.

        Each dict contains:
            - ``column_name``: the column identifier.
            - ``data_type``: the SQL data type string (e.g. ``"character varying"``).

        Args:
            table:  Unqualified table name.
            schema: Schema that owns the table.
        """
        self.has_engine()
        query = text(
            "SELECT column_name, data_type"
            " FROM information_schema.columns"
            " WHERE table_name = :table AND table_schema = :schema"
            " ORDER BY ordinal_position"
        )
        async with self.engine.connect() as conn:
            result = await conn.execute(query, {"table": table, "schema": schema})
            return [dict(row._mapping) for row in result.fetchall()]

    async def fetch_sample_data(
        self,
        table: str,
        schema: str,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        """Return up to *limit* rows from the given table as a list of dicts.

        Because ``table`` and ``schema`` are interpolated as SQL identifiers,
        they are validated using PostgreSQL identifier constraints and then
        safely quoted before query execution.

        Sampling is performed in two passes:
        1) Fetch an initial ``SELECT * ... LIMIT :limit`` core sample.
        2) If columns are entirely NULL in that core sample, probe per-column
              with ``WHERE <column> IS NOT NULL LIMIT 1`` to enrich coverage.
              When already at ``limit``, enrichment may replace low-information
              rows to improve overall column coverage.

        Args:
            table:  Unqualified table name.
            schema: Schema that owns the table.
            limit:  Maximum number of rows to return. Defaults to ``100``.

        Raises:
            ValueError: If ``table`` or ``schema`` fail PostgreSQL identifier validation.
        """
        self.has_engine()
        # Identifiers are not bind parameters; validate and quote explicitly.
        if not self.is_valid_identifier(table) or not self.is_valid_identifier(schema):
            raise ValueError(f"Invalid table or schema name: {schema}.{table}")
        if limit <= 0:
            return []

        quoted_schema = self.quote_identifier(schema)
        quoted_table = self.quote_identifier(table)

        base_query = text(f"SELECT * FROM {quoted_schema}.{quoted_table} LIMIT :limit")
        columns_query = text(
            "SELECT column_name"
            " FROM information_schema.columns"
            " WHERE table_name = :table AND table_schema = :schema"
            " ORDER BY ordinal_position"
        )

        async with self.engine.connect() as conn:
            base_result = await conn.execute(base_query, {"limit": limit})
            rows = [dict(row._mapping) for row in base_result.fetchall()]

            columns_result = await conn.execute(columns_query, {"table": table, "schema": schema})
            column_names = [row[0] for row in columns_result.fetchall()]

            # Probe sparse columns individually to improve sample usefulness.
            for column_name in column_names:
                if any(row.get(column_name) is not None for row in rows):
                    continue
                if not self.is_valid_identifier(column_name):
                    continue

                quoted_column = self.quote_identifier(column_name)
                enrich_query = text(
                    f"SELECT * FROM {quoted_schema}.{quoted_table}"
                    f" WHERE {quoted_column} IS NOT NULL LIMIT 1"
                )
                enrich_result = await conn.execute(enrich_query)
                candidate = enrich_result.fetchone()
                if candidate is None:   # No non-NULL values in this column, skip enrichment.
                    continue

                candidate_row = dict(candidate._mapping)
                if candidate_row in rows:   # Candidate row is already in the sample, skip.
                    continue

                if len(rows) < limit:
                    rows.append(candidate_row)
                    continue

                replacement_index = None 
                replacement_score = len(rows[0]) + 1 if rows else 1 
                for index, existing_row in enumerate(rows): # Find a row with fewer non-NULL values than the candidate to replace.
                    if existing_row.get(column_name) is not None:
                        continue
                    non_null_count = sum(value is not None for value in existing_row.values())
                    if replacement_index is None or non_null_count < replacement_score:
                        replacement_index = index
                        replacement_score = non_null_count

                if replacement_index is not None:
                    rows[replacement_index] = candidate_row

            return rows[:limit]

    async def disconnect(self) -> None:
        """Dispose of the async engine and release all pooled connections."""
        self.has_engine()
        await self.engine.dispose()
