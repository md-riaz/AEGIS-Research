"""
SafeDash Intent Parser Module.

This module provides the IntentParser class and its related providers.
It uses Large Language Models (LLMs) to extract a structured analysis intent 
from natural language requests while strictly adhering to safety constraints.
"""

import json
import logging
import abc
import asyncio
from typing import Optional, Dict, Any, List

import httpx
from .models import IntentObject, IntentClass
from .ai_config import get_llm_config, get_provider, GROQ_MODELS
from .semantic_layer import METRICS, DIMENSIONS

# Configure module-level logger
logger = logging.getLogger(__name__)

class LLMProvider(abc.ABC):
    """Abstract interface for LLM service providers."""

    @abc.abstractmethod
    async def generate_intent(self, prompt: str, system_prompt: str) -> str:
        """Generates a raw completion string from the LLM."""
        pass

class GroqProvider(LLMProvider):
    """Implementation for the Groq API with centralized rate limiting."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.profile = get_provider(model)

    async def generate_intent(self, prompt: str, system_prompt: str) -> str:
        max_retries = 5

        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries):
                # Centralized RPM throttle — waits if budget exhausted
                await self.profile.wait_if_needed()

                try:
                    payload = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.0,
                        "response_format": {"type": "json_object"}
                    }
                    response = await client.post(
                        self.profile.url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json=payload,
                        timeout=45.0
                    )

                    if response.status_code == 429:
                        retry_after = float(response.headers.get("retry-after", 10))
                        logger.warning(f"Rate limited (429). Waiting {retry_after}s (attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status_code != 200:
                        logger.error(f"Groq API Error {response.status_code}: {response.text}")

                    response.raise_for_status()
                    return response.json()["choices"][0]["message"]["content"]

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    delay = 5.0 * (attempt + 1)
                    logger.error(f"Connection/Timeout error: {e}. Waiting {delay}s...")
                    await asyncio.sleep(delay)

            raise ValueError(f"Failed to generate intent after {max_retries} attempts.")

class IntentParser:
    """
    Main parser service for translating natural language into IntentObjects.
    
    This class handles prompt engineering, semantic mapping, and 
    LLM response validation.
    """

    @staticmethod
    def _build_system_prompt() -> str:
        """Builds a token-efficient system prompt with approved vocabulary
        from the semantic layer. The LLM maps user language to canonical IDs."""
        metrics = "|".join(m.id for m in METRICS)
        dims = "|".join(d.id for d in DIMENSIONS)
        # Compact metric descriptions for context
        m_ctx = "; ".join(f"{m.id}={m.description}" for m in METRICS)
        d_ctx = "; ".join(f"{d.id}={d.description}" for d in DIMENSIONS)
        return f"""You extract reporting intent as JSON. Map user language to approved IDs.

OUTPUT: {{"intent_class":"...","metric_term":"...","dimension_term":"...or null","filters":[{{"field":"...","operator":"...","value":"..."}}],"sort":"asc|desc|null","limit":int|null,"time_term":"...or null"}}

METRICS (use exact ID): {metrics}
Context: {m_ctx}

DIMENSIONS (use exact ID): {dims}
Context: {d_ctx}

INTENT CLASSES: kpi=single scalar value (total revenue, order count)|ranking=top/bottom N items|trend=change over time|comparison=A vs B side-by-side|exception=threshold/anomaly filter|summary=multi-metric overview|segment=breakdown by one dimension|funnel=conversion stages|cohort=group behavior|correlate=attribute relationships|tabular=list/show/details of multiple records as a data table

KEY RULE FOR tabular: ANY query starting with "list", "show all", "show me", "get all", "details of", "report of" or requesting a tabular listing of records MUST use intent_class="tabular". This renders as a data table, not a chart.

RULES: 1)Return ONLY raw JSON 2)metric_term/dimension_term must be exact IDs from above 3)Never generate SQL 4)Use key "intent_class" not "intent"

