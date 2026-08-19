"""
FastAPI server for the AEGIS demo. Serves the pipeline API and static dashboard UI.

Endpoints:
  POST   /api/query            — process a natural-language query → widget JSON
  GET    /api/widgets           — list all persisted widgets
  DELETE /api/widgets/{id}      — remove a widget by ID
  DELETE /api/widgets           — clear all widgets
  GET    /api/dashboard         — composed dashboard layout
  GET    /api/coverage          — semantic layer surface (metrics, dimensions)
  GET    /                      — serve the single-page dashboard frontend
"""

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from aegis.server.intent_parser import IntentParser
from aegis.server.mapper import SemanticMapper
from aegis.server.compiler import SQLCompiler
from aegis.server.visualization import VisualizationSelector
from aegis.server.widget_engine import Widget, WidgetRegistry, DashboardComposer
from aegis.server.permission_rewriter import PermissionRewriter
from aegis.server.database_client import DatabaseClient
from aegis.server.ai_config import LLM_API_KEY, LLM_MODEL, GROQ_API_KEY
from aegis.server.semantic_layer import METRICS, DIMENSIONS
from aegis.server.models import IntentClass, Outcome
from aegis.server.explain import explain_plan, explain_bindings
from aegis.server import time_grammar

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aegis.demo")

