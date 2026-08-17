"""
End-to-end live benchmark for the static nopCommerce 500-question dataset.

This runner uses the natural-language prompt as input to AEGIS's live intent
parser, then runs semantic resolution, deterministic SQL compilation, and MySQL
execution. It never generates or edits the dataset.

The committed intent annotation is used only as the expected label for scoring
parser fidelity on supported questions.
"""

from __future__ import annotations

import argparse
import asyncio
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
from aegis.server.intent_parser import IntentParser, RESOLVED_MODEL
from aegis.server.mapper import SemanticMapper
from aegis.server.models import IntentObject, Outcome

load_dotenv(ROOT / ".env")

DATASET = ROOT / "evaluation_dataset" / "nopcommerce_500_natural_questions.json"
OUT = ROOT / "evaluation_dataset" / "nopcommerce_500_live_benchmark_results.json"


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
    return len(cur.fetchall())


def intent_dict(intent: IntentObject | None) -> dict[str, Any]:
    if intent is None:
        return {}
    return intent.model_dump(mode="json")


def expected_intent(item: dict[str, Any]) -> dict[str, Any]:
    return IntentObject(**item["intent"]).model_dump(mode="json")


def same_intent(parsed: dict[str, Any], expected: dict[str, Any]) -> bool:
    fields = ["intent_class", "metric_term", "dimension_term", "time_term", "sort", "limit"]
    for field in fields:
        if parsed.get(field) != expected.get(field):
            return False
    return parsed.get("filters", []) == expected.get("filters", [])


def pct(n: int, total: int) -> float:
    return round(n / total * 100, 1) if total else 0.0


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=str(OUT))
    parser.add_argument("--limit", type=int, default=0, help="Optional first-N smoke run; 0 means all")
    parser.add_argument("--resume", action="store_true", help="Reuse existing successful records")
    args = parser.parse_args()

    data = json.loads(DATASET.read_text(encoding="utf-8"))
    questions = data["questions"][: args.limit or None]

    existing = {}
    out_path = Path(args.json)
    if args.resume and out_path.exists():
        old = json.loads(out_path.read_text(encoding="utf-8"))
        existing = {
            row["id"]: row
            for row in old.get("results", [])
            if row.get("parser_status") == "ok"
        }

    llm_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    intent_parser = IntentParser(api_key=llm_key)
    mapper = SemanticMapper()
    compiler = SQLCompiler()

    results = []
    with connect() as conn:
        cur = conn.cursor()
        for item in questions:
            if item["id"] in existing:
                results.append(existing[item["id"]])
                continue

            row = {
                "id": item["id"],
                "prompt": item["prompt"],
                "expected_outcome": item["expected_outcome"],
                "capability": item["capability"],
                "parser_status": "error",
                "resolved_model": "",
                "parsed_intent": {},
                "expected_intent": item.get("intent", {}),
                "intent_exact": False,
                "resolution_outcome": "",
                "expected_behavior_ok": False,
                "compiled": False,
                "executed": False,
                "row_count": None,
                "sql": "",
                "message": "",
                "error": "",
            }

            try:
                parsed = await intent_parser.parse(item["prompt"])
                row["parser_status"] = "ok"
                row["resolved_model"] = RESOLVED_MODEL.get()
                row["parsed_intent"] = intent_dict(parsed)

                if item["expected_outcome"] == "answer":
                    gold = expected_intent(item)
                    row["expected_intent"] = gold
                    row["intent_exact"] = same_intent(row["parsed_intent"], gold)

                resolution = mapper.resolve(parsed, item["prompt"])
                row["resolution_outcome"] = resolution.outcome.value
                row["message"] = resolution.message or ""

                if item["expected_outcome"] == "reject":
                    row["expected_behavior_ok"] = resolution.outcome in {Outcome.REJECT, Outcome.CLARIFY}
                else:
                    row["expected_behavior_ok"] = resolution.outcome == Outcome.ANSWER
                    if resolution.outcome == Outcome.ANSWER and resolution.plan is not None:
                        sql, params, _ = compiler.compile(resolution.plan)
                        row["compiled"] = True
                        row["sql"] = sql
                        row["row_count"] = execute(cur, sql, params)
                        row["executed"] = True
            except Exception as exc:
                row["error"] = str(exc)

            results.append(row)

            if len(results) % 25 == 0:
                print(f"processed {len(results)}/{len(questions)}")
                write_summary(out_path, data["name"], results)

    write_summary(out_path, data["name"], results)
    print_summary(out_path)
    return 0


def write_summary(path: Path, name: str, results: list[dict[str, Any]]) -> None:
    supported = [r for r in results if r["expected_outcome"] == "answer"]
    boundary = [r for r in results if r["expected_outcome"] == "reject"]
    metrics = {
        "parser_success": {"n": sum(1 for r in results if r["parser_status"] == "ok"), "of": len(results)},
        "supported_intent_exact": {"n": sum(1 for r in supported if r["intent_exact"]), "of": len(supported)},
        "supported_answer_rate": {"n": sum(1 for r in supported if r["expected_behavior_ok"]), "of": len(supported)},
        "supported_execution_validity": {"n": sum(1 for r in supported if r["executed"]), "of": len(supported)},
        "boundary_rejection_accuracy": {"n": sum(1 for r in boundary if r["expected_behavior_ok"]), "of": len(boundary)},
    }
    for metric in metrics.values():
        metric["value"] = pct(metric["n"], metric["of"])
    payload = {
        "benchmark": name,
        "mode": "live_natural_language_end_to_end",
        "total": len(results),
        "metrics": metrics,
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def print_summary(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    print("=" * 72)
    print("NOPCOMMERCE 500 LIVE NL BENCHMARK")
    print("=" * 72)
    for key, metric in payload["metrics"].items():
        print(f"{key:32} {metric['n']}/{metric['of']} ({metric['value']:.1f}%)")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
