"""
AEGIS Intent Parser Module — extraction with a working abstention channel.

This module provides the :class:`IntentParser` service and its LLM providers.
The LLM performs exactly one job: it reads a natural-language request and emits
a typed :class:`~.models.IntentObject`.  It never writes SQL, and it may only
name identifiers that the semantic layer already approves.

The defect this module now fixes
--------------------------------
Dynamic vocabulary injection is what makes the safety property hold: the
approved metric and dimension ids are pasted into the system prompt, so the
model is *structurally unable* to emit an identifier the compiler does not
recognise.  The cost of that guarantee is that the model has no way to say
"this question is outside the vocabulary" through the normal fields — asked for
review sentiment, it must still return some approved metric id.

The previous implementation compounded that cost in two ways:

1. The OUTPUT contract in the system prompt never asked for ``confidence`` or
   ``needs_clarification`` at all, so a well-behaved model never emitted them.
2. ``_fix_common_llm_errors`` then injected ``confidence="high"`` and
   ``needs_clarification=False`` whenever those keys were absent — which was
   always.

The two together converted *absence of evidence* into *evidence of confidence*.
The downstream confidence gate could never fire, and an out-of-scope question
came back as a confident, safely compiled, entirely fictitious answer.  A third
instance of the same pattern: a missing ``intent_class`` silently became
``"kpi"``, so a request the model failed to classify was reported as a
confidently classified scalar.

What changed
------------
* The OUTPUT contract now names ``confidence``, ``needs_clarification``,
  ``clarification_reason`` and ``unmapped_terms``, and the prompt carries
  explicit abstention instructions plus worked out-of-scope examples.
  ``unmapped_terms`` is the only channel the model has for reporting a concept
  it could not bind, precisely because vocabulary injection forbids it from
  naming that concept anywhere else.
* ``_fix_common_llm_errors`` no longer manufactures confidence.  Absent keys
  stay absent so the Pydantic defaults in :mod:`.models` apply — and those
  default ``confidence`` to LOW.
* A missing or unrecognisable ``intent_class`` is marked low-confidence and
  flagged for clarification rather than being silently classified.
"""

import contextvars
import json
import logging
import abc
import asyncio
import random
from typing import Optional, Dict, Any, List

import openai
from openai import AsyncOpenAI
from .models import IntentObject, IntentClass
from .ai_config import get_provider, GROQ_MODELS, LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, GROQ
from .semantic_layer import METRICS, DIMENSIONS, APPROVED_PREDICATES

# Configure module-level logger
logger = logging.getLogger(__name__)

#: Model the provider reported for the most recent completion in this task.
#: Empty until a call succeeds; read it immediately after `parse()`.
RESOLVED_MODEL: contextvars.ContextVar = contextvars.ContextVar(
    "aegis_resolved_model", default=""
)

# Maps common fuzzy/hallucinated intent class values from the LLM to strict enum values.
# Kept at module level for visibility and to allow overriding in tests.
_INTENT_ALIASES: dict = {
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
    "data_table": "tabular", "lookup": "tabular",
}

def _retry_after_seconds(exc: openai.RateLimitError) -> Optional[float]:
    """Read a server-sent ``Retry-After`` off a 429, if one was sent.

    Guessing a backoff when the endpoint already told us exactly how long to
    wait is how three concurrent callers ended up waiting the identical fixed
    10s, then the identical fixed 20s, in lockstep — none of them were using
    the number the server actually gave.
    """
    response = getattr(exc, "response", None)
    header = response.headers.get("retry-after") if response is not None else None
    if header is None:
        return None
    try:
        return max(0.0, float(header))
    except ValueError:
        return None


class LLMProvider(abc.ABC):
    """Abstract interface for LLM service providers."""

    @abc.abstractmethod
    async def generate_intent(self, prompt: str, system_prompt: str) -> str:
        """Generates a raw completion string from the LLM."""
        pass


