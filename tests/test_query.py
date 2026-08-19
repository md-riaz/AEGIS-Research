"""
End-to-end query tests against a running AEGIS demo server.

Sends representative queries to ``/api/query`` and checks that each one
terminates in a well-formed outcome.  Requires the server to be running at
http://localhost:8765 and a configured LLM endpoint, since intent extraction
is the one stage that genuinely needs a model.

Usage:
    python run_demo_server.py   # start server first
    python tests/test_query.py

What this does and does not assert
----------------------------------
It asserts that the pipeline *terminates cleanly* — every query comes back
with a recognised outcome (``answer``, ``clarify`` or ``reject``) rather than
hanging, 500-ing, or returning an unparseable body.

It deliberately does **not** assert that a given query must be answered.  With
the structured validation path in place, declining a request is a designed outcome, not
a failure, and pinning specific queries to specific outcomes here would be an
accuracy claim dressed up as a smoke test.  Measuring which requests *should*
be answered belongs in the evaluation dataset, not in CI.

Previously this script printed results and continued past every error, so it
could not fail regardless of what the server did — a green run proved only
that the process started.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = os.getenv("AEGIS_BASE_URL", "http://localhost:8765")

# The server allows the LLM call up to 45s and retries on connection errors.
# A client timeout shorter than the server's own budget turns a slow-but-
# working model into a test failure; the previous 15s did exactly that.
TIMEOUT_SECONDS = int(os.getenv("AEGIS_QUERY_TIMEOUT", "90"))

#: Queries issued in parallel. The server applies its own in-flight cap
#: (LLM_CONCURRENCY), so this only needs to keep the pipe full.
CONCURRENCY = int(os.getenv("AEGIS_QUERY_CONCURRENCY", "6"))

VALID_OUTCOMES = {"answer", "clarify", "reject"}

QUERIES = [
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
    "Monthly revenue trend",
]


def llm_is_configured() -> bool:
    """Whether an LLM endpoint is available to this environment.

    Intent extraction is the single stage that cannot run offline.  When no
    credentials are configured there is nothing to integrate against, and a
    failure here would report "the code is broken" when the truth is "the
    environment has no model" — so the suite reports a skip instead.

    A misconfigured-but-present key is *not* treated as absent: the request
    then runs and any error fails the suite, which is the behaviour that makes
    a green result meaningful.
    """
    return bool(
        os.getenv("LLM_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or os.getenv("LLM_BASE_URL")
    )


def _submit(query: str):
    """Send one query, returning ``(query, response_or_None, error_or_None)``."""
    try:
        return query, requests.post(
            f"{BASE}/api/query", json={"query": query}, timeout=TIMEOUT_SECONDS
        ), None
    except requests.RequestException as exc:
        return query, None, str(exc)


def run_queries() -> int:
    """Submit every query and verify each terminates in a recognised outcome.

    Queries are issued concurrently. Each one costs an LLM round-trip, so a
    serial loop made the suite's runtime the *sum* of twelve model latencies —
    the single largest cost in the integration job, and the reason it was
    previously bumping the client timeout. Results are collected before
    printing so the output stays grouped per query rather than interleaved.

    Returns:
        Process exit code — 0 when every query produced a valid outcome.
    """
    failures = []

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        responses = dict(
            (query, (response, error))
            for query, response, error in pool.map(_submit, QUERIES)
        )

    for query in QUERIES:
        response, error = responses[query]
        print(f"\n{'=' * 60}\nQUERY: {query}\n{'=' * 60}")
        if error is not None:
            print(f"  TRANSPORT FAILURE: {error}")
            failures.append((query, error))
            continue

        if response.status_code != 200:
            print(f"  HTTP {response.status_code}: {response.text[:200]}")
            failures.append((query, f"HTTP {response.status_code}"))
            continue

        try:
            payload = response.json()
        except ValueError as exc:
            print(f"  UNPARSEABLE BODY: {exc}")
            failures.append((query, "unparseable JSON"))
            continue

        outcome = payload.get("outcome")
        # An "answer" that did not succeed is a crash wearing an answer's
        # label. Reading the default rather than the real field is what let a
        # compiler exception through as a passing query.
        if outcome == "answer" and not payload.get("success"):
            print(f"  CRASHED WHILE ANSWERING: {payload.get('error')}")
            failures.append((query, f"answer but success=False: {payload.get('error')}"))
            continue

        if outcome not in VALID_OUTCOMES:
            print(f"  UNRECOGNISED OUTCOME: {outcome!r} — {payload.get('error')}")
            failures.append((query, f"outcome={outcome!r}"))
            continue

        print(f"  OUTCOME: {outcome}")

        if outcome != "answer":
            # A declined or clarified request must explain itself; an
            # unexplained non-answer is as unhelpful as a wrong answer.
            reason = payload.get("question") or payload.get("error")
            print(f"  REASON: {reason}")
            if not reason:
                failures.append((query, "non-answer with no reason given"))
            continue

        for stage in payload.get("stages", []):
            data = stage.get("data", {})
            if stage["stage"] == "mapping":
                print(f"  PATTERN: {data['pattern']} | METRIC: {data['metric']} "
                      f"| DIM: {data.get('dimension')} | JOINS: {data.get('join_path')}")
            elif stage["stage"] == "sql":
                print(f"  SQL: {data['sql']}")
            elif stage["stage"] == "visualization":
                print(f"  VIS: {data['chart_type']} — \"{data['title']}\"")

    print(f"\n{'=' * 60}")
    if failures:
        print(f"FAILED: {len(failures)} of {len(QUERIES)} queries")
        for query, reason in failures:
            print(f"  - {query}: {reason}")
        return 1

    print(f"PASSED: all {len(QUERIES)} queries returned a valid outcome")
    return 0


if __name__ == "__main__":
    if not llm_is_configured():
        print(
            "SKIPPED: no LLM endpoint configured "
            "(set LLM_BASE_URL/LLM_API_KEY, or GROQ_API_KEY).\n"
            "Intent extraction is the only stage that cannot run offline, so "
            "there is nothing to integrate against. The offline suites — "
            "grounding, coverage, time grammar, visualization, compiler — "
            "cover everything downstream of the model."
        )
        sys.exit(0)

    sys.exit(run_queries())
