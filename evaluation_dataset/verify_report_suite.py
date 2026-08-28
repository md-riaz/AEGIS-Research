"""
Runs the host platform's own standard admin reports through AEGIS.

Section 6.3 of the manuscript claims that all twenty of nopCommerce's standard
admin reports can be reproduced from natural language.  That claim was, until
this script existed, asserted rather than recomputable — which is the position
the figures retracted in Section 6.1 were in, so it needed closing.

The report list is not chosen by this project.  It is nopCommerce's own fixed
admin menu, documented at ``en/running-your-store/reports.md`` in
nopSolutions/nopCommerce-Docs, which is what makes it a stronger test than a
self-authored question set: there was no opportunity to pick questions the
system was known to handle, nor to avoid ones it was known to miss.

Each request goes through the full pipeline — parse, resolve, compile — and the
recorded outcome is the terminal one (``answer`` / ``clarify`` / ``reject`` /
``error``), never a status field that reports a correct refusal and a crash
identically.  A report only counts as reproduced when the outcome is ANSWER
*and* the compiler emitted SQL; anything else is recorded with its reason.

Requires live LLM credentials (``.env``); needs no database, since compilation
is offline.  Whether the resulting SQL returns the same data as nopCommerce's
own report logic is ``verify_report_differential.py``'s question, and that is
the check to quote when asked whether AEGIS reproduces the reports.

Usage:
    python evaluation_dataset/verify_report_suite.py [--json PATH] [--concurrency N]
"""

import argparse
import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aegis.server.intent_parser import IntentParser
from aegis.server.mapper import SemanticMapper
from aegis.server.models import Outcome
from aegis.server.explain import explain_plan
from aegis.server.compiler import SQLCompiler

logging.basicConfig(level=logging.WARNING,
                    format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aegis.report_suite")

OUT = "evaluation_dataset/report_suite_results.json"

# nopCommerce's standard admin reports, each paired with the natural-language
# request a store owner would plausibly type to ask for it.  The wordings are
# deliberately ordinary business phrasing rather than vocabulary-shaped: asking
# in the semantic layer's own words would test nothing, since injection makes
# those resolve by construction.
REPORTS = [
    ("Sales summary by month",        "Show me the monthly sales summary"),
    ("Sales summary today",           "What are today's total sales?"),
    ("Bestsellers by quantity",       "Which products sold the most units?"),
    ("Bestsellers by amount",         "Which products brought in the most revenue?"),
    ("Products never purchased",      "Which products have never been ordered?"),
    ("Country sales",                 "Show total sales by country"),
    ("Best customers by order total", "Who are our top customers by amount spent?"),
    ("Best customers by order count", "Which customers placed the most orders?"),
    ("Registered customers",          "How many customers registered this month?"),
    ("Low stock",                     "Which products are low on stock?"),
    ("Order status breakdown",        "Break down orders by their status"),
    ("Incomplete orders",             "How many orders are incomplete?"),
    ("Latest orders",                 "Show me the most recent orders"),
    ("Sales by category",             "What is total revenue by category?"),
    ("Sales by manufacturer",         "Show revenue by manufacturer"),
    ("Average order value",           "What is our average order value?"),
    ("Shipment count",                "How many shipments have we sent?"),
    ("Refund totals",                 "What is the total amount refunded?"),
    ("Tax collected",                 "How much tax have we collected?"),
    ("Daily revenue trend",           "Show the daily revenue trend"),
]


async def run_one(report, question, parser, mapper, compiler, sem):
    async with sem:
        row = {
            "report": report,
            "question": question,
            "outcome": "",
            "reproduced": False,
            "sql": "",
            "params": {},
            "interpretation": "",
            "message": "",
            "error": "",
        }
        try:
            intent = await parser.parse(question)
            resolution = mapper.resolve(intent, question)
            row["outcome"] = resolution.outcome.value
            row["message"] = resolution.question or resolution.message or ""
            if resolution.outcome is Outcome.ANSWER:
                sql, params, _ = compiler.compile(resolution.plan)
                row["sql"] = sql
                row["params"] = params
                row["interpretation"] = explain_plan(resolution.plan)
                # Reproduced means: decided to answer AND produced a query.
                # An ANSWER outcome with empty SQL is a defect, not a success,
                # so it must not be able to pass this check.
                row["reproduced"] = bool(sql and sql.strip())
        except Exception as exc:               # genuine faults only
            row["outcome"] = "error"
            row["error"] = str(exc)
        return row


async def main_async(args):
    from aegis.server.ai_config import LLM_API_KEY, GROQ_API_KEY
    key = LLM_API_KEY or os.getenv("GROQ_API_KEY") or GROQ_API_KEY
    if not key:
        raise SystemExit(
            "No LLM credentials configured. This script measures the parsing "
            "stage, so it cannot report a coverage figure without them — "
            "refusing to print 0 of 20 for a missing key."
        )

    parser, mapper, compiler = IntentParser(api_key=key), SemanticMapper(), SQLCompiler()
    sem = asyncio.Semaphore(args.concurrency)
    rows = await asyncio.gather(*[
        run_one(r, q, parser, mapper, compiler, sem) for r, q in REPORTS
    ])

    reproduced = [r for r in rows if r["reproduced"]]
    print("=" * 70)
    print("nopCommerce STANDARD ADMIN REPORT SUITE, VIA NATURAL LANGUAGE")
    print("=" * 70)
    for r in rows:
        mark = "OK  " if r["reproduced"] else "MISS"
        print(f"  [{mark}] {r['report']:<32} {r['outcome']}")
        if not r["reproduced"]:
            detail = r["error"] or r["message"] or "(no reason recorded)"
            print(f"         {detail[:100]}")
    print()
    print(f"  Reproduced: {len(reproduced)} of {len(rows)}")
    print("=" * 70)

    payload = {"total": len(rows), "reproduced": len(reproduced), "results": rows}
    with open(args.json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"Wrote {args.json_path}")
    return 0 if len(reproduced) == len(rows) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", dest="json_path", default=OUT)
    ap.add_argument("--concurrency", type=int,
                    default=int(os.getenv("BENCHMARK_CONCURRENCY", "8")))
    sys.exit(asyncio.run(main_async(ap.parse_args())))


if __name__ == "__main__":
    main()