class OpenAICompatibleProvider(LLMProvider):
    """Provider for any OpenAI-compatible API (Groq, OpenRouter, OmniRoute, Ollama, etc.).

    Uses the official `openai` Python SDK so any endpoint that speaks the
    `/v1/chat/completions` protocol works out of the box — just set
    `LLM_BASE_URL` and `LLM_API_KEY` in your environment.
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        self.model = model
        self.profile = get_provider(model)
        # Strip trailing /chat/completions if someone pastes a full URL —
        # the SDK appends the path itself.
        base_url = base_url.rstrip("/")
        if base_url.endswith("/chat/completions"):
            base_url = base_url[: -len("/chat/completions")]
        # max_retries=0 is load-bearing, not a default worth inheriting.
        #
        # The SDK retries 429s internally (default 2), and those retries never
        # pass through `wait_if_needed`/`limiter` below — so the rolling-minute
        # budget could not see them, let alone throttle them. Layered on top of
        # the five attempts in `generate_intent`, a single logical call could
        # issue up to fifteen requests, every one of them against an endpoint
        # that was already answering 429. Retrying harder into a rate limit
        # produces more rate limiting, and the amplification is invisible in
        # our own logs because the SDK does it below our instrumentation.
        #
        # Retry policy belongs in one place, and this module already owns it.
        self.client = AsyncOpenAI(
            base_url=base_url, api_key=api_key, max_retries=0
        )

    async def generate_intent(self, prompt: str, system_prompt: str) -> str:
        """Call the provider for one completion, respecting both throttles.

        Two independent gates apply, in this order:

        1. :meth:`~.ai_config.ProviderProfile.wait_if_needed` — the rolling
           minute budget, protecting the provider's quota. It governs when a
           request may *start*.
        2. :meth:`~.ai_config.ProviderProfile.limiter` — the in-flight cap,
           held for the duration of the request so it genuinely bounds
           concurrency rather than merely spacing call starts.

        Args:
            prompt: The user's natural-language request.
            system_prompt: The vocabulary-injected system prompt.

        Returns:
            The raw completion string.

        Raises:
            ValueError: If every retry is exhausted.
        """
        max_retries = 5

        for attempt in range(max_retries):
            # Checked once here so throttled callers wait before queueing on
            # the semaphore rather than occupying a slot to do it, and again
            # after the slot is won: the queue can be long, and a 429 raised by
            # another caller in the meantime sets a block this one would
            # otherwise ignore, firing into the window the endpoint just
            # closed. Only the second call consumes rolling-minute budget.
            await self.profile.wait_if_needed(record=False)

            try:
                async with self.profile.limiter():
                    await self.profile.wait_if_needed()
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.0,
                        response_format={"type": "json_object"},
                        timeout=45.0,
                    )
                # Record what the gateway actually served. `LLM_MODEL` may be
                # an alias — "auto/chat", "AI Web" — that the router resolves
                # per request, so the configured name does not identify the
                # model that answered. Recording only the alias is how this
                # project ended up unable to say whether an improvement came
                # from its own fixes or from a model changing underneath a run.
                #
                # A ContextVar rather than an attribute: each benchmark query
                # is its own asyncio task, so this stays correct under
                # concurrency where a shared field would race.
                resolved = getattr(response, "model", None)
                if resolved:
                    RESOLVED_MODEL.set(str(resolved))
                return response.choices[0].message.content

            except openai.RateLimitError as e:
                # Back off outside the semaphore so a throttled caller does not
                # hold an in-flight slot while it sleeps.
                #
                # Prefer the endpoint's own Retry-After over a fixed guess —
                # that guess is exactly why the rate-limit window let requests
                # through the endpoint then refused: LLM_RPM (or whatever
                # default applies) is only ever this project's belief about
                # the endpoint's quota, and nothing previously checked that
                # belief against what the endpoint actually said.
                retry_after = _retry_after_seconds(e)
                base = retry_after if retry_after is not None else 10.0 * (attempt + 1)
                # Clamped to the same ceiling the profile applies to its own
                # block. `note_rate_limited` caps what it stores, but `base` is
                # also the upper bound of the jittered sleep below, and that
                # path was unclamped: a `Retry-After: 3600` would have parked
                # this caller for up to an hour while every other caller
                # resumed after 60s, so the run would appear to hang on one
                # query rather than degrade. A negative or malformed value
                # would have made `random.uniform` sample a reversed interval.
                base = min(max(0.0, base), self.profile.MAX_BACKOFF_SECONDS)

                # Feed the refusal back into the shared rolling-minute window
                # so it tightens for *every* caller, not just this attempt.
                # Without this, the window kept admitting new requests at the
                # same nominal rate while the endpoint was actively saying no
                # — which is how three concurrent callers each ran their own
                # isolated backoff and still burned through all five attempts.
                self.profile.note_rate_limited(base)

                # Full jitter: sleep a random amount in [0, base] rather than
                # exactly `base`. The log this fix responds to shows three
                # callers waiting the identical 10.0s, then the identical
                # 20.0s — concurrent callers retrying in lockstep, which
                # reproduces the same collision on every retry round.
                wait = random.uniform(0, base)
                logger.warning(
                    "Rate limited. Waiting %.1fs (attempt %d/%d)%s",
                    wait, attempt + 1, max_retries,
                    f" [server Retry-After={retry_after:.1f}s]" if retry_after is not None else "",
                )
                await asyncio.sleep(wait)
                continue
            except (openai.APIConnectionError, openai.APITimeoutError) as e:
                delay = 5.0 * (attempt + 1)
                logger.error(f"Connection/Timeout error: {e}. Waiting {delay}s...")
                await asyncio.sleep(delay)
                continue
            except Exception:
                raise

        raise ValueError(f"Failed to generate intent after {max_retries} attempts.")


class IntentParser:
    """
    Main parser service for translating natural language into IntentObjects.
    
    This class handles prompt engineering, semantic mapping, and 
    LLM response validation.
    """

    @staticmethod
    def _build_system_prompt() -> str:
        """Build the system prompt: approved vocabulary plus an abstention channel.

        The prompt has two jobs that pull against each other.  Vocabulary
        injection lists every approved metric and dimension id so the model can
        only ever name identifiers the compiler recognises — that is the safety
        guarantee.  But the same closure means the model *cannot* express "this
        question is about something you do not model": whatever it is asked, the
        only identifiers available to it are in-vocabulary ones, so its output
        always validates.

        The OUTPUT contract therefore carries four extra fields that exist
        solely to carry the model's own doubt out of that closed world:
        ``confidence``, ``needs_clarification``, ``clarification_reason`` and
        ``unmapped_terms``.  ``unmapped_terms`` is the important one — it is the
        only place the model can quote the words it could not account for,
        because it is the only field not constrained to approved identifiers.
        :mod:`.coverage` treats a non-empty list as independent evidence of a
        coverage gap.

        Returns:
            The fully rendered system prompt, with the semantic layer's current
            metric and dimension vocabulary inlined.
        """
        metrics = "|".join(m.id for m in METRICS)
        dims = "|".join(d.id for d in DIMENSIONS)
        # Compact metric descriptions for context
        m_ctx = "; ".join(f"{m.id}={m.description}" for m in METRICS)
        d_ctx = "; ".join(f"{d.id}={d.description}" for d in DIMENSIONS)
        # Named conditions are part of the approved vocabulary and must be
        # injected alongside metrics and dimensions. Omitting them made the
        # model ask for a threshold on "low stock" — a Approved definition the
        # deployment already carries — which is a clarification the user has no
        # way to answer correctly and the system did not need to raise.
        conditions = "|".join(APPROVED_PREDICATES)
        c_ctx = "; ".join(f"{k}={v['description']}"
                          for k, v in APPROVED_PREDICATES.items())
        return f"""You extract reporting intent as JSON. Map user language to approved IDs.

