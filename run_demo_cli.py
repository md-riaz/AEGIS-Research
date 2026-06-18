"""
Command-line interface for testing the AEGIS pipeline interactively.

Runs a fixed set of sample queries through the complete pipeline
(Intent Parser → Semantic Mapper → SQL Compiler → Visualization →
Widget Engine) and prints each stage's output to stdout.  Final output
is saved to demo/demo_dashboard.json.

Usage:
    python run_demo_cli.py
"""

import asyncio
import json
import logging
from aegis.server.intent_parser import IntentParser
from aegis.server.mapper import SemanticMapper
from aegis.server.compiler import SQLCompiler
from aegis.server.visualization import VisualizationSelector
from aegis.server.widget_engine import Widget, WidgetRegistry, DashboardComposer
from aegis.server.ai_config import GROQ_API_KEY

logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
logger = logging.getLogger("aegis.cli")


async def process_query(
    query: str,
    parser: IntentParser,
    mapper: SemanticMapper,
    compiler: SQLCompiler,
    vis_selector: VisualizationSelector,
    widget_registry: WidgetRegistry,
) -> Widget:
    """
    Process a single natural-language reporting request through the
    complete AEGIS pipeline.

    Returns the persisted Widget artifact.
    """
    print(f"\n{'='*60}")
    print(f"  USER QUERY: {query}")
    print(f"{'='*60}")

    # Stage 1 — Intent Extraction (LLM)
    intent = await parser.parse(query)
    print(f"\n[1] INTENT EXTRACTED:")
    print(f"    Class:     {intent.intent_class}")
    print(f"    Metric:    {intent.metric_term}")
    print(f"    Dimension: {intent.dimension_term or '—'}")
    print(f"    Time:      {intent.time_term or '—'}")
    print(f"    Filters:   {len(intent.filters)}")
    print(f"    Confidence: {intent.confidence}")

    # Stage 2 — Semantic Mapping (Deterministic)
    plan = mapper.map(intent)
    print(f"\n[2] ANALYSIS PLAN:")
    print(f"    Pattern:   {plan.pattern}")
    print(f"    Metric:    {plan.metric}")
    print(f"    Dimension: {plan.dimension or '—'}")
    print(f"    Visual:    {plan.visual}")
    print(f"    Join Path: {' → '.join(plan.join_path)}")

    # Stage 3 — SQL Compilation (Deterministic + Safe)
    sql = compiler.compile(plan)
    print(f"\n[3] COMPILED SQL:")
    for line in sql.strip().split("\n"):
        print(f"    {line}")

    # Stage 4 — Visualization Selection (Rule-based)
    vis_spec = vis_selector.select(plan)
    print(f"\n[4] VISUALIZATION:")
    print(f"    Chart:   {vis_spec.chart_type}")
    print(f"    Title:   {vis_spec.title}")
    print(f"    X-Axis:  {vis_spec.x_axis or '—'}")
    print(f"    Y-Axis:  {vis_spec.y_axis or '—'}")
    print(f"    Colors:  {vis_spec.color_scheme}")
    print(f"    Options: {json.dumps(vis_spec.options, indent=2)}")

    # Stage 5 — Widget Persistence (Similarity-based)
    widget = Widget(
        original_query=query,
        plan=plan,
        compiled_sql=sql,
        visualization=vis_spec,
    )
    registered = widget_registry.register(widget)
    is_reused = registered.widget_id != widget.widget_id or len(registered.run_history) > 1
    print(f"\n[5] WIDGET PERSISTED:")
    print(f"    ID:      {registered.widget_id}")
    print(f"    Reused:  {'Yes (similar widget found)' if is_reused else 'No (new widget)'}")
    print(f"    Runs:    {len(registered.run_history)}")
    print(f"    Stored:  {widget_registry.count} total widgets")

    return registered


async def main():
    """Run the full AEGIS pipeline demo with sample queries."""

    # Initialize all pipeline components
    parser = IntentParser(api_key=GROQ_API_KEY)
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    vis_selector = VisualizationSelector()
    widget_registry = WidgetRegistry(storage_path="demo/demo_widgets.json")

    # Sample queries demonstrating different intent classes
    queries = [
        # KPI
        "What is the total revenue this month?",
        # Ranking
        "Show me the top 5 products by revenue",
        # Trend
        "Show monthly revenue trend for the last year",
        # Comparison
        "Compare revenue across product categories",
        # Exception
        "List products with stock less than 10",
        # Reuse test — similar to the first KPI query
        "What are total sales this month?",
    ]

    for query in queries:
        try:
            await process_query(
                query, parser, mapper, compiler, vis_selector, widget_registry
            )
        except Exception as e:
            logger.error(f"Pipeline error for '{query}': {e}")

    # Stage 6 — Dashboard Composition
    print(f"\n{'='*60}")
    print(f"  DASHBOARD COMPOSITION")
    print(f"{'='*60}")

    composer = DashboardComposer()
    all_widgets = widget_registry.list_all()
    dashboard = composer.compose(all_widgets, title="AEGIS E-Commerce Dashboard")

    print(f"\n  Title: {dashboard['title']}")
    print(f"  Total Widgets: {dashboard['total_widgets']}")
    print(f"  Grid: {dashboard['grid_columns']} columns")
    print(f"\n  Layout:")
    for item in dashboard["widgets"]:
        pos = item["grid_position"]
        print(
            f"    [{item['chart_type']:15s}] {item['title'][:40]:40s} "
            f"@ col={pos['col']}, row={pos['row']} ({pos['cols']}×{pos['rows']})"
        )

    # Save dashboard spec
    with open("demo/demo_dashboard.json", "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)
    print(f"\n  Dashboard spec saved to demo/demo_dashboard.json")

    # Save widget registry summary
    print(f"\n  Widget Registry Summary:")
    for w in all_widgets:
        print(
            f"    {w.widget_id} | {w.visualization.chart_type:15s} | "
            f"runs={len(w.run_history)} | {w.original_query[:50]}"
        )


if __name__ == "__main__":
    asyncio.run(main())
