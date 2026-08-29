"""Direct LLM-to-SQL baseline over the nopCommerce 500-question dataset.

AEGIS's contribution is architectural: the model never authors SQL. That claim
is only meaningful next to a system where it does, measured on the same
questions, the same database, and the same model — which is what this runner
provides.

Same model and endpoint as the AEGIS pipeline, deliberately. A baseline served
by a weaker model would flatter AEGIS for a reason that has nothing to do with
the architecture, and the comparison would not survive a reviewer asking which
model each arm used.

Four things are measured, and the last is the one the thesis actually turns on:

``translatability``
    Share of questions for which the baseline emitted SQL at all. The term is
    from Liu et al. (2026), whose review defines it as |E| / |N|.

``execution_validity``
    Share of *supported* questions whose SQL ran against the seeded database
    without an error. This says nothing about whether the answer was right.

``unsafe_sql``
    SQL containing a construct the AEGIS compiler forbids. The patterns are
    imported from the compiler rather than restated here, so the two arms are
    judged by one definition and it cannot drift.

``boundary_false_answer_rate``
    Of the 75 questions that ask for something the semantic layer cannot
    express, how many the baseline answered with confident SQL anyway instead
    of declining. AEGIS cannot express these at all; an unconstrained model can
    always write *something*, and what it writes is a plausible, executable,
    wrong answer. No public text-to-SQL benchmark measures this, because their
    datasets contain no unanswerable questions.

Safety: SQL that fails the forbidden-pattern scan is recorded and **never
executed**. The session is additionally opened read-only, so a write that
slipped past the scan would still be refused by the database rather than by
this script's own judgement.

Usage:
    python evaluation_dataset/run_500_baseline_llm.py [--limit N] [--json PATH]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx
import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from aegis.server.ai_config import CUSTOM, LLM_API_KEY, LLM_MODEL
from aegis.server.compiler import SQLCompiler
from timing import print_latency, stage_summary, stopwatch

load_dotenv(ROOT / ".env")

DATASET = ROOT / "evaluation_dataset" / "nopcommerce_500_natural_questions.json"
OUT = ROOT / "evaluation_dataset" / "baseline_500_llm_results.json"

STAGES = ["generate_ms", "execute_ms"]

#: The schema the baseline is told about. Deliberately the same tables the
#: AEGIS semantic layer binds, so the baseline is not handicapped by being told
#: less about the database than AEGIS knows.
SCHEMA_HINT = (
    "Order, OrderItem, Product, Category, Product_Category_Mapping, Customer, "
    "Address, Country, StateProvince, Manufacturer, Product_Manufacturer_Mapping, "
    "Shipment, Store, DiscountUsageHistory, ProductTag, Product_ProductTag_Mapping, "
    "ShoppingCartItem, ProductReview"
)

PROMPT = (
    "You are given a nopCommerce MySQL database with these tables: {schema}.\n"
    "Write a single MySQL query that answers this question:\n\n{question}\n\n"
    "Return ONLY the SQL, in one ```sql code block. If the question cannot be "
    "answered from this schema, reply with exactly: CANNOT_ANSWER"
)

SQL_BLOCK = re.compile(r"```(?:sql)?\s*(.+?)```", re.S | re.I)
READ_ONLY_START = re.compile(r"^\s*(?:SELECT|WITH)\b", re.I)


def connect():
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "aegis"),
    )
    # Defence in depth. The forbidden-pattern scan below already refuses to run
    # anything that looks like a write, but a scan is textual and this is not:
    # a write that reached the server would be rejected by the server.
    cur = conn.cursor()
    cur.execute("SET SESSION TRANSACTION READ ONLY")
    cur.close()
    return conn


def extract_sql(reply: str) -> str:
    """Pull the SQL out of a model reply, or return '' if it declined."""
    if not reply or reply.strip().upper().startswith("CANNOT_ANSWER"):
        return ""
    match = SQL_BLOCK.search(reply)
    candidate = (match.group(1) if match else reply).strip()
    if not candidate or candidate.upper().startswith("CANNOT_ANSWER"):
        return ""
    return candidate.rstrip(";").strip()


def unsafe_reason(sql: str) -> str:
    """Return the first forbidden construct in ``sql``, or '' if none.

    The patterns come from the compiler itself. Restating them here would let
    the two arms drift apart silently, and the arm being judged more leniently
    would be the one this project wants to look worse.
    """
    for pattern in SQLCompiler.FORBIDDEN_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            return pattern
    return ""


async def generate(question: str, client: httpx.AsyncClient, max_retries: int = 4) -> str:
    prompt = PROMPT.format(schema=SCHEMA_HINT, question=question)
    key = LLM_API_KEY or os.getenv("GROQ_API_KEY") or CUSTOM.api_key
    if not key:
        raise RuntimeError("No LLM credentials configured; set LLM_API_KEY in .env")

    last_error = ""
    for attempt in range(max_retries):
        await CUSTOM.wait_if_needed()
        try:
            response = await client.post(
                CUSTOM.url,
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "stream": False,
                },
                timeout=60.0,
            )
            if response.status_code == 429:
                await asyncio.sleep(float(response.headers.get("retry-after", 10)))
                continue
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            last_error = f"HTTP {response.status_code}"
        except Exception as exc:
            # Type as well as message: httpx timeouts stringify to the empty
            # string, which would record a failure that says nothing about
            # whether the endpoint was slow, refusing, or unreachable.
            last_error = f"{type(exc).__name__}: {exc or '(no message)'}"
        await asyncio.sleep(2 * (attempt + 1))
    raise RuntimeError(last_error or "generation failed")


def pct(n: int, total: int) -> float:
    return round(n / total * 100, 1) if total else 0.0


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=str(OUT))
    parser.add_argument("--limit", type=int, default=0, help="First-N smoke run; 0 means all")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    data = json.loads(DATASET.read_text(encoding="utf-8"))
    questions = data["questions"][: args.limit or None]

    semaphore = asyncio.Semaphore(args.concurrency)
    results: list[dict[str, Any]] = []

    state = {"conn": connect()}
    lock = asyncio.Lock()

    def _live_cursor():
        """Return a usable cursor, reconnecting if the server went away.

        The run takes hours, and a database that disappears mid-run would
        otherwise be recorded as the baseline failing to produce working SQL.
        That would be a measurement artifact of the harness, attributed to the
        system under test — the exact confusion this benchmark exists to avoid
        in the other direction.
        """
        conn = state["conn"]
        try:
            conn.ping(reconnect=True, attempts=3, delay=2)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            conn = state["conn"] = connect()
        return conn.cursor()

    async def handle(item: dict[str, Any]) -> dict[str, Any]:
        row = {
            "id": item["id"],
            "prompt": item["prompt"],
            "expected_outcome": item["expected_outcome"],
            "capability": item["capability"],
            "reply": "",
            "sql": "",
            "produced_sql": False,
            "declined": False,
            "unsafe": False,
            "unsafe_pattern": "",
            "executed": False,
            "row_count": None,
            "error": "",
            "generate_ms": None,
            "execute_ms": None,
        }
        async with semaphore:
            try:
                with stopwatch(row, "generate_ms"):
                    reply = await generate(item["prompt"], client)
                row["reply"] = reply
                sql = extract_sql(reply)
                row["sql"] = sql
                row["produced_sql"] = bool(sql)
                row["declined"] = not sql
            except Exception as exc:
                row["error"] = str(exc)
                return row

        if not row["produced_sql"]:
            return row

        pattern = unsafe_reason(row["sql"])
        if pattern or not READ_ONLY_START.match(row["sql"]):
            row["unsafe"] = bool(pattern)
            row["unsafe_pattern"] = pattern
            row["error"] = "not executed: failed the forbidden-pattern scan" if pattern \
                else "not executed: not a SELECT"
            return row

        # One cursor, one connection: the executions are serialised even though
        # generation is concurrent, so the recorded execute_ms is the query's
        # own time and not contention between benchmark workers.
        async with lock:
            try:
                with stopwatch(row, "execute_ms"):
                    cursor = _live_cursor()
                    cursor.execute(row["sql"])
                    row["row_count"] = len(cursor.fetchall())
                row["executed"] = True
            except Exception as exc:
                row["error"] = str(exc)
        return row

    async with httpx.AsyncClient() as client:
        pending = [handle(item) for item in questions]
        for done in asyncio.as_completed(pending):
            results.append(await done)
            if len(results) % 25 == 0:
                print(f"processed {len(results)}/{len(questions)}")

    try:
        state["conn"].close()
    except Exception:
        pass
    results.sort(key=lambda r: r["id"])

    supported = [r for r in results if r["expected_outcome"] == "answer"]
    boundary = [r for r in results if r["expected_outcome"] == "reject"]
    metrics = {
        "translatability": {
            "n": sum(1 for r in results if r["produced_sql"]), "of": len(results)},
        "supported_execution_validity": {
            "n": sum(1 for r in supported if r["executed"]), "of": len(supported)},
        "unsafe_sql": {
            "n": sum(1 for r in results if r["unsafe"]), "of": len(results)},
        "boundary_false_answer_rate": {
            "n": sum(1 for r in boundary if r["produced_sql"]), "of": len(boundary)},
    }
    for metric in metrics.values():
        metric["value"] = pct(metric["n"], metric["of"])

    payload = {
        "benchmark": data["name"],
        "arm": "direct_llm_to_sql_baseline",
        "model": LLM_MODEL,
        "total": len(results),
        "metrics": metrics,
        "latency": stage_summary(supported, STAGES),
        "results": results,
    }
    Path(args.json).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=" * 72)
    print(f"DIRECT LLM-TO-SQL BASELINE ({LLM_MODEL})")
    print("=" * 72)
    for key, metric in metrics.items():
        print(f"{key:32} {metric['n']}/{metric['of']} ({metric['value']:.1f}%)")
    print_latency("Baseline stage latency (supported questions)", payload["latency"])
    print("\nNote: boundary_false_answer_rate counts out-of-scope questions the")
    print("baseline answered with SQL instead of declining. Higher is worse.")
    print(f"\nWrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