OUTPUT: {{"intent_class":"...","metric_term":"...or null","metric_terms":["...only for intent_class=summary, else []"],"dimension_term":"...or null","filters":[{{"field":"...","operator":"...","value":"..."}}],"sort":"asc|desc|null","limit":int|null,"time_term":"...or null","confidence":"high|medium|low","needs_clarification":true|false,"clarification_reason":"...or null","unmapped_terms":["..."]}}

METRICS (use exact ID): {metrics}
Context: {m_ctx}

DIMENSIONS (use exact ID): {dims}
Context: {d_ctx}

NAMED CONDITIONS (use as a filter value with field="condition"): {conditions}
Context: {c_ctx}
These are already defined by the deployment. When the user's request matches one, emit the filter and do NOT ask for a threshold, cutoff or status code — the definition is fixed and is not the user's to supply.

INTENT CLASSES: kpi=single scalar value (total revenue, order count)|ranking=top/bottom N items|trend=change over time|comparison=A vs B side-by-side|exception=threshold/anomaly filter|summary=multi-metric overview|segment=breakdown by one dimension|funnel=conversion stages|cohort=group behavior|correlate=attribute relationships|tabular=list/show/details of multiple records as a data table

KEY RULE FOR summary: a summary names SEVERAL measures ("summarize total sales, average order value and order count by category"). Put EVERY approved metric ID it asks for into "metric_terms", in the order stated, and set "metric_term" to the first of them. Do not pick one and drop the rest — a request for three measures answered with one is a wrong answer, not a partial one. If a summary names no measure at all, leave both empty rather than choosing on the user's behalf.

