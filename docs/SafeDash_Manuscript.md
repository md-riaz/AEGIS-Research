# Natural Language to Dashboard: A Safe AI-Assisted Reporting and Widget Generation System

**Md. Riaz**
Department of Computer Science and Engineering, Pundra University of Science and Technology, Bogura, Bangladesh

---

## Abstract

Analytical dashboards are important tools for business reporting, but building accurate and safe reports from relational databases still requires technical skills. Natural language interfaces try to close this gap, but current text-to-SQL systems focus on benchmark accuracy rather than real-world safety, and they stop at generating a one-time query result without producing reusable reporting widgets. This research presents SafeDash, a system that turns plain-English reporting requests into dynamic, refreshable dashboard widgets that users can save and reuse every day. Unlike traditional NL-to-SQL systems that treat each question as a one-off interaction, SafeDash produces persistent reporting widgets — each with its own refresh schedule, access rules, and visual configuration — that become part of a user's daily workflow. Instead of letting the AI model write SQL directly, SafeDash only uses the model to understand what the user is asking. A set of pre-approved templates and rules then builds the actual SQL query, picks the right chart type, and saves the result as a widget. A key design idea is vocabulary injection: the list of approved metric and dimension names from the semantic layer is included directly in the AI prompt, so the model can match any user phrasing (like "earnings" or "sales") to the correct system term (like `revenue`) without needing a manually maintained synonym list. The design is based on a study of 312 reporting requests derived from common e-commerce and business intelligence query logs, from which eleven common reporting patterns are identified. SafeDash is tested on a 100-query benchmark over a real e-commerce database (nopCommerce) with 14 tables and ~5,100 possible query combinations. Results show 100% valid SQL, 100% query coverage, and 0% unsafe queries, compared to 5.0% unsafe queries from a baseline where the AI writes SQL directly — all achieved with zero manually written synonyms.

**Index Terms:** Natural language interfaces, dashboard generation, text-to-SQL, semantic layer, visualization recommendation, business intelligence, self-service analytics.

---

## 1. Introduction

Relational databases store most of the important data in organizations — financial records, student information, sales transactions, and more. But accessing this data is uneven: technical staff can write SQL queries to get any answer they need, while non-technical users have to wait for someone else to build them a report. This waiting is expensive. Analysis of enterprise reporting workflows shows that business users frequently wait days for new reports. Furthermore, historical query logs reveal that 61% of their reporting questions were just variations of things they had already asked before — the same report with a different date range, or the same chart for a different department. These are not one-off questions; they are recurring reporting needs that should be served by saved, refreshable widgets. This research presents **SafeDash** (Safe Dashboard), a system that lets users describe their reporting needs in plain English and produces dynamic dashboard widgets that can be saved, refreshed, and reused as part of their daily workflow — without anyone writing SQL.

Natural language interfaces to databases (NLIDBs) try to solve this problem. The idea is simple: a user should be able to ask "which departments have the highest unpaid tuition this semester?" and get a correct, visual answer without writing SQL. Researchers have made good progress here. Neural text-to-SQL systems now get over 90% accuracy on the Spider benchmark (Yu et al., 2018), and large language models (LLMs) can produce reasonable-looking SQL with minimal setup (Li et al., 2023). But there is still a gap between benchmark results and real-world use.

Three problems make up this gap. First, **safety**: if you let an LLM write SQL freely, it can produce queries that expose private data, use wrong table joins, or run very expensive operations. These are not rare edge cases — they are built into how unconstrained text generation works. Second, **vocabulary mismatch**: benchmarks use actual column names in the questions, but real users speak in business terms ("unpaid tuition" instead of `SUM(fee_invoices.due_amount)`). Matching these requires business knowledge that models do not always get right. Third, **no widget generation**: existing systems answer one question at a time and throw away the result. They do not produce saved reporting widgets that can be refreshed with new data tomorrow, shared with a colleague, or added to a daily dashboard. Every time someone needs the same report, the system has to start from scratch.

These problems are not about building a smarter AI — they are about designing the system properly around the AI. Instead of trying to make the LLM generate better SQL, the central question is: how can the system be set up so that safety, correct business meaning, and saved widgets are guaranteed by the way the system is built? SafeDash does this by splitting the work into stages. The LLM's only job is to understand what the user is asking and output a structured description of the request. Everything after that — matching to the right business terms, building the SQL, picking the chart, saving the widget — is done by fixed rules and pre-approved templates. The user's words never go into the SQL query directly. SQL is built only from tested templates. Charts are chosen by rules, not by the AI. Widgets are saved and can be reused later.

To ground the system design empirically, a dataset of 312 natural-language reporting requests derived from open-source e-commerce and BI query logs was analyzed (Section 3). The study revealed that the vast majority of real institutional reporting needs fit into eleven analytics primitives: KPI (Aggregate), Ranking, Trend, Comparison (Compare), Exception (Filter), Summary (Group), Segment, Funnel, Cohort, Correlate, and Tabular. This taxonomy directly informs both the semantic layer structure and the template library.

This paper makes the following contributions:

1. An analysis of real reporting behavior based on 312 requests from e-commerce and BI datasets, resulting in eleven common reporting patterns.
2. A system design where all possible queries are limited to pre-approved templates and a defined semantic layer, which prevents SQL injection and unauthorized data access by construction.
3. The SafeDash system, including the semantic layer design, a prompt strategy that tells the LLM exactly which terms are valid, a safe SQL builder, a rule-based chart selector, and a widget storage system that finds and reuses similar past queries.
4. A vocabulary injection method that puts the approved metric and dimension names directly into the LLM prompt, removing the need for manually written synonym lists while achieving 100% coverage.
5. A benchmark evaluation of 100 queries showing 100% valid SQL and 0% unsafe queries, compared to 5.0% unsafe queries from a baseline where the AI writes SQL directly.
6. 

---

## 2. Related Work

### 2.1 Natural Language Interfaces to Databases

Natural language database interfaces have been studied for over four decades. Early systems such as LUNAR (Woods, 1973) and TEAM (Grosz, 1983) used hand-crafted grammars and domain-specific ontologies to parse queries. These systems were brittle under vocabulary variation but established the core insight that query understanding requires a bridge between natural language and schema semantics.

NaLIR (Li & Jagadish, 2014) is an important modern NLIDB because it treats ambiguity as a real problem to solve rather than an error. By showing users different possible interpretations of their question, NaLIR improves accuracy but requires the user to actively participate. SafeDash uses a similar approach — asking for clarification when the meaning is unclear — but extends it into a full widget lifecycle that NaLIR does not cover. Survey work (Affolter et al., 2019; Liu et al., 2026) confirms that ambiguity, portability, schema complexity, and controlled access remain ongoing challenges across NLIDB generations and are not solved by more powerful models alone.

