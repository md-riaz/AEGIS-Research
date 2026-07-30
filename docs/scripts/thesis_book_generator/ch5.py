# -*- coding: utf-8 -*-
"""Chapter 5: Results and Discussion."""
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_table_with_caption, add_code_block, add_figure_placeholder, page_break)


def chapter5(doc):
    add_chapter_heading(doc, 5, "Results and Discussion")
    add_para(doc,
              "This chapter reports results for each of the five research questions introduced in "
              "Section 4.5, followed by a discussion of what the results mean, what AEGIS deliberately "
              "trades away, and how it compares structurally to direct LLM-to-SQL generation.",
              space_after=0)

    # ---------------------------------------------------------------- 5.1
    add_section_heading(doc, "5.1", "Intent Parsing Accuracy (RQ1)")
    add_table_with_caption(
        doc, "Table 5: Intent parsing precision, recall, and F1 by intent class.",
        ["Intent class", "Precision", "Recall", "F1"],
        [
            ["KPI", "1.00", "1.00", "1.00"], ["Ranking", "1.00", "1.00", "1.00"],
            ["Trend", "1.00", "1.00", "1.00"], ["Comparison", "1.00", "1.00", "1.00"],
            ["Exception", "1.00", "1.00", "1.00"], ["Summary", "1.00", "1.00", "1.00"],
            ["Segment", "1.00", "1.00", "1.00"], ["Funnel", "1.00", "1.00", "1.00"],
            ["Cohort", "1.00", "1.00", "1.00"], ["Correlate", "1.00", "1.00", "1.00"],
            ["Tabular", "1.00", "1.00", "1.00"], ["Overall", "1.00", "1.00", "1.00"],
        ])
    add_para(doc,
              "Every intent class reached perfect precision, recall, and F1 on the 100-query benchmark. "
              "This result should be read as a demonstration that vocabulary injection resolves intent "
              "classification within the benchmark's covered vocabulary and phrasing variation, not as "
              "a claim that AEGIS never misclassifies a request in general; Section 5.6 reports the "
              "failure modes observed on the larger, more varied 312-request formative-study set, where "
              "coverage-boundary rejections and clarification requests do occur.", space_after=0)

    # ---------------------------------------------------------------- 5.2
    add_section_heading(doc, "5.2", "SQL Safety and Execution Validity (RQ2)")
    add_table_with_caption(
        doc, "Table 6: SQL safety and execution validity vs. direct LLM-to-SQL baseline.",
        ["System", "Unsafe SQL rate", "Execution validity", "Coverage"],
        [
            ["Baseline B1 (Direct LLM-to-SQL)", "5.0%", "99%", "99%"],
            ["AEGIS (with vocabulary injection)", "0%", "100%", "100%"],
        ])
    add_para(doc,
              "The direct LLM-to-SQL baseline produced 5 unsafe queries out of 100 (a 5.0% unsafe "
              "rate), including INSERT, UPDATE, and DELETE statements and UNION clauses generated in "
              "response to the twenty adversarial prompts in the benchmark. AEGIS eliminated unsafe "
              "queries entirely, not by detecting and blocking them after generation, but by never "
              "allowing the LLM to generate executable SQL in the first place.", space_after=0)
    add_figure_placeholder(doc, 8,
        "Evaluation results across unsafe-SQL rate, execution validity, and coverage",
        "A grouped bar chart with three metric groups on the x-axis (Unsafe SQL Rate, Execution "
        "Validity, Coverage), two bars per group comparing 'Baseline (Direct LLM-to-SQL)' in red/"
        "orange against 'AEGIS' in green. Baseline: 5.0% unsafe, 99% validity, 99% coverage. AEGIS: "
        "0% unsafe, 100% validity, 100% coverage. The AEGIS unsafe-rate bar should read visually as "
        "flat/near-zero next to the baseline's visible red bar, to make the safety contrast the "
        "immediate takeaway of the figure.")

    # ---------------------------------------------------------------- 5.3
    add_section_heading(doc, "5.3", "Expressiveness and Ablation Study (RQ3)")
    add_para(doc,
              "Of the 312 requests analyzed in the formative study (Section 3.2): 81.7% were answered "
              "directly without clarification, 11.5% required one clarification turn, 4.2% were "
              "answered only after the semantic layer was extended with a missing metric or dimension, "
              "and 2.6% could not be answered because they fell outside the template library entirely.",
              space_after=10)
    add_table_with_caption(
        doc, "Table 7: Ablation study - execution validity and coverage per configuration.",
        ["Configuration", "Execution validity", "Coverage"],
        [
            ["Full AEGIS (vocabulary injection)", "100%", "100%"],
            ["- Vocabulary injection (synonym dictionary instead)", "64.7%", "99%"],
            ["- Semantic layer", "88.7%", "91%"],
            ["- AST validation", "100%*", "100%"],
            ["- Confidence-gated clarification", "94.2%", "96%"],
            ["- Permission rewriter", "100%**", "100%"],
            ["- Repair call on parse failure", "92.9%", "95%"],
        ])
    add_para(doc,
              "Removing vocabulary injection in favor of a hand-maintained synonym dictionary produces "
              "the largest single drop, 35.3 percentage points of execution validity, confirming that "
              "vocabulary injection is not a convenience but the component doing the most work in "
              "keeping intent extraction reliable. Removing AST validation or the permission rewriter "
              "leaves the reported metrics unchanged on this benchmark (marked with an asterisk), which "
              "is expected and correctly interpreted as confirming their role as defense-in-depth layers "
              "against attack classes (T3, T4 in Section 3.5) that this particular benchmark's queries "
              "do not exercise, not as evidence that those layers are unnecessary.", space_after=0)
    add_figure_placeholder(doc, 9, "Ablation study results",
        "A horizontal bar chart listing each configuration from Table 7 on the y-axis (Full AEGIS, "
        "minus vocabulary injection, minus semantic layer, minus AST validation, minus "
        "confidence-gated clarification, minus permission rewriter, minus repair-on-parse-failure) "
        "with execution-validity percentage bars: 100%, 64.7%, 88.7%, 100%, 94.2%, 100%, 92.9%. "
        "Highlight the 'minus vocabulary injection' bar in a distinct color (e.g. red), since it shows "
        "the largest drop, to visually confirm it is the single most load-bearing component.")

    # ---------------------------------------------------------------- 5.4
    add_section_heading(doc, "5.4", "Cross-Schema Generalizability (RQ4)")
    add_para(doc,
              "A second semantic layer was built for WooCommerce, a structurally distinct e-commerce "
              "platform with different table naming conventions and business vocabulary (12 metrics, "
              "28 dimensions, 9 join paths, 18 tables), together with a 50-query evaluation set built "
              "using the same methodology as Section 4.3.", space_after=10)
    add_table_with_caption(
        doc, "Table 8: Cross-schema generalizability results.",
        ["Schema", "Build time", "Intent accuracy", "Unsafe SQL rate", "Coverage"],
        [
            ["nopCommerce (primary, 100 queries)", "40 person-hours", "100%", "0%", "100%"],
            ["WooCommerce (transfer, 50 queries)", "14 person-hours", "98.0%", "0%", "96.0%"],
        ])
    add_para(doc,
              "The WooCommerce evaluation achieved 98.0% intent accuracy with zero unsafe SQL using a "
              "semantic layer built in 14 person-hours, 65% less effort than the primary schema "
              "required. The 2% accuracy gap arose from two WooCommerce-specific metric names, resolved "
              "by adding two description entries to the prompt with no code changes required. These "
              "results support the claim that AEGIS's architecture, not just its nopCommerce "
              "configuration, is what generalizes: the LLM, the compiler, and the safety scanner "
              "required zero modification between schemas; only the semantic layer configuration "
              "changed.", space_after=0)

    # ---------------------------------------------------------------- 5.5
    add_section_heading(doc, "5.5", "Pipeline Latency (RQ5)")
    add_table_with_caption(
        doc, "Table 9: Pipeline stage latency.",
        ["Stage", "Median (ms)", "p95 (ms)", "% of total"],
        [
            ["LLM API call (Groq)", "1,850", "2,800", "96.2%"],
            ["Semantic mapping", "12", "18", "0.6%"],
            ["SQL compilation", "8", "12", "0.4%"],
            ["Query execution (MySQL)", "45", "120", "2.3%"],
            ["Visualization selector", "2", "4", "0.1%"],
            ["Widget persistence", "5", "9", "0.3%"],
            ["Total", "1,922", "2,963", "100%"],
        ])
    add_para(doc,
              "AEGIS's safety infrastructure, the deterministic stages that carry out coverage "
              "validation, semantic mapping, permission rewriting, compilation, visualization selection, "
              "and widget persistence combined, adds a median of roughly 20 ms of overhead, negligible "
              "relative to the 1,850 ms median LLM API call. With a locally hosted Ollama model, median "
              "LLM call latency drops to approximately 340 ms, bringing total end-to-end latency below "
              "430 ms. The safety guarantees established in Chapter 3 are, in this sense, effectively "
              "free: the cost of AEGIS's architecture is dominated by the same LLM call a direct "
              "LLM-to-SQL system would also have to make.", space_after=0)
    add_figure_placeholder(doc, 10, "Pipeline stage latency breakdown",
        "A horizontal stacked bar (or waterfall) chart of the six pipeline stages from Table 9 and "
        "their median latency: LLM API call (Groq) 1,850 ms, semantic mapping 12 ms, SQL compilation "
        "8 ms, query execution (MySQL) 45 ms, visualization selector 2 ms, widget persistence 5 ms, "
        "totaling 1,922 ms. Since the LLM call dominates at 96.2% of the total, include an inset panel "
        "zooming into just the five non-LLM stages (the remaining ~72 ms) so their relative "
        "proportions are visible rather than compressed to invisibility next to the LLM bar.")

    # ---------------------------------------------------------------- 5.6
    add_section_heading(doc, "5.6", "Failure Analysis")
    add_para(doc,
              "Among the 2.6% of the 312 formative-study requests that could not be answered at all, "
              "coverage-boundary rejections broke down as follows: metrics not present in the semantic "
              "layer (35% of rejections), unregistered dimensions (28%), requests requiring multi-metric "
              "aggregation beyond a single pattern (18%), causal or explanatory questions such as "
              "“why did revenue drop” (12%), and requests requiring a join path not present in "
              "the join graph (7%). Every rejection, in this study and in the benchmark, included the "
              "full list of available identifiers rather than a bare error, consistent with the design "
              "principle (Section 3.3) that a coverage failure should be actionable rather than opaque.",
              space_after=0)
    add_figure_placeholder(doc, 11,
        "Query outcome distribution and coverage-boundary rejection reasons",
        "Two side-by-side panels. LEFT panel: a donut/pie chart of query outcomes across the 312 "
        "formative-study requests — Answered directly 81.7%, Answered after one clarification 11.5%, "
        "Answered after semantic layer extension 4.2%, Could not be answered 2.6%. RIGHT panel: a "
        "second pie/bar chart breaking down only that 2.6% rejected slice into its underlying reasons: "
        "metrics not in semantic layer 35%, unregistered dimensions 28%, multi-metric aggregation 18%, "
        "causal/explanatory questions 12%, missing join paths 7%.")

    # ---------------------------------------------------------------- 5.7
    add_section_heading(doc, "5.7", "Discussion")

    add_mixed_para(doc, [("5.7.1 AEGIS vs. direct LLM-to-SQL: structural comparison. ", True, False)],
                   space_before=10, space_after=6)
    add_para(doc,
              "A natural question is why not simply ask a capable LLM to write SQL directly. The "
              "differences below are architectural, not accuracy-based: they would hold even against a "
              "future, more capable model.", space_after=8)
    add_table_with_caption(
        doc, "Table 10: Structural comparison of AEGIS vs. direct LLM-to-SQL.",
        ["Property", "Direct LLM-to-SQL", "AEGIS"],
        [
            ["SQL generation", "Model-generated (probabilistic)", "Deterministic compiler"],
            ["Schema exposure to LLM", "Required (tables, columns, keys)", "Not required (labels only)"],
            ["Business metric definitions", "Implied from schema names", "Explicit in semantic layer"],
            ["SQL injection prevention", "Prompt-level (best-effort)", "Structural (by design)"],
            ["Permission enforcement", "External or none", "Built-in, post-LLM"],
            ["Dashboard widget persistence", "Not provided", "First-class artifact"],
            ["Auditability of query origin", "Difficult", "Full provenance per widget"],
            ["Model dependency", "Tied to specific model quality", "Model-independent"],
        ])
    add_para(doc,
              "AEGIS does not claim to produce more creative SQL than a frontier LLM. It claims that, "
              "for the analytics requests it supports, results are guaranteed correct by construction, "
              "auditable, and safe, properties that probabilistic generation cannot offer "
              "unconditionally, no matter how capable the underlying model becomes.", space_after=10)

    add_mixed_para(doc, [("5.7.2 Why a semantic layer instead of retrieval-augmented generation? ",
                           True, False)], space_after=6)
    add_para(doc,
              "Retrieval-augmented generation (RAG) for NL-to-SQL retrieves relevant schema fragments "
              "to give the LLM better context. This is a useful technique, but it solves a different "
              "problem from the semantic layer and does not eliminate the safety risk. RAG asks which "
              "schema information the LLM should see; it is an access-optimization technique that "
              "narrows the schema the model reasons over, but the LLM still generates a free-form SQL "
              "string as output. The semantic layer asks which analytical concepts are allowed to exist, "
              "what they mean, and who may access them; it is a governance mechanism that defines the "
              "complete set of answerable questions and their canonical SQL translations before any "
              "query is processed, and the LLM outputs a typed intent object rather than SQL. An "
              "organization that wants both better schema context and controlled output could use RAG "
              "to select relevant semantic layer sections for very large vocabularies, thousands of "
              "metrics, while still routing every query through the AEGIS compiler; the two techniques "
              "are complementary rather than competing.", space_after=10)

    add_mixed_para(doc, [("5.7.3 Scope and coverage boundary. ", True, False)], space_after=6)
    add_para(doc,
              "AEGIS only supports queries that fit within its defined metrics, dimensions, and "
              "patterns, an approximately 5,610-combination space (15 metrics times 34 dimensions "
              "times 11 patterns, in the nopCommerce configuration). Out-of-scope queries receive a "
              "structured rejection listing available identifiers rather than a silent wrong answer:",
              space_after=8)
    add_code_block(doc, """Unknown metric 'conversion_rate'.
Available: avg_order_value, customer_count, discount_amount,
           order_count, profit, refund_amount, revenue, ...""")
    add_para(doc,
              "Extending coverage requires only adding rows to the semantic layer, with no model "
              "retraining and no synonym curation required, since vocabulary injection (Section 3.8) "
              "propagates a new entry to the LLM's available vocabulary automatically. For open-ended "
              "data exploration requiring custom joins or schema-level operations outside this space, an "
              "unconstrained system may be more appropriate; AEGIS is designed for the everyday "
              "reporting needs identified in the formative study (Section 3.2), not ad hoc data science "
              "exploration.", space_after=0)
    page_break(doc)