KEY RULE FOR tabular: ANY query starting with "list", "show all", "show me", "get all", "details of", "report of" or requesting a tabular listing of records MUST use intent_class="tabular". This renders as a data table, not a chart.

RULES: 1)Return ONLY raw JSON 2)metric_term/dimension_term must be exact IDs from above 3)Never generate SQL 4)Use key "intent_class" not "intent"

CONFIDENCE AND ABSTENTION (read carefully — this is not optional):
5)Always report "confidence". Use "high" only when every content word in the question is accounted for by an approved METRIC, DIMENSION, filter value, or time expression. Use "medium" when the mapping is plausible but you had to interpret. Use "low" whenever you are guessing.
6)"unmapped_terms" lists only DOMAIN CONCEPTS this vocabulary cannot express — a thing, entity or measure that simply is not modelled here. Quote the user's own words. If everything is expressible, return [].
6a)NEVER list: time expressions or granularity ("today","last month","past 60 days","daily","monthly","week over week"); aggregation or comparison words ("total","average","percentage","rate","top 5","highest","growth","decline","trend"); ordinary verbs ("generated","placed","incurred","sold","redeemed","selling"); adjectives of degree ("major","overall","key","international"). All of these are handled by other parts of the pipeline. Listing them causes the system to refuse a question it can answer.
6b)DO list things like: "page load time", "support tickets", "employee", "bounce rate", "product tags", "marketing campaign", "sentiment" — nouns naming data this vocabulary has no binding for.
7)If the question asks about data this vocabulary does not model — free text, sentiment, web/app telemetry, staff, support tickets, suppliers, marketing channels, competitors, anything absent from the lists above — you MUST STILL return valid JSON, but set "confidence":"low", "needs_clarification":true, put the offending words in "unmapped_terms", and explain in "clarification_reason". Do NOT substitute the nearest approved ID to make the request answerable. A near-miss substitution produces a confident wrong answer, which is worse than no answer.
8)This system is READ-ONLY. If the question asks to change, cancel, delete, update, refund, email or export anything, do not map it to a read query. Set "intent_class":"kpi", "metric_term":null, "confidence":"low", "needs_clarification":true and say so in "clarification_reason".
9)If you cannot determine the intent_class, still set "needs_clarification":true and "confidence":"low" rather than guessing silently.