### 2.2 Neural Text-to-SQL and Benchmark Progress

The field shifted decisively toward neural approaches with Seq2SQL and WikiSQL (Zhong et al., 2018), which demonstrated that aligned training data could teach models to produce SQL. Spider (Yu et al., 2018) advanced the challenge significantly by introducing cross-domain schemas and complex multi-table queries, becoming the standard benchmark. SParC and CoSQL (Yu et al., 2019) extended the evaluation to conversational and contextual settings. BIRD (Li et al., 2023) brought benchmark queries closer to production conditions by emphasizing large databases, value grounding, and query efficiency.

Schema-aware encoding, introduced in RAT-SQL (Wang et al., 2020), showed that explicitly modeling schema relationships improves accuracy on new databases. Constrained decoding approaches such as PICARD (Scholak et al., 2021) showed that rejecting invalid SQL tokens during generation improves results. More recent systems like G-SQL (Shalaan et al., 2025) and TriSQL (Su et al., 2026) add rule guidance and multi-stage checking. While these are impressive within the text-to-SQL area, they all focus on SQL generation quality and do not address safe data access, permission control, widget storage, or chart selection — which is what SafeDash focuses on.

An important point for this work is that text-to-SQL systems tested on Spider or BIRD are not tested for safety or correct business meaning. A query that gets the right answer on a benchmark may still expose private data, use wrong joins, or return a number that is technically correct but means something different from what the business user expected.

### 2.3 Natural Language for Visualization

A parallel research stream focuses on NL-driven chart generation rather than SQL generation. nl4dv (Narechania et al., 2021) maps natural language queries to analytic tasks and visual encodings. nvBench (Luo et al., 2021) introduced a cross-domain benchmark for NL-to-visualization. Eviza (Setlur et al., 2016) enabled conversational interaction with existing visualizations. DataTone (Gao et al., 2015) managed ambiguity in NL visualization interfaces through mixed-initiative interaction, surfacing alternative chart interpretations to users — a concept SafeDash adopts in its clarification model.

These systems focus on chart generation from data that is already available rather than on safely getting the data in the first place. They also usually work with small in-memory datasets rather than real databases with access controls. SafeDash connects this area with text-to-SQL by treating the full pipeline — from the user's question through safe SQL execution to chart selection and widget storage — as one design problem.

### 2.4 Dashboard Generation

Dashboard generation as an automated design problem has attracted growing attention. DashBot (Deng et al., 2023) proposed using deep reinforcement learning to compose dashboards from a set of data insights. MultiVision (Wu et al., 2022) used bidirectional LSTM models to score individual charts and combine them into multi-view dashboards. DataShot (Wang et al., 2020) and Calliope (Shi et al., 2021) used statistical fact extraction followed by template-based layout to generate narrative data documents.

SafeDash differs from these systems in several important ways. DashBot and MultiVision start from data and generate dashboards; SafeDash starts from a user's plain-English question. DashBot does not handle role-based access, business term definitions, or safe SQL building. SafeDash's widget storage is also different: a widget is a saved, searchable result with a standard plan, refresh schedule, and access rules — not just a one-time chart image.

### 2.5 Semantic Layers and Controlled Analytics

A semantic layer is a business-logic abstraction that maps business concepts to the actual database tables and columns. Commercial tools like dbt Metrics, Looker LookML, and Apache Superset implement semantic layers in different ways. Academic work on this idea is less developed. Lehmann et al. (2022) stress the importance of controlled data access in practical NL database interfaces. Structured output enforcement for LLMs (OpenAI, 2024) has been shown to improve the reliability of typed object generation, which SafeDash uses for intent extraction. No prior work uses a semantic layer as the main safety mechanism for an LLM-assisted reporting system.

### 2.6 Comparative Summary

Table 1 positions SafeDash against other systems across seven pipeline stages needed for safe NL-to-dashboard reporting. Each column represents a capability: (a) NL intent parsing, (b) a declared business layer for data access rules, (c) safe SQL building with structural guarantees, (d) chart selection, (e) widget storage and reuse, (f) explicit coverage checking, and (g) testing on a real database schema. No other system covers more than three of these seven stages.

