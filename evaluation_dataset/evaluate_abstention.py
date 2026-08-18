"""
Five-metric evaluation for a benchmark run.

Why a separate harness
----------------------
``evaluate_metrics.py`` answers "did the SQL compile?" and ``verify_execution.py``
answers "did the SQL run?".  Neither can answer "did the system do the right
thing?", because on roughly half of this dataset the right thing is to decline.

A single aggregate accuracy figure over a mixed set is meaningless in both
directions: it punishes a correct refusal as a failure, and it rewards a
confident wrong answer as a success. This script therefore reports the request
strata separately and never collapses them into one headline number.

The metrics
-----------
Named after Liu et al. (2026), who canonicalise the first two for NLIDBs, plus
three that the refusal channel requires and that no paper in the reference
corpus measures:

``translatability``
    Produced *something* executable, over all requests. The classic NLIDB
    metric. High translatability with low precision is the signature of a
    system that always answers.

``translation_precision``
    Produced the *expected* result. Computed only where a ground-truth label
    exists.

``abstention_recall``
    Of the requests that should have been declined, how many were. This is
    the number the architecture exists to move. Reported alone it is trivially
    gamed by refusing everything, which is why the next metric is mandatory
    beside it.

``false_abstention_rate``
    Of the requests that should have been answered, how many were declined.
    The cost side of abstention. Four separate bugs during development were
    supported requests being wrongly refused, so this is not hypothetical.

``silent_error_rate``
    Answered confidently, and wrongly, with no error and no clarification.
    NaLIR (Li et al., 2014) found users detected only 7 of 32 such answers
    unaided, which makes this the metric that matters most for a Approved
    reporting system and the one an aggregate accuracy figure hides.

Usage
-----
    python evaluation_dataset/evaluate_abstention.py
    python evaluation_dataset/evaluate_abstention.py --results path.json --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RESULTS = os.path.join(HERE, "benchmark_results.json")
DEFAULT_LABELS = os.path.join(HERE, "semantic_correctness_annotations.json")

#: Labels in the annotation file that mean "the system should not have answered".
NON_ANSWER_BEHAVIOURS = {"clarify_or_reject", "reject_write_request"}

#: Outcomes that count as the system declining to answer.
DECLINED_OUTCOMES = {"clarify", "reject"}


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def pct(numerator: int, denominator: int) -> Optional[float]:
    """Percentage, or ``None`` when the stratum is empty.

    Returning ``None`` rather than 0.0 matters: "no such cases existed" and
    "every case failed" are different findings, and printing 0.0% for the
    former would be a fabricated result.
    """
    if denominator == 0:
        return None
    return round(100.0 * numerator / denominator, 1)


def show(label: str, value: Optional[float], detail: str = "") -> str:
    rendered = "n/a" if value is None else f"{value:5.1f}%"
    return f"  {label:<26} {rendered}  {detail}"


class Evaluation:
    """Scores one benchmark run against the annotated expectations."""

    def __init__(self, results: List[dict], labels: Optional[List[dict]] = None):
        self.results = results
        self.labels = {row["id"]: row for row in (labels or [])}

    # -- classification helpers -------------------------------------------

    #: Every outcome this harness knows how to score.
    KNOWN_OUTCOMES = {"answer", "clarify", "reject", "error", "unknown"}

    def outcome(self, row: dict) -> str:
        """The terminal decision for a row, tolerating older result files.

        Runs recorded before the outcome field existed only have
        ``aegis_status``, where a correct refusal and a crash are both
        "failed". Those rows cannot distinguish abstention from breakage, and
        are reported as ``unknown`` rather than guessed at.

        Enum-repr forms such as ``"Outcome.ANSWER"`` are normalised: a results
        file was once written with ``str(enum)`` instead of ``enum.value``, and
        every outcome silently failed to match. Salvaging those files avoids
        re-spending an LLM budget to recover data that is already correct in
        substance.
        """
        recorded = (row.get("aegis_outcome") or "").strip().lower()
        if recorded:
            # "outcome.answer" -> "answer"
            return recorded.rsplit(".", 1)[-1] if "." in recorded else recorded
        status = (row.get("aegis_status") or "").strip().lower()
        if status == "success":
            return "answer"
        return "unknown"

    def validate(self) -> List[str]:
        """Reject a results file this harness cannot honestly score.

        Silence is the failure mode being guarded against here. An outcome
        vocabulary the harness does not recognise yields empty ``answered`` and
        ``declined`` sets, and every derived metric then reads 0.0% — which is
        indistinguishable on the page from a real measurement of zero. The
        harness must say "I could not read this" rather than print zeros.
        """
        problems: List[str] = []

        unrecognised = Counter(
            self.outcome(r) for r in self.results
            if self.outcome(r) not in self.KNOWN_OUTCOMES
        )
        if unrecognised:
            problems.append(
                f"unrecognised outcome values: {dict(unrecognised)} — "
                f"expected one of {sorted(self.KNOWN_OUTCOMES)}"
            )

        scored = sum(
            1 for r in self.results
            if self.outcome(r) in ("answer", "clarify", "reject")
        )
        if self.results and scored == 0:
            problems.append(
                "no row carries a scoreable outcome; the metrics below would "
                "all be 0.0% for want of data rather than for want of success"
            )

        if not self.labels:
            problems.append(
                "no expected-behaviour labels loaded; abstention recall, "
                "false-abstention rate and precision cannot be computed"
            )

        return problems

    def should_decline(self, row_id: int) -> Optional[bool]:
        label = self.labels.get(row_id)
        if label is None:
            return None
        return label.get("expected_behavior") in NON_ANSWER_BEHAVIOURS

    def is_correct(self, row_id: int) -> Optional[bool]:
        label = self.labels.get(row_id)
        if label is None:
            return None
        return bool(label.get("aegis_correct"))

    # -- metrics -----------------------------------------------------------

    def compute(self) -> Dict[str, Any]:
        total = len(self.results)
        outcomes = Counter(self.outcome(r) for r in self.results)

        answered = [r for r in self.results if self.outcome(r) == "answer"]
        declined = [r for r in self.results if self.outcome(r) in DECLINED_OUTCOMES]
        errored = [r for r in self.results if self.outcome(r) in ("error", "unknown")]

        # Translatability: produced an executable artefact.
        executable = [r for r in answered if (r.get("aegis_sql") or "").strip()]

        # Strata from the annotations.
        should_decline = [
            r for r in self.results if self.should_decline(r["id"]) is True
        ]
        should_answer = [
            r for r in self.results if self.should_decline(r["id"]) is False
        ]
        unlabelled = total - len(should_decline) - len(should_answer)

        declined_correctly = [
            r for r in should_decline if self.outcome(r) in DECLINED_OUTCOMES
        ]
        wrongly_declined = [
            r for r in should_answer if self.outcome(r) in DECLINED_OUTCOMES
        ]

        # Translation precision, over rows that carry a correctness label.
        labelled = [r for r in self.results if self.is_correct(r["id"]) is not None]
        correct = [r for r in labelled if self.is_correct(r["id"])]

        # Silent errors: answered, no error surfaced, and known to be wrong.
        silent_errors = [
            r for r in answered
            if self.is_correct(r["id"]) is False and not (r.get("error") or "")
        ]

        return {
            "total_requests": total,
            "outcome_counts": dict(outcomes),
            "strata": {
                "should_answer": len(should_answer),
                "should_decline": len(should_decline),
                "unlabelled": unlabelled,
            },
            "metrics": {
                "translatability": {
                    "value": pct(len(executable), total),
                    "n": len(executable), "of": total,
                    "definition": "produced executable SQL, over all requests",
                },
                "translation_precision": {
                    "value": pct(len(correct), len(labelled)),
                    "n": len(correct), "of": len(labelled),
                    "definition": "produced the expected result, over labelled requests",
                },
                "abstention_recall": {
                    "value": pct(len(declined_correctly), len(should_decline)),
                    "n": len(declined_correctly), "of": len(should_decline),
                    "definition": "correctly declined, over requests that should be declined",
                },
                "false_abstention_rate": {
                    "value": pct(len(wrongly_declined), len(should_answer)),
                    "n": len(wrongly_declined), "of": len(should_answer),
                    "definition": "wrongly declined, over requests that should be answered",
                },
                "silent_error_rate": {
                    "value": pct(len(silent_errors), total),
                    "n": len(silent_errors), "of": total,
                    "definition": "answered confidently and wrongly, with no error raised",
                },
            },
            "hard_failures": len(errored),
            "wrongly_declined_ids": [r["id"] for r in wrongly_declined],
            "missed_abstention_ids": [
                r["id"] for r in should_decline
                if self.outcome(r) not in DECLINED_OUTCOMES
            ],
            "silent_error_ids": [r["id"] for r in silent_errors],
        }


def render(report: Dict[str, Any]) -> str:
    lines = ["", "=" * 68, "AEGIS ABSTENTION-AWARE EVALUATION", "=" * 68]
    lines.append(f"Requests: {report['total_requests']}")

    strata = report["strata"]
    lines.append(
        f"Strata:   {strata['should_answer']} answerable | "
        f"{strata['should_decline']} should decline | "
        f"{strata['unlabelled']} unlabelled"
    )
    counts = ", ".join(f"{k}={v}" for k, v in sorted(report["outcome_counts"].items()))
    lines.append(f"Outcomes: {counts}")
    lines.append("")

    m = report["metrics"]
    for key in ("translatability", "translation_precision", "abstention_recall",
                "false_abstention_rate", "silent_error_rate"):
        entry = m[key]
        lines.append(show(key, entry["value"], f"({entry['n']}/{entry['of']})"))

    lines.append("")
    lines.append(f"  hard failures (crash/unknown)   {report['hard_failures']}")

    if report["wrongly_declined_ids"]:
        lines.append("")
        lines.append(f"  wrongly declined: {report['wrongly_declined_ids'][:20]}")
    if report["missed_abstention_ids"]:
        lines.append(f"  should have declined but answered: "
                     f"{report['missed_abstention_ids'][:20]}")
    if report["silent_error_ids"]:
        lines.append(f"  silent errors: {report['silent_error_ids'][:20]}")

    lines.append("")
    lines.append("Abstention recall must always be read beside false-abstention")
    lines.append("rate: refusing every request scores 100% on the first alone.")
    lines.append("=" * 68)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default=DEFAULT_RESULTS,
                        help="benchmark results JSON")
    parser.add_argument("--labels", default=DEFAULT_LABELS,
                        help="annotation file supplying expected behaviour")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="also write the report as JSON to this path")
    args = parser.parse_args()

    if not os.path.exists(args.results):
        print(f"Results file not found: {args.results}", file=sys.stderr)
        return 1

    results = load_json(args.results)
    labels = load_json(args.labels) if os.path.exists(args.labels) else []
    if not labels:
        print(
            "WARNING: no annotation file found. Translation precision, "
            "abstention recall and silent-error rate all require expected "
            "labels and will report n/a.",
            file=sys.stderr,
        )

    evaluation = Evaluation(results, labels)

    problems = evaluation.validate()
    if problems:
        print("REFUSING TO SCORE THIS RUN", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nPrinting metrics anyway would report 0.0% for every stratum, "
            "which reads identically to a genuine result.",
            file=sys.stderr,
        )
        return 2

    report = evaluation.compute()
    print(render(report))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        print(f"\nWrote {args.json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
