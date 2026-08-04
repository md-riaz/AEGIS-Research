# AEGIS Thesis Figure Replacement Notes

This file stores the image/diagram design notes that were intentionally removed from visible thesis figure placeholders. Keep the placeholder boxes and captions in the thesis book until real figures are inserted.

## Figure 1: Design Science Research Workflow for AEGIS

Page in current draft: 10

Create a compact workflow diagram showing Problem Relevance, Design Rigor, Build-Evaluate Cycles, and Final Evaluation. Under Build-Evaluate Cycles, show Cycle 1: semantic layer and compiler, Cycle 2: analytical patterns and vocabulary injection, and Cycle 3: widget persistence and benchmark harness.

## Figure 2: Pattern Classification of the Answerable Analytical Benchmark Subset

Page in current draft: 11

Create a bar chart, sorted descending, showing the share of the full 107-request benchmark accounted for by each pattern: KPI/Aggregate 26.2%, Ranking 19.6%, Exception/Filter 16.8%, Trend Analysis 9.3%, Comparison 9.3%, Summary/Group 8.4%, Cohort 1.9%, Funnel 0.9%, Correlate 0.9%, Segment 0%, Tabular 0%, and Additional mixed requests 6.5%. Highlight the top three analytical patterns in an accent color; together they account for 67 of 107 requests, about 62.6% of the mixed benchmark.

## Figure 3: AEGIS Architecture Pipeline

Page in current draft: 16

Create a left-to-right flowchart of the seven stages in sequence: User Request, LLM Intent Parser, Coverage Validator, Semantic Mapper, Permission Rewriter, Safe Query Compiler, Query Executor, Visualization Selector, Widget Engine, and Dashboard. Color-code by responsibility: blue for the single AI/LLM stage, purple for semantic mapping, red for the two safety-enforcement stages, and green for execution/output stages. Add branch arrows from Coverage Validator and Safe Query Compiler to a Structured Clarification / Rejection Message box.

## Figure 4: Semantic Layer Modularity

Page in current draft: 16

Create a split-panel comparison. Left panel, labeled AEGIS: a small set of labeled building blocks (Metric, Dimension, Filter, Join Path, Pattern) snapping together into complete query shapes. Right panel, labeled Direct LLM-to-SQL: an unbounded free-form SQL string with a warning icon. The visual point is that AEGIS composes from bounded safe parts while direct generation is unbounded.

## Figure 5: Vocabulary Injection Workflow

Page in current draft: 18

Create a three-lane sequence diagram: Semantic Layer, System Prompt Builder, and LLM. Show metric/dimension entries flowing into the prompt builder, then an example typed IntentObject produced by the LLM.

## Figure 6: Taxonomy of the Eleven AEGIS Analytical Patterns

Page in current draft: 19

Create a tree or grid diagram with eleven labeled leaves: KPI, Ranking, Trend, Comparison, Exception, Summary, Segment, Funnel, Cohort, Correlate, and Tabular. Under each leaf, show a small icon of its default visualization.

## Figure 7: Two-Layer SQL Safety Defence

Page in current draft: 20

Create a vertical two-stage flowchart. Layer 1 is Parameterized Query Engine. Layer 2 is Post-Compilation Safety Scanner. Below, split into Safe SQL Executed and SecurityError Raised outcomes.

## Figure 8: Widget Lifecycle and Refresh Model

Page in current draft: 21

Create a cyclical flowchart. Start with New Natural-Language Question, then Full Seven-Stage Pipeline Runs, Analysis Plan Hashed, an identical-hash decision, Return Cached Widget or Save New Widget, and a Dashboard Widget loop with Scheduled Refresh.

## Figure 9: Verified Safety and Execution-Validity Comparison

Page in current draft: 27

Create a grouped bar chart comparing B1, AEGIS, and B3 where available. Show unsafe SQL as counts and true execution validity as successful executions out of 107. Do not plot semantic correctness here; correctness is a separate annotated benchmark.
