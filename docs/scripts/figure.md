# AEGIS Thesis Figure Replacement Notes

This file stores the image/diagram design notes that were intentionally removed from visible thesis figure placeholders. Keep the placeholder boxes and captions in the thesis book until real figures are inserted.

## Figure 1: Design Science Research Workflow for AEGIS

Page in current draft: 10

Create a formal Design Science Research workflow diagram for AEGIS. Use five connected stages: Problem Identification, Artifact Design, Build and Evaluation Cycles, Final Evaluation, and Thesis Contribution. Under Build and Evaluation Cycles, show Cycle 1: semantic layer and compiler, Cycle 2: analytical patterns and vocabulary injection, and Cycle 3: widget persistence and benchmark harness. Keep the layout clean and thesis-neutral, with labeled boxes and arrows only.

## Figure 2: Pattern Classification of the Answerable Analytical Benchmark Subset

Page in current draft: 11

Create a thesis-style bar chart showing the distribution of the 107 mixed benchmark requests by pattern. Sort bars from highest to lowest and label each bar with both count and percentage: KPI/Aggregate 28 (26.2%), Ranking 21 (19.6%), Exception/Filter 18 (16.8%), Trend Analysis 10 (9.3%), Comparison 10 (9.3%), Summary/Group 9 (8.4%), Cohort 2 (1.9%), Funnel 1 (0.9%), Correlate 1 (0.9%), Segment 0 (0%), Tabular 0 (0%), and Additional mixed requests 7 (6.5%). Use a single restrained highlight for the top three patterns and include a small note: denominator = 107 mixed requests.

## Figure 3: AEGIS Architecture Pipeline

Page in current draft: 16

Create a formal system architecture flowchart for AEGIS. Show the processing path from User Request to Dashboard Widget through these labeled stages: LLM Intent Parser, Coverage Validator, Semantic Mapper, Permission Rewriter, Safe Query Compiler, Query Executor, Visualization Selector, and Widget Engine. Mark the LLM Intent Parser as the only AI-assisted stage. Mark Coverage Validator, Permission Rewriter, Safe Query Compiler, Query Executor, Visualization Selector, and Widget Engine as deterministic stages. Add rejection or clarification branches from Coverage Validator and Safe Query Compiler to a Structured Clarification or Rejection Message box. Do not rely only on color; use text labels for stage responsibility.

## Figure 4: Semantic Layer Modularity

Page in current draft: 16

Create a formal split-panel comparison between bounded semantic composition and unconstrained SQL generation. Left panel: AEGIS semantic layer, showing approved Metrics, Dimensions, Filters, Join Paths, and Patterns feeding into a Validated Intent Object and then a parameterized SQL template. Right panel: Direct LLM-to-SQL, showing Natural-Language Request feeding directly into free-form SQL generation. Emphasize architectural control boundaries, not decorative metaphors. Use neutral labels and simple arrows.

## Figure 5: Vocabulary Injection Workflow

Page in current draft: 18

Create a three-lane sequence diagram with lanes: Semantic Layer, Prompt Builder, and LLM Intent Parser. Show approved metric and dimension labels flowing from the Semantic Layer into the Prompt Builder. Show the Prompt Builder sending a constrained instruction context to the LLM Intent Parser. Show the LLM returning a typed IntentObject, not SQL. The IntentObject should include example fields such as metric_term, dimension_term, filters, time_range, and intent_type. Keep the example generic and avoid code-heavy detail.

## Figure 6: Taxonomy of the Eleven AEGIS Analytical Patterns

Page in current draft: 19

Create a clean taxonomy grid for the eleven AEGIS analytical patterns: KPI, Ranking, Trend, Comparison, Exception, Summary, Segment, Funnel, Cohort, Correlate, and Tabular. For each pattern, include its default output type in short text, such as card, bar chart, line chart, grouped bar chart, table, card grid, pie chart, funnel chart, or scatter plot. Icons may be used only if they remain simple and academic; the text labels must carry the meaning.

## Figure 7: Two-Layer SQL Safety Defence

Page in current draft: 20

Create a vertical safety-control flowchart showing two deterministic SQL safety layers. Layer 1: Parameterized Query Compiler, where approved semantic identifiers and bound values are inserted into fixed templates. Layer 2: Post-Compilation Safety Scanner, where non-SELECT statements, forbidden SQL operators, execution commands, and system-table references are rejected. End with two possible outcomes: Safe SELECT Query Executed or SecurityError Raised Before Database Execution. Keep the wording precise and avoid implying that semantic correctness is guaranteed by this figure.

## Figure 8: Widget Lifecycle and Refresh Model

Page in current draft: 21

Create a lifecycle or state diagram for AEGIS widget persistence. Show New Natural-Language Question leading to Full AEGIS Pipeline Execution, then Analysis Plan Hashing. Add a decision state: Existing Widget Hash Found? If yes, return the cached widget. If no, save a new widget containing SQL, chart configuration, access rule, and refresh schedule. Show Dashboard Widget as the persisted state, with Scheduled Refresh re-executing the stored safe query against fresh data. Keep the diagram focused on reuse and refresh behavior.

## Figure 9: Verified Safety and Execution-Validity Comparison

Page in current draft: 27

Create a grouped bar chart using completed benchmark measurements only. Compare B1 direct LLM-to-SQL, AEGIS, and B3 template-only where the metric was measured. Show unsafe SQL count and true execution-validity count out of 107. Do not include semantic correctness, latency, B2, or B4 because those measurements are not completed. Label the figure as measured safety and execution-validity results, not a full accuracy comparison.