EXAMPLES:
"top 5 products by sales"->{{"intent_class":"ranking","metric_term":"revenue","dimension_term":"product_name","limit":5,"sort":"desc"}}
"monthly revenue trend"->{{"intent_class":"trend","metric_term":"revenue","dimension_term":"order_date"}}
"revenue by category"->{{"intent_class":"segment","metric_term":"revenue","dimension_term":"category_name"}}
"list latest order details"->{{"intent_class":"tabular","metric_term":null,"dimension_term":"order_id","sort":"desc","limit":10}}
"show low stock products details"->{{"intent_class":"tabular","metric_term":"quantity","dimension_term":"product_name","filters":[{{"field":"quantity","operator":"<","value":10}}]}}
"list products never sold"->{{"intent_class":"tabular","metric_term":"item_quantity","dimension_term":"product_name","filters":[{{"field":"item_quantity","operator":"=","value":0}}]}}
"list all customers registered this year"->{{"intent_class":"tabular","metric_term":null,"dimension_term":"customer_email","filters":[{{"field":"customer_registration_date","operator":"=","value":"this year"}}]}}
"show orders with refund amount greater than 0"->{{"intent_class":"tabular","metric_term":"refund_amount","dimension_term":"order_id","filters":[{{"field":"refund_amount","operator":">","value":0}}]}}
"products with stock less than 10"->{{"intent_class":"tabular","metric_term":"quantity","dimension_term":"product_name","filters":[{{"field":"quantity","operator":"<","value":10}}]}}
"list best customers by order total"->{{"intent_class":"tabular","metric_term":"order_total","dimension_term":"customer_email","sort":"desc","limit":20}}"""

    def __init__(self, api_key: Optional[str] = None, model: str = GROQ_MODELS[0]):
        # Build the system prompt dynamically from the semantic layer
        self.system_prompt = self._build_system_prompt()
        
        """Initializes the parser with a specific provider."""
        url, key, p_type = get_llm_config(model)
        actual_key = api_key or key
        
        if not actual_key:
            raise ValueError("No API key provided for IntentParser.")

        if p_type == "openai" or "groq" in url:
            self.provider = GroqProvider(actual_key, model)
        else:
            raise NotImplementedError(f"Provider type {p_type} not yet implemented.")

    async def parse(self, query: str) -> IntentObject:
        """Parses a user query into a validated IntentObject."""
        logger.info(f"Parsing query: {query}")
        try:
            raw_response = await self.provider.generate_intent(query, self.system_prompt)
            
            # Clean possible markdown formatting
            if "```json" in raw_response:
                raw_response = raw_response.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_response:
                raw_response = raw_response.split("```")[1].strip()

            intent_data = json.loads(raw_response)
            intent_data = self._fix_common_llm_errors(intent_data)
            
            # Final validation
            return IntentObject(**intent_data)

        except Exception as e:
            logger.error(f"Intent parsing failed: {e}")
            raise ValueError(f"Failed to extract intent from query: {str(e)}")

    def _fix_common_llm_errors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes variations in LLM output to match strict Pydantic requirements."""
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            else:
                data = {}

        # 1. Fix top-level Intent Class
        if "intent" in data and "intent_class" not in data:
            data["intent_class"] = data["intent"]
            
        if "intent_class" in data:
            val = str(data["intent_class"]).lower()
            # Mapping common fuzzy terms to strict enums
            mapping = {
                "revenue": "kpi", "sales": "kpi", "count": "kpi", "total": "kpi",
                "get_total": "kpi", "get_count": "kpi",
                "get_top_n": "ranking", "get_top_customers": "ranking",
                "get_top_products": "ranking", "growth": "trend", "chart": "trend",
                "plot": "trend", "compare": "comparison", "difference": "comparison",
                "breakdown": "segment", "by_category": "segment", "distribution": "segment",
                "conversion": "funnel", "pipeline": "funnel", "stages": "funnel",
                "group_analysis": "cohort", "new_vs_returning": "cohort", "customer_type": "cohort",
                "correlation": "correlate", "relationship": "correlate", "association": "correlate",
                "list": "tabular", "show": "tabular", "details": "tabular",
                "report": "tabular", "records": "tabular", "datatable": "tabular",
                "data_table": "tabular", "lookup": "tabular"
            }
            if val in mapping:
                data["intent_class"] = mapping[val]
            
            # Regex-like fuzzy match (e.g. "top_n" -> "ranking")
            for key, target in [("top", "ranking"), ("trend", "trend"), ("comp", "comparison"),
                                ("segment", "segment"), ("funnel", "funnel"), ("cohort", "cohort"),
                                ("correlat", "correlate"), ("list", "tabular"),
                                ("detail", "tabular"), ("lookup", "tabular")]:
                if key in val and data["intent_class"] == val:
                    data["intent_class"] = target
        else:
            data["intent_class"] = "kpi" # Safe default

        # 2. Fix Filters
        if "filters" in data:
            if not isinstance(data["filters"], list):
                # Handle single dict as list
                if isinstance(data["filters"], dict):
                    data["filters"] = [data["filters"]]
                else:
                    data["filters"] = []
            
            clean_filters = []
            for f in data["filters"]:
                if not isinstance(f, dict): continue
                
                # Map hallucinated field names
                f_field = f.get("field") or f.get("dimension") or f.get("metric") or f.get("name")
                f_op = f.get("operator") or f.get("op") or "="
                f_val = f.get("value")
                
                if f_field and f_val is not None:
                    clean_filters.append({
                        "field": str(f_field),
                        "operator": str(f_op),
                        "value": f_val
                    })
            data["filters"] = clean_filters
        else:
            data["filters"] = []

        # 3. Ensure defaults for other fields
        if "confidence" not in data: data["confidence"] = "high"
        if "needs_clarification" not in data: data["needs_clarification"] = False
        
        # 4. Handle metric_term and dimension_term as lists (LLM sometimes hallucinates multiple metrics)
        for field in ["metric_term", "dimension_term"]:
            if field in data and isinstance(data[field], list):
                if len(data[field]) > 0:
                    data[field] = str(data[field][0])
                else:
                    data[field] = None
            
        return data
