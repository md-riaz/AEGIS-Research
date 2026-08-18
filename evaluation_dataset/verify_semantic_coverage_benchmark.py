"""
nopCommerce Semantic Coverage Benchmark for AEGIS.

This benchmark complements the built-in admin analytics oracle. It asks natural
questions over the deployed nopCommerce semantic layer and compares the result
against reference SQL written from the same Approved metric/dimension
definitions. Boundary tasks are expected to be declined.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aegis.server.compiler import SQLCompiler
from aegis.server.intent_parser import IntentParser
from aegis.server.mapper import SemanticMapper
from aegis.server.models import IntentObject, Outcome

load_dotenv(ROOT / ".env")

QUESTIONS = ROOT / "evaluation_dataset" / "nopcommerce_semantic_coverage_questions.json"
OUT = ROOT / "evaluation_dataset" / "semantic_coverage_benchmark_results.json"


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


def dec(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def label(row: dict[str, Any]) -> str:
    if "label" in row:
        return "" if row["label"] is None else str(row["label"])
    return "" if not row else str(next(iter(row.values())))


def value(row: dict[str, Any]) -> Any:
    if "value" in row:
        return row["value"]
    vals = list(row.values())
    return vals[1] if len(vals) > 1 else (vals[0] if vals else None)


def same_value(left: Any, right: Any, tolerance: Decimal) -> bool:
    lnum = dec(left)
    rnum = dec(right)
    if lnum is not None and rnum is not None:
        return abs(lnum - rnum) <= tolerance
    return ("" if left is None else str(left)) == ("" if right is None else str(right))


def compare_scalar(aegis_rows, oracle_rows, tolerance: Decimal) -> list[str]:
    if len(aegis_rows) != 1 or len(oracle_rows) != 1:
        return [f"expected one row each, got AEGIS={len(aegis_rows)} oracle={len(oracle_rows)}"]
    if not same_value(value(aegis_rows[0]), value(oracle_rows[0]), tolerance):
        return [f"value mismatch: AEGIS={value(aegis_rows[0])!r} oracle={value(oracle_rows[0])!r}"]
    return []


def compare_label_rows(aegis_rows, oracle_rows) -> list[str]:
    left = [label(r) for r in aegis_rows]
    right = [label(r) for r in oracle_rows]
    if left != right:
        return [f"label rows mismatch: AEGIS={left[:5]!r} oracle={right[:5]!r}"]
    return []


def compare_ordered(aegis_rows, oracle_rows, tolerance: Decimal) -> list[str]:
    problems = []
    if len(aegis_rows) != len(oracle_rows):
        problems.append(f"row count mismatch: AEGIS={len(aegis_rows)} oracle={len(oracle_rows)}")
    for idx, (left, right) in enumerate(zip(aegis_rows, oracle_rows), start=1):
        if label(left) != label(right):
            problems.append(f"row {idx} label mismatch: AEGIS={label(left)!r} oracle={label(right)!r}")
            break
        if not same_value(value(left), value(right), tolerance):
            problems.append(f"row {idx} value mismatch for {label(left)!r}: AEGIS={value(left)!r} oracle={value(right)!r}")
            break
    return problems


def compare_table(aegis_rows, oracle_rows, tolerance: Decimal) -> list[str]:
    problems = compare_ordered(aegis_rows, oracle_rows, tolerance)
    if problems:
        return problems
    if not aegis_rows and not oracle_rows:
        return []
    common = [c for c in oracle_rows[0].keys() if c in aegis_rows[0]]
    if not common:
        return [f"table columns mismatch: AEGIS={list(aegis_rows[0].keys())} oracle={list(oracle_rows[0].keys())}"]
    for i, (left, right) in enumerate(zip(aegis_rows, oracle_rows), start=1):
        for col in common:
            if not same_value(left.get(col), right.get(col), tolerance):
                return [f"row {i} column {col!r} mismatch: AEGIS={left.get(col)!r} oracle={right.get(col)!r}"]
    return []


def compare(mode: str, aegis_rows, oracle_rows, tolerance: Decimal) -> list[str]:
    if mode == "scalar":
        return compare_scalar(aegis_rows, oracle_rows, tolerance)
    if mode == "label_rows":
        return compare_label_rows(aegis_rows, oracle_rows)
    if mode == "ordered_rows":
        return compare_ordered(aegis_rows, oracle_rows, tolerance)
    if mode == "table_rows":
        return compare_table(aegis_rows, oracle_rows, tolerance)
    return [f"unsupported compare mode: {mode}"]


def shape_ok(shape: str, rows: list[dict[str, Any]]) -> tuple[bool, str]:
    if not rows:
        return True, "empty result is shape-compatible"
    cols = set(rows[0].keys())
    if shape == "scalar":
        return len(rows) == 1 and bool(cols), ""
    if shape in {"trend", "ranking"}:
        return {"label", "value"}.issubset(cols), f"expected label/value columns, got {sorted(cols)}"
    if shape == "table":
        return len(cols) >= 1, ""
    return False, f"unknown shape {shape}"


async def compile_aegis(task: dict[str, Any], parser, mapper, compiler) -> dict[str, Any]:
    item = {"outcome": "error", "sql": "", "params": {}, "message": "", "error": ""}
    try:
        if task.get("intent_override"):
            intent = IntentObject(**task["intent_override"])
        else:
            intent = await parser.parse(task["prompt"])
        resolution = mapper.resolve(intent, task["prompt"])
        if resolution.outcome != Outcome.ANSWER:
            item["outcome"] = resolution.outcome.value
            item["message"] = resolution.message
            return item
        sql, params, _ = compiler.compile(resolution.plan)
        item.update({"outcome": "answer", "sql": sql, "params": params, "message": resolution.message})
    except Exception as exc:
        item["error"] = str(exc)
    return item


def preview(rows: list[dict[str, Any]], limit: int = 3) -> list[dict[str, str]]:
    return [{k: str(v) for k, v in row.items()} for row in rows[:limit]]


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=str(OUT))
    args = parser.parse_args()

    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    llm_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    intent_parser = IntentParser(api_key=llm_key)
    mapper = SemanticMapper()
    compiler = SQLCompiler()

    results = []
    with connect() as conn:
        cur = conn.cursor()
        for task in data["tasks"]:
            aegis = await compile_aegis(task, intent_parser, mapper, compiler)
            expected = task["expected_outcome"]
            result = {
                "id": task["id"],
                "capability": task["capability"],
                "prompt": task["prompt"],
                "expected_outcome": expected,
                "aegis": aegis,
                "execution_valid": False,
                "shape_valid": False,
                "result_valid": False,
                "boundary_valid": False,
                "problems": [],
            }

            aegis_rows = []
            oracle_rows = []
            if expected == "reject":
                result["boundary_valid"] = aegis["outcome"] in {"reject", "clarify"}
                if not result["boundary_valid"]:
                    result["problems"].append("expected boundary rejection, but AEGIS answered")
                result["result_valid"] = result["boundary_valid"]
            elif aegis["outcome"] == "answer" and aegis["sql"]:
                try:
                    oracle_rows = execute(cur, task["reference_sql"], {})
                    aegis_rows = execute(cur, aegis["sql"], aegis.get("params") or {})
                    result["execution_valid"] = True
                    ok, shape_problem = shape_ok(task["shape"], aegis_rows)
                    result["shape_valid"] = ok
                    if not ok:
                        result["problems"].append(shape_problem)
                    tolerance = Decimal(str(task.get("tolerance", 0.01)))
                    compare_problems = compare(task["compare_mode"], aegis_rows, oracle_rows, tolerance)
                    result["result_valid"] = not compare_problems
                    result["problems"].extend(compare_problems)
                except Exception as exc:
                    result["problems"].append(str(exc))
            else:
                result["problems"].append(aegis.get("message") or aegis.get("error") or "AEGIS did not answer")

            result["oracle_rows"] = len(oracle_rows)
            result["oracle_preview"] = preview(oracle_rows)
            result["aegis_rows"] = len(aegis_rows)
            result["aegis_preview"] = preview(aegis_rows)
            results.append(result)

    supported = [r for r in results if r["expected_outcome"] == "answer"]
    boundary = [r for r in results if r["expected_outcome"] == "reject"]
    metrics = {
        "supported_execution_validity": {
            "n": sum(1 for r in supported if r["execution_valid"]),
            "of": len(supported),
        },
        "supported_shape_accuracy": {
            "n": sum(1 for r in supported if r["shape_valid"]),
            "of": len(supported),
        },
        "supported_result_accuracy": {
            "n": sum(1 for r in supported if r["result_valid"]),
            "of": len(supported),
        },
        "boundary_rejection_accuracy": {
            "n": sum(1 for r in boundary if r["boundary_valid"]),
            "of": len(boundary),
        },
    }
    for metric in metrics.values():
        metric["value"] = round(metric["n"] / metric["of"] * 100, 1) if metric["of"] else 0.0

    payload = {
        "benchmark": data["name"],
        "total": len(results),
        "supported_total": len(supported),
        "boundary_total": len(boundary),
        "metrics": metrics,
        "results": results,
    }
    Path(args.json).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=" * 72)
    print("NOPCOMMERCE SEMANTIC COVERAGE BENCHMARK")
    print("=" * 72)
    for key, metric in metrics.items():
        print(f"{key:30} {metric['n']}/{metric['of']} ({metric['value']:.1f}%)")
    print()
    for r in results:
        passed = r["boundary_valid"] if r["expected_outcome"] == "reject" else r["result_valid"]
        mark = "PASS" if passed else "FAIL"
        print(f"{mark:4} {r['id']} {r['prompt']}")
        for problem in r["problems"][:2]:
            print(f"     - {problem}")
    print(f"\nWrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
