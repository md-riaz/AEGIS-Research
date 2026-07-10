"""
Integration smoke-test for the SemanticMapper → SQLCompiler pipeline.

Exercises 8 representative intent patterns (segment, ranking, exception, etc.)
and prints the compiled SQL and parameter bindings to stdout.  Run directly:
    python tests/test_compiler.py
"""

from aegis.server.models import IntentObject
from aegis.server.mapper import SemanticMapper
from aegis.server.compiler import SQLCompiler

intents = [
    IntentObject(intent_class="segment", metric_term="revenue", dimension_term="order_date"),
    IntentObject(intent_class="ranking", metric_term="item_quantity", dimension_term="product_name", limit=10, sort="desc"),
    IntentObject(intent_class="segment", metric_term="revenue", dimension_term="country_name"),
    IntentObject(intent_class="segment", metric_term="customer_count", dimension_term="order_date"),
    IntentObject(intent_class="ranking", metric_term="revenue", dimension_term="customer_email", limit=10, sort="desc"),
    IntentObject(intent_class="ranking", metric_term="order_count", dimension_term="customer_email", limit=10, sort="desc"),
    IntentObject(intent_class="exception", metric_term="order_count", dimension_term="order_status", time_term="30 days ago", filters=[{"field": "order_status", "operator": "==", "value": "Pending"}]),
    IntentObject(intent_class="exception", metric_term="refund_count", dimension_term="order_id", filters=[{"field": "refund_amount", "operator": ">", "value": 50}])
]

mapper = SemanticMapper()
compiler = SQLCompiler()

for i, intent in enumerate(intents, 1):
    print(f"\n--- Report {i} ---")
    plan = mapper.map(intent)
    sql, params, rationale = compiler.compile(plan)
    print(f"SQL:\n{sql}")
    print(f"Params: {params}")
    print(f"Rationale: {rationale}")
