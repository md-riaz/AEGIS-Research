# -*- coding: utf-8 -*-
"""
Baseline B2 — Decomposed LLM (chain-of-thought entity extraction, then SQL).

Unlike B1 (single-shot "write SQL directly") and unlike AEGIS (single-shot
structured JSON intent extraction, constrained to a closed vocabulary), B2
gives the *same* unconstrained LLM two sequential calls per query:

  Step 1 (reasoning): "Think step by step about which tables, columns,
    joins, and filters this question needs. Do not write SQL yet."
  Step 2 (generation): "Given that reasoning, now write the MySQL query."

This tests whether decomposition alone (without a semantic-layer vocabulary
constraint) meaningfully improves on B1's single-shot generation — i.e.
whether AEGIS's advantage comes from the constrained vocabulary specifically,
or just from "thinking before writing SQL" in general.

Requires the same LLM credentials as B1 (LLM_BASE_URL/LLM_API_KEY/LLM_MODEL
in .env) — each query costs 2 LLM calls instead of B1's 1, so a full run is
roughly double the API cost/time of B1.

Usage:
    python run_benchmark_b2.py            # resume from existing results
    python run_benchmark_b2.py --rerun     # force full re-evaluation
    python run_benchmark_b2.py --limit 5   # smoke test before a full run
"""
import asyncio
import json
import logging
import os
import sys

import httpx

logging.basicConfig(level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aegis.benchmark.b2")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from aegis.server.ai_config import CUSTOM, LLM_MODEL, LLM_API_KEY, GROQ_MODELS

RESULTS_FILE = "evaluation_dataset/benchmark_results_b2.json"
CONCURRENCY_LIMIT = int(os.getenv("BENCHMARK_CONCURRENCY", "1"))

SCHEMA_DESC = ("Order, OrderItem, Product, Category, Customer, Address, Country, "
               "StateProvince, Manufacturer, Shipment, Store, etc.")

REASONING_PROMPT_TMPL = (
    "Given the nopCommerce schema ({schema}), think step by step about which tables, "
    "columns, joins, and filters would be needed to answer this analytical question:\n\n"
    "\"{query}\"\n\n"
    "List the relevant tables, the join path between them, the columns/aggregates needed, "
    "and any filters (including date ranges). Do NOT write SQL yet - reasoning only."
)

SQL_PROMPT_TMPL = (
    "Given the nopCommerce schema ({schema}) and this reasoning about the required tables, "
    "joins, columns, and filters:\n\n{reasoning}\n\n"
    "Now write the final MySQL query for: \"{query}\". Return ONLY SQL code blocks."
)


async def _call_llm(prompt: str, client: httpx.AsyncClient, max_retries: int = 5) -> str:
    url = CUSTOM.url
    key = LLM_API_KEY or os.getenv("GROQ_API_KEY") or CUSTOM.api_key
    model = LLM_MODEL or GROQ_MODELS[0]

    for attempt in range(max_retries):
        if not key:
            logger.warning("No API key configured - aborting B2 call.")
            return "Failed"
        await CUSTOM.wait_if_needed()
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "stream": False,
            }
            response = await client.post(
                url, headers={"Authorization": f"Bearer {key}"}, json=payload, timeout=45.0
            )
            if response.status_code == 429:
                retry_after = float(response.headers.get("retry-after", 10))
                await asyncio.sleep(retry_after)
                continue
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            logger.warning("Error %s from %s", response.status_code, model)
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning("Attempt %d exception: %s", attempt + 1, e)
            await asyncio.sleep(2)
    return "Failed"


async def run_decomposed(query: str, client: httpx.AsyncClient) -> dict:
    reasoning_prompt = REASONING_PROMPT_TMPL.format(schema=SCHEMA_DESC, query=query)
    reasoning = await _call_llm(reasoning_prompt, client)

    if reasoning == "Failed":
        return {"reasoning": "", "sql": "Failed"}

    sql_prompt = SQL_PROMPT_TMPL.format(schema=SCHEMA_DESC, reasoning=reasoning, query=query)
    sql = await _call_llm(sql_prompt, client)
    return {"reasoning": reasoning, "sql": sql}


def _update_total_results(total_results, result_item):
    index = {r["id"]: i for i, r in enumerate(total_results)}
    if result_item["id"] in index:
        total_results[index[result_item["id"]]] = result_item
    else:
        total_results.append(result_item)
    total_results.sort(key=lambda x: x["id"])


async def process_query(i, query, client, semaphore, total_results):
    async with semaphore:
        result_item = {"id": i + 1, "query": query, "b2_reasoning": "", "b2_sql": "", "b2_status": "pending"}
        try:
            logger.info("[%d] Processing: %s...", i + 1, query[:50])
            out = await run_decomposed(query, client)
            result_item["b2_reasoning"] = out["reasoning"]
            result_item["b2_sql"] = out["sql"]
            result_item["b2_status"] = "failed" if out["sql"] == "Failed" else "success"
        except Exception as e:
            result_item["b2_status"] = "fatal_error"
            result_item["error"] = str(e)

        _update_total_results(total_results, result_item)
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(total_results, f, indent=2)


async def run_benchmark(force_rerun: bool = False, limit: int = 0):
    with open("evaluation_dataset/questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    results = []
    if not force_rerun and os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    results = json.loads(content)
        except Exception:
            results = []

    processed_ids = {r["id"] for r in results if r.get("b2_status") == "success"} if not force_rerun else set()
    if force_rerun:
        results = []

    if limit > 0:
        questions = questions[:limit]

    logger.info("B2 benchmark: %d total queries, %d already successful.", len(questions), len(processed_ids))

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    async with httpx.AsyncClient() as client:
        tasks = []
        for i, query in enumerate(questions):
            if (i + 1) in processed_ids:
                continue
            tasks.append(process_query(i, query, client, semaphore, results))
            if len(tasks) >= CONCURRENCY_LIMIT:
                await asyncio.gather(*tasks)
                tasks = []
        if tasks:
            await asyncio.gather(*tasks)

    total = len(results)
    successes = [r for r in results if r.get("b2_status") == "success"]
    print("\n" + "=" * 50)
    print("B2 (DECOMPOSED LLM) BENCHMARK SUMMARY")
    print("=" * 50)
    print(f"Total Queries: {total}")
    print(f"Succeeded (produced SQL): {len(successes)}/{total} ({len(successes)/total*100:.1f}%)")
    print("=" * 50)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerun", action="store_true", help="Force rerun all queries")
    parser.add_argument("--limit", type=int, default=int(os.getenv("CI_QUERY_LIMIT", "0")),
                        help="Cap number of queries (0 = all)")
    args = parser.parse_args()
    asyncio.run(run_benchmark(force_rerun=args.rerun, limit=args.limit))