# ---------------------------------------------------------------------------
# Shared pipeline components (initialized once at startup)
# ---------------------------------------------------------------------------
parser: IntentParser = None
mapper: SemanticMapper = None
compiler: SQLCompiler = None
vis_selector: VisualizationSelector = None
widget_registry: WidgetRegistry = None
dashboard_composer: DashboardComposer = None
permission_rewriter: PermissionRewriter = None
db_client: DatabaseClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize pipeline on startup, cleanup on shutdown."""
    global parser, mapper, compiler, vis_selector, widget_registry, dashboard_composer, permission_rewriter, db_client
    
    parser = IntentParser(api_key=LLM_API_KEY or GROQ_API_KEY)
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    vis_selector = VisualizationSelector()
    storage_path = os.getenv("AEGIS_WIDGET_STORAGE", "demo/demo_widgets.json")
    widget_registry = WidgetRegistry(storage_path=storage_path)
    dashboard_composer = DashboardComposer()
    permission_rewriter = PermissionRewriter()
    db_client = DatabaseClient()
    # Retry connection for up to 60 seconds
    for attempt in range(12):
        try:
            db_client.connect()
            if db_client._connection and db_client._connection.is_connected():
                logger.info("Connected to database successfully.")
                break
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt+1} failed: {e}")
        logger.info("Waiting for database to be ready...")
        time.sleep(5)
    else:
        logger.error("Could not connect to database after 60 seconds. Continuing anyway...")
    
    logger.info(f"Pipeline ready. {widget_registry.count} widgets loaded from storage.")
    yield
    db_client.disconnect()
    logger.info("Shutting down.")


app = FastAPI(
    title="AEGIS Conference Demo",
    description="Controlled NL→SQL→Widget pipeline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str


class PipelineStage(BaseModel):
    stage: str
    label: str
    data: dict


class QueryResponse(BaseModel):
    """Result of one pipeline run.

    ``outcome`` distinguishes the three ways a request can end.  Previously a
    non-answer was only ever an ``error`` string, which conflated "I cannot
    express this" with "something broke" — the first is a designed response
    and the second is a fault, and a caller needs to tell them apart.
    """
    success: bool
    widget_id: str
    is_reused: bool
    stages: list[PipelineStage]
    widget: dict
    outcome: str = "answer"
    question: str | None = None
    options: list[str] = []
    error: str | None = None


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.post("/api/query", response_model=QueryResponse)
async def process_query(req: QueryRequest):
    """Process a natural-language query through the full AEGIS pipeline."""
    stages = []
    
    try:
        # Stage 1 — Intent Extraction
        intent = await parser.parse(req.query)
        stages.append(PipelineStage(
            stage="intent",
            label="Intent Extraction (LLM)",
            data={
                "intent_class": intent.intent_class,
                "metric_term": intent.metric_term,
                "dimension_term": intent.dimension_term,
                "time_term": intent.time_term,
                "filters": [f.model_dump() for f in intent.filters] if intent.filters else [],
                "confidence": intent.confidence,
                "needs_clarification": intent.needs_clarification,
            }
        ))
        
        # Stage 2 - Grounding, narrow safety/scope cues, and time resolution.
        #
        # The LLM output is the normalized system language. The original text is
        # retained only for narrow cues that should not execute regardless of how
        # the model normalizes them: writes, direct secret requests, and explicit
        # prediction/causal modes outside this SQL-only prototype.
        result = mapper.resolve(intent, req.query)
        stages.append(PipelineStage(
            stage="resolution",
            label=f"Grounding & Intent Validation ({result.outcome.upper()})",
            data={
                "outcome": result.outcome,
                "bindings": [b.model_dump() for b in result.bindings],
                "coverage": result.coverage.model_dump(),
                "interpretation": explain_plan(result.plan) if result.plan else None,
                "evidence": explain_bindings(result.bindings),
            }
        ))

        if result.outcome != Outcome.ANSWER:
            # A request the vocabulary cannot express, or one that is genuinely
            # underdetermined, terminates here with a reason rather than being
            # answered from a substituted binding.
            return QueryResponse(
                success=False, widget_id="", is_reused=False,
                stages=stages, widget={},
                outcome=result.outcome,
                question=result.question,
                options=result.options,
                error=result.question or result.message,
            )

        plan = result.plan
        stages.append(PipelineStage(
            stage="mapping",
            label="Semantic Mapping",
            data={
                "pattern": plan.pattern,
                "metric": plan.metric,
                "dimension": plan.dimension,
                "matrix_summary": plan.matrix_summary,
                "time_rule": plan.time_rule,
                "time_range": plan.time_range.model_dump() if plan.time_range else None,
                "join_path": plan.join_path,
                "visual": plan.visual,
            }
        ))
        
        # Stage 3 — SQL Compilation
        sql, params, rationale = compiler.compile(plan)
        sql = permission_rewriter.rewrite(sql, role="public")
        
        stages.append(PipelineStage(
            stage="sql",
            label="SQL Compilation (Safe)",
            data={
                "sql": sql, 
                "params": params, 
                "template": plan.pattern,
                "rationale": rationale
            }
        ))
        
        # Stage 4 — Data Fetching
        #
        # Execution comes before chart selection so the selector can see the
        # real result shape. Selecting first meant the cardinality rules never
        # fired in the live pipeline: a breakdown over 200 manufacturers was
        # still emitted as a pie chart, because nothing had counted the rows
        # yet.
        data = []
        try:
            data = db_client.execute_query(sql, params)
        except Exception as db_err:
            logger.error(f"Failed to fetch data for widget: {db_err}")
            return QueryResponse(
                success=False,
                widget_id="",
                is_reused=False,
                stages=stages,
                widget={},
                outcome="error",
                error=str(db_err),
            )

        # Stage 5 — Visualization Selection
        vis_spec = vis_selector.select(plan, row_count=len(data) if data else None)
        stages.append(PipelineStage(
            stage="visualization",
            label="Visualization Selection",
            data=vis_spec.to_dict()
        ))

        # Stage 5 — Widget Persistence
        widget = Widget(
            original_query=req.query,
            plan=plan,
            compiled_sql=sql,
            visualization=vis_spec,
            sql_params=params,
            data=data,
            stages=[s.model_dump() for s in stages],
        )
        registered = widget_registry.register(widget)
        is_reused = registered.widget_id != widget.widget_id or len(registered.run_history) > 1
        
        stages.append(PipelineStage(
            stage="persistence",
            label="Widget Persistence",
            data={
                "widget_id": registered.widget_id,
                "is_reused": is_reused,
                "run_count": len(registered.run_history),
                "total_widgets": widget_registry.count,
            }
        ))
        
        return QueryResponse(
            success=True,
            widget_id=registered.widget_id,
            is_reused=is_reused,
            stages=stages,
            widget=registered.to_dict(),
        )
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        # `outcome` must not fall back to its "answer" default here: a caller
        # (and the live-query suite) would otherwise read a crashed request as
        # a successfully answered one, which is exactly how a compiler crash on
        # "Monthly revenue trend" passed CI.
        return QueryResponse(
            success=False,
            widget_id="",
            is_reused=False,
            stages=stages,
            widget={},
            outcome="error",
            error=str(e),
        )


@app.get("/api/widgets")
async def list_widgets():
    """List all persisted widgets."""
    widgets = widget_registry.list_all()
    return {
        "count": len(widgets),
        "widgets": [w.to_dict() for w in widgets],
    }


@app.delete("/api/widgets/{widget_id}")
async def delete_widget(widget_id: str):
    """Delete a widget by ID."""
    if widget_registry.delete(widget_id):
        return {"deleted": True, "widget_id": widget_id}
    raise HTTPException(status_code=404, detail="Widget not found")


@app.delete("/api/widgets")
async def clear_all_widgets():
    """Clear all widgets."""
    for w in widget_registry.list_all():
        widget_registry.delete(w.widget_id)
    return {"deleted": True, "count": 0}


@app.get("/api/dashboard")
async def get_dashboard():
    """Get the composed dashboard layout."""
    widgets = widget_registry.list_all()
    return dashboard_composer.compose(widgets, title="AEGIS Live Dashboard")


@app.get("/api/health")
async def health_check():
    """Container and demo smoke-test endpoint."""
    db_ok = False
    try:
        if not db_client._connection or not db_client._connection.is_connected():
            db_client.connect()
        if db_client._connection and db_client._connection.is_connected():
            cur = db_client._connection.cursor()
            cur.execute("SELECT COUNT(*) FROM `Order`")
            order_count = cur.fetchone()[0]
            cur.close()
            db_ok = True
        else:
            order_count = None
    except Exception as exc:
        return {
            "status": "degraded",
            "database": "unavailable",
            "error": str(exc),
        }

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "orders": order_count,
        "widgets": widget_registry.count,
    }


@app.get("/api/coverage")
async def get_coverage():
    """Return the semantic layer's answerable surface.

    Time expressions are part of that surface. A request can be rejected purely
    because its period could not be modelled, so a caller building a "what can
    I ask?" affordance needs the temporal vocabulary alongside the metrics and
    dimensions.
    """
    return {
        "metrics": [m.id for m in METRICS],
        "dimensions": [d.id for d in DIMENSIONS],
        "intent_classes": [e.value for e in IntentClass],
        "time_expressions": time_grammar.supported_expressions(),
        "combinations": len(METRICS) * len(DIMENSIONS) * len(IntentClass),
    }


# Note on structured validation.
#
# The pipeline validates the model structured output as the normalized system
# language. Raw text is used only for narrow non-executable cues such as writes,
# direct secrets, and explicit unsupported prediction/causal modes.
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the single-page dashboard frontend from static/index.html."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
        html = html.replace("Llama 3.1 8B (Groq)", LLM_MODEL)
        return HTMLResponse(html)
    raise HTTPException(status_code=404, detail="Frontend not found. Ensure static/index.html exists.")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AEGIS_PORT", "8765"))
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
