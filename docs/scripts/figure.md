# AEGIS Thesis Figure Replacement Notes

This file stores the image/diagram design notes that were intentionally removed from visible thesis figure placeholders. Keep the placeholder boxes and captions in the thesis book until real figures are inserted.

## Figure 1: AEGIS Architecture Pipeline

Page in current draft: 18

Create a left-to-right flowchart of the seven stages in sequence: User Request, LLM Intent Parser, Coverage Validator, Semantic Mapper, Permission Rewriter, Safe Query Compiler, Query Executor, Visualization Selector, Widget Engine, and Dashboard. Color-code by responsibility: blue for the single AI/LLM stage, purple for semantic mapping, red for the two safety-enforcement stages (Permission Rewriter, Safe Query Compiler), green for execution/output stages. Add small orange branch arrows from Coverage Validator and Safe Query Compiler pointing to a "Structured Clarification / Rejection Message" box, showing that invalid requests exit early with an actionable error rather than a silent failure.

## Figure 2: Semantic Layer Modularity

Page in current draft: 18

Create a split-panel comparison. Left panel, labeled "AEGIS": a small set of labeled building blocks (Metric, Dimension, Filter, Join Path, Pattern) shown snapping together into two or three example complete query shapes. Right panel, labeled "Direct LLM-to-SQL": an unbounded free-form SQL string with a warning icon. The visual point is that AEGIS composes from a bounded set of safe parts while direct generation is unbounded and can take an unsafe shape.

## Figure 3: Vocabulary Injection Workflow

Page in current draft: 20

Create a three-lane sequence diagram: "Semantic Layer (semantic_layer.py)", "System Prompt Builder", and "LLM". Show the Semantic Layer box listing a few example metric/dimension entries with plain-English descriptions; an arrow labeled "serializes into approximately 1,100 tokens" into the System Prompt Builder; then into the LLM, whose output arrow produces an example IntentObject such as `{metric_term: "revenue", dimension_term: "category"}`. Annotate with a small callout showing the user phrase "earnings" mapping to the approved ID "revenue" even though "earnings" appears in no synonym list.

## Figure 4: Taxonomy of the Eleven AEGIS Analytical Patterns

Page in current draft: 21

Create a tree or grid diagram with "Eleven Analytical Patterns" at the top branching into eleven labeled leaves: KPI, Ranking, Trend, Comparison, Exception, Summary, Segment, Funnel, Cohort, Correlate, Tabular. Under each leaf, show a small icon of its default visualization matching Table 2/Table 3: card, bar chart, line chart, grouped bar, table, card grid, pie chart, funnel chart, grouped bar, scatter plot, table. Caption note for later figure construction: approximately 5,610 valid combinations across 15 metrics, 34 dimensions, and 11 patterns.

## Figure 5: Pattern Classification of the Answerable Analytical Benchmark Subset

Page in current draft: 12

Create a bar chart, sorted descending, showing the real share of the answerable analytical benchmark subset accounted for by each of the eleven patterns: KPI/Aggregate 28%, Ranking 21%, Exception/Filter 18%, Trend Analysis 10%, Comparison 10%, Summary/Group 9%, Cohort 2%, Funnel 1%, Correlate 1%, Segment 0%, Tabular 0%. Highlight the top three bars (KPI, Ranking, Exception/Filter) in an accent color, since together they account for 67% of the benchmark. Caption note for later figure construction: classified by the author against `evaluation_dataset/questions.json`; see `evaluation_dataset/pattern_classification.json` for the per-question labels.

## Figure 6: Two-Layer SQL Safety Defence

Page in current draft: 22

Create a vertical two-stage flowchart. A crafted/adversarial input enters at the top with a warning icon. Layer 1 box: "Parameterized Query Engine - user text never enters the SQL string; only IDs and bound values appear." Arrow down to Layer 2 box: "Post-Compilation Safety Scanner - rejects non-SELECT statements, UNION/EXCEPT/INTERSECT, EXEC, and system-table references (16 forbidden patterns checked)." Below, split into two outcomes: a green "Safe SQL Executed" box for a legitimate query, and a red "SecurityError Raised" box for a rejected one, showing the attack is caught before it can reach the database regardless of which layer catches it.

## Figure 7: Widget Lifecycle and Refresh Model

Page in current draft: 23

Create a cyclical flowchart. Start with "New Natural-Language Question", then "Full Seven-Stage Pipeline Runs", then "Analysis Plan Hashed (SHA-256)", then a decision diamond "Identical widget hash already exists?". If yes, continue to "Return Cached Widget Immediately". If no, continue to "Save New Widget (SQL, chart config, access rule, refresh schedule)". Both paths converge into a "Dashboard Widget" box, from which a looping arrow labeled "Scheduled Refresh (re-executes stored SQL on fresh data)" curves back into the same box, illustrating that a widget keeps answering the same recurring question rather than being discarded after one use.

## Figure 8: Verified Safety and Execution-Validity Comparison

Page in current draft: 30

Create a grouped bar chart comparing B1, AEGIS, and B3 where available. Show unsafe SQL as counts and true execution validity as successful executions out of 107. Do not plot semantic correctness here; correctness is a separate annotated benchmark.
