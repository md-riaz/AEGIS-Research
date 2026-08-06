# -*- coding: utf-8 -*-
"""Create a conservative semantic-correctness annotation for the 107-query benchmark.

This script turns the existing benchmark outputs into a reviewable annotation
artifact. It does not treat SQL execution as correctness. A result is counted as
semantically correct only when:

1. the recorded SQL executed successfully against the seeded database, and
2. the SQL/intent shape matches the requested metric, grouping, time/filter, and
   behavior at a conservative keyword level.

The output is intentionally reviewable: every row carries expected labels,
per-system correctness flags, and the reason for each decision. A human reviewer
can adjust the JSON/CSV decisions without rerunning the LLM benchmarks.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "evaluation_dataset"

OUT_JSON = DATA / "semantic_correctness_annotations.json"
OUT_CSV = DATA / "semantic_correctness_annotations.csv"
SUMMARY_JSON = DATA / "semantic_correctness_summary.json"


SYSTEMS = {
    "aegis": {
        "label": "AEGIS",
        "file": DATA / "benchmark_results.json",
        "sql_field": "aegis_sql",
        "params_field": "aegis_params",
        "summary_label": "AEGIS",
    },
    "b1": {
        "label": "B1 Direct LLM-to-SQL",
        "file": DATA / "benchmark_results.json",
        "sql_field": "baseline_sql",
        "params_field": None,
        "summary_label": "B1 Direct LLM-to-SQL",
    },
    "b2": {
        "label": "B2 Decomposed LLM",
        "file": DATA / "benchmark_results_b2.json",
        "sql_field": "b2_sql",
        "params_field": None,
        "summary_label": "B2 Decomposed LLM",
    },
    "b3": {
        "label": "B3 Template-only",
        "file": DATA / "benchmark_results_b3.json",
        "sql_field": "b3_sql",
        "params_field": "b3_params",
        "summary_label": "B3 Template-only",
    },
}


UNSUPPORTED_MARKERS = [
    ("homepage", "homepage visitor/conversion source is not in the benchmark schema"),
    ("visitor", "visitor/session/pageview source is not in the benchmark schema"),
    ("supplier", "supplier delivery concept is not in the semantic layer"),
    ("product bundles", "bundle or basket-pair analysis is not directly supported"),
    ("referral source", "referral-source attribution is not directly supported"),
    ("cart abandonment", "cart-abandonment event data is not in the benchmark schema"),
    ("google ads", "ad-channel traffic data is not in the benchmark schema"),
    ("facebook ads", "ad-channel traffic data is not in the benchmark schema"),
    ("mobile versus desktop", "device-channel data is not in the benchmark schema"),
    ("mobile devices versus desktop", "device-channel data is not in the benchmark schema"),
    ("site redesign", "redesign event marker is not in the benchmark schema"),
    ("invalid coupon", "coupon validity history is not in the benchmark schema"),
    ("shipping delays", "shipping-delay calculation is not a supported semantic metric"),
    ("time from order placement to shipment", "order-to-shipment duration is not a supported semantic metric"),
    ("department", "department grouping is not in the benchmark schema"),
    ("marketing campaign", "marketing campaign performance is not linked to orders in the semantic layer"),
    ("sales channel", "sales-channel grouping is not in the semantic layer"),
    ("abandoned carts", "cart recovery event data is not in the benchmark schema"),
    ("payment method has the highest failure rate", "checkout failure data is not in the benchmark schema"),
    ("sales promotions", "promotion ROI data is not in the benchmark schema"),
    ("product variants", "variant attributes are not in the semantic layer"),
    ("gift-wrapped", "gift-wrap flag is not in the benchmark schema"),
    ("free shipping coupon", "coupon-type history is not in the semantic layer"),
    ("customer segments", "age/segment/cross-sell model is not in the semantic layer"),
    ("referral programs", "referral-program acquisition-cost data is not in the benchmark schema"),
    ("saved payment method", "saved-payment-method flag is not in the benchmark schema"),
    ("subscription-based", "subscription product type is not in the semantic layer"),
    ("manual fraud review", "fraud-review flag is not in the benchmark schema"),
    ("shipping carriers", "carrier/on-time-rate data is not in the semantic layer"),
    ("loyalty point", "loyalty redemption detail is not in the semantic layer"),
    ("top 10% of spenders", "percentile/customer-lifetime-value calculation is not supported"),
    ("through the api", "API order source is not in the semantic layer"),
    ("email campaigns", "email click-through data is not in the benchmark schema"),
    ("peak traffic hours", "hour-of-day traffic context is not in the semantic layer"),
    ("shipping distance", "shipping distance is not stored in the benchmark schema"),
    ("promotional code that expired", "promotion expiry history is not in the semantic layer"),
    ("out-of-stock items", "lost revenue from stockout events is not stored"),
    ("product attributes", "attribute-correlation analysis is not in the semantic layer"),
    ("social media login", "social-login source is not in the benchmark schema"),
    ("support tickets", "support-ticket data is not in the benchmark schema"),
    ("product pages", "product-page analytics are not in the benchmark schema"),
    ("duplicate payment", "duplicate-payment review flag is not in the benchmark schema"),
    ("incorrect product descriptions", "return reason text is not in the benchmark schema"),
    ("upsell offers", "upsell offer attribution is not in the benchmark schema"),
    ("forecast", "forecasting is outside the current SQL-only evaluation scope"),
    ("third-party marketplace", "marketplace integration source is not in the semantic layer"),
    ("automating order invoicing", "automation cost saving is not in the benchmark schema"),
    ("what do customers say", "free-text sentiment/review analysis is outside current analytics scope"),
    ("which employee", "employee/support ownership data is not in the benchmark schema"),
    ("page load time", "web-performance telemetry is not in the benchmark schema"),
]


METRIC_RULES = [
    ("avg_order_value", ["average order value", "aov", "average customer lifetime value"]),
    ("profit", ["gross profit", "profit margin", "net profit", "higher margins", "margin"]),
    ("refund", ["refund", "returns", "returned"]),
    ("discount", ["discount", "coupon", "promotional code"]),
    ("shipping_cost", ["shipping cost"]),
    ("shipment", ["shipment", "shipped", "delivered"]),
    ("customer_count", ["new customers", "customers signed up", "first-time buyers", "repeat buyers"]),
    ("quantity", ["quantity", "units sold", "items", "sold units"]),
    ("revenue", ["revenue", "sales", "total spending", "spend", "order total"]),
    ("order_count", ["orders", "order count"]),
    ("stock", ["stock", "inventory"]),
    ("rating", ["rating", "stars"]),
]


DIMENSION_RULES = [
    ("category", ["category", "categories", "clothing", "home-goods", "electronics", "apparel"]),
    ("product", ["product", "sku", "items", "bundles", "variants"]),
    ("customer", ["customer", "buyers"]),
    ("country", ["country", "countries", "us", "canada", "international"]),
    ("payment_method", ["payment method"]),
    ("shipping_method", ["shipping method", "standard", "express"]),
    ("order_status", ["pending status", "status"]),
    ("date", ["by month", "daily", "weekly", "quarterly", "trend", "month-over-month", "month by month"]),
    ("store", ["store"]),
]


TIME_RULES = [
    ("today", ["today", "this morning"]),
    ("yesterday", ["yesterday"]),
    ("current_week", ["current week", "this week"]),
    ("last_month", ["last month"]),
    ("current_month", ["this month"]),
    ("current_quarter", ["current quarter", "this quarter"]),
    ("last_30_days", ["last 30 days", "past 30 days"]),
    ("last_90_days", ["last 90 days", "past 90 days"]),
    ("last_180_days", ["past 180 days"]),
    ("last_year", ["last year", "past year", "last 12 months"]),
    ("year_2023", ["2023"]),
    ("year_2022_2023", ["2022-2023", "2022‑2023"]),
]


METRIC_SQL_TOKENS = {
    "revenue": [["ordertotal"], ["priceexcltax", "priceincltax", "unitprice"]],
    "order_count": [["count", "o.id"], ["count", "order"]],
    "avg_order_value": [["avg", "ordertotal"], ["sum", "ordertotal", "count"]],
    "profit": [["profit"], ["productcost"], ["originalproductcost"], ["ordersubtotalexcltax"]],
    "refund": [["refund"]],
    "discount": [["discount"], ["coupon"]],
    "shipping_cost": [["shipping"]],
    "shipment": [["shipment"], ["shippeddateutc"], ["deliverydateutc"]],
    "customer_count": [["count", "customer"], ["count", "cu.id"]],
    "quantity": [["quantity"], ["item_quantity"]],
    "stock": [["stockquantity"], ["stock"]],
    "rating": [["rating"], ["approvedtotalreviews"], ["review"]],
}


DIM_SQL_TOKENS = {
    "category": [["category"], ["c.name"]],
    "product": [["product"], ["p.name"], ["sku"]],
    "customer": [["customer"], ["cu.email"], ["c.email"], ["firstname"], ["lastname"]],
    "country": [["country"], ["co.name"]],
    "payment_method": [["paymentmethodsystemname"], ["payment method"]],
    "shipping_method": [["shippingmethod"], ["shipping method"]],
    "order_status": [["orderstatusid"], ["order status"]],
    "date": [["createdonutc"], ["date_format"], ["yearweek"], ["quarter("]],
    "store": [["store"]],
}


TIME_SQL_TOKENS = {
    "today": [["utc_date"], ["curdate"], ["utc_timestamp"], ["createdonutc"]],
    "yesterday": [["interval 1 day"], ["date_sub"], ["createdonutc"]],
    "current_week": [["weekday"], ["week"], ["interval 7 day"], ["createdonutc"]],
    "last_month": [["interval 1 month"], ["last month"], ["createdonutc"]],
    "current_month": [["date_format"], ["month("], ["createdonutc"]],
    "current_quarter": [["quarter"], ["createdonutc"]],
    "last_30_days": [["interval 30 day"], ["30 day"], ["createdonutc"]],
    "last_90_days": [["interval 90 day"], ["90 day"], ["createdonutc"]],
    "last_180_days": [["interval 180 day"], ["180 day"], ["createdonutc"]],
    "last_year": [["interval 1 year"], ["12 month"], ["year"], ["createdonutc"]],
    "year_2023": [["2023"], ["createdonutc"]],
    "year_2022_2023": [["2022"], ["2023"], ["createdonutc"]],
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: Any) -> str:
    if text is None:
        return ""
    text = json.dumps(text, ensure_ascii=False) if not isinstance(text, str) else text
    text = text.lower()
    text = text.replace("`", "").replace("[", "").replace("]", "")
    text = text.replace("‑", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text)


def clean_sql(sql: str) -> str:
    if not sql:
        return ""
    matches = re.findall(r"```(?:sql)?\s*(.*?)```", sql, re.DOTALL | re.IGNORECASE)
    return matches[0].strip() if matches else sql.strip()


def any_phrase(text: str, phrases: Iterable[str]) -> bool:
    return any(p in text for p in phrases)


def first_match(text: str, rules: List[Tuple[str, List[str]]]) -> Optional[str]:
    for label, phrases in rules:
        if any_phrase(text, phrases):
            return label
    return None


def expected_dimension_for(question_norm: str, pattern: str) -> Optional[str]:
    """Infer grouping only when the question asks for grouped output."""
    if pattern in {"Ranking", "Trend", "Comparison", "Summary", "Segment", "Cohort", "Correlate", "Tabular"}:
        if "by month" in question_norm or "daily" in question_norm or "weekly" in question_norm:
            return "date"
        return first_match(question_norm, DIMENSION_RULES)
    if " per payment method" in question_norm:
        return "payment_method"
    return None


def expected_metric_for(question_norm: str) -> str:
    if "average number of items per order" in question_norm:
        return "quantity"
    return first_match(question_norm, METRIC_RULES) or "order_count"


def expected_for(qid: int, question: str, pattern_map: Dict[int, str]) -> Dict[str, Any]:
    q = normalize(question)
    unsupported = [reason for marker, reason in UNSUPPORTED_MARKERS if marker in q]
    behavior = "answer" if not unsupported else "clarify_or_reject"

    pattern = pattern_map.get(qid, "Unsupported/Mixed")
    metric = expected_metric_for(q)
    dimension = expected_dimension_for(q, pattern)
    time_rule = first_match(q, TIME_RULES)

    if qid == 106:
        behavior = "clarify_or_reject"
        unsupported.append("vague business-health request lacks a specific metric or grouping")
    if qid == 107:
        behavior = "multi_part_answer"
        unsupported.append("compound request asks for two result shapes in one answer")
        metric = "revenue"
        dimension = "date_and_customer"
    if qid == 105:
        behavior = "reject_write_request"
        unsupported.append("write action should be rejected or clarified, not converted into write SQL")
        metric = "order_count"
        dimension = "order_status"

    return {
        "expected_behavior": behavior,
        "expected_intent_class": pattern,
        "expected_metric": metric,
        "expected_dimension": dimension,
        "expected_time_or_filter": time_rule,
        "unsupported_reason": "; ".join(dict.fromkeys(unsupported)),
    }


def load_pattern_map() -> Dict[int, str]:
    path = DATA / "pattern_classification.json"
    if not path.exists():
        return {}
    data = load_json(path)
    return {int(r["index"]) + 1: r["pattern"] for r in data.get("records", [])}


def execution_ok_map(summary: Dict[str, Any], summary_label: str) -> Dict[int, bool]:
    block = summary.get(summary_label, {})
    failures = {int(f["id"]) for f in block.get("failures", []) if "id" in f}
    total = int(block.get("total", 0) or 0)
    return {i: i not in failures for i in range(1, total + 1)}


def groups_unexpectedly(sql_norm: str, expected: Dict[str, Any]) -> bool:
    if expected["expected_intent_class"] in {"Ranking", "Trend", "Comparison", "Summary", "Segment", "Cohort", "Correlate", "Tabular"}:
        return False
    if expected.get("expected_dimension"):
        return False
    return " group by " in sql_norm


def has_token_group(sql_norm: str, groups: List[List[str]]) -> bool:
    if not groups:
        return True
    return any(all(tok in sql_norm for tok in group) for group in groups)


def score_sql(sql: str, params: Any, expected: Dict[str, Any], executed: bool) -> Tuple[bool, str]:
    raw_sql = clean_sql(sql)
    sql_norm = normalize(raw_sql + " " + normalize(params))
    behavior = expected["expected_behavior"]

    if behavior in {"clarify_or_reject", "reject_write_request"}:
        refusal_tokens = ["cannot answer", "not available", "not supported", "outside", "clarify"]
        has_sql_action = any(t in sql_norm for t in ["select ", "update ", "delete ", "insert ", "drop ", "alter "])
        if any(t in sql_norm for t in refusal_tokens) and not has_sql_action:
            return True, "correctly avoided unsupported or unsafe request"
        return False, expected.get("unsupported_reason") or "request should be clarified or rejected"

    if behavior == "multi_part_answer":
        if not executed:
            return False, "SQL did not execute"
        has_trend = ("date_format" in sql_norm or "month" in sql_norm) and "ordertotal" in sql_norm
        has_customer_rank = "customer" in sql_norm and ("limit 5" in sql_norm or "top 5" in sql_norm)
        return (has_trend and has_customer_rank, "requires both monthly revenue trend and top customer ranking")

    if not executed:
        return False, "SQL did not execute against seeded MySQL"

    if expected.get("unsupported_reason"):
        return False, expected["unsupported_reason"]

    metric = expected.get("expected_metric")
    if metric and not has_token_group(sql_norm, METRIC_SQL_TOKENS.get(metric, [])):
        return False, f"missing expected metric evidence: {metric}"

    dim = expected.get("expected_dimension")
    if dim and dim != "date_and_customer" and not has_token_group(sql_norm, DIM_SQL_TOKENS.get(dim, [])):
        return False, f"missing expected grouping/filter evidence: {dim}"

    time_rule = expected.get("expected_time_or_filter")
    if time_rule and not has_token_group(sql_norm, TIME_SQL_TOKENS.get(time_rule, [])):
        return False, f"missing expected time/filter evidence: {time_rule}"

    if groups_unexpectedly(sql_norm, expected):
        return False, "query asks for one aggregate value but SQL groups the result"

    return True, "executed SQL matches expected metric/grouping/time at conservative keyword level"


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "method": (
            "Conservative single-reviewer annotation generated from expected labels, "
            "SQL execution status, and SQL/intent keyword checks. Execution validity "
            "alone is not counted as semantic correctness."
        ),
        "review_status": (
            "Machine-assisted first pass. The CSV/JSON rows are ready for manual "
            "supervisor or author spot-checking before final thesis submission."
        ),
        "total_questions": len(rows),
        "behavior_counts": {},
        "systems": {},
    }
    behaviors = sorted({r["expected_behavior"] for r in rows})
    for behavior in behaviors:
        out["behavior_counts"][behavior] = sum(1 for r in rows if r["expected_behavior"] == behavior)

    for key, cfg in SYSTEMS.items():
        field = f"{key}_correct"
        correct = sum(1 for r in rows if r[field] is True)
        incorrect = sum(1 for r in rows if r[field] is False)
        review = sum(1 for r in rows if r.get(f"{key}_needs_human_review") is True)
        answer_rows = [r for r in rows if r["expected_behavior"] == "answer"]
        answer_correct = sum(1 for r in answer_rows if r[field] is True)
        unsupported_rows = [r for r in rows if r["expected_behavior"] in {"clarify_or_reject", "reject_write_request"}]
        unsupported_correct = sum(1 for r in unsupported_rows if r[field] is True)
        out["systems"][cfg["label"]] = {
            "correct": correct,
            "incorrect": incorrect,
            "accuracy_percent": round(correct / len(rows) * 100.0, 1) if rows else 0.0,
            "answerable_questions_correct": answer_correct,
            "answerable_questions_total": len(answer_rows),
            "answerable_accuracy_percent": round(answer_correct / len(answer_rows) * 100.0, 1) if answer_rows else 0.0,
            "unsupported_or_write_requests_handled": unsupported_correct,
            "unsupported_or_write_requests_total": len(unsupported_rows),
            "unsupported_handling_percent": round(unsupported_correct / len(unsupported_rows) * 100.0, 1) if unsupported_rows else 0.0,
            "needs_human_review": review,
        }
    return out


def update_supervisor_summary(semantic_summary: Dict[str, Any]) -> None:
    path = DATA / "supervisor_metric_summary.json"
    if not path.exists():
        return
    summary = load_json(path)
    summary["semantic_correctness_annotation"] = {
        "file": str(OUT_JSON.relative_to(ROOT)),
        "csv_file": str(OUT_CSV.relative_to(ROOT)),
        "summary_file": str(SUMMARY_JSON.relative_to(ROOT)),
        "status": semantic_summary["review_status"],
        "method": semantic_summary["method"],
        "total_questions": semantic_summary["total_questions"],
        "behavior_counts": semantic_summary["behavior_counts"],
        "systems": semantic_summary["systems"],
    }
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    questions: List[str] = load_json(DATA / "questions.json")
    pattern_map = load_pattern_map()
    supervisor_summary = load_json(DATA / "supervisor_metric_summary.json")

    system_rows: Dict[str, Dict[int, Dict[str, Any]]] = {}
    exec_ok: Dict[str, Dict[int, bool]] = {}
    for key, cfg in SYSTEMS.items():
        rows = load_json(cfg["file"])
        system_rows[key] = {int(r["id"]): r for r in rows}
        exec_ok[key] = execution_ok_map(supervisor_summary, cfg["summary_label"])

    annotations: List[Dict[str, Any]] = []
    for qid, question in enumerate(questions, start=1):
        expected = expected_for(qid, question, pattern_map)
        row: Dict[str, Any] = {
            "id": qid,
            "query": question,
            **expected,
        }
        for key, cfg in SYSTEMS.items():
            src = system_rows[key].get(qid, {})
            correct, reason = score_sql(
                src.get(cfg["sql_field"], ""),
                src.get(cfg["params_field"], {}) if cfg["params_field"] else {},
                expected,
                exec_ok.get(key, {}).get(qid, False),
            )
            row[f"{key}_correct"] = correct
            row[f"{key}_reason"] = reason
            row[f"{key}_needs_human_review"] = False
        annotations.append(row)

    summary = summarize(annotations)
    OUT_JSON.write_text(json.dumps(annotations, indent=2, ensure_ascii=False), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    update_supervisor_summary(summary)

    fieldnames = list(annotations[0].keys())
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(annotations)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Saved: {OUT_JSON.relative_to(ROOT)}")
    print(f"Saved: {OUT_CSV.relative_to(ROOT)}")
    print(f"Saved: {SUMMARY_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
