"""Durable, local, read-only-queryable research catalog backed by SQLite."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1


class CatalogStore:
    def __init__(self, path: Path):
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS catalog_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY, record_schema_version INTEGER NOT NULL, kind TEXT NOT NULL,
            identity_json TEXT NOT NULL, build_scope_json TEXT NOT NULL, state TEXT NOT NULL,
            confidence TEXT NOT NULL, supported_claims_json TEXT NOT NULL,
            unsupported_claims_json TEXT NOT NULL, open_questions_json TEXT NOT NULL,
            contradictions_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS evidence (
            record_id TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            path TEXT NOT NULL, PRIMARY KEY(record_id, path)
        );
        CREATE TABLE IF NOT EXISTS contradictions (
            id TEXT PRIMARY KEY, record_id TEXT NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            claim_a TEXT NOT NULL, claim_b TEXT NOT NULL, status TEXT NOT NULL,
            resolution TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_records_kind_state ON records(kind, state);
        CREATE INDEX IF NOT EXISTS idx_evidence_path ON evidence(path);
        INSERT OR REPLACE INTO catalog_meta(key, value) VALUES ('schema_version', '1');
        """)
        self.connection.commit()

    def import_records(self, records: Iterable[dict[str, Any]]) -> int:
        count = 0
        with self.connection:
            for record in records:
                self.connection.execute(
                    """INSERT OR REPLACE INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (record["id"], record.get("record_schema_version", 1), record["kind"],
                     json.dumps(record["identity"], sort_keys=True), json.dumps(record.get("build_scope", [])),
                     record["state"], record.get("confidence", "unknown"),
                     json.dumps(record.get("supported_claims", [])), json.dumps(record.get("unsupported_claims", [])),
                     json.dumps(record.get("open_questions", [])), json.dumps(record.get("contradictions", []))),
                )
                self.connection.execute("DELETE FROM evidence WHERE record_id = ?", (record["id"],))
                self.connection.executemany("INSERT INTO evidence VALUES (?, ?)", [(record["id"], path) for path in record["evidence"]])
                count += 1
        return count

    def records(self, *, kind: str | None = None, state: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM records WHERE 1=1"
        args: list[str] = []
        if kind:
            query += " AND kind = ?"; args.append(kind)
        if state:
            query += " AND state = ?"; args.append(state)
        query += " ORDER BY id"
        rows = self.connection.execute(query, args).fetchall()
        output = []
        for row in rows:
            evidence = self.connection.execute("SELECT path FROM evidence WHERE record_id = ? ORDER BY path", (row["id"],)).fetchall()
            output.append({"record_schema_version": row["record_schema_version"], "id": row["id"], "kind": row["kind"],
                           "identity": json.loads(row["identity_json"]), "build_scope": json.loads(row["build_scope_json"]),
                           "state": row["state"], "confidence": row["confidence"],
                           "supported_claims": json.loads(row["supported_claims_json"]),
                           "unsupported_claims": json.loads(row["unsupported_claims_json"]),
                           "open_questions": json.loads(row["open_questions_json"]),
                           "contradictions": json.loads(row["contradictions_json"]),
                           "evidence": [item["path"] for item in evidence]})
        return output

    def close(self) -> None:
        self.connection.close()

    def add_contradiction(self, contradiction: dict[str, str]) -> None:
        if contradiction.get("status") not in {"open", "resolved", "accepted-uncertainty"}:
            raise ValueError("invalid contradiction status")
        with self.connection:
            self.connection.execute("INSERT OR REPLACE INTO contradictions VALUES (?, ?, ?, ?, ?, ?)",
                                    (contradiction["id"], contradiction["record_id"], contradiction["claim_a"],
                                     contradiction["claim_b"], contradiction["status"], contradiction.get("resolution", "")))

    def resolve_contradiction(self, contradiction_id: str, status: str, resolution: str) -> None:
        if status not in {"resolved", "accepted-uncertainty"} or not resolution.strip():
            raise ValueError("a contradiction resolution needs a terminal status and explanation")
        with self.connection:
            updated = self.connection.execute("UPDATE contradictions SET status = ?, resolution = ? WHERE id = ?",
                                              (status, resolution, contradiction_id)).rowcount
        if not updated:
            raise KeyError(contradiction_id)

    def unresolved_contradictions(self) -> list[dict[str, str]]:
        rows = self.connection.execute("SELECT * FROM contradictions WHERE status = 'open' ORDER BY id").fetchall()
        return [dict(row) for row in rows]
