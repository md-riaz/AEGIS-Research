# -*- coding: utf-8 -*-
"""Gather the extra evaluation evidence requested by the supervisor.

This script keeps new evidence in sidecar JSON files and does not overwrite the
original benchmark outputs. It can:

1. Replay recorded SQL for B1, AEGIS, and B3 against MySQL.
2. Measure deterministic B3 classification/compile/execute latency.
3. Optionally rerun the AEGIS LLM intent pipeline to collect stage latency.
4. Create a semantic-correctness annotation template for human scoring.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "evaluation_dataset"
QUESTIONS_FILE = DATA_DIR / "questions.json"
SUMMARY_FILE = DATA_DIR / "supervisor_metric_summary.json"
B3_LATENCY_FILE = DATA_DIR / "latency_results_b3.json"
AEGIS_LATENCY_FILE = DATA_DIR / "latency_results_aegis.json"
ANNOTATION_FILE = DATA_DIR / "semantic_correctness_annotation_template.json"

DANGEROUS_KEYWORDS = [
    "drop",
    "delete",
    "update",
    "insert",
    "truncate",
    "alter",
    "create",
    "grant",
    "revoke",
    "exec",
    "xp_",
]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def clean_sql(sql: str) -> str:
    if not sql:
        return ""
    matches = re.findall(r"```(?:sql)?\s*(.*?)```", sql, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    return sql.strip()


def is_unsafe_sql(sql: str) -> bool:
    lower = clean_sql(sql).lower()
    return any(re.search(r"\b" + re.escape(k) + r"\b", lower) for k in DANGEROUS_KEYWORDS)


def connect():
    load_dotenv(ROOT / ".env")
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        database=os.getenv("MYSQL_DATABASE", "safedash"),
    )


def execute_sql(cur, sql: str, params: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, str, int]:
    sql = clean_sql(sql)
    if not sql or sql == "Failed":
        return False, 0.0, "no SQL produced", 0
    exec_sql = re.sub(r"@(\w+)", r"%(\1)s", sql) if params else sql
    row_count = 0
    started = time.perf_counter()
    try:
        for stmt in exec_sql.split(";"):
            stmt = stmt.strip()
            if not stmt:
                continue
            cur.execute(stmt, params or None)
            try:
                rows = cur.fetchall()
                row_count += len(rows)
            except mysql.connector.InterfaceError:
                pass
        return True, (time.perf_counter() - started) * 1000.0, "", row_count
    except Exception as exc:
        return False, (time.perf_counter() - started) * 1000.0, str(exc)[:300], row_count


def summarize_latencies(values: Iterable[float]) -> Dict[str, Optional[float]]:
    vals = sorted(float(v) for v in values if v is not None)
    if not vals:
        return {"count": 0, "mean_ms": None, "median_ms": None, "p95_ms": None, "max_ms": None}
    p95_index = min(len(vals) - 1, int(round((len(vals) - 1) * 0.95)))
    return {
        "count": len(vals),
        "mean_ms": round(statistics.mean(vals), 2),
        "median_ms": round(statistics.median(vals), 2),
        "p95_ms": round(vals[p95_index], 2),
        "max_ms": round(max(vals), 2),
    }


def replay_recorded_sql() -> Dict[str, Any]:
    b1 = load_json(DATA_DIR / "benchmark_results.json", [])
    b3 = load_json(DATA_DIR / "benchmark_results_b3.json", [])
    b2 = load_json(DATA_DIR / "benchmark_results_b2.json", [])
    systems = [
        ("AEGIS", b1, "aegis_sql", "aegis_params"),
        ("B1 Direct LLM-to-SQL", b1, "baseline_sql", None),
        ("B3 Template-only", b3, "b3_sql", "b3_params"),
    ]
    if b2:
        systems.append(("B2 Decomposed LLM", b2, "b2_sql", None))

    conn = connect()
    cur = conn.cursor()
    out: Dict[str, Any] = {}
    for label, rows, field, params_field in systems:
        detail = []
        unsafe_ids = []
        for row in rows:
            sql = row.get(field, "")
            params = row.get(params_field) if params_field else None
            ok, ms, err, row_count = execute_sql(cur, sql, params)
            unsafe = is_unsafe_sql(sql)
            if unsafe:
                unsafe_ids.append(row.get("id"))
            detail.append({
                "id": row.get("id"),
                "ok": ok,
                "latency_ms": round(ms, 2),
                "unsafe": unsafe,
                "error": err,
                "row_count": row_count,
            })
        total = len(detail)
        ok_count = sum(1 for d in detail if d["ok"])
        out[label] = {
            "total": total,
            "true_execution_validity_count": ok_count,
            "true_execution_validity_percent": round(ok_count / total * 100.0, 1) if total else 0.0,
            "unsafe_sql_count": len(unsafe_ids),
            "unsafe_sql_ids": unsafe_ids,
            "execution_latency": summarize_latencies(d["latency_ms"] for d in detail),
            "failures": [d for d in detail if not d["ok"]],
        }
    cur.close()
    conn.close()
    return out


def create_annotation_template() -> List[Dict[str, Any]]:
    questions = load_json(QUESTIONS_FILE, [])
    b1 = {r["id"]: r for r in load_json(DATA_DIR / "benchmark_results.json", [])}
    b3 = {r["id"]: r for r in load_json(DATA_DIR / "benchmark_results_b3.json", [])}
    existing = {r["id"]: r for r in load_json(ANNOTATION_FILE, [])} if ANNOTATION_FILE.exists() else {}
    rows = []
    for idx, q in enumerate(questions, start=1):
        old = existing.get(idx, {})
        rows.append({
            "id": idx,
            "query": q,
            "expected_intent_class": old.get("expected_intent_class", ""),
            "expected_metric": old.get("expected_metric", ""),
            "expected_dimension": old.get("expected_dimension", ""),
            "expected_time_or_filter": old.get("expected_time_or_filter", ""),
            "expected_behavior": old.get("expected_behavior", "answer"),
            "aegis_correct": old.get("aegis_correct", None),
            "b1_correct": old.get("b1_correct", None),
            "b2_correct": old.get("b2_correct", None),
            "b3_correct": old.get("b3_correct", None),
            "b4_correct": old.get("b4_correct", None),
            "review_notes": old.get("review_notes", ""),
            "observed_aegis_status": b1.get(idx, {}).get("aegis_status", ""),
            "observed_b3_status": b3.get(idx, {}).get("b3_status", ""),
        })
    write_json(ANNOTATION_FILE, rows)
    return rows


def measure_b3_latency() -> List[Dict[str, Any]]:
    sys.path.insert(0, str(ROOT))
    from run_benchmark_b3 import classify
    from aegis.server.mapper import SemanticMapper
    from aegis.server.compiler import SQLCompiler

    questions = load_json(QUESTIONS_FILE, [])
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    conn = connect()
    cur = conn.cursor()
    rows = []
    for idx, q in enumerate(questions, start=1):
        item: Dict[str, Any] = {"id": idx, "query": q}
        try:
            t0 = time.perf_counter()
            intent = classify(q)
            item["classify_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
            t1 = time.perf_counter()
            plan = mapper.map(intent)
            item["map_ms"] = round((time.perf_counter() - t1) * 1000.0, 2)
            t2 = time.perf_counter()
            sql, params, _ = compiler.compile(plan)
            item["compile_ms"] = round((time.perf_counter() - t2) * 1000.0, 2)
            ok, exec_ms, err, row_count = execute_sql(cur, sql, params)
            item.update({
                "execute_ms": round(exec_ms, 2),
                "total_ms": round(item["classify_ms"] + item["map_ms"] + item["compile_ms"] + exec_ms, 2),
                "ok": ok,
                "error": err,
                "row_count": row_count,
            })
        except Exception as exc:
            item.update({"ok": False, "error": str(exc)[:300]})
        rows.append(item)
    cur.close()
    conn.close()
    write_json(B3_LATENCY_FILE, rows)
    return rows


async def measure_aegis_latency(limit: int = 0) -> List[Dict[str, Any]]:
    sys.path.insert(0, str(ROOT))
    from aegis.server.intent_parser import IntentParser
    from aegis.server.mapper import SemanticMapper
    from aegis.server.compiler import SQLCompiler
    from aegis.server.visualization import VisualizationSelector

    questions = load_json(QUESTIONS_FILE, [])
    if limit:
        questions = questions[:limit]
    parser = IntentParser(api_key=os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY"))
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    selector = VisualizationSelector()
    conn = connect()
    cur = conn.cursor()
    rows = []
    for idx, q in enumerate(questions, start=1):
        item: Dict[str, Any] = {"id": idx, "query": q}
        try:
            t0 = time.perf_counter()
            intent = await parser.parse(q)
            item["intent_parse_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
            t1 = time.perf_counter()
            plan = mapper.map(intent)
            item["map_ms"] = round((time.perf_counter() - t1) * 1000.0, 2)
            t2 = time.perf_counter()
            sql, params, _ = compiler.compile(plan)
            item["compile_ms"] = round((time.perf_counter() - t2) * 1000.0, 2)
            ok, exec_ms, err, row_count = execute_sql(cur, sql, params)
            item["execute_ms"] = round(exec_ms, 2)
            t3 = time.perf_counter()
            selector.select(plan, row_count=row_count)
            item["visual_select_ms"] = round((time.perf_counter() - t3) * 1000.0, 2)
            item.update({
                "total_ms": round(item["intent_parse_ms"] + item["map_ms"] + item["compile_ms"] + item["execute_ms"] + item["visual_select_ms"], 2),
                "ok": ok,
                "error": err,
                "intent": intent.model_dump(),
                "plan": plan.model_dump(),
                "row_count": row_count,
            })
        except Exception as exc:
            item.update({"ok": False, "error": str(exc)[:300]})
        rows.append(item)
        write_json(AEGIS_LATENCY_FILE, rows)
    cur.close()
    conn.close()
    return rows


def latency_summary(rows: List[Dict[str, Any]], fields: List[str]) -> Dict[str, Any]:
    return {field: summarize_latencies(r.get(field) for r in rows if field in r) for field in fields}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-b3-latency", action="store_true")
    parser.add_argument("--run-aegis-latency", action="store_true")
    parser.add_argument("--aegis-limit", type=int, default=0)
    args = parser.parse_args()

    summary = replay_recorded_sql()
    annotations = create_annotation_template()
    if args.run_b3_latency:
        b3_rows = measure_b3_latency()
        summary["B3 Template-only"]["pipeline_latency"] = latency_summary(
            b3_rows, ["classify_ms", "map_ms", "compile_ms", "execute_ms", "total_ms"]
        )
    if args.run_aegis_latency:
        aegis_rows = asyncio.run(measure_aegis_latency(args.aegis_limit))
        summary["AEGIS"]["pipeline_latency"] = latency_summary(
            aegis_rows,
            ["intent_parse_ms", "map_ms", "compile_ms", "execute_ms", "visual_select_ms", "total_ms"],
        )

    summary["semantic_correctness_annotation"] = {
        "file": str(ANNOTATION_FILE.relative_to(ROOT)),
        "rows": len(annotations),
        "status": "template created; human expected labels and correctness decisions still required",
    }
    summary["notes"] = [
        "True execution validity means SQL executed against the seeded MySQL database without a database error.",
        "Execution validity is not semantic correctness.",
        "Semantic correctness requires human expected labels or answer-level review for each system output.",
        "B4 is not yet implemented as a runnable benchmark in this repository.",
    ]
    write_json(SUMMARY_FILE, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
