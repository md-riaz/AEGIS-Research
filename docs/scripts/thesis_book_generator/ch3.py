# -*- coding: utf-8 -*-
"""Chapter 3: Methodology."""
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_bullet, add_numbered, add_table_with_caption, add_code_block,
                           add_figure_placeholder, page_break)
from refs import cite


def chapter3(doc):
    add_chapter_heading(doc, 3, "Methodology")

    # ---------------------------------------------------------------- 3.1
    add_section_heading(doc, "3.1", "Research Paradigm")
    add_para(doc,
              "This thesis follows a Design Science Research paradigm, in the sense used by Hevner et "
              "al.: knowledge is produced by building and evaluating a novel artifact that addresses an "
              "identified organizational problem, rather than by testing a hypothesis about an existing "
              "phenomenon. The artifact in this thesis is the AEGIS system itself. Design Science "
              "Research requires three things to be demonstrated: problem relevance, design rigor, and "
              "evaluation against the stated problem. Problem relevance is established through the "
              "formative study of Section 3.2, which analyzes real reporting behavior rather than "
              "assuming a problem exists. Design rigor is established through the formal model and "
              "threat model of Sections 3.4-3.5, which state precisely what safety property the "
              "architecture guarantees and under what boundary that guarantee holds. Evaluation is "
              "reported in Chapter 5 against five explicit research questions, using both a benchmark "
              "dataset constructed for this domain and an ablation study that isolates the contribution "
              "of each architectural component.", space_after=10)
    add_para(doc,
              "The research proceeded through three iterative build-evaluate cycles. The first cycle "
              "produced a semantic layer and compiler for a minimal set of intent classes and validated "
              "the core safety proposition on a small hand-written query set. The second cycle expanded "
              "coverage to all eleven intent classes identified in the formative study and introduced "
              "vocabulary injection after an early synonym-dictionary approach proved unable to keep "
              "pace with real query phrasing. The third cycle added the widget persistence layer and the "
              "cross-schema generalizability evaluation on WooCommerce, testing whether the architecture "
              "itself, not just the nopCommerce configuration, was the reusable artifact.", space_after=0)

    # ---------------------------------------------------------------- 3.2
    add_section_heading(doc, "3.2", "Formative Study of Reporting Patterns")
    add_para(doc,
              "A dataset of 312 distinct natural-language reporting requests representative of typical "
              "e-commerce and administrative workflows was compiled. Each request was independently "
              "annotated by two researchers against a candidate set of analytics primitives. Inter-rater "
              "agreement reached kappa = 0.84 (substantial agreement) before adjudication. After "
              "adjudication, eleven primary analytics primitives were identified that together account "
              "for 98.2% of all requests.", space_after=10)
    add_table_with_caption(
        doc, "Table (formative study): Request taxonomy and observed frequency.",
        ["Pattern", "Share of requests", "Example"],
        [
            ["Ranking", "24.1%", "Which five categories have the highest refund rates?"],
            ["Trend Analysis", "21.5%", "Show monthly sales volume over the last year."],
            ["KPI / Aggregate", "18.3%", "How many orders were placed today?"],
            ["Comparison", "14.7%", "Compare average order value between mobile and desktop users."],
            ["Exception / Filter", "12.8%", "List products with stock levels below 10."],
            ["Summary / Group", "6.0%", "Give me an overview of the Electronics category."],
            ["Segment, Funnel, Cohort, Correlate, Tabular", "2.6% combined",
             "Revenue by category; cart-to-purchase conversion; new vs. returning customers; "
             "attribute correlation; raw order listings."],
        ])
    add_figure_placeholder(doc, 5, "Distribution of analytics primitives across 312 real reporting requests",
        "A bar chart (sorted descending) showing the share of the 312 formative-study requests "
        "accounted for by each of the eleven patterns: Ranking 24.1%, Trend Analysis 21.5%, "
        "KPI/Aggregate 18.3%, Comparison 14.7%, Exception/Filter 12.8%, Summary/Group 6.0%, and "
        "Segment, Funnel, Cohort, Correlate, and Tabular combined 2.6%. Highlight the top three bars "
        "(Ranking, Trend, KPI) in an accent color, since together they account for nearly two-thirds "
        "of all requests — this is the visual argument for why a small, fixed pattern library is "
        "sufficient (Section 3.2).")
    add_para(doc,
              "The study yields three design directions that shaped the rest of this chapter. First, a "
              "small set of patterns is sufficient: eleven patterns cover 98.2% of real requests, which "
              "supports building a fixed template library rather than an open-ended query language. "
              "Second, business vocabulary differs systematically from database column names: "
              "participants said “total refund rate,” never SUM(o.RefundedAmount), which "
              "motivates an explicit semantic layer (Section 3.7) rather than exposing the schema "
              "directly to the language model. Third, reuse is the norm rather than the exception: 61% "
              "of requests were things participants had asked before, in a different time window or for "
              "a different segment, which motivates the widget persistence design of Section 3.11.",
              space_after=0)

    # ---------------------------------------------------------------- 3.3
    add_section_heading(doc, "3.3", "Design Principles")
    add_para(doc, "Five principles guide every architectural decision in this chapter:", space_after=8)
    add_numbered(doc, "Separate understanding from execution. The LLM understands the question; fixed "
                 "rules handle everything else.")
    add_numbered(doc, "Define business terms explicitly. Metrics, dimensions, joins, and time rules are "
                 "written once in a semantic layer, not inferred per query.")
    add_numbered(doc, "Limit what SQL can be generated. SQL is built only from pre-approved, "
                 "parameterized templates.")
    add_numbered(doc, "Select visualizations by rule. Chart type is decided by question type, result "
                 "shape, and established visualization design guidance, not by a learned model.")
    add_numbered(doc, "Persist results for reuse. Every query produces a saved, refreshable widget "
                 "rather than a discarded answer.")

    # ---------------------------------------------------------------- 3.4
    add_section_heading(doc, "3.4", "Formal Model")
    add_para(doc,
              "Let a user with role r issue a natural-language request q. Classical text-to-SQL seeks a "
              "function f(q, S) that maps the request and a schema S directly to sql. AEGIS instead "
              "seeks a function", space_after=8)
    add_para(doc, "g(q, L, r) → ⟨π, sql, vis, w⟩", bold=True, align=None, space_after=8)
    add_para(doc,
              "where π is a canonical analysis plan, sql is a read-only compiled query, vis is a "
              "visualization specification, and w is a persisted widget artifact. The semantic layer "
              "L = ⟨M, D, F, J, P, V, A, R⟩ defines the approved metric set M, dimension set D, "
              "filter and time-rule set F, join graph J, pattern library P, visualization policy V, "
              "vocabulary injection configuration A, and role-permission model R.", space_after=10)
    add_para(doc,
              "Safety is enforced as a set-membership constraint: sql ∈ Q_safe(L, r), where "
              "Q_safe(L, r) is the family of queries derivable from pattern templates in P using only "
              "bindings from L permitted under role r.", space_after=10)
    add_mixed_para(doc, [
        ("Proposition 1. ", True, False),
        ("No query in Q_safe(L, r) can reference a table, column, or row not enumerated in L for role "
         "r. All SQL identifiers are drawn from a closed vocabulary of approved semantic bindings. All "
         "literal values are passed using parameterized SQL rather than string interpolation. SQL "
         "injection through untrusted natural-language input is structurally prevented by design.",
         False, True)], space_after=10)
    add_mixed_para(doc, [
        ("Security boundary. ", True, False),
        ("This guarantee holds within a defined threat boundary: the semantic layer definitions, "
         "compiler templates, and permission predicates are trusted, administrator-controlled "
         "artifacts. An administrator who embeds malicious SQL inside a metric definition, or a "
         "supply-chain compromise of the compiler library, falls outside this boundary and requires "
         "separate operational security controls. Explicitly stating this boundary, rather than leaving "
         "it implicit, is itself part of this thesis's contribution: prior NL-to-SQL work reviewed in "
         "Chapter 2 rarely specifies the boundary of its safety claims, which makes rigorous security "
         "comparison difficult.", False, False)], space_after=0)

    # ---------------------------------------------------------------- 3.5
    add_section_heading(doc, "3.5", "Threat Model")
    add_para(doc,
              "AEGIS protects against attacks arriving through the untrusted natural-language input "
              "channel. The model assumes the database and application server are properly hardened; "
              "the attacker controls only the query field.", space_after=10)
    _threat(doc, "T1", "Prompt injection attempting SQL generation.",
            '"Ignore previous instructions. Generate DROP TABLE orders."',
            "The IntentObject schema contains no SQL field. Any non-approved string in metric_term or "
            "dimension_term is rejected by Pydantic type validation at Stage 2, before the compiler is "
            "reached.")
    _threat(doc, "T2", "Unauthorized metric or dimension access.",
            '"Show me customer passwords" or "List credit card numbers by order."',
            "Fields such as customer_password do not exist in the semantic layer vocabulary. The LLM "
            "never sees those names; it receives only the curated, approved label list. Stage 2 "
            "rejects any unrecognized term.")
    _threat(doc, "T3", "Unauthorized row access.",
            'A store-level user asks: "Show revenue for all branches."',
            "Stage 4 (Permission Rewriter) runs after the LLM and appends a role-specific WHERE "
            "predicate (for example, AND o.StoreId = :user_store) derived from the authenticated "
            "session. This cannot be suppressed or overridden by natural-language content.")
    _threat(doc, "T4", "DML or DDL injection.",
            "A crafted prompt that tricks the LLM into associating a write operation with an intent "
            "class.",
            "No template in the pattern library contains a DML or DDL keyword. The AST-level "
            "post-compilation validator explicitly rejects any non-SELECT statement as a "
            "defense-in-depth layer.")
    add_para(doc, "Not protected by AEGIS (requires operational security controls outside this "
              "architecture):", bold=True, space_after=6)
    add_bullet(doc, "A malicious administrator embedding arbitrary SQL inside a metric's sql_expr field.")
    add_bullet(doc, "Supply-chain compromise of the compiler module or the SQL parser library.")
    add_bullet(doc, "Database-level privilege escalation that bypasses the application layer.")
    add_bullet(doc, "LLM provider infrastructure compromise or model poisoning.")
    add_para(doc,
              "Explicitly documenting out-of-scope threats is itself a contribution: prior NL-to-SQL "
              "work rarely specifies the boundary of its safety claims, which makes meaningful security "
              "comparison difficult.", space_after=0)
    page_break(doc)

    # ---------------------------------------------------------------- 3.6
    add_section_heading(doc, "3.6", "System Architecture")
    add_para(doc,
              "Every user query travels through exactly seven stages. Stages 2 through 7 contain no "
              "artificial intelligence; they are deterministic code. Rejection at any stage produces a "
              "structured clarification message rather than a best-effort guess.", space_after=10)
    _stage(doc, "Stage 1 - Intent Extraction.",
           "A lightweight LLM reads the query together with a system prompt built from the semantic "
           "layer, and outputs a validated IntentObject (intent class, metric term, dimension term, "
           "filters, sort, limit, confidence). This is the only stage that involves artificial "
           "intelligence.")
    _stage(doc, "Stage 2 - Coverage Validation.",
           "The server checks that both the metric term and the dimension term exist in the semantic "
           "layer vocabulary before anything else runs. Unknown identifiers are rejected here, with a "
           "structured message listing the available identifiers, rather than being passed to the "
           "compiler.")
    _stage(doc, "Stage 3 - Semantic Mapping.",
           "Business-logic aliases are expanded (for example, “abandoned” maps to a specific "
           "OrderStatusId), and relative time expressions such as “this month” are resolved to "
           "concrete date predicates.")
    _stage(doc, "Stage 4 - Permission Rewriting.",
           "A role-specific WHERE predicate is appended based on the authenticated user's session. "
           "This runs after the LLM has already finished, so no natural-language content can influence "
           "it.")
    _stage(doc, "Stage 5 - SQL Compilation.",
           "A breadth-first search over the join graph finds the minimal join path connecting the "
           "tables required by the resolved metric and dimension, and pre-compiled SQL expressions are "
           "substituted into a parameterized template. No SQL text is ever assembled from concatenated "
           "user input.")
    _stage(doc, "Stage 6 - Visualization Selection.",
           "A rule engine maps the intent class and result shape to a default chart type (Section "
           "3.10). This stage contains no learned model.")
    _stage(doc, "Stage 7 - Widget Persistence.",
           "The analysis plan is hashed (SHA-256) to detect duplicates, and the query, chart "
           "configuration, and access rules are stored as a widget artifact that can be refreshed on a "
           "schedule (Section 3.11).")
    add_figure_placeholder(doc, 1, "AEGIS architecture pipeline (User Request to Dashboard Widget)",
        "A left-to-right flowchart of the seven stages in sequence: User Request -> LLM Intent Parser "
        "-> Coverage Validator -> Semantic Mapper -> Permission Rewriter -> Safe Query Compiler -> "
        "Query Executor -> Visualization Selector -> Widget Engine -> Dashboard. Color-code by "
        "responsibility: blue for the single AI/LLM stage, purple for semantic mapping, red for the "
        "two safety-enforcement stages (Permission Rewriter, Safe Query Compiler), green for "
        "execution/output stages. Add small orange branch arrows from Coverage Validator and Safe "
        "Query Compiler pointing to a 'Structured Clarification / Rejection Message' box, showing "
        "that invalid requests exit early with an actionable error rather than a silent failure.",
        height_in=2.2)

    # ---------------------------------------------------------------- 3.7
    add_section_heading(doc, "3.7", "Semantic Layer Design")
    add_para(doc,
              "The semantic layer is the most important non-AI component of AEGIS. It separates "
              "business language from the underlying database structure and defines exactly which "
              "metrics, joins, and permissions are allowed to exist. A useful analogy is LEGO blocks "
              "rather than free-form clay: the semantic layer defines a finite set of composable "
              "building blocks. User questions are unlimited, but every answerable question is a "
              "composition of these blocks.", space_after=10)
    add_figure_placeholder(doc, 2, "Semantic layer modularity - composable blocks vs. free-form SQL generation",
        "A split-panel comparison. LEFT panel, labeled 'AEGIS': a small set of labeled building "
        "blocks (Metric, Dimension, Filter, Join Path, Pattern) shown snapping together into two or "
        "three example complete query shapes, like LEGO bricks combining into a finished model. RIGHT "
        "panel, labeled 'Direct LLM-to-SQL': a shapeless, cracked blob of clay with a warning icon, "
        "annotated '5.0% unsafe queries in baseline (Chapter 5, Section 5.2)'. The visual point is "
        "that AEGIS composes from a bounded set of safe parts while direct generation is unbounded "
        "and can take an unsafe shape.")
    add_table_with_caption(
        doc, "Table 1: Semantic layer object model.",
        ["Object", "Field", "Example"],
        [
            ["Metric", "label, SQL expression, joins, visual default, security class",
             "revenue = SUM(o.OrderTotal - o.RefundedAmount)"],
            ["Dimension", "label, SQL expression, datatype, access scope",
             "category = c.Name from Category"],
            ["Filter", "label, SQL predicate, datatype",
             "payment_status : o.PaymentStatusId = :val"],
            ["Time rule", "label, SQL predicate, granularity", "current_week : DATEADD(week, ...)"],
            ["Join path", "source, target, ON clause", "Order → OrderItem → Product → Category"],
            ["Pattern", "required slots, SQL template, visualization default",
             "ranking : metric + dimension → bar chart"],
            ["Permission", "rule", "store_manager → filtered by store location"],
        ])
    add_para(doc,
              "In the nopCommerce prototype, the semantic layer defines 15 metrics, 34 dimensions, and "
              "11 join paths across 12 analytics-relevant tables. The full nopCommerce schema contains "
              "126 tables; the remaining 114 (system, content-management, configuration, authentication, "
              "vendor, and promotions tables) are deliberately not represented in the semantic layer at "
              "all. No business analyst asks “show me revenue by ScheduleTask,” and excluding "
              "these tables functions as an implicit table-level access control: even a crafted prompt "
              "that names a hidden system table directly is rejected at Stage 2, because the identifier "
              "simply does not exist in L.", space_after=0)

    # ---------------------------------------------------------------- 3.8
    add_section_heading(doc, "3.8", "Intent Parsing with Dynamic Vocabulary Injection")
    add_para(doc,
              "The central technique that makes Stage 1 reliable is vocabulary injection. At startup, "
              "AEGIS builds the system prompt by listing every approved metric and dimension name, with "
              "a plain-English description, directly from the semantic layer (approximately 1,100 tokens "
              "for 15 metrics and 34 dimensions). The LLM sees exactly which identifiers are valid and "
              "maps any user phrasing to the correct identifier without a manually maintained synonym "
              "list. This has three advantages over a synonym dictionary: zero maintenance, since adding "
              "a metric automatically updates the vocabulary the model sees; broad coverage of "
              "arbitrary user phrasing, since the model performs the mapping rather than a fixed lookup "
              "table; and token efficiency, since the full vocabulary for 15 metrics and 34 dimensions "
              "fits in roughly 1,100 tokens.", space_after=10)
    add_para(doc,
              f"Structured output enforcement for LLMs {cite('openai24')} constrains the model's "
              "response to a fixed JSON schema before any downstream validation occurs, which is why "
              "Stage 1 can rely on a typed IntentObject rather than free-form text: malformed or "
              "off-schema output is rejected at the API boundary, before Stage 2 coverage validation "
              "ever runs.", space_after=10)
    add_para(doc, "The output schema enforces typed fields:", space_after=6)
    add_code_block(doc, """{
  "intent_class": "kpi | ranking | trend | comparison | exception |
                   summary | segment | funnel | cohort | correlate | tabular",
  "metric_term": "string",
  "dimension_term": "string or null",
  "time_term": "string or null",
  "filters": [{"field": "string", "operator": "string", "value": "string"}],
  "sort": "asc | desc | null",
  "limit": "integer or null",
  "confidence": "low | medium | high",
  "needs_clarification": "boolean"
}""")
    add_figure_placeholder(doc, 3, "Vocabulary injection workflow",
        "A three-lane sequence diagram: 'Semantic Layer (semantic_layer.py)' -> 'System Prompt "
        "Builder' -> 'LLM'. Show the Semantic Layer box listing a few example metric/dimension "
        "entries with plain-English descriptions; an arrow labeled 'serializes into ~1,100 tokens' "
        "into the System Prompt Builder; then into the LLM, whose output arrow produces an example "
        "IntentObject such as {metric_term: 'revenue', dimension_term: 'category'}. Annotate with a "
        "small callout showing the user phrase 'earnings' mapping to the approved ID 'revenue' even "
        "though 'earnings' appears in no synonym list.")
    page_break(doc)

    # ---------------------------------------------------------------- 3.9
    add_section_heading(doc, "3.9", "Safe Query Compiler")
    add_para(doc,
              "The compiler instantiates SQL from a library of parameterized templates, one per "
              "analytics pattern.", space_after=10)
    add_figure_placeholder(doc, 4, "Taxonomy of the eleven AEGIS analytical patterns",
        "A tree or grid diagram with 'Eleven Analytical Patterns' at the top branching into eleven "
        "labeled leaves: KPI, Ranking, Trend, Comparison, Exception, Summary, Segment, Funnel, "
        "Cohort, Correlate, Tabular. Under each leaf, show a small icon of its default visualization "
        "(matching Table 2/3): card, bar chart, line chart, grouped bar, table, card grid, pie chart, "
        "funnel chart, grouped bar, scatter plot, table. Caption note: '~5,610 valid combinations "
        "across 15 metrics x 34 dimensions x 11 patterns.'")
    add_table_with_caption(
        doc, "Table 2: The eleven AEGIS analytical patterns.",
        ["Pattern", "Required slots", "Optional slots", "Default visual"],
        [
            ["KPI (Aggregate)", "metric", "time_rule, filter", "kpi_card"],
            ["Ranking", "metric, dimension", "time_rule, filter, limit", "bar_chart"],
            ["Trend", "metric, time_grain", "time_rule, filter", "line_chart"],
            ["Comparison", "metric, segment", "time_rule, filter", "grouped_bar"],
            ["Exception", "metric, threshold", "dimension, time_rule", "table"],
            ["Summary", "metric[], dimension", "time_rule, filter", "multi_card"],
            ["Segment", "metric, dimension", "time_rule, filter", "pie_chart"],
            ["Funnel", "metric, stages", "time_rule, filter", "funnel_chart"],
            ["Cohort", "metric, group_def", "time_rule, filter", "grouped_bar"],
            ["Correlate", "metric, attribute", "time_rule, filter", "scatter_plot"],
            ["Tabular", "dimension", "filters, time_rule", "table"],
        ])
    add_para(doc,
              "After placeholder substitution, two safety layers apply in sequence. Layer 1 is a "
              "parameterized query engine that separates SQL structure from user-supplied inputs, so no "
              "user text is ever concatenated into the SQL string. Layer 2 is a post-compilation safety "
              "scanner that rejects any assembled query containing a forbidden construct: non-SELECT "
              "statements, UNION, EXCEPT or INTERSECT, EXEC, or references to system tables. If any "
              "forbidden pattern is detected, the compiler raises a SecurityError rather than returning "
              "a partially safe query.", space_after=0)
    add_figure_placeholder(doc, 6, "Two-layer SQL safety defence",
        "A vertical two-stage flowchart. A crafted/adversarial input enters at the top with a warning "
        "icon. Layer 1 box: 'Parameterized Query Engine — user text never enters the SQL string; only "
        "IDs and bound values appear.' Arrow down to Layer 2 box: 'Post-Compilation Safety Scanner — "
        "rejects non-SELECT statements, UNION/EXCEPT/INTERSECT, EXEC, and system-table references (16 "
        "forbidden patterns checked).' Below, split into two outcomes: a green 'Safe SQL Executed' "
        "box for a legitimate query, and a red 'SecurityError Raised' box for a rejected one, showing "
        "the attack is caught before it can reach the database regardless of which layer catches it.")

    # ---------------------------------------------------------------- 3.10
    add_section_heading(doc, "3.10", "Visualization Selector")
    add_table_with_caption(
        doc, "Table 3: Visualization selector mapping.",
        ["Intent", "Result shape", "Selected visualization"],
        [
            ["KPI", "scalar", "KPI card"],
            ["Ranking", "1 measure, up to 20 categories", "Horizontal bar chart"],
            ["Trend", "1 measure, time series", "Line chart"],
            ["Comparison", "1 measure, 2-4 segments", "Grouped bar chart"],
            ["Exception", "row-level detail", "Sortable table"],
            ["Summary", "2-4 scalar measures", "KPI card grid"],
            ["Segment", "1 measure, categorical", "Pie chart"],
            ["Funnel", "ordered conversion stages", "Funnel chart"],
            ["Cohort", "1 measure, 2+ groups", "Grouped bar chart"],
            ["Correlate", "2 measures, continuous", "Scatter plot"],
            ["Tabular", "raw records", "Sortable table"],
        ])
    add_para(doc,
              "Two additional rules apply after the data is known, rather than at selection time: bar "
              "charts with more than 20 categories are automatically converted to a table, and pie "
              "charts with more than 8 slices are converted to a bar chart. Both rules exist because "
              "the initial chart choice is made before the exact cardinality of the result is known.",
              space_after=0)

    # ---------------------------------------------------------------- 3.11
    add_section_heading(doc, "3.11", "Widget Persistence and Reuse")
    add_para(doc,
              "Each widget stores a unique identifier (a SHA-256 hash of the analysis plan), the "
              "original question, the analysis plan in JSON form, a hash of the SQL template used, "
              "chart configuration, timestamps, access rules, and run history. A new question triggers "
              "the full seven-stage pipeline; if an identical widget already exists, determined by a "
              "match on the plan hash, the cached artifact is returned immediately rather than "
              "recompiled. Scheduled refresh re-executes the stored SQL against fresh data on a "
              "configurable interval, which directly addresses the formative-study finding (Section "
              "3.2) that 61% of reporting requests are recurring: a widget answers the question once "
              "and then continues answering it as new data arrives, rather than requiring the same "
              "natural-language request to be re-processed from scratch every time.", space_after=0)
    add_figure_placeholder(doc, 7, "Widget lifecycle and refresh model",
        "A cyclical flowchart. Start: 'New Natural-Language Question' -> 'Full Seven-Stage Pipeline "
        "Runs' -> 'Analysis Plan Hashed (SHA-256)' -> a decision diamond 'Identical widget hash "
        "already exists?'. If YES, arrow to 'Return Cached Widget Immediately'. If NO, arrow to 'Save "
        "New Widget (SQL, chart config, access rule, refresh schedule)'. Both paths converge into a "
        "'Dashboard Widget' box, from which a looping arrow labeled 'Scheduled Refresh (re-executes "
        "stored SQL on fresh data)' curves back into the same box — illustrating that a widget keeps "
        "answering the same recurring question rather than being discarded after one use.")
    page_break(doc)


def _threat(doc, tid, title, attack, control):
    add_mixed_para(doc, [(f"{tid} - {title} ", True, False)], space_after=4, space_before=8)
    add_mixed_para(doc, [("Attack: ", True, True), (attack, False, True)], space_after=2)
    add_mixed_para(doc, [("Control: ", True, False), (control, False, False)], space_after=6)


def _stage(doc, title, body):
    add_mixed_para(doc, [(title + " ", True, False), (body, False, False)], space_after=8)
