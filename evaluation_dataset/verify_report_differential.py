"""
Differential report benchmark: AEGIS output vs. nopCommerce report oracles.

The report-suite check answers "did AEGIS produce SQL for the same admin
report request?". This script asks the stronger question: when AEGIS and the
host platform's own report logic are executed against the same seeded database,
do they return the same data?

Usage:
    python evaluation_dataset/verify_report_differential.py
    python evaluation_dataset/verify_report_differential.py --json evaluation_dataset/report_differential_results.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

REPORT_SUITE = ROOT / "evaluation_dataset" / "report_suite_results.json"
ORACLES = ROOT / "evaluation_dataset" / "nopcommerce_report_oracles.json"
OUT = ROOT / "evaluation_dataset" / "report_differential_results.json"


def connect():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "aegis"),
    )


def bind_params(sql: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    for key in params:
        sql = sql.replace(f"@{key}", f"%({key})s")
    return sql, params


def execute(cur, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    sql, bound = bind_params(sql, params or {})
    cur.execute(sql, bound)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def as_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def normalize_label(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def normalize_value(value: Any) -> Any:
    numeric = as_decimal(value)
    if numeric is not None:
        return numeric
    return normalize_label(value)


def first_value(row: dict[str, Any]) -> Any:
    if "value" in row:
        return row["value"]
    return next(iter(row.values())) if row else None


def row_label(row: dict[str, Any]) -> str:
    if "label" in row:
        return normalize_label(row["label"])
    return normalize_label(next(iter(row.values()))) if row else ""


def row_value(row: dict[str, Any]) -> Any:
    if "value" in row:
        return row["value"]
    values = list(row.values())
    return values[1] if len(values) > 1 else (values[0] if values else None)


def values_match(left: Any, right: Any, tolerance: Decimal) -> bool:
    lnum = as_decimal(left)
    rnum = as_decimal(right)
    if lnum is not None and rnum is not None:
        return abs(lnum - rnum) <= tolerance
    return normalize_label(left) == normalize_label(right)


def compare_scalar(aegis_rows, oracle_rows, tolerance: Decimal) -> tuple[bool, list[str]]:
    problems = []
    if len(aegis_rows) != 1 or len(oracle_rows) != 1:
        problems.append(f"expected one row each, got AEGIS={len(aegis_rows)} oracle={len(oracle_rows)}")
        return False, problems
    left = first_value(aegis_rows[0])
    right = first_value(oracle_rows[0])
    if not values_match(left, right, tolerance):
        problems.append(f"value mismatch: AEGIS={left!r} oracle={right!r}")
    return not problems, problems


def compare_ordered(aegis_rows, oracle_rows, tolerance: Decimal) -> tuple[bool, list[str]]:
    problems = []
    if len(aegis_rows) != len(oracle_rows):
        problems.append(f"row count mismatch: AEGIS={len(aegis_rows)} oracle={len(oracle_rows)}")
    for idx, (left, right) in enumerate(zip(aegis_rows, oracle_rows), start=1):
        if row_label(left) != row_label(right):
            problems.append(f"row {idx} label mismatch: AEGIS={row_label(left)!r} oracle={row_label(right)!r}")
            break
        if not values_match(row_value(left), row_value(right), tolerance):
            problems.append(f"row {idx} value mismatch for {row_label(left)!r}: AEGIS={row_value(left)!r} oracle={row_value(right)!r}")
            break
    return not problems, problems


def compare_rows(mode: str, aegis_rows, oracle_rows, tolerance: Decimal) -> tuple[bool, list[str]]:
    if mode == "scalar":
        return compare_scalar(aegis_rows, oracle_rows, tolerance)
    if mode == "ordered_rows":
        return compare_ordered(aegis_rows, oracle_rows, tolerance)
    return False, [f"unsupported compare mode: {mode}"]


def preview(rows: list[dict[str, Any]], limit: int = 3) -> list[dict[str, str]]:
    out = []
    for row in rows[:limit]:
        out.append({k: str(v) for k, v in row.items()})
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=str(OUT))
    args = parser.parse_args()

    suite = json.loads(REPORT_SUITE.read_text(encoding="utf-8-sig"))
    oracles = json.loads(ORACLES.read_text(encoding="utf-8"))
    suite_by_report = {r["report"]: r for r in suite["results"]}

    results = []
    with connect() as conn:
        cur = conn.cursor()
        for oracle in oracles["reports"]:
            name = oracle["report"]
            aegis = suite_by_report.get(name)
            item = {
                "report": name,
                "compare_mode": oracle["compare_mode"],
                "source": oracle["source"],
                "aegis_rows": 0,
                "oracle_rows": 0,
                "match": False,
                "problems": [],
            }
            if not aegis or not aegis.get("sql"):
                item["problems"].append("AEGIS did not produce SQL for this report")
                results.append(item)
                continue
            try:
                aegis_rows = execute(cur, aegis["sql"], aegis.get("params") or {})
                oracle_rows = execute(cur, oracle["reference_sql"], {})
                tolerance = Decimal(str(oracle.get("tolerance", 0)))
                ok, problems = compare_rows(oracle["compare_mode"], aegis_rows, oracle_rows, tolerance)
                item.update({
                    "aegis_rows": len(aegis_rows),
                    "oracle_rows": len(oracle_rows),
                    "match": ok,
                    "problems": problems,
                    "aegis_preview": preview(aegis_rows),
                    "oracle_preview": preview(oracle_rows),
                })
            except Exception as exc:
                item["problems"].append(str(exc))
            results.append(item)

    total = len(results)
    matched = sum(1 for r in results if r["match"])
    payload = {
        "total": total,
        "matched": matched,
        "accuracy": round((matched / total) * 100, 1) if total else 0.0,
        "results": results,
    }
    Path(args.json).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=" * 64)
    print("NOPCOMMERCE DIFFERENTIAL REPORT BENCHMARK")
    print("=" * 64)
    print(f"Matched reports: {matched}/{total} ({payload['accuracy']:.1f}%)")
    for r in results:
        mark = "PASS" if r["match"] else "FAIL"
        print(f"{mark:4} {r['report']}")
        for problem in r["problems"][:2]:
            print(f"     - {problem}")
    print(f"\nWrote {args.json}")
    return 0 if matched == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
