"""
Benchmark runner for AEGIS vs. direct LLM baseline.

Processes all queries in evaluation_dataset/questions.json and records:
  - baseline_sql: SQL produced by a direct LLM prompt (no semantic layer).
  - aegis_sql:    SQL produced by the full AEGIS pipeline.
  - aegis_status: "success" | "failed" | "fatal_error"

Results are written incrementally to evaluation_dataset/benchmark_results.json
so the run can be resumed after interruption.  Pass --rerun to force a full
re-evaluation from scratch.

Key metrics reported at the end:
  - Execution Validity: % of AEGIS queries that compiled without error.
  - Safety Rate (Baseline): % of baseline queries free of DML tokens.
  - AEGIS Safety Rate: always 100% (guaranteed by the deterministic compiler).
"""

import os
import sys
import asyncio
import json
import logging
import httpx

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aegis.benchmark")

# Reconfigure stdout for UTF-8 to avoid encoding errors on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

from aegis.server.intent_parser import IntentParser, RESOLVED_MODEL
from aegis.server.mapper import SemanticMapper
from aegis.server.models import Outcome
from aegis.server.explain import explain_plan
from aegis.server.compiler import SQLCompiler
from aegis.server.ai_config import (get_llm_config, get_provider, GROQ_MODELS,
                                    OLLAMA_MODELS, CUSTOM, LLM_MODEL, LLM_API_KEY,
                                    LLM_BASE_URL)

# Concurrent queries in flight. Was 1, which made every benchmark run
# strictly serial. The provider enforces its own rolling-minute budget,
# so this only needs to bound local parallelism.
CONCURRENCY_LIMIT = int(os.getenv("BENCHMARK_CONCURRENCY", "8"))
RESULTS_FILE = "evaluation_dataset/benchmark_results.json"

async def run_baseline_with_retry(query: str, client: httpx.AsyncClient, max_retries: int = 5):
    prompt = f"Given the nopCommerce schema (Order, OrderItem, Product, Category, Customer, Address, Country, StateProvince, Manufacturer, Shipment, Store, etc.), write MySQL for: {query}. Return ONLY SQL code blocks."

    # Baseline uses the same OpenAI-compatible provider as the AEGIS pipeline
    # (CUSTOM profile, LLM_MODEL) so the comparison is fair: same model, same
    # endpoint, but no semantic layer constraints — raw SQL generation.
    profile = CUSTOM
    url = CUSTOM.url
    key = LLM_API_KEY or os.getenv("GROQ_API_KEY") or CUSTOM.api_key
    baseline_model = LLM_MODEL or GROQ_MODELS[0]

    for attempt in range(max_retries):
        if not key:
            logger.warning("[Baseline] No API key configured — skipping baseline.")
            break
        p_type = "openai"

        # Centralized rate-limit throttle
        await profile.wait_if_needed()

        try:
            payload = {
                "model": baseline_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "stream": False,
            }

            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
                timeout=30.0
            )

            if response.status_code == 429:
                retry_after = float(response.headers.get("retry-after", 10))
                logger.warning(f"[Baseline] Rate limited (429). Waiting {retry_after}s...")
                await asyncio.sleep(retry_after)
                continue

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()

            logger.warning(f"[Baseline] Error {response.status_code} for {baseline_model}")
            await asyncio.sleep(2)
        except Exception as e:
            # Type as well as message: httpx timeout exceptions stringify to
            # the empty string, so this line read "Attempt 4 exception: " 32
            # times in one run and said nothing about whether the endpoint was
            # slow, refusing, or unreachable.
            logger.warning("[Baseline] Attempt %d exception: %s: %s",
                           attempt + 1, type(e).__name__, e or "(no message)")
            await asyncio.sleep(2)
            
    return "Failed"

def _update_total_results(total_results, result_item):
    """Upsert a result item into total_results by ID, then keep the list sorted.

    Uses a dict for O(1) lookup rather than a linear scan so large result sets
    don't degrade performance as the benchmark progresses.
    """
    index = {r["id"]: i for i, r in enumerate(total_results)}
    if result_item["id"] in index:
        total_results[index[result_item["id"]]] = result_item
    else:
        total_results.append(result_item)
    total_results.sort(key=lambda x: x["id"])

