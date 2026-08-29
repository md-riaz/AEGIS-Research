"""Per-stage timing for the evaluation runners.

Every runner that reports a latency figure computes it here, so the stages are
measured the same way and summarised the same way in each result artifact.

Two decisions worth stating, because both change what the numbers mean:

``perf_counter`` is used rather than wall-clock time, so the figures are not
affected by clock adjustments during a run that takes several minutes.

The summary reports the **median and p95 alongside the mean**. A mean alone
hides the shape of an LLM latency distribution, which is the one stage here
with a long tail: a handful of slow calls move the mean far more than they move
the median, and a reader given only the mean cannot tell a uniformly slow stage
from a fast one with occasional stalls.
"""

from __future__ import annotations

import statistics
from contextlib import contextmanager
from time import perf_counter
from typing import Any, Iterable, Iterator, List


@contextmanager
def stopwatch(sink: dict, key: str) -> Iterator[None]:
    """Record the elapsed milliseconds of the enclosed block into ``sink[key]``.

    The value is written in a ``finally`` block, so a stage that raises still
    records how long it ran before failing. A stage whose timing is missing from
    a result row therefore means the stage never started, not that it failed —
    the two are different, and a benchmark that cannot distinguish them will
    eventually report one as the other.
    """
    start = perf_counter()
    try:
        yield
    finally:
        sink[key] = round((perf_counter() - start) * 1000, 3)


def summarize(values: Iterable[Any]) -> dict[str, Any]:
    """Summarise a sample of millisecond timings.

    ``None`` entries are dropped rather than counted as zero: a stage that never
    ran is absent from the sample, not instantaneous.
    """
    sample: List[float] = [float(v) for v in values if v is not None]
    if not sample:
        return {"n": 0}
    ordered = sorted(sample)
    return {
        "n": len(ordered),
        "mean_ms": round(statistics.fmean(ordered), 2),
        "median_ms": round(statistics.median(ordered), 2),
        "p95_ms": round(ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))) ], 2),
        "max_ms": round(ordered[-1], 2),
    }


def stage_summary(rows: Iterable[dict], stages: Iterable[str]) -> dict[str, dict]:
    """Summarise each named stage across result rows."""
    rows = list(rows)
    return {stage: summarize(r.get(stage) for r in rows) for stage in stages}


def print_latency(title: str, summary: dict[str, dict]) -> None:
    print(f"\n{title}")
    print(f"{'stage':24} {'n':>5} {'mean':>10} {'median':>10} {'p95':>10} {'max':>10}")
    for stage, stats in summary.items():
        if not stats.get("n"):
            print(f"{stage:24} {0:>5}          -          -          -          -")
            continue
        print(f"{stage:24} {stats['n']:>5} {stats['mean_ms']:>9.2f}ms {stats['median_ms']:>9.2f}ms "
              f"{stats['p95_ms']:>9.2f}ms {stats['max_ms']:>9.2f}ms")
