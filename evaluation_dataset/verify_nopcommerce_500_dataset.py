"""
Verify the static nopCommerce 500-question dataset.

This runner treats the dataset as a fixed research artifact. It does not
generate or mutate questions. For supported questions it uses the committed
intent annotation to exercise the deterministic AEGIS stages:

    intent -> semantic resolution -> SQL compilation -> MySQL execution

For boundary questions it verifies the expected boundary labels are present and
records them separately; live parser-based refusal measurement belongs in a
separate LLM run because it is provider/model dependent.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aegis.server.compiler import SQLCompiler
from aegis.server.mapper import SemanticMapper
from aegis.server.models import IntentObject, Outcome

sys.path.insert(0, str(Path(__file__).resolve().parent))
from timing import print_latency, stage_summary, stopwatch

#: The deterministic stages, in pipeline order. No parser stage appears here:
#: this runner feeds committed intent annotations straight to the mapper, so
#: there is no model call to time.
STAGES = ["resolve_ms", "compile_ms", "execute_ms"]

load_dotenv(ROOT / ".env")

DATASET = ROOT / "evaluation_dataset" / "nopcommerce_500_natural_questions.json"
OUT = ROOT / "evaluation_dataset" / "nopcommerce_500_dataset_results.json"


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


def execute(cur, sql: str, params: dict[str, Any] | None = None) -> int:
    sql, bound = bind_params(sql, params or {})
    cur.execute(sql, bound)
    rows = cur.fetchall()
    return len(rows)


def pct(n: int, total: int) -> float:
    return round(n / total * 100, 1) if total else 0.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=str(OUT))
    args = parser.parse_args()

    payload = json.loads(DATASET.read_text(encoding="utf-8"))
    questions = payload["questions"]
    mapper = SemanticMapper()
    compiler = SQLCompiler()

    results = []
    with connect() as conn:
        cur = conn.cursor()
        for item in questions:
            result = {
                "id": item["id"],
                "prompt": item["prompt"],
                "expected_outcome": item["expected_outcome"],
                "capability": item["capability"],
                "resolved": False,
                "compiled": False,
                "executed": False,
                "boundary_label_valid": False,
                "row_count": None,
                "sql": "",
                "error": "",
                "resolve_ms": None,
                "compile_ms": None,
                "execute_ms": None,
            }

            if item["expected_outcome"] == "reject":
                result["boundary_label_valid"] = bool(item.get("boundary_concept") and item.get("reason"))
                results.append(result)
                continue

            try:
                intent = IntentObject(**item["intent"])
                with stopwatch(result, "resolve_ms"):
                    resolution = mapper.resolve(intent, item["prompt"])
                if resolution.outcome != Outcome.ANSWER or resolution.plan is None:
                    result["error"] = resolution.message or "did not resolve to ANSWER"
                    results.append(result)
                    continue
                result["resolved"] = True

                with stopwatch(result, "compile_ms"):
                    sql, params, _ = compiler.compile(resolution.plan)
                result["compiled"] = True
                result["sql"] = sql
                with stopwatch(result, "execute_ms"):
                    result["row_count"] = execute(cur, sql, params)
                result["executed"] = True
            except Exception as exc:
                result["error"] = str(exc)

            results.append(result)

    supported = [r for r in results if r["expected_outcome"] == "answer"]
    boundary = [r for r in results if r["expected_outcome"] == "reject"]
    summary = {
        "dataset": payload["name"],
        "total": len(results),
        "supported_total": len(supported),
        "boundary_total": len(boundary),
        "metrics": {
            "supported_resolution_validity": {
                "n": sum(1 for r in supported if r["resolved"]),
                "of": len(supported),
            },
            "supported_compilation_validity": {
                "n": sum(1 for r in supported if r["compiled"]),
                "of": len(supported),
            },
            "supported_execution_validity": {
                "n": sum(1 for r in supported if r["executed"]),
                "of": len(supported),
            },
            "boundary_label_validity": {
                "n": sum(1 for r in boundary if r["boundary_label_valid"]),
                "of": len(boundary),
            },
        },
        "latency": stage_summary(supported, STAGES),
        "results": results,
    }
    for metric in summary["metrics"].values():
        metric["value"] = pct(metric["n"], metric["of"])

    Path(args.json).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("=" * 72)
    print("NOPCOMMERCE 500-QUESTION DATASET VERIFICATION")
    print("=" * 72)
    for name, metric in summary["metrics"].items():
        print(f"{name:34} {metric['n']}/{metric['of']} ({metric['value']:.1f}%)")
    print_latency("Deterministic stage latency (supported questions)", summary["latency"])
    failures = [r for r in supported if not r["executed"]]
    if failures:
        print()
        for failure in failures[:20]:
            print(f"FAIL {failure['id']} {failure['prompt']}")
            print(f"     - {failure['error']}")
    print(f"\nWrote {args.json}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
