"""Full test of all datatable & important queries."""
import requests, json

BASE = "http://localhost:8765"

queries = [
    "Products with stock less than 10",
    "List all registered customers this year",
    "List products never sold",
    "Total revenue KPI",
    "Top 5 bestsellers by quantity",
    "Low stock products details",
    "Show orders with refund amount greater than 0",
    "Revenue by manufacturer",
    "List recent shipments with tracking details",
    "Top 5 categories by total profit",
    "Compare order count by country",
    "Monthly revenue trend"
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {q}")
    print('='*60)
    r = requests.post(f"{BASE}/api/query", json={"query": q}, timeout=15)
    d = r.json()
    if not d.get("success"):
        print(f"  ERROR: {d.get('error')}")
        continue
    for s in d.get("stages", []):
        if s["stage"] == "mapping":
            plan = s["data"]
            print(f"  PATTERN: {plan['pattern']} | METRIC: {plan['metric']} | DIM: {plan.get('dimension')} | JOINS: {plan.get('join_path')}")
        if s["stage"] == "sql":
            print(f"  SQL: {s['data']['sql']}")
        if s["stage"] == "visualization":
            print(f"  VIS: {s['data']['chart_type']} — \"{s['data']['title']}\"")
