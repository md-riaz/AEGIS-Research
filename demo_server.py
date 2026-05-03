"""
SafeDash Conference Demo — FastAPI Backend.

Serves the full governed pipeline over HTTP:
  POST /api/query → process a natural-language query → return widget JSON
  GET  /api/widgets → list all persisted widgets
  DELETE /api/widgets/{id} → remove a widget
  GET  / → serve the dashboard frontend
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from safedash.server.intent_parser import IntentParser
from safedash.server.mapper import SemanticMapper
from safedash.server.compiler import SQLCompiler
from safedash.server.visualization import VisualizationSelector
from safedash.server.widget_engine import Widget, WidgetRegistry, DashboardComposer
from safedash.server.permission_rewriter import PermissionRewriter
from safedash.server.ai_config import GROQ_API_KEY
from safedash.server.semantic_layer import METRICS, DIMENSIONS
from safedash.server.models import IntentClass

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("safedash.demo")

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize pipeline on startup, cleanup on shutdown."""
    global parser, mapper, compiler, vis_selector, widget_registry, dashboard_composer, permission_rewriter
    
    parser = IntentParser(api_key=GROQ_API_KEY)
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    vis_selector = VisualizationSelector()
    widget_registry = WidgetRegistry(storage_path="demo_widgets.json")
    dashboard_composer = DashboardComposer()
    permission_rewriter = PermissionRewriter()
    
    logger.info(f"Pipeline ready. {widget_registry.count} widgets loaded from storage.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="SafeDash Conference Demo",
    description="Governed NL→SQL→Widget pipeline",
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
    """Process a natural-language query through the full SafeDash pipeline."""
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
        sql, params = compiler.compile(plan)
        
        # Stage 3.5 — Permission Rewriting (§4.3)
        sql = permission_rewriter.rewrite(sql, role="public")
        
        stages.append(PipelineStage(
            stage="sql",
            label="SQL Compilation (Safe)",
            data={"sql": sql, "params": params, "template": plan.pattern}
        ))
        
        # Stage 4 — Visualization Selection
        vis_spec = vis_selector.select(plan)
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
    return dashboard_composer.compose(widgets, title="SafeDash Live Dashboard")


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
    """Serve the single-page dashboard frontend."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    # Fallback: return the inline frontend
    return HTMLResponse(get_inline_frontend())


def get_inline_frontend():
    """Return the full frontend as inline HTML (no build step needed)."""
    return ""  # Frontend is served from static/index.html


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, reload=False)
