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
from aegis.server.models import IntentClass

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
    widget_registry = WidgetRegistry(storage_path="demo/demo_widgets.json")
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
    success: bool
    widget_id: str
    is_reused: bool
    stages: list[PipelineStage]
    widget: dict
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
        
        # Stage 1.5 — Coverage Validation (reject what we can't safely answer)
        validation = _validate_coverage(intent)
        if not validation["valid"]:
            stages.append(PipelineStage(
                stage="validation",
                label="Coverage Check (REJECTED)",
                data=validation,
            ))
            return QueryResponse(
                success=False, widget_id="", is_reused=False,
                stages=stages, widget={},
                error=validation["reason"],
            )
        
        # Stage 2 — Semantic Mapping
        plan = mapper.map(intent)
        stages.append(PipelineStage(
            stage="mapping",
            label="Semantic Mapping",
            data={
                "pattern": plan.pattern,
                "metric": plan.metric,
                "dimension": plan.dimension,
                "time_rule": plan.time_rule,
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
        
        # Stage 4 — Visualization Selection
        vis_spec = vis_selector.select(plan)
        stages.append(PipelineStage(
            stage="visualization",
            label="Visualization Selection",
            data=vis_spec.to_dict()
        ))
        
        # Stage 4.5 — Data Fetching
        data = []
        try:
            data = db_client.execute_query(sql, params)
        except Exception as db_err:
            logger.error(f"Failed to fetch data for widget: {db_err}")

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
        return QueryResponse(
            success=False,
            widget_id="",
            is_reused=False,
            stages=stages,
            widget={},
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


@app.get("/api/coverage")
async def get_coverage():
    """Return the semantic layer's answerable surface."""
    return {
        "metrics": [m.id for m in METRICS],
        "dimensions": [d.id for d in DIMENSIONS],
        "intent_classes": [e.value for e in IntentClass],
        "combinations": len(METRICS) * len(DIMENSIONS) * len(IntentClass),
    }


# ---------------------------------------------------------------------------
# Coverage validator — explicit rejection for out-of-scope queries (§8.5)
# Uses SemanticMapper.can_resolve() to avoid duplicating resolution logic.
# ---------------------------------------------------------------------------
METRIC_IDS = {m.id for m in METRICS}
DIMENSION_IDS = {d.id for d in DIMENSIONS}

def _validate_coverage(intent) -> dict:
    """Check if the LLM's parsed terms resolve to known semantic layer IDs.
    
    Delegates to SemanticMapper.can_resolve() so resolution logic is
    defined in exactly one place (DRY principle).
    """
    metric_term = (intent.metric_term or "").lower().strip()
    dim_term = (intent.dimension_term or "").lower().strip()
    
    # Check metric resolvability via the canonical mapper
    metric_ok = not metric_term or SemanticMapper.can_resolve(metric_term, "metric")
    # Check dimension resolvability
    dim_ok = not dim_term or SemanticMapper.can_resolve(dim_term, "dimension")
    
    if metric_ok and dim_ok:
        return {"valid": True}
    
    parts = []
    if not metric_ok:
        parts.append(f"Unknown metric '{metric_term}'. Available: {', '.join(sorted(METRIC_IDS))}")
    if not dim_ok:
        parts.append(f"Unknown dimension '{dim_term}'. Available: {', '.join(sorted(DIMENSION_IDS))}")
    
    return {"valid": False, "reason": ". ".join(parts)}


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
    uvicorn.run(app, host="127.0.0.1", port=8765, reload=False)
