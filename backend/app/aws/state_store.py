"""State stores: SQLite (local) and DynamoDB (cloud).

Persists per-request POMDP episode traces keyed by request id. Values are JSON
documents. The SQLite store is used locally and in CI; the DynamoDB store uses
the default credential chain in the cloud.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.aws.interfaces import StateStore


class SQLiteStateStore(StateStore):
    """Local SQLite-backed key/value store for episode traces."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False so the FastAPI threadpool can share it safely
        # (all access is short, single-statement, and serialised by SQLite).
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS episodes (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._conn.commit()

    def put(self, key: str, value: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO episodes (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        self._conn.commit()

    def get(self, key: str) -> dict | None:
        cursor = self._conn.execute(
            "SELECT value FROM episodes WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None


class DynamoDBStateStore(StateStore):
    """Amazon DynamoDB state store (cloud mode)."""

    def __init__(self, table_name: str, region: str) -> None:
        if not table_name:
            raise ValueError("DynamoDB table name is required in cloud mode")
        import boto3  # lazy import

        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def put(self, key: str, value: dict) -> None:
        self._table.put_item(Item={"request_id": key, "trace": json.dumps(value)})

    def get(self, key: str) -> dict | None:
        response = self._table.get_item(Key={"request_id": key})
        item = response.get("Item")
        return json.loads(item["trace"]) if item else None