EXAMPLES (answerable):
"top 5 products by sales"->{{"intent_class":"ranking","metric_term":"revenue","dimension_term":"product_name","limit":5,"sort":"desc","confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"monthly revenue trend"->{{"intent_class":"trend","metric_term":"revenue","dimension_term":"order_date","confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"revenue by category"->{{"intent_class":"segment","metric_term":"revenue","dimension_term":"category_name","confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"list latest order details"->{{"intent_class":"tabular","metric_term":null,"dimension_term":"order_id","sort":"desc","limit":10,"confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"show low stock products details"->{{"intent_class":"tabular","metric_term":"quantity","dimension_term":"product_name","filters":[{{"field":"quantity","operator":"<","value":10}}],"confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"list products never sold"->{{"intent_class":"tabular","metric_term":"item_quantity","dimension_term":"product_name","filters":[{{"field":"item_quantity","operator":"=","value":0}}],"confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"list all customers registered this year"->{{"intent_class":"tabular","metric_term":null,"dimension_term":"customer_email","filters":[{{"field":"customer_registration_date","operator":"=","value":"this year"}}],"confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"show orders with refund amount greater than 0"->{{"intent_class":"tabular","metric_term":"refund_amount","dimension_term":"order_id","filters":[{{"field":"refund_amount","operator":">","value":0}}],"confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"products with stock less than 10"->{{"intent_class":"tabular","metric_term":"quantity","dimension_term":"product_name","filters":[{{"field":"quantity","operator":"<","value":10}}],"confidence":"high","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}
"list best customers by order total"->{{"intent_class":"tabular","metric_term":"order_total","dimension_term":"customer_email","sort":"desc","limit":20,"confidence":"medium","needs_clarification":false,"clarification_reason":null,"unmapped_terms":[]}}

EXAMPLES (NOT answerable — abstain, do not substitute):
"what do customers say in reviews about shipping speed"->{{"intent_class":"tabular","metric_term":null,"dimension_term":null,"filters":[],"sort":null,"limit":null,"time_term":null,"confidence":"low","needs_clarification":true,"clarification_reason":"Review text and sentiment are not modelled; only the count of approved reviews (product_rating) exists, which cannot say what customers wrote.","unmapped_terms":["say","reviews","shipping speed"]}}
"average page load time on checkout"->{{"intent_class":"kpi","metric_term":null,"dimension_term":null,"filters":[],"sort":null,"limit":null,"time_term":null,"confidence":"low","needs_clarification":true,"clarification_reason":"There is no web telemetry in this semantic layer — no page views, load times or checkout events.","unmapped_terms":["page load time","checkout"]}}
"which employee closed the most tickets"->{{"intent_class":"ranking","metric_term":null,"dimension_term":null,"filters":[],"sort":"desc","limit":null,"time_term":null,"confidence":"low","needs_clarification":true,"clarification_reason":"Employees and support tickets are not part of this vocabulary; only customers, orders, products and shipments are.","unmapped_terms":["employee","tickets"]}}
"cancel all orders stuck in pending"->{{"intent_class":"kpi","metric_term":null,"dimension_term":null,"filters":[],"sort":null,"limit":null,"time_term":null,"confidence":"low","needs_clarification":true,"clarification_reason":"This is a write request. The system can only read and report; it cannot modify orders. It could instead show pending orders as a report.","unmapped_terms":["cancel"]}}"""

    def __init__(self, api_key: Optional[str] = None, model: str = GROQ_MODELS[0]):
        self.system_prompt = self._build_system_prompt()

        # Resolve base_url and key: explicit env vars win, then fall back to Groq defaults.
        # Groq is OpenAI-compatible, so one provider class handles all cases.
        base_url = LLM_BASE_URL or GROQ.url
        # When a custom endpoint is configured, LLM_API_KEY must win over any
        # legacy key passed by callers (e.g. GROQ_API_KEY from demo entrypoints).
        if LLM_BASE_URL:
            actual_key = LLM_API_KEY or api_key or GROQ.api_key
        else:
            actual_key = api_key or LLM_API_KEY or GROQ.api_key
        actual_model = LLM_MODEL or model

        if not actual_key:
            raise ValueError(
                "No LLM API key found. Set LLM_API_KEY (generic) or GROQ_API_KEY in your .env."
            )

        self.provider = OpenAICompatibleProvider(base_url, actual_key, actual_model)

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

    #: Canonical intent classes, used to tell a successful repair from a guess.
    _KNOWN_CLASSES = {
        "kpi", "ranking", "trend", "comparison", "exception", "summary",
        "segment", "funnel", "cohort", "correlate", "tabular",
    }

    def _fix_common_llm_errors(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise LLM output shape without manufacturing confidence.

        This method repairs *syntactic* variation — a key named ``intent``
        instead of ``intent_class``, a filter object where a list was expected,
        a single-element list where a string was expected.  Those repairs are
        safe because they do not change what the model asserted.

        What it must never do is invent *semantic* content.  The previous
        implementation ended with::

            if "confidence" not in data: data["confidence"] = "high"
            if "needs_clarification" not in data: data["needs_clarification"] = False

        Since the prompt never asked for either field, neither was ever
        present, so every request was stamped high-confidence and
        no-clarification-needed regardless of what the model actually knew.
        The confidence gate downstream was unreachable by construction.  Absent
        keys are now left absent, and :mod:`.models` defaults ``confidence`` to
        LOW — the conservative direction.

        Args:
            data: Parsed JSON object returned by the model.

        Returns:
            The same mapping, normalised in place, ready for ``IntentObject``
            validation.
        """
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
            # Normalize LLM variations using the module-level alias map
            if val in _INTENT_ALIASES:
                data["intent_class"] = _INTENT_ALIASES[val]

            # Regex-like fuzzy match (e.g. "top_n" -> "ranking")
            for key, target in [("top", "ranking"), ("trend", "trend"), ("comp", "comparison"),
                                ("segment", "segment"), ("funnel", "funnel"), ("cohort", "cohort"),
                                ("correlat", "correlate"), ("list", "tabular"),
                                ("detail", "tabular"), ("lookup", "tabular")]:
                if key in val and data["intent_class"] == val:
                    data["intent_class"] = target

        # An unrecognised or missing class is a classification *failure*, not a
        # KPI request.  We still have to emit a schema-valid value for the
        # enum, so we fall back to "kpi" — but we mark the fallback, so the
        # resolver treats it as a request for clarification instead of a
        # confident scalar.  Silently defaulting here is how an HR question
        # became a bare order count.
        if str(data.get("intent_class", "")).lower() not in self._KNOWN_CLASSES:
            logger.warning(
                "Unclassifiable intent_class %r — marking low confidence.",
                data.get("intent_class"),
            )
            data["intent_class"] = "kpi"
            data["confidence"] = "low"
            data["needs_clarification"] = True
            data.setdefault(
                "clarification_reason",
                "The kind of report being requested could not be determined.",
            )

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

        # 3. Normalise the abstention channel.
        #    Deliberately no defaults for `confidence` / `needs_clarification`:
        #    a model that stayed silent about its confidence has not told us it
        #    is confident.  models.IntentObject defaults confidence to LOW.
        if "confidence" in data:
            level = str(data["confidence"]).lower().strip()
            data["confidence"] = level if level in {"high", "medium", "low"} else "low"

        if "needs_clarification" in data:
            data["needs_clarification"] = bool(data["needs_clarification"])

        # `unmapped_terms` is the model's only channel for reporting a concept
        # it could not bind, so accept the shapes a model plausibly emits
        # rather than discarding the signal on a formatting slip.
        raw_unmapped = data.get("unmapped_terms")
        if raw_unmapped is None:
            data.pop("unmapped_terms", None)
        elif isinstance(raw_unmapped, str):
            data["unmapped_terms"] = [raw_unmapped] if raw_unmapped.strip() else []
        elif isinstance(raw_unmapped, list):
            data["unmapped_terms"] = [
                str(t).strip() for t in raw_unmapped if str(t).strip()
            ]
        else:
            data["unmapped_terms"] = [str(raw_unmapped)]


        # 4. Handle metric_term and dimension_term as lists (LLM sometimes hallucinates multiple metrics)
        for field in ["metric_term", "dimension_term"]:
            if field in data and isinstance(data[field], list):
                if len(data[field]) > 0:
                    data[field] = str(data[field][0])
                else:
                    data[field] = None

        # 5. metric_terms is the inverse case: it must be a list, and the model
        # sometimes returns a bare string for it just as it sometimes returns a
        # list for the singular fields above. Without this, a format slip
        # raises a Pydantic ValidationError that surfaces as a crash — the one
        # outcome this pipeline is built to avoid in favour of a reasoned
        # decline. Normalising costs nothing and keeps a shape wobble from
        # becoming a hard failure.
        raw_terms = data.get("metric_terms")
        if raw_terms is None:
            data.pop("metric_terms", None)
        elif isinstance(raw_terms, str):
            data["metric_terms"] = [raw_terms] if raw_terms.strip() else []
        elif isinstance(raw_terms, list):
            data["metric_terms"] = [str(t) for t in raw_terms if t]
        else:
            data["metric_terms"] = []

        return data
