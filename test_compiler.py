from safedash.server.models import IntentObject
from safedash.server.mapper import SemanticMapper
from safedash.server.compiler import SQLCompiler

intents = [
    IntentObject(intent_class="segment", metric_term="revenue", dimension_term="order_date"),
    IntentObject(intent_class="ranking", metric_term="item_quantity", dimension_term="product_name", limit=10, sort="desc"),
    IntentObject(intent_class="segment", metric_term="revenue", dimension_term="country_name"),
    IntentObject(intent_class="segment", metric_term="customer_count", dimension_term="order_date"),
    IntentObject(intent_class="ranking", metric_term="revenue", dimension_term="customer_email", limit=10, sort="desc"),
    IntentObject(intent_class="ranking", metric_term="order_count", dimension_term="customer_email", limit=10, sort="desc")
]

mapper = SemanticMapper()
compiler = SQLCompiler()

for i, intent in enumerate(intents, 1):
    print(f"\n--- Report {i} ---")
    plan = mapper.map(intent)
    sql, params = compiler.compile(plan)
    print(f"SQL:\n{sql}")
    print(f"Params: {params}")
