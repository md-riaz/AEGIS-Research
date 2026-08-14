# -*- coding: utf-8 -*-
"""
Baseline B3 — Template-only, no LLM.

A deterministic keyword-matching classifier builds an IntentObject directly
from the raw query text (no model call at all), then hands it to AEGIS's
*unmodified* SemanticMapper and SQLCompiler — the same two stages the real
LLM-driven pipeline uses. This isolates what the LLM stage actually buys
you: everything downstream of intent extraction is identical to AEGIS.

By design this classifier is intentionally naive (substring/keyword rules
only, no synonym understanding, no real language comprehension) — that gap
between B3 and AEGIS is the point of the comparison, not a bug to fix.

Usage:
    python run_benchmark_b3.py            # resume from existing results
    python run_benchmark_b3.py --rerun     # force full re-evaluation
    python run_benchmark_b3.py --limit 10  # cap query count (smoke test / CI)

No API key or database connection is required — this is pure Python,
deterministic, and safe to run at any time for free.
"""
import json
import logging
import os
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aegis.benchmark.b3")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from aegis.server.mapper import SemanticMapper
from aegis.server.compiler import SQLCompiler
from aegis.server.models import IntentObject, Filter
from aegis.server.semantic_layer import METRICS, DIMENSIONS

RESULTS_FILE = "evaluation_dataset/benchmark_results_b3.json"

# --- Keyword tables, ordered most-specific-first so earlier matches win ---
METRIC_KEYWORDS = [
    ("avg_order_value", ["average order value", "aov"]),
    ("line_item_revenue", ["product revenue"]),
    ("line_item_cost", ["product cost"]),
    ("line_item_discount", ["line item discount"]),
    ("refund_amount", ["refund amount", "refunded amount", "total refund"]),
    ("refund_count", ["refunds", "number of refunds"]),
    ("discount_amount", ["discount"]),
    ("shipping_cost", ["shipping cost", "shipping fee"]),
    ("shipment_count", ["shipments", "shipment count"]),
    ("tax_amount", ["tax"]),
    ("profit", ["profit", "margin"]),
    ("item_quantity", ["quantity sold", "units sold", "items sold", "sold units"]),
    ("customer_count", ["customers", "new customers"]),
    ("revenue", ["revenue", "sales", "sold for"]),
    ("order_count", ["orders", "order count", "how many orders"]),
]

DIMENSION_KEYWORDS = [
    ("product_sku", ["sku"]),
    ("product_stock", ["stock"]),
    ("product_rating", ["rating"]),
    ("product_price", ["price"]),
    ("product_cost", ["product cost"]),
    ("product_name", ["product"]),
    ("category_name", ["category", "categories"]),
    ("manufacturer_name", ["manufacturer", "brand"]),
    ("customer_email", ["customer", "buyer"]),
    ("order_status", ["status"]),
    ("payment_method", ["payment method"]),
    ("shipping_method", ["shipping method"]),
    ("country_name", ["country"]),
    ("store_name", ["store"]),
    ("order_month", ["month", "monthly"]),
    ("order_year", ["year", "yearly", "annual"]),
    ("order_date", ["date", "daily", "day"]),
]

INTENT_RULES = [
    ("tabular", [r"^\s*list\b", r"\bshow all\b", r"\bshow me\b", r"\bget all\b", r"\bdetails of\b", r"\breport of\b"]),
    ("ranking", [r"\btop \d+", r"\bbottom \d+", r"\bwhich \d+", r"\brank\b"]),
    ("trend", [r"\btrend\b", r"\bover time\b", r"\bweekly\b", r"\bdaily\b", r"\bmonth-over-month\b", r"\bchart the\b", r"\bplot the\b", r"\bgrowth rate\b"]),
    ("comparison", [r"\bcompare\b", r"\bvs\.?\b", r"\bversus\b", r"\bcontrast\b", r"\bdifference between\b"]),
    ("exception", [r"\bexceed", r"\bbelow \d", r"\bgreater than\b", r"\bless than\b", r"\bmore than \d", r"\bunder \d", r"\bflagged\b"]),
    ("funnel", [r"\babandon", r"\bconversion\b", r"\bfunnel\b"]),
    ("cohort", [r"\bcohort\b", r"\bnew vs\.? returning\b", r"\bfirst-time\b", r"\bfirst‑time\b"]),
    ("correlate", [r"\bcorrelat", r"\brelationship between\b"]),
    ("summary", [r"\boverview\b", r"\bsummary\b", r"\bsnapshot\b", r"\bdashboard\b", r"\bhealth score\b"]),
    ("segment", [r"\bbreakdown\b", r"\bby category\b", r"\bby country\b", r"\bsegment"]),
]

