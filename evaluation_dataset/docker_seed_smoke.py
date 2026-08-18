"""
Docker seed smoke check for AEGIS.

This intentionally avoids live LLM calls. It verifies that the Docker MySQL
seed loaded and that the deterministic AEGIS mapper/compiler can execute a
representative matrix query against that seeded database.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aegis.server.compiler import SQLCompiler
from aegis.server.mapper import SemanticMapper
from aegis.server.models import IntentObject, Outcome

load_dotenv(ROOT / ".env")


def connect():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "aegis"),
    )


def bind_params(sql: str, params: dict):
    for key in params:
        sql = sql.replace(f"@{key}", f"%({key})s")
    return sql


def scalar(cur, sql: str) -> int:
    cur.execute(sql)
    return int(cur.fetchone()[0])


def main() -> int:
    mapper = SemanticMapper()
    compiler = SQLCompiler()

    with connect() as conn:
        cur = conn.cursor()
        counts = {
            "Order": scalar(cur, "SELECT COUNT(*) FROM `Order`"),
            "OrderItem": scalar(cur, "SELECT COUNT(*) FROM `OrderItem`"),
            "Product": scalar(cur, "SELECT COUNT(*) FROM `Product`"),
            "Customer": scalar(cur, "SELECT COUNT(*) FROM `Customer`"),
        }
        empty = [name for name, count in counts.items() if count <= 0]
        if empty:
            raise RuntimeError(f"seed tables are empty: {', '.join(empty)}")

        intent = IntentObject(
            intent_class="segment",
            metric_term="avg_order_value",
            dimension_term="order_status",
        )
        result = mapper.resolve(
            intent,
            question="Show the dashboard order average report by status",
        )
        if result.outcome != Outcome.ANSWER or result.plan is None:
            raise RuntimeError(f"AEGIS did not answer smoke intent: {result.outcome}")

        sql, params, _ = compiler.compile(result.plan)
        cur.execute(bind_params(sql, params), params)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]

        expected_columns = ["label", "today", "week", "month", "year", "all_time"]
        if columns != expected_columns:
            raise RuntimeError(f"unexpected matrix columns: {columns}")
        if len(rows) < 4:
            raise RuntimeError(f"expected at least four status rows, got {len(rows)}")

    print("Docker seed smoke passed")
    print(f"Seed counts: {counts}")
    print(f"Matrix columns: {expected_columns}")
    print(f"Matrix rows: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