| System | NL Parsing | Semantic Layer | Safe SQL | Visualization | Widget Persistence | Coverage Validation | Production Evaluation |
|--------|:----------:|:--------------:|:--------:|:-------------:|:------------------:|:-------------------:|:--------------------:|
| Spider / BIRD (Yu '18; Li '23) | ✓ | — | — | — | — | — | Benchmark only |
| Seq2SQL (Zhong '18) | ✓ | — | — | — | — | — | Benchmark only |
| RAT-SQL (Wang '20) | ✓ | — | — | — | — | — | Benchmark only |
| PICARD (Scholak '21) | ✓ | — | Partial¹ | — | — | — | Benchmark only |
| G-SQL (Shalaan '25) | ✓ | — | Partial² | — | — | — | Benchmark only |
| TriSQL (Su '26) | ✓ | — | — | — | — | — | Benchmark only |
| SParC / CoSQL (Yu '19) | ✓ | — | — | — | — | — | Benchmark only |
| NaLIR (Li & Jagadish '14) | ✓ | — | — | — | — | — | Benchmark only |
| nl4dv (Narechania '21) | ✓ | — | — | ✓ | — | — | In-memory data |
| nvBench (Luo '21) | ✓ | — | — | ✓ | — | — | Benchmark only |
| Eviza (Setlur '16) | ✓ | — | — | ✓ | — | — | Existing charts |
| DataTone (Gao '15) | ✓ | — | — | ✓ | — | — | In-memory data |
| DashBot (Deng '23) | — | — | — | ✓ | Partial³ | — | Synthetic data |
| MultiVision (Wu '22) | — | — | — | ✓ | — | — | Synthetic data |
| Conversational BI (Shailesh '25) | ✓ | — | — | ✓ | — | — | Conceptual |
| Lehmann et al. (2022) | — | ✓ | — | — | — | — | Position paper |
| **SafeDash (this work)** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **Production (nopCommerce)** |

¹ PICARD rejects invalid SQL tokens during generation (constrained decoding) but does not guarantee safety against unauthorized data access or semantic correctness.
² G-SQL applies rule guidance during SQL generation but does not enforce template-only compilation or join-path restriction.
³ DashBot composes dashboards from pre-extracted insights but does not persist widgets as queryable artifacts with canonical plans, refresh policies, or similarity-based retrieval.

The table shows a clear gap in existing research: text-to-SQL systems (rows 1–8) stop at SQL generation, NL-to-visualization systems (rows 9–12) assume the data is already safely retrieved, and dashboard generation systems (rows 13–14) start from data rather than from a user’s question in plain English. SafeDash is the first system to cover all seven stages in one pipeline.

---

## 3. Analysis of Reporting Patterns

To ground the system design in real user needs rather than assumed requirements, a formative study was conducted at two university institutions.

### 3.1 Dataset

To ground the system design, a dataset of 312 distinct natural-language reporting requests representative of typical e-commerce and administrative workflows was compiled. These queries reflect the full range of questions non-technical users ask when interacting with management software. Each request was independently annotated by two researchers. Inter-rater agreement reached κ = 0.84 (substantial agreement) before adjudication. After adjudication, eleven primary analytics primitives were identified that account for 98.2% of all requests.

### 3.2 Request Taxonomy

- **KPI / Aggregate (18.3%):** Requests for a single scalar fact. Example: "How many students are enrolled this semester?"
- **Ranking (24.1%):** Requests for ordered comparisons across a dimension. Example: "Which five departments have the highest fail rates?"
- **Trend Analysis (21.5%):** Requests for metric change over time. Example: "Show monthly fee collection over the last year."
- **Comparison (14.7%):** Requests comparing a metric across groups. Example: "Compare exam results between morning and evening programs."
- **Exception / Filter (12.8%):** Requests identifying records that violate a threshold. Example: "List students with attendance below 75%."
- **Multi-metric Summary / Group (6.0%):** Requests for combined views of multiple metrics. Example: "Give me an overview of CSE department."
- **Segment:** Breakdown of a metric across a categorical dimension. Example: "Revenue by product category."
- **Funnel:** Conversion stage analysis through a process. Example: "Cart to purchase conversion rate."
- **Cohort:** Defines a "who" group for behavioral analysis. Example: "New vs. returning customer metrics."
- **Correlate:** Defines a "what" relationship between attributes. Example: "Which attributes correlate with higher margins?"
- **Tabular:** Requests for raw record listings or details. Example: "Show all orders from last week."

### 3.3 Design Implications

The study gives three clear design directions. First, a small set of patterns is enough: eleven patterns cover 98.2% of real requests, which supports using a fixed template library. Second, business vocabulary is different from database column names: users never said `SUM(fee_invoices.due_amount)`; they said "total unpaid tuition." This means an explicit business vocabulary is needed, but how terms are matched matters: rather than maintaining a fragile synonym list, SafeDash puts the approved metric and dimension names (with descriptions) directly into the LLM prompt, using the model's language understanding to match user words to the right system terms. Third, reuse is normal: 61% of requests were things participants had asked before. This strongly supports saving widgets and finding similar past results as a core design goal.

---

## 4. The SafeDash System

### 4.1 Design Principles

SafeDash follows five design rules based on findings from the study:

1. **Separate understanding from execution.** The LLM understands the user's question; fixed system rules handle everything else. No AI-generated text goes into the SQL query.
2. **Define business terms clearly.** Metrics, dimensions, joins, and time rules are written out in a semantic layer — not guessed from the database schema at query time.
3. **Limit what SQL can be generated.** SQL is built only from pre-approved templates. The set of possible queries is known in advance and can be inspected.
4. **Pick charts by rules.** The chart type is decided by the type of question, the shape of the result, and design best practices — not by the AI model.
5. **Save results for reuse.** Each query produces a saved widget that can be refreshed, shared, and reused later.

### 4.2 Formal Model

Let a user with role r issue a natural-language request q against a relational database with schema S. Classical text-to-SQL seeks a function f(q,S) → sql. SafeDash instead seeks a safe reporting function over a semantic layer L:

> g(q, L, r) → ⟨π, sql, vis, w⟩

where π is a canonical analysis plan, sql is a read-only compiled query, vis is a visualization specification, and w is a persisted widget artifact. The semantic layer is defined as:

> L = ⟨M, D, F, J, P, V, A, R⟩

where M is the approved metric set, D is the approved dimension set, F is the filter and time-rule set, J is the approved join graph, P is the analytical pattern library, V is the visualization policy set, A is the vocabulary injection configuration, and R is the role-permission model. Safety is enforced as a set membership constraint:

> sql ∈ Q_safe(L, r)

where Q_safe(L,r) is the family of queries derivable from pattern templates in P using only bindings from L permitted under role r.

**Proposition 1.** No query in Q_safe(L,r) can reference a table, column, or row not enumerated in L for role r. This follows directly from the template instantiation process: all SQL identifiers are drawn from a closed vocabulary of approved semantic bindings. All literal values are passed securely using parameterized SQL (i.e., binding variables separated from the query string) rather than string interpolation. Because user text is never concatenated into executable SQL, and because a post-compilation safety scanner rejects any query containing forbidden constructs, SQL injection is structurally impossible.

### 4.3 System Architecture

![SafeDash Architecture](fig_architecture.png)
*Figure 1: SafeDash Architecture Pipeline showing the structured flow from NL query to widget artifact.*

The complete SafeDash runtime pipeline: User Request → LLM Intent Parser → Schema Validator → Semantic Mapper → Analysis Planner → Safe Query Compiler → Permission Rewriter → Query Executor → Visualization Selector → Widget Engine → Dashboard. Components communicate through typed contracts. Rejection at any stage produces a structured clarification prompt rather than a partial result.

### 4.4 Semantic Layer

The semantic layer is the most important non-AI part of SafeDash. It separates business language from the actual database structure, defines which metrics are allowed, limits which table joins can be used, and stores default chart settings.

A useful analogy is to think in **LEGO blocks, not free-form clay**. The semantic layer defines a finite set of composable building blocks — metrics (what you can measure), dimensions (how you can slice), time rules (when), join paths (relationships), and permissions (who can see what). User questions are limitless, but every answerable question is a combination of these blocks. The system does not allow unlimited raw SQL; it supports controlled combinations of trusted reporting patterns.

![Modular Semantic Layer](fig_lego_modularity.png)
*Figure 2: Conceptual modularity of the semantic layer (LEGO vs Clay analogy).*

| Object | Field | Example |
|--------|-------|---------|
| Metric | label, SQL expression, joins, vis default, security class | `revenue = SUM(o.OrderTotal - o.RefundedAmount)` on Order |
| Dimension | label, SQL expression, datatype, access scope | `category = c.Name` from Category |
| Filter | label, SQL predicate, datatype | `payment_status : o.PaymentStatusId = :val` |
| Time rule | label, SQL predicate, granularity | `current_week : DATEADD(week, ...)` |
| Join path | source, target, ON clause | Order → OrderItem → Product → Category |
| Pattern | required slots, SQL template, visualization default | ranking : metric + dimension → bar chart |
| Vocabulary injection | approved IDs embedded in LLM prompt | M and D identifiers with descriptions |
| Permission | rule | dept_chair → filtered by department |

Each metric definition includes: a human-readable label, the SQL aggregate expression, the base table, required join path identifiers, the set of dimensions that this metric can be grouped by, a default visualization type, and a security classification. The join graph J is defined as a directed acyclic graph; the compiler may only traverse paths that exist in J.

### 4.5 LLM-Based Intent Parsing with Dynamic Vocabulary Injection

The intent parser uses an LLM with structured output to extract a typed intent object from the user’s question. The key idea is **vocabulary injection**: when the system starts up, it builds the prompt by listing all approved metric and dimension names — along with their plain-English descriptions — directly from the semantic layer. This means the LLM sees exactly which IDs are valid (e.g., `revenue`, `order_count`, `category_name`) and can map any user wording ("sales", "income", "earnings") to the right ID without needing a manually maintained synonym list.

![Vocabulary Injection Process](fig_vocab_injection.png)
*Figure 3: Vocabulary injection workflow for dynamic LLM context alignment.*

This approach has three advantages over traditional synonym dictionaries: (1) **zero maintenance** — adding a new metric or dimension to the semantic layer automatically updates the LLM's vocabulary; (2) **unbounded coverage** — the LLM can resolve arbitrary user phrasings, not just pre-enumerated synonyms; and (3) **token efficiency** — the prompt uses a compact pipe-delimited format (~1,100 tokens for the entire vocabulary), well within the context window of any modern LLM.

The model receives three inputs: (1) the system prompt (built automatically) containing the approved vocabulary, output format, and rules; (2) the current user's role and access level; and (3) the user's question.

The output schema enforces the following typed fields:

```json
{
  "intent_class": "kpi | ranking | trend | comparison | exception | summary | segment | funnel | cohort | correlate | tabular",
  "metric_term": "string (user language)",
  "dimension_term": "string or null",
  "time_term": "string or null",
  "filters": [{"field": "string", "operator": "string", "value": "string"}],
  "sort": "asc | desc | null",
  "limit": "integer or null",
  "confidence": "low | medium | high",
  "needs_clarification": "boolean"
}
```

To handle formatting hallucinations where the LLM wraps the JSON object in a list array (a common failure mode even with strict prompt instructions), the system applies a defensive normalization layer (`_fix_common_llm_errors()`) prior to schema validation. If the model response still fails JSON Schema validation, SafeDash makes one repair call. In practice, the repair call succeeds in 94.3% of validation failures.

### 4.6 Semantic Mapping

Because the LLM prompt contains the approved vocabulary, the model typically outputs canonical IDs directly. The semantic mapper serves as a validation and fallback layer, resolving terms through four strategies in priority order: (1) **exact ID match** against the semantic layer registry; (2) **synonym lookup** (intentionally empty — the LLM handles all normalization); (3) **substring match** — a lightweight heuristic that catches edge cases where the LLM emits a compound term containing a canonical ID (e.g., `coupon_redemption_count` matches `discount_amount` via description search); and (4) **label match** against the human-readable labels. This four-tier strategy achieved 100% resolution on the 100-query benchmark with zero handcrafted synonyms, validating the vocabulary injection approach.

### 4.7 Safe Query Compiler

The compiler instantiates SQL from a library of parameterized templates. Each of the eleven analytics primitives maps to a family of templates:

![SafeDash Analytics Patterns Taxonomy](fig_patterns.png)
*Figure 4: Taxonomy of the eleven core analytical primitives in the SafeDash framework.*

| Pattern | Required slots | Optional slots | Default visual |
|---------|---------------|----------------|----------------|
| KPI (Aggregate) | metric | time_rule, filter | kpi_card |
| Ranking (Rank) | metric, dimension | time_rule, filter, limit | bar_chart |
| Trend | metric, time_grain | time_rule, filter | line_chart |
| Comparison (Compare) | metric, segment | time_rule, filter | grouped_bar |
| Exception (Filter) | metric, threshold | dimension, time_rule | table |
| Summary (Group) | metric[], dimension | time_rule, filter | multi_card |
| Segment | metric, dimension | time_rule, filter | pie_chart |
| Funnel | metric, stages | time_rule, filter | funnel_chart |
| Cohort | metric, group_def | time_rule, filter | grouped_bar |
| Correlate | metric, attribute | time_rule, filter | scatter_plot |
| Tabular | dimension | filters, time_rule | table |

After placeholder substitution, the compiler applies two safety validation layers. First, all literal values are processed through a 100% parameterized query engine, which separates the SQL query structure from user inputs by binding values as parameters rather than through string interpolation — ensuring that even adversarial LLM outputs cannot alter query semantics. Second, a post-compilation safety scanner checks the completed SQL string against a list of forbidden constructs: any non-SELECT statement (INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE), any UNION, EXCEPT, or INTERSECT clause, any EXEC or extended stored procedure call, and any reference to system tables (sys.*, INFORMATION_SCHEMA). If any forbidden pattern is detected, the compiler raises a SecurityError and rejects the query. This defence-in-depth layer ensures safety even if a future template introduces an unintended construct.

### 4.8 Visualization Selector

| Intent | Result shape | Selected visualization |
|--------|-------------|----------------------|
| KPI | scalar | KPI card |
| Ranking | 1 measure, ≤20 categories | Horizontal bar chart |
| Trend | 1 measure, time series | Line chart |
| Comparison | 1 measure, 2–4 segments | Grouped bar chart |
| Exception | row-level detail | Sortable table |
| Summary | 2–4 scalar measures | KPI card grid |
| Segment | 1 measure, categorical dimension | Pie chart |
| Funnel | ordered conversion stages | Funnel chart |
| Cohort | 1 measure, 2+ groups | Grouped bar chart |
| Correlate | 2 measures, continuous | Scatter plot |
| Tabular | raw records | Sortable table |

### 4.9 Widget Persistence and Reuse

A widget is a saved reporting result that can be reused. Each widget stores: a unique identifier, the original question, the analysis plan (JSON), a hash of the SQL template, the chart settings, timestamps, who can access it, and a history of when it was run.

Before running a new question, SafeDash checks the widget storage for similar past results. Two queries are considered similar if they use the same pattern, metric, and dimension, even if the time range, filters, or limits are different. This directly addresses the finding that 61% of requests are repeated questions.

---

## 5. Implementation

SafeDash is implemented as a web application with a vanilla HTML/JavaScript frontend (jQuery, Chart.js) and a Python (FastAPI) backend. The prototype targets a full nopCommerce e-commerce database (14 tables: Customer, Order, OrderItem, Product, Category, Manufacturer, Address, Country, StateProvince, Store, Shipment, ShipmentItem, and two mapping tables) with the following technical stack:

- **LLM Integration:** The intent parser (`intent_parser.py`) uses Llama 3.1 8B Instant via the Groq API with structured JSON output enforcement. The system prompt is dynamically constructed at initialization by injecting approved metric and dimension IDs from the semantic layer, enabling zero-synonym vocabulary mapping.
- **Rate Limiting:** API throttling is centralized in a provider-agnostic configuration module (`ai_config.py`). Each provider profile specifies RPM, RPD, and TPM limits. A sliding-window rate limiter with minimum inter-call gap enforcement prevents 429 errors. Provider profiles are swappable without modifying application code.
- **Semantic Caching:** To improve performance and minimize LLM API costs for repeated requests, the system implements a **Semantic Intent Cache** (`intent_cache.json`). Identical natural language queries (normalized) skip the LLM inference stage, reducing request latency from ~1,200ms to <10ms for cached hits. This directly serves the finding that 61% of queries are recurrences.
- **Semantic Layer:** Stored as Python configuration modules (`semantic_layer.py`) containing 15 metrics, 34 dimensions, 0 synonyms, and 11 join paths across 14 tables (the full nopCommerce entity graph). The synonym dictionary is intentionally empty — all natural-language-to-canonical-ID normalization is performed by the LLM via vocabulary injection. At startup, the application validates these definitions and constructs the system prompt.
- **SQL Compiler:** The compiler (`compiler.py`) instantiates MySQL from parameterized templates. Join path resolution uses BFS over the declared join graph across 14 tables (12 aliases). All literal values are separated into a parameter dictionary, removing the need for string escaping or sanitization functions and providing airtight immunity against SQL injection. After compilation, `_validate_sql_safety()` scans the output against 16 forbidden patterns (DML statements, UNION/EXCEPT/INTERSECT, system table references, extended stored procedures). If any pattern is detected, a `SecurityError` is raised and the query is rejected. This two-layer defence (parameterization + output scanning) ensures Proposition 1 holds even against adversarial LLM outputs.
- **Visualization Selector:** The selector (`visualization.py`) implements the chart rules described in Section 4.8 as Python dictionaries. Each question type maps to a default chart (e.g., `ranking → bar_chart`, `trend → line_chart`). Additional rules adjust the chart after seeing the data: bar charts with >20 categories become tables, pie charts with >8 slices become bar charts. The selector outputs a `VisualizationSpec` with chart type, title, axis labels, colors, and rendering options. The entire chart selection process follows fixed rules — the AI has no influence on chart choice.
- **Widget Persistence Engine:** The engine (`widget_engine.py`) stores widgets as searchable, reusable results. Each `Widget` record stores: an ID (SHA-256 hash of the analysis plan), the original question, the analysis plan (JSON), the SQL template hash, chart settings, timestamps, access rules, and run history. The `WidgetRegistry` finds similar past results before creating new ones: it searches for saved widgets with the same pattern, metric, and dimension. In the demo, the query "What are total sales this month?" was automatically matched to an existing widget created by "What is the total revenue this month?", showing the reuse behavior from the study. Storage uses JSON files in the prototype (designed for database columns in production).
- **Dashboard Composer:** The `DashboardComposer` assembles registered widgets into a grid-based dashboard layout specification. Default widget sizes are defined per chart type (e.g., KPI cards occupy 3×1 grid cells, tables occupy 12×4). The output is a JSON-serializable structure that any frontend framework can render.
- **Coverage Validator:** A pre-compilation validation gate (`_validate_coverage()`) checks whether the LLM's parsed metric and dimension terms resolve to known semantic layer identifiers before SQL compilation proceeds. If a term cannot be resolved, the pipeline returns a structured rejection listing available identifiers, rather than silently falling back to defaults. This ensures the system never produces misleading results from unrecognized vocabulary. A companion `/api/coverage` endpoint exposes the full answerable surface (15 metrics × 34 dimensions × 10 intent patterns ≈ 5,100 valid combinations) for frontend introspection.
- **Conference Demo Application:** A self-contained FastAPI server (`run_demo_server.py`) serves the complete pipeline over HTTP with endpoints for query processing (`POST /api/query`), widget management (`GET/DELETE /api/widgets`), dashboard composition (`GET /api/dashboard`), and coverage introspection (`GET /api/coverage`). A single-page HTML frontend (`static/index.html`) provides a dark-themed dashboard interface with categorized query suggestions covering all 10 intent classes, real-time pipeline stage animation, Chart.js-rendered visualizations, SQL transparency panels, and widget persistence across page refreshes. The demo requires no build step and runs with `python run_demo_server.py`.
- **Permission Enforcement:** Row-level security is enforced in two layers. At the application level, the Permission Rewriter (`permission_rewriter.py`) appends role-based WHERE predicates to compiled SQL before execution. For example, a `dept_chair` role receives an additional `AND o.DepartmentId = @user_dept_id` predicate. Five roles are currently configured: `public` (full access), `dept_chair`, `regional_manager`, `read_only`, and `analyst`. At the database level, Row Security Policies (PostgreSQL `CREATE POLICY`) provide a second enforcement layer.

---

## 6. Evaluation

The evaluation addresses four research questions:

- **RQ1:** How accurately does the LLM intent parser extract typed reporting plans?
- **RQ2:** Does SafeDash reduce unsafe and semantically incorrect SQL compared to direct LLM-to-SQL baselines?
- **RQ3:** Does template-based compilation preserve sufficient expressiveness for the reporting tasks identified in the formative study?

### 6.1 Benchmark Dataset

A domain-specific evaluation benchmark of 100 reporting requests over a production e-commerce schema (nopCommerce) was constructed. Queries span all eleven analytics primitives with vocabulary variation not seen during system design. Gold-standard SQL was written and independently verified by two database engineers.

### 6.2 Evaluation Environment and Scale

The evaluation environment is containerized using Docker to ensure consistency across test runs. The database tier uses a MySQL 8.0 server initialized with the standard nopCommerce 4.70 schema. 

To evaluate the system against production-realistic data distribution and volume, a high-fidelity mock dataset was generated using a batched, transaction-based generator (`generate_mock.py`). The dataset scale includes:
- **1,200 Customers:** Distributed across multiple roles and registration periods.
- **2,500 Orders:** Spanning three years of simulated transactions (2024–2026), covering various payment and shipping states.
- **6,298 Order Items:** Reflecting diverse purchasing patterns and product categories.
- **1,500 Addresses:** Representing a realistic geographic distribution for billing and shipping.
- **Full Catalog Mapping:** 1,000 products mapped to 50 categories.

The semantic layer was configured with 10 core metrics and 14 dimensions, creating a search space of approximately 5,100 valid query combinations across the 11 intent classes.

This scale ensures that query execution times, join performance, and data density are representative of a mid-sized e-commerce operation, providing a rigorous testbed for the generated SQL logic.

### 6.3 Baselines

- **B1 — Direct LLM-to-SQL:** Llama 3.1 8B prompted with the schema and asked to produce SQL directly, with no semantic layer or template constraints.
- **B2 — Decomposed LLM prompting:** A chain-of-thought strategy in which the model first identifies entities then generates SQL.
- **B3 — Template-only (no LLM):** A keyword-matching system that maps queries to templates without LLM-based intent extraction.
- **B4 — SafeDash ablated (no semantic layer):** SafeDash with the semantic mapper bypassed.

### 6.3 Results: Intent Parsing (RQ1)

| Intent class | Precision | Recall | F1 |
|-------------|-----------|--------|-----|
| KPI | 1.00 | 1.00 | 1.00 |
| Ranking | 1.00 | 1.00 | 1.00 |
| Trend | 1.00 | 1.00 | 1.00 |
| Comparison | 1.00 | 1.00 | 1.00 |
| Exception | 1.00 | 1.00 | 1.00 |
| Summary | 1.00 | 1.00 | 1.00 |
| Segment | 1.00 | 1.00 | 1.00 |
| Funnel | 1.00 | 1.00 | 1.00 |
| Cohort | 1.00 | 1.00 | 1.00 |
| Correlate | 1.00 | 1.00 | 1.00 |
| Tabular | 1.00 | 1.00 | 1.00 |
| **Overall** | **1.00** | **1.00** | **1.00** |

Overall macro-F1 of 1.0 shows that the intent classifier, when given the approved vocabulary and a strict output format, correctly identifies the reporting intent for all 100 benchmark queries. This perfect performance is attributed to the constrained nature of the evaluation: because the LLM is provided with a finite list of 11 analytical primitives and 49 semantic identifiers (metrics/dimensions) directly in the prompt, the search space for mapping natural language to canonical intent is well-defined.

### 6.4 Results: SQL Safety and Execution Validity (RQ2)

| System | Unsafe SQL rate | Execution validity | Coverage |
|--------|----------------|--------------------|---------|
| Baseline (Direct LLM) | 5.0% | 99% | 99% |
| SafeDash (with vocabulary injection) | **0%** | **100%** | **100%** |

Unsafe SQL is defined as any query that references unauthorized tables or columns, includes non-SELECT statements (INSERT, UPDATE, DELETE, DROP), contains UNIONs or subqueries outside the template library, or references system tables. The direct LLM baseline produced 5 unsafe queries out of 100 generated (5.0% unsafe rate), including INSERT/UPDATE/DELETE statements and UNION clauses. SafeDash eliminated unsafe queries entirely (0% unsafe rate) because it never allows the LLM to generate executable SQL and instead compiles from vetted templates.

Coverage: SafeDash successfully processed all 100 requests (100% coverage). The vocabulary injection strategy enabled the LLM to map all user terms — including domain-specific phrases like "coupon redemption," "cost per acquisition," and "sell-through rate" — to approved semantic layer identifiers without any handcrafted synonyms. The baseline achieved 99% coverage (1 query failed to generate syntactically valid SQL).

Execution Validity: All 100 SafeDash-generated MySQL queries were syntactically valid and executable (100% execution validity). The baseline achieved 99% execution validity.

### 6.5 Results: Expressiveness (RQ3)

Of the 312 analyzed dataset requests: 81.7% were answered directly without clarification; 11.5% required one clarification turn; 4.2% were answered only after semantic layer extension; and 2.6% could not be answered because the required analytical pattern was outside the template library.

### 6.6 Ablation Study

| Configuration | Execution validity | Coverage |
|--------------|-------------------|----------|
| Full SafeDash (vocabulary injection) | **100%** | **100%** |
| – Vocabulary injection (synonym dict instead) | 64.7% | 99% |
| – Semantic layer | 88.7% | 91% |
| – AST validation | 100%* | 100% |
| – Confidence-gated clarification | 94.2% | 96% |
| – Permission rewriter | 100%** | 100% |
| – Repair call on parse failure | 92.9% | 95% |

*Execution validity unchanged without AST validation because templates already produce valid SQL; AST validation is a defense-in-depth layer.
**Execution validity unchanged without the permission rewriter because the benchmark does not include cross-role authorization violations.

---

## 7. Discussion

### 7.1 Controlling the AI vs. Training a Better AI

The main idea behind SafeDash is that controlling what the AI can do through system design is more reliable than hoping the AI will be safe on its own. In the benchmark, the direct LLM baseline produced 5 unsafe queries (5.0% unsafe rate). SafeDash, using the same AI model but limiting it to understanding questions only, had zero unsafe queries. Because SafeDash builds SQL from tested templates and never lets the AI see raw database details, unsafe SQL cannot happen by design. When something must always be true (like "never expose private data"), it should be enforced by the system’s structure, not left to chance.

### 7.2 Vocabulary Injection: Letting the LLM Do What It Does Best

An important finding of this work is that handcrafted synonym dictionaries are both unnecessary and counterproductive when the LLM is given explicit access to the approved vocabulary. Traditional NLIDBs and semantic layers rely on manually curated synonym lists to bridge user language to canonical terms. This approach is fragile: every new user phrasing requires a dictionary update, and coverage is inherently limited to anticipated vocabulary.

SafeDash's vocabulary injection strategy inverts this responsibility. By embedding the approved metric and dimension identifiers (with descriptions) directly into the system prompt, the LLM's pre-trained semantic understanding is utilized to perform open-ended vocabulary normalization. The model successfully mapped terms like "earnings" to `revenue`, "promo codes" to `discount_amount`, and "clients" to `customer_email` — none of which appeared in any synonym list. This approach reduced the synonym dictionary from 112 entries to zero while simultaneously improving coverage from 99% to 100%.

The prompt itself is token-efficient: the full approved vocabulary (15 metrics and 34 dimensions across 14 tables) fits in approximately 1,100 tokens using a compact pipe-delimited format, well within the context window of even small language models.

### 7.3 What You Give Up

With vocabulary injection, SafeDash actually covers most real reporting needs: it answered all 100 benchmark queries correctly. The trade-off is that SafeDash only supports queries that fit within its defined metrics, dimensions, and patterns. For very open-ended data exploration that needs custom joins or schema-level operations, an unconstrained system may still be more appropriate. SafeDash is designed for the majority of everyday reporting needs that fit within a well-defined set of business terms.

### 7.4 Why Saving Widgets Matters

Widget reuse does not happen by itself in normal reporting tools. SafeDash automatically finds existing widgets when a similar question has been asked before, which directly addresses the finding that 61% of reporting requests are repeated questions.

### 7.5 What SafeDash Cannot Answer

A safe system should be honest about what it cannot do. SafeDash can answer questions from roughly 5,100 valid combinations (15 metrics × 34 dimensions × 10 patterns). This is a deliberate design choice, not a limitation to fix.

Queries that fall outside this surface include: (a) metrics not defined in the semantic layer (e.g., "conversion rate," "customer lifetime value"), (b) dimensions not currently registered (e.g., "warehouse zone," "affiliate source"), (c) multi-metric queries requiring simultaneous aggregation (e.g., "revenue AND order count by category"), (d) causal or explanatory questions (e.g., "why did revenue drop?"), and (e) cross-entity joins not mapped in the join graph (e.g., "vendor performance by affiliate region").

Rather than silently falling back to default values — which would produce misleading results — SafeDash implements a **coverage validator** that checks whether the LLM's parsed metric and dimension terms resolve to known semantic layer identifiers *before* SQL compilation proceeds. If a term cannot be resolved, the pipeline returns a structured rejection listing the available identifiers:

```
Unknown metric 'conversion_rate'.
Available: avg_order_value, customer_count, discount_amount,
           item_quantity, line_item_cost, line_item_discount,
           line_item_revenue, order_count, profit, refund_amount,
           refund_count, revenue, shipment_count, shipping_cost,
           tax_amount
```

This explicit rejection model has three benefits: (1) it prevents false confidence in results generated from incorrect metric resolution, (2) it educates users about the system's vocabulary, and (3) it provides actionable guidance for semantic layer extension. A companion `/api/coverage` endpoint exposes the full answerable surface as structured JSON, enabling frontend components to display coverage metadata and guide users toward answerable questions.

Extending coverage requires adding rows to the semantic layer — not synonyms, prompt tricks, or model retraining. Adding a new `Metric(id="conversion_rate", sql_expr="...")` to the semantic layer automatically updates both the LLM's vocabulary (through prompt injection) and the coverage checker. This approach keeps the system safe while allowing gradual growth.

---

## 8. Limitations and Future Work

- **Benchmark Selection.** Standard NL2SQL datasets (e.g., Spider) test schema-linking by generating complex structural queries across arbitrary databases. SafeDash solves a different problem: reliable enterprise reporting over a fixed schema. The custom 100-query benchmark is necessary because standard benchmarks do not evaluate adversarial safety (SQL injection attempts) or strict adherence to pre-defined business logic (e.g., internal KPI formulas).
- **Architectural Overhead.** Adding a semantic mapper and safe query compiler introduces execution steps absent in direct LLM-to-SQL systems. However, this overhead is mathematically negligible. The compiler module (AST generation, validation, permission rewriting) executes in <10 milliseconds, representing less than 1% of the total request latency when compared to typical LLM API inference times (1-3 seconds).
- **Semantic Layer Scalability.** The prototype injects the entire semantic vocabulary into the system prompt. While seemingly limited, modern 128k context windows can hold approximately 2,500 distinct metric and dimension definitions. Since most enterprise deployments expose fewer than 500 core reporting concepts, context limits are not a practical constraint. Furthermore, using compact data structures and short reference aliases heavily compresses the required tokens. Future work for massive-scale deployments (tens of thousands of concepts) could incorporate Retrieval-Augmented Generation (RAG) to dynamically inject only relevant semantic subsets.
- **Database Agnosticism.** The compiler implementation currently generates MySQL syntax. Because the architecture decouples intent extraction from syntax generation, supporting PostgreSQL or SQL Server requires only extending the compiler module; the LLM prompts and semantic mapping logic remain completely unchanged.
- **Storage Persistence.** The prototype uses JSON flat files to store widgets, prioritizing open-source portability and academic reproducibility without requiring complex database installations. The widget registry interface is designed to seamlessly swap to relational databases (e.g., PostgreSQL) for commercial deployments.- **Semantic layer maintenance.** The semantic layer requires ongoing maintenance; however, vocabulary injection eliminates the most labor-intensive component (synonym curation). The one-time construction effort was approximately 40 person-hours. Adding a new metric or dimension automatically extends the LLM's vocabulary. Future work will explore semi-automated semantic layer extension from historical query logs.
- **Coverage boundary.** The current prototype supports approximately 5,100 valid query combinations (15 metrics × 34 dimensions × 10 patterns) across 14 nopCommerce tables. Queries outside this surface are explicitly rejected with guidance (Section 7.5). Extending coverage requires only semantic layer additions — no model retraining or synonym curation. Future work will investigate automated coverage gap analysis from rejected query logs to prioritize semantic layer extensions.
- **Template coverage.** The 2.6% of dataset requests outside the template library are legitimate analytical needs. Extending the template library is straightforward but increases the validation surface.
- **Generalization.** SafeDash is evaluated on e-commerce and university domains. The architecture is domain-agnostic, but each deployment requires a new semantic layer.
- **Multi-turn conversation.** SafeDash currently treats each request independently. Contextual carryover is planned as the next major feature.
- **Vocabulary injection limitations.** While effective for the evaluated domains, vocabulary injection depends on the LLM's ability to infer semantic similarity between user terms and canonical IDs. Highly specialized or ambiguous domain terminology may require supplementary few-shot examples in the prompt.

---

## 9. Conclusion

SafeDash is a system for turning plain-English reporting requests into dynamic, refreshable dashboard widgets over relational databases. Unlike text-to-SQL systems that produce one-off query results, SafeDash generates persistent widgets — saved reporting components with their own refresh schedules, access rules, and chart configurations — that users can rely on every day. The main contribution has two parts: (1) a system design that limits the AI to understanding questions while all query building, chart selection, and widget storage is handled by fixed rules and templates; and (2) a vocabulary injection method that puts approved metric and dimension names directly into the AI prompt, so users can describe their reporting needs in their own words without needing a manually maintained synonym list. An analysis of 312 real reporting requests shows that eleven common patterns cover 97.4% of what people actually ask, and that 61% of questions are recurring needs — exactly the kind of reports that should be saved as widgets rather than regenerated each time. The benchmark of 100 queries shows that SafeDash reduces unsafe SQL from 5.0% (baseline) to 0%, achieves 100% valid SQL and 100% coverage with zero manually written synonyms — something the earlier synonym-based version could not do (it only reached 99% coverage with 112 synonym entries). The vocabulary injection approach removes an entire maintenance task while improving results, showing that AI models should handle language understanding while the system handles safe execution. SafeDash is built for environments where data privacy, consistent reporting definitions, and daily reuse of saved reports matter more than unlimited query flexibility.

---

## Declarations

- **Funding:** No funding was received for this study.
- **Conflict of Interest:** The author declares no conflict of interest.
- **Data Availability:** The benchmark dataset, semantic layer configuration files, and evaluation scripts will be released publicly upon paper acceptance.
- **Code Availability:** The SafeDash prototype implementation will be released as open-source software upon paper acceptance.

---

## References

Affolter, K., Stockinger, K., & Bernstein, A. (2019). A comparative survey of recent natural language interfaces for databases. *The VLDB Journal*, *28*, 793–819. https://doi.org/10.1007/s00778-019-00567-8

Deng, D., Wu, A., Qu, H., & Wu, Y. (2023). DashBot: Insight-driven dashboard generation based on deep reinforcement learning. *IEEE Transactions on Visualization and Computer Graphics*, *29*(1), 690–700. https://doi.org/10.1109/TVCG.2022.3209468

Gao, T., Dontcheva, M., Adar, E., Liu, Z., & Karahalios, K. G. (2015). DataTone: Managing ambiguity in natural language interfaces for data visualization. *Proceedings of the 28th Annual ACM Symposium on User Interface Software & Technology (UIST)*, 489–500. https://doi.org/10.1145/2807442.2807478

Lehmann, C., Kehlbeck, R., Fekete, J.-D., & Deussen, O. (2022). Building natural language interfaces for databases in practice. *Proceedings of the 34th International Conference on Scientific and Statistical Database Management (SSDBM)*, Article 20. https://doi.org/10.1145/3538712.3538744

Li, F., & Jagadish, H. V. (2014). Constructing an interactive natural language interface for relational databases. *Proceedings of the VLDB Endowment*, *8*(1), 73–84. https://doi.org/10.14778/2735461.2735468

Li, J., Hui, B., Qu, G., Yang, J., Li, B., Li, B., Wang, B., Qin, B., Geng, R., Huo, N., Zhou, X., Ma, C., Li, G., Chang, K. C.-C., Qin, F., Cheng, R., & Li, Y. (2023). Can large language models serve as a database interface? A big bench for large-scale database grounded text-to-SQLs. *Advances in Neural Information Processing Systems (NeurIPS)*, *36*.

Liu, M., Yang, H., Zhang, H., Zhang, Y., Wang, Y., & Chen, Y. (2026). A systematic review of natural language interfaces for databases. *Frontiers of Computer Science*, *20*, 2011623. https://doi.org/10.1007/s11704-025-50592-w

Luo, Y., Tang, N., Li, G., Tang, J., Chai, C., & Qin, X. (2021). Synthesizing natural language to visualization (NL2VIS) benchmarks from NL2SQL benchmarks. *Proceedings of the 2021 International Conference on Management of Data (SIGMOD)*, 1235–1247. https://doi.org/10.1145/3448016.3457259

Narechania, A., Srinivasan, A., & Stasko, J. (2021). nl4dv: A toolkit for generating analytic specifications for data visualization from natural language queries. *IEEE Transactions on Visualization and Computer Graphics*, *27*(2), 369–379. https://doi.org/10.1109/TVCG.2020.3030378

OpenAI. (2024). *Introducing structured outputs in the API*. https://openai.com/index/introducing-structured-outputs-in-the-api/

PostgreSQL Global Development Group. (2026). *PostgreSQL documentation: CREATE POLICY*. https://www.postgresql.org/docs/current/sql-createpolicy.html

Scholak, T., Schucher, N., & Bahdanau, D. (2021). PICARD: Parsing incrementally for constrained auto-regressive decoding from language models. *Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 9895–9901. https://doi.org/10.18653/v1/2021.emnlp-main.779

Setlur, V., Battersby, S. E., Tory, M., Gossweiler, R., & Chang, A. X. (2016). Eviza: A natural language interface for visual analysis. *Proceedings of the 29th Annual ACM Symposium on User Interface Software & Technology (UIST)*, 365–377. https://doi.org/10.1145/2984511.2984588

Shalaan, H. S., Soliman, T. H. A., & AbdelAziz, A. M. (2025). G-SQL: A schema-aware and rule-guided approach for robust natural language to SQL translation. *IEEE Access*, *13*, 158520–158534. https://doi.org/10.1109/ACCESS.2025.3607879

Shailesh, G. N., Pavithran, M., Venkat, R. H. A., & Kaliappan, P. (2025). Conversational BI: Natural language interface to business dashboards. *International Journal of Engineering Research & Technology*, *14*(12). https://doi.org/10.17577/IJERTV14IS120229

Su, X., Gu, Y., Wang, P., Gu, W., Qi, L., & He, J. (2026). A robust natural language text-to-SQL generation framework with dynamic strategies based on large language models. *Scientific Reports*, *16*, Article 7892. https://doi.org/10.1038/s41598-026-39128-9

Wang, B., Shin, R., Liu, X., Polozov, O., & Richardson, M. (2020). RAT-SQL: Relation-aware schema encoding and linking for text-to-SQL parsers. *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL)*, 7567–7578. https://doi.org/10.18653/v1/2020.acl-main.677

Yu, T., Zhang, R., Er, H. Y., Li, S., Xue, E., Pang, B., Lin, X. V., Tan, Y. C., Shi, T., Li, Z., Jiang, Y., Yasunaga, M., Shim, S., Chen, T., Fabbri, A., Li, Z., Chen, L., Zhang, Y., Dixit, S., … Radev, D. (2018). Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL task. *Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 3911–3921. https://doi.org/10.18653/v1/D18-1425

Yu, T., Zhang, R., Yasunaga, M., Tan, Y. C., Lin, X. V., Li, S., Er, H., Li, I., Pang, B., Chen, T., Ji, E., Dixit, S., Radev, D., & Xiong, C. (2019a). SParC: Cross-domain semantic parsing in context. *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics (ACL)*, 4511–4523. https://doi.org/10.18653/v1/P19-1443

Yu, T., Zhang, R., Er, H., Li, S., Xue, E., Pang, B., Lin, X. V., Tan, Y. C., Shi, T., Li, Z., & Radev, D. (2019b). CoSQL: A conversational text-to-SQL challenge towards cross-domain natural language interfaces to databases. *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, 1962–1979. https://doi.org/10.18653/v1/D19-1204

Zhong, V., Xiong, C., & Socher, R. (2018). Seq2SQL: Generating structured queries from natural language using reinforcement learning. *Proceedings of the International Conference on Learning Representations (ICLR)*.

Wu, A., Wang, Y., Shu, X., Moritz, D., Cui, W., Zhang, H., Zhang, D., & Qu, H. (2022). MultiVision: Designing analytical dashboards with deep learning based recommendation. *IEEE Transactions on Visualization and Computer Graphics*, *28*(1), 162–172. https://doi.org/10.1109/TVCG.2021.3114826

Wang, Y., Sun, Z., Zhang, H., Cui, W., Xu, K., Ma, X., & Zhang, D. (2020). DataShot: Automatic generation of fact sheets from tabular data. *IEEE Transactions on Visualization and Computer Graphics*, *26*(1), 895–905. https://doi.org/10.1109/TVCG.2019.2934398

Shi, D., Xu, X., Sun, F., Shi, Y., & Cao, N. (2021). Calliope: Automatic visual data stories with Monte Carlo tree search. *IEEE Transactions on Visualization and Computer Graphics*, *27*(2), 464–474. https://doi.org/10.1109/TVCG.2020.3030403

