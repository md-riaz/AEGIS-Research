from safedash.server.mapper import SemanticMapper
from safedash.server.compiler import SQLCompiler
from safedash.server.models import IntentObject

m = SemanticMapper()
c = SQLCompiler()

for p in ["segment", "funnel", "cohort", "correlate"]:
    intent = IntentObject(intent_class=p, metric_term="order_count", dimension_term="payment_method")
    plan = m.map(intent)
    sql = c.compile(plan)
    print(f"=== {p.upper()} ===")
    print(f"Visual: {plan.visual}")
    print(sql)
    print()
