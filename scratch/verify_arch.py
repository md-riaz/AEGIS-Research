import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'safedash', 'server'))
import models, ai_config, semantic_layer

metrics = "|".join(m.id for m in semantic_layer.METRICS)
dims = "|".join(d.id for d in semantic_layer.DIMENSIONS)
m_ctx = "; ".join(f"{m.id}={m.description}" for m in semantic_layer.METRICS)
d_ctx = "; ".join(f"{d.id}={d.description}" for d in semantic_layer.DIMENSIONS)

prompt = f"""You extract reporting intent as JSON. Map user language to approved IDs.

OUTPUT: {{"intent_class":"...","metric_term":"...","dimension_term":"...or null","filters":[{{"field":"...","operator":"...","value":"..."}}],"sort":"asc|desc|null","limit":int|null,"time_term":"...or null"}}

METRICS (use exact ID): {metrics}
Context: {m_ctx}

DIMENSIONS (use exact ID): {dims}
Context: {d_ctx}

INTENT CLASSES: kpi=scalar|ranking=top/bottom N|trend=over time|comparison=A vs B|exception=threshold filter|summary=multi-metric overview|segment=breakdown by dimension|funnel=conversion stages|cohort=group behavior|correlate=attribute relationships|point_lookup=specific record

RULES: 1)Return ONLY raw JSON 2)metric_term/dimension_term must be exact IDs from above 3)Never generate SQL 4)Use key "intent_class" not "intent"

EXAMPLES:
"top 5 products by sales"->{{"intent_class":"ranking","metric_term":"revenue","dimension_term":"product_name","limit":5,"sort":"desc"}}
"monthly revenue trend"->{{"intent_class":"trend","metric_term":"revenue","dimension_term":"order_date"}}
"revenue by category"->{{"intent_class":"segment","metric_term":"revenue","dimension_term":"category_name"}}"""

print(f"Prompt length: {len(prompt)} chars")
print(f"Approx tokens: ~{len(prompt)//4}")
print(f"Synonyms: {len(semantic_layer.SYNONYMS)}")
print()
print("=== FULL PROMPT ===")
print(prompt)