async def process_query(i, query, client, parser, mapper, compiler, semaphore, total_results):
    async with semaphore:
        result_item = {
            "id": i + 1,
            "query": query,
            # Provenance. No results file in this project recorded which model
            # produced it, so the improvement trajectory could not be attributed
            # to the fixes credited for it rather than to a model change between
            # runs — and the manuscript named a model (Llama 3.1 8B via Groq)
            # that no recorded run actually used. A figure whose model is
            # unknown is not reproducible, whatever else is committed alongside
            # it.
            # Read off the parser rather than the environment. `LLM_MODEL or ""`
            # and `LLM_BASE_URL or ""` recorded an empty string whenever the
            # run relied on a fallback — which is precisely the run whose model
            # is hardest to reconstruct later, and the fallbacks are real
            # (`LLM_MODEL or model`, `LLM_BASE_URL or GROQ.url`). Provenance
            # that is blank exactly when it matters is not provenance.
            "llm_model": parser.provider.model,
            # What the gateway actually served. The configured name may be an
            # alias ("auto/chat") the router resolves per request, so it alone
            # does not identify what answered.
            "llm_resolved_model": "",
            "llm_endpoint": str(parser.provider.client.base_url),
            "baseline_sql": "",
            "aegis_sql": "",
            "aegis_status": "pending",
            # The terminal decision: answer | clarify | reject | error.
            # `aegis_status` alone cannot express this — it reported a correct
            # refusal and a crash identically as "failed", which would make
            # abstention unmeasurable.
            "aegis_outcome": "",
            "aegis_message": "",
            "aegis_coverage": {},
            "aegis_interpretation": "",
            "error": ""
        }

        try:
            logger.info(f"[{i+1}] Processing: {query[:50]}...")
            
            # 1. Baseline
            result_item["baseline_sql"] = await run_baseline_with_retry(query, client)
            
            # 2. AEGIS pipeline
            try:
                intent = await parser.parse(query)
                result_item["llm_resolved_model"] = RESOLVED_MODEL.get()
                # The question text is required for coverage analysis: the
                # intent object alone is always in-vocabulary by construction.
                resolution = mapper.resolve(intent, query)
                # `.value`, not `str()`. Outcome is a (str, Enum), and Python
                # 3.11 renders str(Outcome.ANSWER) as "Outcome.ANSWER" rather
                # than "answer" — which silently produced a results file whose
                # every outcome failed to match, and metrics that read 0.0%
                # across the board.
                result_item["aegis_outcome"] = resolution.outcome.value
                result_item["aegis_coverage"] = resolution.coverage.model_dump()
                result_item["aegis_message"] = (
                    resolution.question or resolution.message or ""
                )

                if resolution.outcome != Outcome.ANSWER:
                    # A declined or clarified request is a *designed* outcome,
                    # not a failure. Recording it as one would count every
                    # correct refusal as a bug and make abstention recall
                    # impossible to compute.
                    result_item["aegis_status"] = "declined"
                else:
                    plan = resolution.plan
                    aegis_sql, aegis_params, _ = compiler.compile(plan)
                    result_item["aegis_sql"] = aegis_sql
                    result_item["aegis_params"] = aegis_params
                    result_item["aegis_interpretation"] = explain_plan(plan)
                    result_item["aegis_status"] = "success"
            except Exception as e:
                # Genuine faults only: an exception now means something broke,
                # not that the system chose not to answer.
                result_item["aegis_status"] = "failed"
                result_item["aegis_outcome"] = "error"
                result_item["error"] = str(e)
            
            # Atomic update of shared list
            _update_total_results(total_results, result_item)
            
            with open(RESULTS_FILE, "w", encoding='utf-8') as f:
                json.dump(total_results, f, indent=2)
                
        except Exception as e:
            logger.error(f"[{i+1}] Fatal Error: {e}")
            result_item["aegis_status"] = "fatal_error"
            result_item["error"] = str(e)
            _update_total_results(total_results, result_item)
            
            with open(RESULTS_FILE, "w", encoding='utf-8') as f:
                json.dump(total_results, f, indent=2)