TIME_PATTERNS = [
    (r"\btoday\b", "today"),
    (r"\byesterday\b", "yesterday"),
    (r"\bthis morning\b", "today"),
    (r"\bpast (\d+) days?\b", None),   # handled specially below
    (r"\b(\d+) days? ago\b", None),
    (r"\blast week\b", "last week"),
    (r"\bthis week\b", "this week"),
    (r"\blast month\b", "last month"),
    (r"\bthis month\b", "this month"),
    (r"\blast year\b", "last year"),
    (r"\bthis year\b", "this year"),
    (r"\bcurrent quarter\b", "this month"),  # coarse fallback: no native quarter support
]

THRESHOLD_PATTERN = re.compile(
    r"\b(?:exceeds?|greater than|more than|above|over)\s+\$?([\d,]+)|"
    r"\b(?:less than|below|under)\s+\$?([\d,]+)"
)


def classify(query: str) -> IntentObject:
    q = query.lower()

    intent_class = "kpi"
    for cls, patterns in INTENT_RULES:
        if any(re.search(p, q) for p in patterns):
            intent_class = cls
            break

    metric_term = None
    for metric_id, keywords in METRIC_KEYWORDS:
        if any(kw in q for kw in keywords):
            metric_term = metric_id
            break

    dimension_term = None
    for dim_id, keywords in DIMENSION_KEYWORDS:
        if any(kw in q for kw in keywords):
            dimension_term = dim_id
            break

    time_term = None
    m = re.search(r"\bpast (\d+) days?\b", q)
    if m:
        time_term = "past %s days" % m.group(1)
    else:
        m = re.search(r"\b(\d+) days? ago\b", q)
        if m:
            time_term = "%s days ago" % m.group(1)
        else:
            for pattern, label in TIME_PATTERNS:
                if label and re.search(pattern, q):
                    time_term = label
                    break

    limit = None
    sort = None
    m = re.search(r"\btop (\d+)", q)
    if m:
        limit = int(m.group(1))
        sort = "desc"
    else:
        m = re.search(r"\bbottom (\d+)", q)
        if m:
            limit = int(m.group(1))
            sort = "asc"

    filters = []
    tm = THRESHOLD_PATTERN.search(q)
    if tm and dimension_term:
        if tm.group(1):
            filters.append(Filter(field=dimension_term, operator=">", value=tm.group(1).replace(",", "")))
        elif tm.group(2):
            filters.append(Filter(field=dimension_term, operator="<", value=tm.group(2).replace(",", "")))

    return IntentObject(
        intent_class=intent_class,
        metric_term=metric_term,
        dimension_term=dimension_term,
        time_term=time_term,
        filters=filters,
        sort=sort,
        limit=limit,
        confidence="rule-based",
    )


def _update_total_results(total_results, result_item):
    index = {r["id"]: i for i, r in enumerate(total_results)}
    if result_item["id"] in index:
        total_results[index[result_item["id"]]] = result_item
    else:
        total_results.append(result_item)
    total_results.sort(key=lambda x: x["id"])


def run_benchmark(force_rerun: bool = False, limit: int = 0):
    mapper = SemanticMapper()
    compiler = SQLCompiler()

    with open("evaluation_dataset/questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    if not force_rerun and os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    results = json.loads(content)
        except Exception:
            results = []

    processed_ids = {r["id"] for r in results} if not force_rerun else set()
    if force_rerun:
        results = []

    if limit > 0:
        questions = questions[:limit]

    for i, query in enumerate(questions):
        qid = i + 1
        if qid in processed_ids:
            continue

        result_item = {
            "id": qid,
            "query": query,
            "b3_intent": None,
            "b3_sql": "",
            "b3_status": "pending",
            "error": "",
        }
        try:
            intent = classify(query)
            result_item["b3_intent"] = intent.model_dump()
            plan = mapper.map(intent, query)
            sql, params, rationale = compiler.compile(plan)
            result_item["b3_sql"] = sql
            result_item["b3_params"] = params
            result_item["b3_status"] = "success"
            logger.info("[%d] %s -> pattern=%s status=success", qid, query[:50], plan.pattern)
        except Exception as e:
            result_item["b3_status"] = "failed"
            result_item["error"] = str(e)
            logger.warning("[%d] %s -> FAILED: %s", qid, query[:50], e)

        _update_total_results(results, result_item)
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    total = len(results)
    successes = [r for r in results if r["b3_status"] == "success"]
    print("\n" + "=" * 50)
    print("B3 (TEMPLATE-ONLY, NO LLM) BENCHMARK SUMMARY")
    print("=" * 50)
    print(f"Total Queries: {total}")
    print(f"Classified & Compiled Without Exception: {len(successes)}/{total} ({len(successes)/total*100:.1f}%)")
    print("=" * 50)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerun", action="store_true", help="Force rerun all queries")
    parser.add_argument("--limit", type=int, default=0, help="Cap number of queries (0 = all)")
    args = parser.parse_args()
    run_benchmark(force_rerun=args.rerun, limit=args.limit)
