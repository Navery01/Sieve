import asyncio
import importlib
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src" / "client-agent"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

PostgresConnector = importlib.import_module("connectors.rdbms.postgres_connector").PostgresConnector


class FakeRow:
    def __init__(self, mapping: dict[str, object]):
        self._mapping = mapping

    def __getitem__(self, index: int) -> object:
        if not isinstance(index, int):
            raise TypeError("FakeRow only supports integer indexing")
        return list(self._mapping.values())[index]


class FakeResult:
    def __init__(self, rows: list[dict[str, object]]):
        self._rows = rows

    def fetchall(self):
        return [FakeRow(row) for row in self._rows]

    def fetchone(self):
        if not self._rows:
            return None
        return FakeRow(self._rows[0])


class FakeConnectionContext:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_connector_with_execute_results(results: list[FakeResult]):
    connector = PostgresConnector()

    conn = MagicMock()
    conn.execute = AsyncMock(side_effect=results)

    engine = MagicMock()
    engine.connect.return_value = FakeConnectionContext(conn)

    connector.engine = engine
    return connector


def test_identifier_validation_and_quoting() -> None:
    connector = PostgresConnector()

    assert connector.is_valid_identifier("public")
    assert connector.is_valid_identifier("users_table")
    assert not connector.is_valid_identifier("")
    assert not connector.is_valid_identifier("bad\x00name")
    assert not connector.is_valid_identifier("a" * 64)

    assert connector.quote_identifier("public") == '"public"'
    assert connector.quote_identifier('my"schema') == '"my""schema"'


def test_fetch_sample_data_rejects_invalid_identifiers() -> None:
    connector = PostgresConnector()
    connector.engine = MagicMock()

    try:
        asyncio.run(connector.fetch_sample_data("bad\x00table", "public"))
        assert False, "Expected ValueError for invalid identifier"
    except ValueError as exc:
        assert "Invalid table or schema name" in str(exc)


def test_fetch_sample_data_enriches_sparse_columns_when_below_limit() -> None:
    connector = make_connector_with_execute_results(
        [
            FakeResult(
                [
                    {"id": 1, "name": None, "email": None},
                    {"id": 2, "name": "Alice", "email": None},
                ]
            ),
            FakeResult(
                [
                    {"column_name": "id"},
                    {"column_name": "name"},
                    {"column_name": "email"},
                ]
            ),
            FakeResult(
                [
                    {"id": 3, "name": "Bob", "email": "bob@example.com"},
                ]
            ),
        ]
    )

    rows = asyncio.run(connector.fetch_sample_data("users", "public", limit=5))

    assert len(rows) == 3
    assert any(row.get("email") is not None for row in rows)


def test_fetch_sample_data_replaces_low_information_row_at_limit() -> None:
    connector = make_connector_with_execute_results(
        [
            FakeResult(
                [
                    {"id": 1, "name": "A", "email": None},
                    {"id": 2, "name": "B", "email": None},
                ]
            ),
            FakeResult(
                [
                    {"column_name": "id"},
                    {"column_name": "name"},
                    {"column_name": "email"},
                ]
            ),
            FakeResult(
                [
                    {"id": 3, "name": "C", "email": "c@example.com"},
                ]
            ),
        ]
    )

    rows = asyncio.run(connector.fetch_sample_data("users", "public", limit=2))

    assert len(rows) == 2
    assert any(row.get("email") is not None for row in rows)
    assert any(row.get("id") == 3 for row in rows)