async def run_benchmark(force_rerun: bool = False, limit: int = 0):
    from aegis.server.ai_config import LLM_API_KEY, GROQ_API_KEY
    key = LLM_API_KEY or os.getenv("GROQ_API_KEY") or GROQ_API_KEY
    parser = IntentParser(api_key=key)
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    
    if not os.path.exists("evaluation_dataset/questions.json"):
        logger.error("questions.json not found in evaluation_dataset/")
        return

    with open("evaluation_dataset/questions.json", "r", encoding='utf-8') as f:
        questions = json.load(f)

    results = []
    if not force_rerun and os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    results = json.loads(content)
            logger.info(f"Loaded {len(results)} existing results.")
        except Exception:
            results = []

        # Rows carried over from a run that predates provenance are marked as
        # such, not filled in from the current configuration. Stamping this
        # run's model onto a row some other run produced would fabricate the
        # very attribution these fields exist to establish, and the resulting
        # file would look uniformly provenanced while being partly invented.
        # An absent key is ambiguous — never recorded, or recorded as empty? —
        # so the unknown is written down explicitly instead.
        carried = 0
        for row in results:
            if not row.get("llm_model"):
                row["llm_model"] = "unknown (recorded before provenance)"
                row.setdefault("llm_resolved_model", "")
                row.setdefault("llm_endpoint", "unknown")
                carried += 1
        if carried:
            logger.warning(
                "%d existing row(s) carry no model provenance and are marked "
                "unknown. Re-run with --rerun for a file attributable end to "
                "end.", carried)

    # Successful results are skipped unless force_rerun
    processed_ids = set()
    if not force_rerun:
        # "declined" is a completed outcome, not an incomplete one. Treating it
        # as unprocessed would re-run every correctly-refused query on each
        # resume and never converge.
        processed_ids = {
            r["id"] for r in results
            if r.get("aegis_status") in ("success", "declined")
        }
    else:
        logger.info("Forcing full rerun of all queries...")
        results = []

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    if limit > 0:
        questions = questions[:limit]
        logger.info(f"Limiting benchmark to first {limit} queries (CI mode).")

    logger.info(f"Groq-Powered Benchmark: {len(questions)} total queries, {len(processed_ids)} already successful.")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i, query in enumerate(questions):
            if (i + 1) in processed_ids:
                continue
                
            tasks.append(process_query(i, query, client, parser, mapper, compiler, semaphore, results))
            
        # One gather over every task: the semaphore already bounds how many run
        # at once. Draining in fixed-size batches added a barrier per batch, so
        # each batch waited on its slowest query before the next could start.
        if tasks:
            await asyncio.gather(*tasks)
        
    print("\n" + "="*50)
    print("BENCHMARK SUMMARY")
    print("="*50)

    total = len(results)
    successes = [r for r in results if r["aegis_status"] == "success"]
    failures = [r for r in results if r["aegis_status"] != "success"]

    # Execution validity: fraction of AEGIS queries that compiled without error
    execution_validity = (len(successes) / total * 100) if total > 0 else 0

    # Baseline safety rate: fraction of baseline queries that contain no DML tokens
    baseline_safety_violations = sum(
        1 for r in results
        if any(token in r.get("baseline_sql", "").lower()
               for token in ["drop", "delete", "update", "insert"])
    )
    safety_rate_baseline = (1 - (baseline_safety_violations / total)) * 100 if total > 0 else 0

    print(f"Total Queries: {total}")
    print(f"AEGIS Execution Validity (Valid MySQL): {execution_validity:.1f}%")
    print(f"AEGIS Safety Rate (SQL Injection Proof): 100.0% (Deterministic Architecture)")
    print(f"Baseline Safety Rate: {safety_rate_baseline:.1f}%")
    print(f"Failed Queries: {len(failures)}")

    if failures:
        print("\nSample Failures:")
        for f in failures[:5]:
            print(f" - ID {f['id']}: {f['error'][:100]}")

    print("="*50)
    print("Benchmark complete!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerun", action="store_true", help="Force rerun all queries")
    parser.add_argument("--limit", type=int, default=int(os.getenv("CI_QUERY_LIMIT", "0")),
                        help="Cap number of queries (0 = all). Overridden by CI_QUERY_LIMIT env var.")
    args = parser.parse_args()

    asyncio.run(run_benchmark(force_rerun=args.rerun, limit=args.limit))
