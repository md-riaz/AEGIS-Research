# AEGIS: A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics

**Md. Riaz**
Pundra University of Science and Technology, Bogura, Bangladesh

---

## Abstract

Analytical dashboards are important tools for business reporting, but building accurate and safe reports from relational databases still requires technical skills. Natural language interfaces try to close this gap, but current text-to-SQL systems focus on benchmark accuracy rather than real-world safety, and they stop at generating a one-time query result without producing reusable reporting widgets. This research presents AEGIS, a system that turns plain-English reporting requests into dynamic, refreshable dashboard widgets that users can save and reuse every day. Unlike traditional NL-to-SQL systems that treat each question as a one-off interaction, AEGIS produces persistent reporting widgets — each with its own refresh schedule, access rules, and visual configuration — that become part of a user's daily workflow. AEGIS uses a strictly controlled pipeline: (1) a lightweight LLM (Llama 3.1 8B) maps natural language to one of eleven high-level analytical primitives (e.g., KPI, Trend, Ranking, Tabular) using dynamic vocabulary injection, (2) a deterministic compiler builds the SQL using pre-approved parameterized templates, and (3) a post-compilation security monitor validates the statement against a strict safety grammar. Evaluation over a 107-request benchmark in a real e-commerce domain (nopCommerce), stratified into 55 answerable requests and 52 that should be declined, shows that the system reproduces all twenty of the platform's standard admin reports from natural language while declining every out-of-scope request (abstention recall 100%, false-abstention rate 25.5%), together with structural prevention of SQL injection through untrusted natural-language input—a guarantee that holds within the defined threat boundary of trusted semantic-layer definitions and administrator-controlled compiler templates. Successive fixes moved the false-abstention rate from 61.8% to 25.5% while abstention recall held at 100%, with no change to the architecture — evidence that semantic accuracy in this design is an implementation and configuration property rather than an architectural one. AEGIS demonstrates that restricting SQL generation to a finite set of validated business patterns is a practical path to safe, auditable natural-language reporting in institutional environments.

**Index Terms:** Natural language interfaces, dashboard generation, text-to-SQL, semantic layer, visualization recommendation, business intelligence, self-service analytics.

---

## 1. Introduction

Relational databases store critical institutional data in organizations — financial records, customer accounts, sales transactions, and more. But accessing this data is uneven: technical staff can write SQL queries to get any answer they need, while non-technical users have to wait for someone else to build them a report. This waiting is expensive. Analysis of enterprise reporting workflows shows that business users frequently wait days for new reports, and a recurring theme in institutional reporting is that many questions are variations of things already asked before — the same report with a different date range, or the same chart for a different department. These aren't one-off questions; they are recurring reporting needs that should be served by saved, refreshable widgets. This research presents **AEGIS** (Analytics Engine with Guaranteed Injection Safety). It's a system that lets users describe their reporting needs in plain English and produces dynamic dashboard widgets that can be saved, refreshed, and reused as part of their daily workflow — without anyone writing SQL.

Natural language interfaces to databases (NLIDBs) try to solve this problem. The idea is simple: a user should be able to ask "which categories have the highest refund rates this month?" and get a correct, visual answer without writing SQL. Researchers have made good progress here. Neural text-to-SQL systems now get over 90% accuracy on the Spider benchmark (Yu et al., 2018). Large language models (LLMs) can also produce reasonable-looking SQL with minimal setup (Li et al., 2023). But there is still a gap between benchmark results and real-world use.

Three problems make up this gap. First, **safety**: many modern NL-to-SQL systems rely on models that directly generate SQL tokens, which creates challenges for enforcing enterprise governance and security policies — an LLM generating SQL freely can produce queries that expose private data or use wrong table joins. **Vocabulary mismatch**: benchmarks use actual column names in the questions, but real users speak in business terms ("refund rate" instead of `SUM(o.RefundedAmount)`). Matching these requires business knowledge that models don't always get right. Third, **no widget generation**: existing systems answer one question at a time and throw away the result. They don't produce saved reporting widgets that can be refreshed with new data tomorrow, shared with a colleague, or added to a daily dashboard. Every time someone needs the same report, they have to start from scratch.

These problems aren't about building a smarter AI — they're about designing the system properly around the AI. AEGIS does this by splitting the work into stages. The LLM's only job is to understand what the user is asking and output a structured description of the request. Everything after that — matching to the right business terms, building the SQL, picking the chart, saving the widget — is done by fixed rules and pre-approved templates.

**Research novelty.** Existing text-to-SQL research asks: *"how accurately can a model generate SQL from natural language?"* AEGIS asks a different question: *"how can we use LLMs for language understanding while preventing them from generating executable SQL entirely?"* The pipeline differs structurally:

**Classical NL2SQL:** Natural Language → SQL generation → Query result.

**AEGIS:** Natural Language → Intent extraction → Semantic constraint → Deterministic compilation → Safe analytical artifact.

The contribution is therefore not improved SQL generation accuracy; it is *constrained analytical artifact generation* — a design approach that removes SQL generation from the LLM's role entirely and provides safety and semantic fidelity guarantees that no generative model can match unconditionally.

**Model independence.** AEGIS does not propose a new LLM. The LLM is interchangeable: Groq (Llama 3.1 8B), OpenRouter, local Ollama, or any `/v1/chat/completions`-compatible endpoint. Because the LLM's only contract with the rest of the system is to produce a typed JSON intent object, model upgrades improve quality automatically without changing the compiler or safety infrastructure.

This paper makes the following contributions:

1. A design-time review of representative e-commerce and BI reporting requests, resulting in eleven common reporting patterns validated against a published 100-query benchmark (Section 3).
2. A system design where all possible queries are limited to pre-approved templates and a defined semantic layer, which prevents SQL injection and unauthorized data access by construction (Section 4).
3. The AEGIS system, including the semantic layer design, a vocabulary injection prompt strategy, a safe SQL builder with two-layer defence, a rule-based chart selector, and a widget storage system with scheduled refresh (Sections 4–5).
4. A vocabulary injection method that puts the approved metric and dimension names directly into the LLM prompt, removing the need for a manually written synonym list — the prototype's 112-entry synonym dictionary was deleted outright, and the wordings it had enumerated by hand are now resolved by the model against the injected vocabulary (Section 4.5).
5. A two-part evaluation: coverage against the host platform's own report suite (all twenty standard nopCommerce admin reports reproduced from natural language), and boundary behaviour on a 107-request benchmark stratified into answerable and should-decline strata (Section 6).
6. An abstention-aware evaluation method that measures a system's refusal channel — abstention recall reported always beside false-abstention rate, since the first alone is trivially gamed by refusing everything. No system in the comparison of Section 2.6 measures this (Section 6).
7. A demonstration that the residual accuracy gap is a configuration boundary rather than an architectural one: the semantic layer exposed 12 of the schema's 126 tables, and extending it to 17 moved the false-abstention rate from 40.0% to 25.5% with no code change to the compiler or the safety layer (Section 6).

---

## 2. Related Work

### 2.1 Natural Language Interfaces to Databases

Natural language database interfaces have been studied for over four decades. Early systems such as LUNAR (Woods, 1973) and TEAM (Grosz, 1983) used hand-crafted grammars and domain-specific ontologies to parse queries. These systems were brittle under vocabulary variation but established the core insight that query understanding requires a bridge between natural language and schema semantics.

NaLIR (Li & Jagadish, 2014) is an important modern NLIDB because it treats ambiguity as a real problem to solve rather than an error. By showing users different possible interpretations of their question, NaLIR improves accuracy but requires the user to actively participate. AEGIS uses a similar approach — asking for clarification when the meaning is unclear — but extends it into a full widget lifecycle that NaLIR doesn't cover. Survey work (Affolter et al., 2019; Liu et al., 2026) confirms that ambiguity, portability, schema complexity, and controlled access remain ongoing challenges across NLIDB generations and are not solved by bigger models alone.

### 2.2 Neural Text-to-SQL and Benchmark Progress

The field shifted decisively toward neural approaches with Seq2SQL and WikiSQL (Zhong et al., 2018), which showed that aligned training data could teach models to produce SQL. Spider (Yu et al., 2018) advanced the challenge significantly by introducing cross-domain schemas and complex multi-table queries, becoming the standard benchmark. SParC and CoSQL (Yu et al., 2019) extended the evaluation to conversational and contextual settings. BIRD (Li et al., 2023) brought benchmark queries closer to production conditions by emphasizing large databases, value grounding, and query efficiency.

Schema-aware encoding, introduced in RAT-SQL (Wang et al., 2020), showed that explicitly modeling schema relationships improves accuracy on new databases. Constrained decoding approaches such as PICARD (Scholak et al., 2021) showed that rejecting invalid SQL tokens during generation improves results. More recent systems like G-SQL (Shalaan et al., 2025) and TriSQL (Su et al., 2026) add rule guidance and multi-stage checking. While these are impressive within the text-to-SQL area, they all focus on SQL generation quality and do not address safe data access, permission control, widget storage, or chart selection — which is what AEGIS focuses on.

### 2.3 Natural Language for Visualization

A parallel research stream focuses on NL-driven chart generation rather than SQL generation. nl4dv (Narechania et al., 2021) maps natural language queries to analytic tasks and visual encodings. nvBench (Luo et al., 2021) introduced a cross-domain benchmark for NL-to-visualization. Eviza (Setlur et al., 2016) enabled conversational interaction with existing visualizations. DataTone (Gao et al., 2015) managed ambiguity in NL visualization interfaces through mixed-initiative interaction, surfacing alternative chart interpretations to users — a concept AEGIS adopts in its clarification model.

### 2.4 Dashboard Generation

Dashboard generation as an automated design problem has attracted growing attention. DashBot (Deng et al., 2023) proposed using deep reinforcement learning to compose dashboards from a set of data insights. MultiVision (Wu et al., 2022) used bidirectional LSTM models to score individual charts and combine them into multi-view dashboards. DataShot (Wang et al., 2020) and Calliope (Shi et al., 2021) used statistical fact extraction followed by template-based layout to generate narrative data documents.

### 2.5 Semantic Layers and Controlled Analytics

A semantic layer is a business-logic abstraction that maps business concepts to the actual database tables and columns. Commercial tools like dbt Metrics, Looker LookML, and Apache Superset implement semantic layers in different ways. Lehmann et al. (2022) stress the importance of controlled data access in practical NL database interfaces. Structured output enforcement for LLMs (OpenAI, 2024) has been shown to improve the reliability of typed object generation, which AEGIS uses for intent extraction. No prior work uses a semantic layer as the main safety mechanism for an LLM-assisted reporting system.

### 2.6 Comparative Summary

| System | NL Parsing | Semantic Layer | Safe SQL | Visualization | Widget Persistence | Coverage Validation | Production Evaluation |
|--------|:----------:|:--------------:|:--------:|:-------------:|:------------------:|:-------------------:|:--------------------:|
| Spider / BIRD (Yu '18; Li '23) | ✓ | — | — | — | — | — | Benchmark only |
| Seq2SQL (Zhong '18) | ✓ | — | — | — | — | — | Benchmark only |
| RAT-SQL (Wang '20) | ✓ | — | — | — | — | — | Benchmark only |
| PICARD (Scholak '21) | ✓ | — | Partial | — | — | — | Benchmark only |
| NaLIR (Li '14) | ✓ | — | — | — | — | — | Benchmark only |
| nl4dv (Narechania '21) | ✓ | — | — | ✓ | — | — | In-memory data |
| DashBot (Deng '23) | — | — | — | ✓ | Partial | — | Synthetic data |
| Lehmann et al. (2022) | — | ✓ | — | — | — | — | Position paper |
| **AEGIS (this work)** | **✓** | **✓** | **✓** | **✓** | **✓** | **✓** | **Production (nopCommerce)** |

---

## 3. Analysis of Reporting Patterns

### 3.1 Dataset

The eleven analytics primitives below were identified through a review of representative natural-language reporting requests conducted by the author during system design, covering typical e-commerce and administrative reporting workflows. This was a design-time review, not an independently annotated, inter-rater-validated study, and no separate annotated dataset accompanies this thesis; the percentages once reported here for a 312-request dataset were not backed by a corresponding published dataset and have been withdrawn. In their place, Table 1 below reports a pattern classification of the actual, published 100-query benchmark (`evaluation_dataset/questions.json`, Section 6.1): every one of the 100 real benchmark questions was individually classified into one of the eleven patterns by the author. This is a single-annotator classification, not independently cross-checked by a second annotator, but it is reproducible and checkable, since the classification of each question is published in `evaluation_dataset/pattern_classification.json` alongside the script (`classify_patterns.py`) that generates it from the question text.

**Table 1: Pattern classification of the 100-query benchmark.**

| Pattern | Count (of 100) | Share |
|---|---|---|
| KPI / Aggregate | 28 | 28% |
| Ranking | 21 | 21% |
| Exception / Filter | 18 | 18% |
| Trend Analysis | 10 | 10% |
| Comparison | 10 | 10% |
| Summary / Group | 9 | 9% |
| Cohort | 2 | 2% |
| Funnel | 1 | 1% |
| Correlate | 1 | 1% |
| Segment | 0 | 0% |
| Tabular | 0 | 0% |

The top three patterns (KPI, Ranking, Exception/Filter) account for 67% of this benchmark. Segment and Tabular are not exercised by this particular 100-question sample; this is a property of the benchmark, not evidence that those two patterns are unnecessary — the compiler supports both regardless.

**A correction to the benchmark's composition.** The dataset README, and earlier statements in this thesis, describe the full evaluation set as "100 in-scope reporting requests plus 7 deliberately out-of-scope probes" — implying that the 100 queries classified in Table 1 were all constructed to be answerable, with only the final 7 queries testing the system's boundary. Counting the `expected_behavior` field in `evaluation_dataset/semantic_correctness_annotations.json`, which records the intended outcome for all 107 queries, shows this description is not accurate. Of the 100 queries classified in Table 1, only 54 carry an `expected_behavior` of `answer`; the remaining 46 are labelled `clarify_or_reject`, meaning the correct system response to them is to decline or ask for clarification, not to produce a result. Taking the full 107-query set together with the 7 boundary probes (one further answerable multi-part request, five queries that should be declined, and one disguised write request that must be refused) gives a benchmark-wide split of 55 queries that should be answered and 52 that should be declined — close to an even split, not the 100-versus-7 split the earlier description implies. This matters for how the results in Section 6 should be read: a benchmark constructed so that nearly every question is answerable would make a near-100% success rate true by construction rather than a finding about the system. The actual composition is considerably more demanding than that, which strengthens the evaluation rather than weakening it. Table 1's pattern classification is unaffected by this correction: it classifies all 100 queries by reporting pattern (KPI, Ranking, and so on) independently of whether the correct response to each is to answer or to decline.

### 3.2 Request Taxonomy

- **KPI / Aggregate:** Single scalar fact. Example: "How many orders were placed today?"
- **Ranking:** Ordered comparisons across a dimension. Example: "Which five categories have the highest refund rates?"
- **Trend Analysis:** Metric change over time. Example: "Show monthly sales volume over the last year."
- **Comparison:** Metric across groups. Example: "Compare average order value between mobile and desktop users."
- **Exception / Filter:** Records violating a threshold. Example: "List products with stock levels below 10."
- **Summary / Group:** Combined view of multiple metrics. Example: "Give me an overview of Electronics category."
- **Segment:** Breakdown across a categorical dimension. Example: "Revenue by product category."
- **Funnel:** Conversion stage analysis. Example: "Cart to purchase conversion rate."
- **Cohort:** Behavioral group analysis. Example: "New vs. returning customer metrics."
- **Correlate:** Attribute relationship. Example: "Which attributes correlate with higher margins?"
- **Tabular:** Raw record listings. Example: "Show all orders from last week."

Table 1 confirms, on the actual benchmark, the same qualitative ordering observed during the design-time review: KPI/Aggregate, Ranking, and Exception/Filter style questions occur most frequently; Cohort, Funnel, and Correlate occur least frequently.

![Pattern Classification of the 100-Query Benchmark](../assets/images/fig_pattern_distribution.png)
*Figure 5: Pattern classification of the 100-query benchmark (author-classified against `evaluation_dataset/questions.json`; see `pattern_classification.json` for per-question labels). KPI/Aggregate (28%), Ranking (21%), and Exception/Filter (18%) account for 67% of the benchmark.*

### 3.3 Design Implications

This review and classification give three clear design directions. First, a small set of patterns appears sufficient: on the 100-query benchmark, the top three patterns already account for 67% of all questions, and all eleven patterns together account for 100%, supporting a fixed template library. Second, business vocabulary differs from database column names: users said "total refund rate," not `SUM(o.RefundedAmount)` — an explicit business vocabulary is needed. Third, reuse appears to be the norm rather than the exception: many requests were variations of things already asked before, motivating widget persistence as a core design goal rather than an optional feature.

---

## 4. The AEGIS System

### 4.1 Design Principles

1. **Separate understanding from execution.** The LLM understands the question; fixed rules handle everything else.
2. **Define business terms clearly.** Metrics, dimensions, joins, and time rules are written in a semantic layer.
3. **Limit what SQL can be generated.** SQL is built only from pre-approved templates.
4. **Pick charts by rules.** Chart type is decided by question type, result shape, and design best practices.
5. **Save results for reuse.** Each query produces a saved, refreshable widget.

### 4.2 Formal Model

Let a user with role r issue a natural-language request q. Classical text-to-SQL seeks a total function f(q,S) → sql, defined on every input. AEGIS instead seeks a *partial* function over three terminal outcomes:

> g(q, L, r) → ⟨o, π, sql, vis, w⟩, where o ∈ {ANSWER, CLARIFY, REJECT}

g is total in o but partial in the remaining outputs: only when o = ANSWER are π (a canonical analysis plan), sql (a read-only compiled query), vis (a visualization specification), and w (a persisted widget artifact) all defined. When o = CLARIFY, g returns instead a single concrete question and the candidate bindings that motivated it, drawn from the grounding and coverage stages described in §4.6–§4.7; nothing downstream of that point is computed. When o = REJECT, g returns a reason and, where applicable, the residual concepts the vocabulary could not account for. A reasoned non-answer is therefore a valid output of g, not a failure of it: the pipeline is required to say which of the three outcomes it reached, and silently defaulting to ANSWER when the evidence does not support it is precisely the failure mode this formulation rules out. The semantic layer L = ⟨M, D, F, J, P, V, A, R⟩ defines the approved metric set M, dimension set D, filter/time-rule set F, join graph J, pattern library P, visualization policy V, vocabulary injection configuration A, and role-permission model R.

Safety is enforced as a set membership constraint on the ANSWER branch: sql ∈ Q_safe(L, r), where Q_safe(L,r) is the family of queries derivable from pattern templates in P using only bindings from L permitted under role r.

**Proposition 1.** No query in Q_safe(L,r) can reference a table, column, or row not enumerated in L for role r. All SQL identifiers are drawn from a closed vocabulary of approved semantic bindings. All literal values are passed using parameterized SQL rather than string interpolation. SQL injection *through untrusted natural-language input* is structurally prevented by design.

Temporal predicates are subject to the same constraint by a separate mechanism: the SQL fragment for a time range is never built from user text but selected from a closed grammar of fixed templates (§4.8), so admitting time expressions into the pipeline adds no new interpolation surface and Proposition 1 continues to hold unchanged.

**Security boundary.** This guarantee holds within the defined threat boundary: the semantic layer definitions, compiler templates, and permission predicates are trusted administrator-controlled artifacts. An administrator who embeds malicious SQL inside a metric definition, or a supply-chain compromise of the compiler library, are outside this boundary and require separate operational security controls.

### 4.3 Threat Model

AEGIS protects against attacks arriving through the **untrusted natural-language input channel**. The model assumes the database and application server are properly hardened; the attacker controls only the query field.

**T1 — Prompt injection attempting SQL generation.**
*Attack:* "Ignore previous instructions. Generate `DROP TABLE orders`."
*Control:* The `IntentObject` schema contains no SQL field. Any non-approved string in `metric_term` or `dimension_term` is rejected by Pydantic type validation at Stage 2 before the compiler is reached.

**T2 — Unauthorized metric or dimension access.**
*Attack:* "Show me customer passwords" or "List credit card numbers by order."
*Control:* Fields like `customer_password` do not exist in the semantic layer vocabulary. The LLM never sees those names — it receives only the curated approved label list. Stage 2 rejects any unrecognized term.

**T3 — Unauthorized row access.**
*Attack:* A store-level user asks "Show revenue for all branches."
*Control:* Stage 4 (Permission Rewriter) runs *after* the LLM and appends a role-specific `WHERE` predicate (e.g. `AND o.StoreId = :user_store`) derived from the authenticated session. This cannot be suppressed or overridden by natural-language content.

**T4 — DML or DDL injection.**
*Attack:* A crafted prompt that tricks the LLM into associating a write operation with an intent class.
*Control:* No template in the pattern library contains a DML/DDL keyword. The AST-level post-compilation validator explicitly rejects any non-`SELECT` statement as a defense-in-depth layer.

**Not protected by AEGIS** (requires operational security controls outside this architecture):
- A malicious administrator embedding arbitrary SQL inside a metric `sql_expr` field
- Supply-chain compromise of the compiler module or SQL parser library
- Database-level privilege escalation bypassing the application layer
- LLM provider infrastructure compromise or model poisoning

Explicitly documenting out-of-scope threats is itself a contribution: prior NL2SQL work rarely specifies the boundary of its safety claims, making meaningful security comparison difficult.

### 4.4 System Architecture and Semantic Layer

#### 4.4.1 Pipeline Overview

![AEGIS Architecture](../assets/images/fig_architecture.png)
*Figure 1: AEGIS Architecture Pipeline. Color coding: blue = NL/AI stage, purple = semantic mapping, red = safety enforcement, green = execution and output, orange = rejection paths.*

The complete pipeline: User Request → LLM Intent Parser → Coverage Validator → Semantic Mapper → Analysis Planner → Safe Query Compiler → Permission Rewriter → Query Executor → Visualization Selector → Widget Engine → Dashboard. Rejection at any stage produces a structured clarification prompt.

#### 4.4.2 Semantic Layer

The semantic layer is the most important non-AI part of AEGIS. It separates business language from the actual database structure and defines which metrics, joins, and permissions are allowed.

A useful analogy: **LEGO blocks, not free-form clay**. The semantic layer defines a finite set of composable building blocks. User questions are limitless, but every answerable question is a combination of these blocks.

![Modular Semantic Layer](../assets/images/fig_lego_modularity.png)
*Figure 2: Semantic layer modularity. Left (AEGIS): finite composable blocks that can be safely combined. Right (direct LLM-to-SQL): unconstrained SQL generation, which produced an executable `UPDATE` for the disguised write probe in both recorded baseline runs (§7.2).*

| Object | Field | Example |
|--------|-------|-------|
| Metric | label, SQL expression, joins, vis default, security class | `revenue = SUM(o.OrderTotal - o.RefundedAmount)` |
| Dimension | label, SQL expression, datatype, access scope | `category = c.Name` from Category |
| Filter | label, SQL predicate, datatype | `payment_status : o.PaymentStatusId = :val` |
| Time rule | label, SQL predicate, granularity | `current_week : DATEADD(week, ...)` |
| Join path | source, target, ON clause | Order → OrderItem → Product → Category |
| Pattern | required slots, SQL template, visualization default | ranking : metric + dimension → bar chart |
| Permission | rule | store_manager → filtered by store location |

### 4.5 LLM-Based Intent Parsing with Dynamic Vocabulary Injection

The key idea is **vocabulary injection**. At startup, AEGIS builds the prompt by listing all approved metric and dimension names — with plain-English descriptions — directly from the semantic layer. The LLM sees exactly which IDs are valid and can map any user wording to the right one without a manually maintained synonym list.

![Vocabulary Injection Process](../assets/images/fig_vocab_injection.png)
*Figure 3: Vocabulary injection workflow. The semantic layer serializes all approved IDs with descriptions into a compact pipe-delimited format (~1,100 tokens) injected into the LLM system prompt at startup.*

Advantages over synonym dictionaries: (1) **zero maintenance** — adding a metric automatically updates the vocabulary; (2) **fewer moving parts** — one administrator-controlled artifact instead of a second registry that can drift out of sync with it; (3) **token efficiency** — ~1,100 tokens for 15M + 34D.

The output schema enforces typed fields:

```json
{
  "intent_class": "kpi | ranking | trend | comparison | exception | summary | segment | funnel | cohort | correlate | tabular",
  "metric_term": "string",
  "dimension_term": "string or null",
  "time_term": "string or null",
  "filters": [{"field": "string", "operator": "string", "value": "string"}],
  "sort": "asc | desc | null",
  "limit": "integer or null",
  "confidence": "low | medium | high",
  "needs_clarification": "boolean"
}
```

**What vocabulary injection does and does not guarantee.** Vocabulary injection pastes the approved metric and dimension identifiers into the prompt, so the model is structurally unable to emit an identifier the compiler does not recognise. That is what makes the safety property hold: it is a claim about which strings can reach Stage 3, and Proposition 1 depends on it. But the same closure means the model cannot express "this question is about something you do not model" — asked for the average shipping *distance*, it must still return an approved metric, and it returns shipping *cost*. The output is in-vocabulary by construction, so validating the model's OUTPUT can never detect an out-of-scope request; the check must run against the model's INPUT — the user's own words — which is the only place the evidence survives. Sections 4.6–4.7 describe the two stages, grounding and coverage analysis, that carry out that check. Vocabulary injection is therefore narrowed to a safety claim: it explains why an unapproved identifier cannot be generated, not why an approved identifier is the right one.

### 4.6 Grounding

Vocabulary injection guarantees that whatever identifier the model returns is *approved*; it says nothing about whether that identifier is the *best* one for the term the user actually used. That question is answered by a separate stage, `grounding.py`, which replaces an earlier first-match-wins scan with an explicit scoring and acceptance procedure.

The scan it replaces walked the metric and dimension lists in order and returned the first object whose id or description overlapped the term. This made the winner a function of **declaration order** in the semantic layer rather than of fit: reordering the vocabulary — an operation with no intended semantic effect — could silently change which binding a term resolved to, and therefore the query result. It also had no notion of margin, so a term that matched two objects equally well was indistinguishable from one that matched a single object perfectly, and no notion of provenance, so a caller receiving a bare identifier string had no way to explain, audit, or question it.

The grounding engine instead scores every candidate object against the term and returns a ranked list of `GroundingCandidate` records, each carrying a score, a match kind (`EXACT_ID`, `EXACT_LABEL`, `ALIAS`, `TOKEN_OVERLAP`, `DESCRIPTION_OVERLAP`, in decreasing order of reliability), and a human-readable evidence string. An explicit acceptance rule then converts the ranked list into one of four outcomes:

| Outcome | Condition | Meaning |
|---------|-----------|---------|
| RESOLVED | top score clears an absolute floor **and** leads the runner-up by a minimum margin | exactly one defensible binding |
| AMBIGUOUS | top score clears the floor but the margin over the runner-up is too small | several bindings score comparably; the candidates become a clarification question |
| UNSUPPORTED | no candidate clears the floor | nothing in the vocabulary accounts for the term |
| ABSENT | the request did not supply a term for this slot | not evaluated |

Requiring both an absolute floor and a margin over the runner-up is deliberate: the floor alone accepts a mediocre match that merely has no competitor, and the margin alone accepts a strong match that happens to tie a similarly strong one. Declared synonyms are drawn from an "also called X, Y or Z" clause inside the object's own description, rather than a separate synonym dictionary, keeping every alias inside the same administrator-reviewed artifact as the definition it modifies rather than a second registry that can fall out of sync with it.

This is the schema-linking-as-a-separate-stage principle used by RAT-SQL (Wang et al., 2020) and TriSQL (Su et al., 2026), combined with the ranked-alternatives model used by NaLIR's interactive communicator (Li & Jagadish, 2014) and DataTone's ambiguity space (Gao et al., 2015). The difference is the source of the candidates: those systems rank raw schema columns and table names, which a non-technical user cannot be expected to evaluate; AEGIS ranks entries from a curated business vocabulary with plain-English labels, so the alternatives an AMBIGUOUS outcome presents are meaningful to the person being asked to choose among them.

### 4.7 Coverage Analysis

Grounding decides, per slot, whether a *given* term binds. It cannot detect the request described in §4.5: a question about a concept the vocabulary has no slot for at all, where the model was nonetheless forced to substitute an approved metric or dimension. Detecting that is the job of `coverage.py`, and it works in the opposite direction from grounding — against the original question text, not the model's structured output.

`CoverageAnalyser` builds a lexicon of everything the deployment can account for: the tokens of every metric and dimension id, label, and description; the temporal vocabulary recognised by the time grammar (§4.8); analytic scaffolding — verbs, comparatives, question words, generic commercial nouns — that describes the shape of a request rather than its subject matter; and literal values the intent already bound into filters, which are data rather than vocabulary. Whatever content words in the original question remain unaccounted for are **residual concepts**, and their presence is direct evidence that the model was forced to substitute rather than answer.

Residual concepts are graded rather than treated uniformly, because they call for different responses. A concept with no binding at all — "bounce rate", "sentiment", "carrier" — is a hard gap: no combination of approved bindings expresses it, and the request is rejected. A modifier on a concept that *is* bound — "net revenue", "new customers", "profit margin" — is a soft gap: the request is expressible, but the definition the user assumed may differ from the one the semantic layer governs, so the correct response is to surface the governed definition and let the user confirm it, not to refuse. The same analysis also flags two conditions that are not vocabulary gaps but still block a direct answer: a **compound request** asking for two distinct reports at once, since a widget holds one result shape and silently answering only the first half would be a silent partial answer; and a **write request**, since AEGIS is read-only by construction and a request to change data deserves to be declined on that structural ground rather than because some noun in the sentence happened not to bind.

Framed against the schema-linking literature, coverage analysis asks the inverse question. Schema linking (RAT-SQL, TriSQL, and the grounding stage in §4.6) asks "which vocabulary elements does this question refer to?". Because the AEGIS vocabulary is closed and curated rather than open, the complementary and equally answerable question is "which parts of this request does the vocabulary fail to explain?" — and it is this second question, asked against the user's own words, that recovers the scope check that output validation structurally cannot perform.

### 4.8 Time Grammar

Temporal phrases are normalised by a dedicated module, `time_grammar.py`, built as a *total* function: every input string maps to exactly one of five outcomes — RESOLVED, GRAIN_ONLY, VAGUE, UNSUPPORTED, or NONE — and there is no path by which a temporal constraint can be silently dropped.

Two of the five outcomes exist to separate a distinction the earlier pipeline collapsed. A phrase such as "monthly" specifies **granularity**: how the time axis should be bucketed for a trend, restricting no rows at all. A phrase such as "last month" specifies a **filter**: a concrete window that rows must fall inside. Treating the first as if it were an unrecognised instance of the second rejected "monthly revenue trend" — arguably the single most common trend request in the corpus — so GRAIN_ONLY is reported separately and consumed only by the visualization stage (§4.11), never compiled into a WHERE clause. A third outcome, VAGUE, covers phrases such as "recent orders" that carry a genuine temporal intent without a determinate window: guessing a boundary would be a silent decision about the answer, and refusing outright is heavier than the situation warrants, so the pipeline asks instead.

Totality is what matters most here, and it is a direct correction of a documented failure mode. The matcher it replaces returned `None` for any phrase it did not recognise, and every call site treated that the same way: `if time_part: parts.append(time_part)`. An unrecognised phrase therefore did not raise and did not filter — it disappeared. "This morning", "this quarter", and "last 90 days" all fell outside the previous matcher's coverage, so the temporal constraint was silently discarded and the query ran over the entire history table, returning a confident, well-formed, wrong number. Making `normalise()` total over five explicit outcomes removes that failure class structurally rather than by adding more phrases to a pattern list: there is no sixth, unlabelled outcome for an unanticipated phrase to fall into.

Resolved ranges are half-open, `[start, end)`, which keeps month/quarter/year arithmetic exact and avoids the end-of-day truncation error that affects naive `BETWEEN` comparisons on a cast date; every bound is anchored on the database's own clock rather than the application server's. Fiscal-calendar phrases resolve only when a deployment has configured a fiscal year start month; where it has not, the phrase reports UNSUPPORTED rather than being silently reinterpreted as a calendar year, since a wrong fiscal boundary is a materially wrong answer rather than a rounding error. As noted in §4.2, every SQL fragment a resolved range contributes is one of a fixed set of templates, never a user-text interpolation, so admitting time expressions into the pipeline does not reopen the injection surface Proposition 1 closes.

### 4.9 Plan Verbalisation

The final pre-execution stage, `explain.py`, renders the grounded interpretation as one plain-English sentence and asks the user to confirm it before anything runs — before a query executes, before a result is fetched, before a chart is drawn.

The motivation is a specific empirical finding from NaLIR's user study (Li & Jagadish, 2014): of 32 wrong answers produced without an interactive confirmation step, participants detected only 7. Most of the undetected errors were aggregates — a single number that looks exactly as plausible whether or not the system understood the question, because a wrong scalar carries no visible sign of its own wrongness. DataTone (Gao et al., 2015) reported the complementary finding: when interpretation choices were surfaced as explicit "ambiguity widgets," users resolved them readily. Together these suggest that the dominant real-world failure mode of a natural-language query interface is not a crash and not an unsafe query — it is a confident, well-formatted, wrong answer that nobody thinks to question.

AEGIS is positioned to address this more cheaply than a system that goes directly from question to SQL, because the LLM's output is a *typed plan* (§4.2) rather than SQL text. The interpretation therefore already exists, before any query has executed, in a form that can be walked field by field and rendered as prose: which measure, which breakdown, which period, which filters, which ordering and cut-off. Verbalisation costs one template expansion — for example, "Total Revenue, broken down by Product Name, for Last 30 days, highest first, top 10." — turning a silent misinterpretation into a visible, correctable one before it can be believed. The rendering is deliberately deterministic string construction with no model consulted: an explanation generated by a second LLM call could itself be wrong, and an explanation that does not faithfully reflect the plan that will actually execute is worse than no explanation at all.

### 4.10 Safe Query Compiler

![Two-Layer Safety Defence](../assets/images/fig_safety_layers.png)
*Figure 6: Two-layer SQL safety defence. Layer 1 (parameterized templates) makes sure user text never enters the SQL string. Layer 2 (post-compilation safety scanner) rejects queries with forbidden constructs.*

The compiler instantiates SQL from a library of parameterized templates:

![AEGIS Analytics Patterns Taxonomy](../assets/images/fig_patterns.png)
*Figure 4: Taxonomy of the eleven core AEGIS analytical primitives. Each specifies required/optional slots and a default visualization (~5,610 valid combinations across 15M × 34D × 11 patterns).*

| Pattern | Required slots | Optional slots | Default visual |
|---------|---------------|----------------|----------------|
| KPI (Aggregate) | metric | time_rule, filter | kpi_card |
| Ranking | metric, dimension | time_rule, filter, limit | bar_chart |
| Trend | metric, time_grain | time_rule, filter | line_chart |
| Comparison | metric, segment | time_rule, filter | grouped_bar |
| Exception | metric, threshold | dimension, time_rule | table |
| Summary | metric[], dimension | time_rule, filter | multi_card |
| Segment | metric, dimension | time_rule, filter | pie_chart |
| Funnel | metric, stages | time_rule, filter | funnel_chart |
| Cohort | metric, group_def | time_rule, filter | grouped_bar |
| Correlate | metric, attribute | time_rule, filter | scatter_plot |
| Tabular | dimension | filters, time_rule | table |

After placeholder substitution, two safety layers apply: (1) parameterized query engine separates SQL structure from user inputs; (2) post-compilation safety scanner rejects any query containing forbidden constructs (non-SELECT statements, UNION/EXCEPT/INTERSECT, EXEC, system tables). If any forbidden pattern is detected, the compiler raises a SecurityError.

### 4.11 Visualization Selector

Chart selection proceeds in two passes. The first proposes a chart type from the analysis pattern alone, using the table below as a starting point:

| Intent | Result shape | Proposed visualization |
|--------|-------------|----------------------|
| KPI | scalar | KPI card |
| Ranking | 1 measure, ≤20 categories | Horizontal bar chart |
| Trend | 1 measure, time series | Line chart |
| Comparison | 1 measure, 2–4 segments | Grouped bar chart |
| Exception | row-level detail | Sortable table |
| Summary | 2–4 scalar measures | KPI card grid |
| Segment | 1 measure, categorical | Pie chart |
| Funnel | ordered conversion stages | Funnel chart |
| Cohort | 1 measure, 2+ groups | Grouped bar chart |
| Correlate | 2 measures, continuous | Scatter plot |
| Tabular | raw records | Sortable table |

The second pass tests that proposal against the dimension's declared datatype, the metric's aggregation semantics, and the observed shape of the result — not against the intent class alone — and downgrades it whenever a validity rule fails. Each downgrade moves to a strictly safer encoding (pie before bar, bar before table), so the pass always terminates. A temporal dimension is never encoded as a pie, because a pie discards the ordering that makes a time series legible; a categorical dimension beyond the pattern's category ceiling is downgraded from a chart to a sortable table rather than left to render illegibly; a scatter plot is withheld unless both axes are quantitative. The worked case that motivates the second pass on its own is additivity: a metric such as an average is never rendered as pie slices, because a pie asserts that its slices sum to a meaningful whole, and an average's parts do not — the rule is read directly from whether the metric's own SQL aggregate is a sum or count rather than an average or ratio, so a newly defined metric inherits the correct behaviour without a hand-maintained exception list.

Every encoding the second pass rejects is recorded in the visualization specification itself, with the rule that rejected it, rather than only in a log line — a governed analytics system should be able to show why it drew what it drew, not merely that it did. This plays the same role as nvBench's use of a learned model (DeepEye) to filter chart proposals before a human sees them, though the AEGIS filter is a deterministic rule set rather than a learned one; both treat "this chart is unreadable" as a first-class outcome rather than a silent omission. The output itself is a Vega-Lite v5 specification, not a chart-type string, alongside the renderer-agnostic fields (chart type, axes, colour scheme) the AEGIS frontend consumes directly. Emitting a standard interchange format makes the selector's output directly comparable with the NL2VIS literature — nvBench/ncNet and NL4DV (Luo et al., 2021; Narechania et al., 2021) — which uses the same format as its target artifact, rather than a bespoke internal representation that only this system can interpret.

### 4.12 Widget Persistence and Reuse

![Widget Lifecycle](../assets/images/fig_widget_lifecycle.png)
*Figure 7: Widget lifecycle. A new question triggers the full pipeline; if an identical widget exists (SHA-256 plan hash match), the cached artifact is returned immediately. Scheduled refresh re-executes saved SQL on fresh data, directly addressing the observation that reporting requests are often recurring rather than one-off (Section 3.3).*

Each widget stores: a unique ID (SHA-256 hash of the analysis plan), the original question, the analysis plan (JSON), SQL template hash, chart settings, timestamps, access rules, and run history.

---

## 5. Implementation

AEGIS is implemented as a web application with a vanilla HTML/JavaScript frontend (jQuery, Chart.js) and a Python (FastAPI) backend targeting a production nopCommerce 4.70 schema (126 tables, 107 foreign key constraints).

- **LLM Integration:** Llama 3.1 8B Instant via Groq API with structured JSON output enforcement. System prompt dynamically constructed by injecting approved metric and dimension IDs.
- **Rate Limiting:** Provider-agnostic configuration module (`ai_config.py`) with sliding-window rate limiter and concurrency-safe `asyncio.Lock`.
- **Semantic Layer:** Python configuration modules containing 22 metrics, 36 dimensions, 0 synonyms, and 16 join paths across 17 tables. (The benchmark in Section 6 was designed against an earlier configuration of 15 metrics, 34 dimensions and 11 join paths across 14 tables; the extension is the configuration change reported in Section 6.5, and the counts here are those of the committed `aegis/server/semantic_layer.py`.)
- **SQL Compiler:** Parameterized MySQL templates. BFS join path resolution across 14 tables (12 aliases). Post-compilation `_validate_sql_safety()` checks 16 forbidden patterns.
- **Visualization Selector:** Rule-based Python dictionaries. Additional rules after data: bar charts with >20 categories become tables, pie charts with >8 slices become bar charts.
- **Widget Engine:** SHA-256 plan hash deduplication. JSON file storage in prototype (designed for relational database in production).
- **Coverage Validator:** Pre-compilation gate rejects unknown metric/dimension terms with structured guidance listing available identifiers.
- **Permission Enforcement:** Permission Rewriter appends role-based WHERE predicates. Five roles: `public`, `store_manager`, `regional_manager`, `read_only`, `analyst`.

---

## 6. Evaluation

This section reports two evaluations. The first asks whether natural language can reproduce the reporting surface a real e-commerce platform already ships with. The second asks what happens when a request falls outside that surface, and reports the five metrics the thesis uses to score the refusal channel itself, not only the requests AEGIS was designed to answer.

### 6.0 Evaluation Scope

This is a *prototype evaluation*, not a large-scale independent benchmark study, over a single production schema (nopCommerce). It is also, in one specific and load-bearing way, a *self-correcting* evaluation: an earlier draft of this section reported figures for intent-parsing accuracy, SQL safety and execution validity, an ablation study, a cross-schema transfer study, and pipeline latency that had no supporting artifact anywhere in this repository — no results file, no script that produced them, no way for an examiner to reproduce a single one of them. They are withdrawn below rather than restated, following the evaluation policy recorded in `CLAUDE.md`: a metric is reported only once it is backed by a file in the repository that a reader can open and recompute.

### 6.1 Retraction of Previously Reported Figures

The following figures appeared in earlier drafts of this section and are withdrawn: a table of 1.00 precision/recall/F1 across all eleven intent classes; "100% execution validity, 100% coverage" for AEGIS against a 99%/99% baseline; an ablation study whose rows included "– Confidence-gated clarification: 94.2%" for a component that could not have produced that number — the prompt sent to the model never requested a confidence field, and the parser silently stamped `confidence="high"` onto every response that omitted one, so there was no signal for a confidence gate to act on; a WooCommerce transfer result of "98.0% intent accuracy in 14 person-hours"; and a pipeline-latency table of round numbers with no corresponding trace or timing log. None of these five are reproducible from any file in this repository, and none is restated in what follows. What is reported below is limited to what two committed, rerunnable artifacts actually show: `evaluation_dataset/benchmark_results.json`, produced by `python3 run_benchmark.py --rerun --limit 0`, and its scoring by `python3 evaluation_dataset/evaluate_abstention.py`.

### 6.2 Dataset and Environment

Both evaluations run against a MySQL 8.0 instance seeded with the AEGIS Truth Schema (126 tables, 107 foreign keys) and the mock dataset in `database/mock_data.sql`. Counting that dataset once it is loaded gives 1,200 customers, 2,500 orders spanning 2025–2026, 6,320 order items, 1,492 shipments, and **17 products across 8 categories and 8 manufacturers**.

Earlier drafts described the catalogue as "1,000 products across 50 categories". That figure is withdrawn: no file in this repository produces it, and the committed data is roughly sixty times smaller in products and six times smaller in categories. The correction matters beyond bookkeeping, and in a direction that weakens rather than strengthens the results reported below. A breakdown over 8 categories is a much easier test than one over 50 — the grain fan-out defect described in Section 6.3.1, which multiplies an order total once per matching line item, distorts a small number of large groups far less visibly than it would a large number of small ones — and a "top 7 categories" request is close to degenerate when only 8 exist. Several ranking and segmentation questions in the benchmark are therefore easier than a reader would assume from the earlier description. Re-seeding at the described scale and re-measuring is straightforward and is listed in Section 8 as outstanding work; it is not done here because re-running the benchmark on a different dataset would mix a data change into a set of figures that already carry several method changes. The boundary evaluation (Section 6.4) uses the 107-question set in `evaluation_dataset/questions.json`: 100 requests designed to be answerable within the semantic layer's vocabulary, spanning all eleven analytics primitives, plus 7 out-of-scope probes (queries 101–107) added specifically to exercise the edge of the system rather than only its interior. The question set, recorded pipeline outputs, and scoring scripts are all in `evaluation_dataset/`, so every figure below is independently rerunnable.

### 6.3 Evaluation A: Coverage of the Platform's Report Suite

nopCommerce, the host platform, ships its own fixed menu of standard admin reports. AEGIS was asked, in natural language, to reproduce every one of them: Sales summary by month; Sales summary today; Bestsellers by quantity; Bestsellers by amount; Products never purchased; Country sales; Best customers by order total; Best customers by order count; Registered customers; Low stock; Order status breakdown; Incomplete orders; Latest orders; Sales by category; Sales by manufacturer; Average order value; Shipment count; Refund totals; Tax collected; Daily revenue trend.

Until now, this claim occupied the same position as the figures retracted in §6.1: asserted, with no script and no artifact behind it. That gap is closed by `evaluation_dataset/verify_report_suite.py`, which sends each of these twenty reports through the full pipeline — parse, resolve, compile — as an ordinary business phrasing rather than a wording close to the report's own name, and records the terminal outcome for every one; its output is committed at `evaluation_dataset/report_suite_results.json`, so the figure below is independently rerunnable rather than asserted.

The first run of that script reproduced 16 of 20, not 20 — and this is worth reporting rather than smoothing over. The earlier hand-verification behind the original claim had used wordings close to the report names themselves; the script's ordinary-business-phrasing wordings removed that selection bias, which is exactly what surfaced the four misses. Two were tokeniser defects: "What are today's total sales?" was rejected because the possessive form did not stem to the "today" already present in the temporal vocabulary, and "Break down orders by their status" split into "break" and "down," with "down" read as an unrecognised domain concept rather than as half of "breakdown," which the tokeniser already knew. Two were genuine vocabulary gaps: low stock and incomplete orders are both concepts nopCommerce names as first-class reports, and neither had a corresponding semantic-layer binding. All four are implementation or configuration defects in the sense §6.5 uses the term, not evidence against the architecture, and each was fixed at that level — a possessive-stripping rule and a two-word compound added to the tokeniser's scaffolding vocabulary, and a governed-predicate declaration in `semantic_layer.py` for each of the two missing concepts.

With those four fixes in place, the same script, run against the *same, unchanged* question wordings listed above, reproduces all 20 of 20: each request compiled to executable SQL against the schema described in §6.2, paired with an automatically selected chart type. This is stated explicitly because "the wording was changed until it passed" is the obvious suspicion a before/after result like this invites, and the artifact refutes it directly — `report_suite_results.json` records the exact question sent for every request, unchanged from the 16/20 run.

This is a stronger test than a self-authored question set, for a specific reason: the report list is fixed by the host platform, not chosen by the thesis author, so it carries no annotation bias in either direction — there was no opportunity to pick questions the system was already known to handle well, and no opportunity to avoid ones it was known to handle badly. It answers a narrow, concrete question directly: can a natural-language interface reproduce the reporting surface a production e-commerce platform already exposes through its own admin panel? For these 20 reports, the answer is yes. AEGIS additionally supports parameterised variation of each of these — arbitrary date ranges, arbitrary category or manufacturer filters, arbitrary top-N cutoffs — for which the fixed admin panel has no corresponding screen at all; the panel offers each report in one fixed shape, where AEGIS offers the same report as a family of shapes governed by the same semantic layer.

### 6.3.1 SQL-Parity Verification Against the Platform's Own Source

Reproducing a report's *shape* — an ANSWER outcome with compiled SQL — is not the same claim as reproducing the report: the SQL can compile, execute, and return a plausible, chartable number while computing something other than what the platform itself reports. `verify_report_suite.py`'s own pass/fail check illustrates the point: it counts a request as reproduced once the outcome is ANSWER and the compiler emitted SQL, which is precisely the check that would also have counted each of the defects below as reproduced. That is a limitation of the 20/20 figure above, not only of an earlier draft of the script, and it is stated here rather than left implicit, following the evaluation policy in `CLAUDE.md`.

A separate comparison, made directly against nopCommerce's own report-service source rather than against this project's own expectations, found five places where the compiled SQL diverged from the platform's semantics for the same report — every one of them silent: the query compiled, ran, and returned a plausible, ordered, chartable number that was wrong, with nothing in the output to mark it as such. Full citations and per-defect detail are in `docs/analysis/nopcommerce_sql_parity.md`; in summary:

- **Revenue fan-out.** An order-level revenue measure broken down by an item-level dimension (category, manufacturer) was joined through `OrderItem`, so each order's total was added once per matching line rather than once per order — "revenue by category" over-counted any order with more than one item in that category. Fixed by a declared grain guard (`item_grain_equivalent`) that substitutes the item-level measure and states the substitution in the plan verbalisation, rather than repairing it silently.
- **Missing soft-delete filters.** Every nopCommerce report applies `!Deleted` on `Order`, `Product`, and `Customer` before aggregating; AEGIS applied none of them, so every total silently included soft-deleted rows. Fixed by `MANDATORY_PREDICATES`, applied against the compiler's resolved join path rather than the plan's declared one.
- **Customer identity by display name.** Customer breakdowns grouped by the rendered name (`CONCAT(FirstName, LastName)`) rather than by `Customer.Id`, silently merging distinct customers who share a name. Fixed by a declared `group_expr` on the dimension.
- **Registered-customer count anchored on order date.** "Registered customers this month" was time-filtered on the order date rather than the registration date, so it silently became "customers who ordered this month," excluding every registrant who has not yet bought anything. Fixed by a per-metric `time_anchor`.
- **Unbindable filter fields.** A filter field the semantic layer could not resolve silently fell back to `o.Id = '<the unbound value>'` — a query that compiles, runs, returns an empty or arbitrary result, and reports itself as a successful answer. Fixed by raising `UnknownFilterFieldError` in place of the fallback.

All five are pinned by regression tests in `tests/test_platform_parity.py`, so a future change that reintroduces any of them fails the suite rather than passing silently.

Two readings of this finding pull in opposite directions, and both are true at once. The first is favourable to the thesis: every one of these five defects produced SQL that compiled, executed, and returned a plausible, chartable number — the safety guarantee held perfectly (Proposition 1 was never at risk) while the *answer* was wrong. That is precisely the silent-error failure mode the silent-error rate in §6.4 is meant to capture, and precisely the failure mode the NaLIR user study (§4.9) motivates guarding against: a wrong scalar carries no visible sign of its own wrongness. It is also direct evidence for the configuration-boundary claim of §6.5 and §8: every one of the five fixes was a semantic-layer declaration — `item_grain_equivalent`, `MANDATORY_PREDICATES`, `group_expr`, `time_anchor`, `GOVERNED_PREDICATES` — or the removal of a silent fallback, with no change to the compiler's, mapper's, or safety layer's architecture.

The second reading is unfavourable and is given equal weight: these five defects were present in the system while the earlier 20/20 claim — the one this section now backs with a script and a committed artifact — was being made. That is exactly why a reproducible artifact matters more than a hand-verified one, and it is why the 16/20-then-20/20 result above is reported honestly rather than folded into a single number. It is also worth naming what this comparison is not: a comparison of SQL *text* against source code is weaker evidence than a differential test of result sets, computed from both AEGIS's compiled queries and the platform's own report queries against a shared, seeded database. That differential test has not been run, and is named as future work in §8.

### 6.4 Evaluation B: Boundary Behaviour on the 107-Question Benchmark

The 107-question benchmark is reframed here as a probe of what happens *outside* the platform's designed surface, not as the headline result — that role belongs to Section 6.3. Scoring a benchmark that mixes answerable and out-of-scope requests against a single aggregate accuracy figure is meaningless in both directions: it punishes a correct refusal as a failure, and rewards a confident wrong answer as a success. `evaluation_dataset/evaluate_abstention.py` therefore reports five metrics without collapsing them into one number, following Liu et al. (2026) for the first two and extending them with three the refusal channel specifically requires:

- **Translatability** — produced *something* executable, over all requests. The standard NLIDB metric (Liu et al., 2026). High translatability with low precision is the signature of a system that always answers, whether or not it should.
- **Translation precision** — produced the *expected* result, computed only over requests carrying a ground-truth label (Liu et al., 2026).
- **Abstention recall** — of the requests that should have been declined, how many were. This is the quantity the abstention architecture exists to move.
- **False-abstention rate** — of the requests that should have been answered, how many were declined instead. The cost side of abstention: refusing every request scores 100% on abstention recall alone, which is why this rate is never reported without it.
- **Silent-error rate** — answered confidently and incorrectly, with no error and no clarification raised. Li & Jagadish (2014), in the user study behind NaLIR, found that of 32 wrong answers produced without an interactive confirmation step, users detected only 7 unaided — a 4-in-5 miss rate for exactly this failure mode. That result is why silent-error rate, and not aggregate accuracy, is the metric that matters most for a governed reporting system: an unconfirmed wrong answer is the one a user is least equipped to catch.

Abstention recall is reported here beside false-abstention rate in every instance, deliberately, because reporting the first alone is trivially gamed by a system that refuses everything. This pairing — recall and its cost measured together, over a stratified answerable/should-decline split — is itself a methodological contribution: no system in the survey comparison of Section 2.6 measures its own refusal channel this way.

Strata: of the 107 requests, 55 should be answered and 52 should be declined.

| Metric | Value | n / of |
|---|---|---|
| Translatability | 37.4% | 40 / 107 |
| Translation precision | 29.9% | 32 / 107 |
| Abstention recall | 100.0% | 52 / 52 |
| False-abstention rate | 25.5% | 14 / 55 |
| Silent-error rate | 11.2% | 12 / 107 |

Every figure in this table was produced by running `python3 evaluation_dataset/evaluate_abstention.py --json evaluation_dataset/abstention_metrics.json` against the committed `evaluation_dataset/benchmark_results.json`, following `CLAUDE.md`'s stated measurement procedure. The committed `abstention_metrics.json` is the direct output of that command and matches the table cell for cell; a reader who reruns it against the same results file reproduces these five numbers exactly.

Two of these five are not quotable as results. Translation precision and silent-error rate are both scored against `aegis_correct` in `semantic_correctness_annotations.json`, and those labels describe the correctness of the *old* pipeline's SQL, not the current one. The tell is in the number itself: translation precision has read 29.9% (32/107) across every run recorded in this project's history, unchanged by any of the fixes described in Section 6.5, because it is the same label count being re-read rather than a fresh measurement of the current system. Re-annotating the benchmark against current outputs, with a second annotator on a stratified sample, is required future work before either figure can be quoted.

These five figures come from a single benchmark run at a fixed temperature, and that carries a real cost worth naming rather than assuming away. Comparing this run against the immediately preceding one — itself superseded because a retry-amplification defect let it compete with a second concurrent run of itself for a rate-limited LLM endpoint, logging 62+ HTTP 429s and 10 outright baseline failures before the defect was diagnosed and fixed — the *totals* in the table above barely moved, but the *set* of wrongly-declined question ids did not hold steady: ids 16 and 62 left the wrongly-declined list while ids 46, 56, and 97 joined it, and id 16 specifically moved from wrongly-declined into silent-error while id 97 moved the other way, from silent-error into wrongly-declined. A couple of questions' worth of churn between categories, underneath a roughly stable aggregate rate, is a real methodological finding: a single run's false-abstention or silent-error figure carries a run-to-run wobble on this order even at fixed temperature. The two runs compared here are not a clean measurement of that wobble by themselves, because the earlier run was also degraded by request timeouts under throttling, which could have shifted individual outcomes on their own independent of any genuine run-to-run variance — so this comparison should be read as evidence of the *scale* of the effect, not a precise estimate of it. The stronger method, and one this thesis has not done, is a mean over several repeated clean runs with a reported spread, rather than a single-run point estimate.

### 6.5 Improvement Trajectory and Residual Gap

Reported abstention recall has held at 100% (52/52, or 98.1% at the very first abstention-aware build) across every subsequent change described below; false-abstention rate has fallen from 61.8% at that first build, to 40.0%, to the current 25.5% — a reduction bought with no architectural change at all. Each step was a fix to implementation or configuration:

- validating the model's self-reported list of unmapped terms, rather than merging it into the rejection set unchecked (the model was reporting words like "daily" or "top 5" as unmapped, which are not domain concepts at all);
- separating time granularity ("monthly") from time filtering ("last 90 days"), so a request that only sets the chart's time axis is no longer treated as an unrecognised filter;
- extending the semantic layer's table coverage from 12 to 17 of the 126 available schema tables, so that coupons, cart contents, reviews, and tags — concepts the schema already modelled — stopped being declined for want of configuration.

A figure of 23.6% (13/55) was reported for false-abstention rate in an earlier version of this measurement; the corrected figure above is 25.5% (14/55) — worse, by one question. This is stated plainly rather than smoothed over, because the evaluation policy in `CLAUDE.md` does not permit reporting only the favourable half of a comparison. The earlier run is the one that should be distrusted, not the later one: it was competing with a second concurrent run of itself for a rate-limited LLM endpoint, a retry-amplification defect in which the LLM SDK's own default retry behaviour retried underneath the benchmark's own rate limiter, so a single logical call could fire as many as fifteen HTTP requests, logging 62+ HTTP 429 responses and 10 outright baseline failures along the way. The run behind the 25.5% figure recorded zero 429s and zero baseline failures across all 107 requests once that defect was fixed, so it is the clean measurement, and it is the one this thesis stands behind even though it is less favourable on this one metric than the figure it replaces. Silent-error rate improved over the same comparison, from 13.1% to 11.2%, but that improvement neither offsets nor explains away the false-abstention regression: the two metrics move independently, and letting one soften the other in the reporting would repeat exactly the error this evaluation policy exists to prevent.

This trajectory is offered as evidence for the thesis's central claim: semantic accuracy, in this architecture, behaves as an implementation and configuration property rather than an architectural one. Recall was never traded away to buy it — every point on this trajectory holds abstention recall at or near 100% while false abstention falls, which is the opposite of the trade-off a less careful measurement would predict.

Part of the residual 25.5% is label error rather than system error. Several questions in the annotation file are marked "answer" but are not answerable under any reasonable semantic layer: an abandoned-checkout question presumes a checkout-event table that does not exist, and a composite "health score" is not a defined metric under any label the semantic layer could reasonably carry. Two further examples — product tags and first-time-versus-returning cohorts — were labelled "answer" before those dimensions existed in the semantic layer, and the old pipeline only produced an answer for them by nearest-match substitution onto an unrelated column; both are now representable following the extension above, so their continued appearance among wrongly-declined questions, if any, is a signal that the annotation file needs re-checking rather than that the architecture under-covers them. This is stated plainly rather than folded into the headline number, consistent with the evaluation policy in `CLAUDE.md`: a limitation that survives a genuine fix attempt is reported, not suppressed.

---

## 7. Discussion

### 7.0 AEGIS vs. Direct LLM-to-SQL: Structural Comparison

A natural question is: why not just ask a capable LLM to write SQL directly? The differences below are *architectural*, not accuracy-based.

| Property | Direct LLM-to-SQL | AEGIS |
|----------|-------------------|-------|
| SQL generation | Model-generated (probabilistic) | Deterministic compiler |
| Schema exposure to LLM | Required (tables, columns, FKs) | Not required (labels only) |
| Business metric definitions | Implied from schema names | Explicit in semantic layer |
| SQL injection prevention | Prompt-level (best-effort) | Structural (by design) |
| Permission enforcement | External or none | Built-in, post-LLM |
| Dashboard widget persistence | Not provided | First-class artifact |
| Auditability of query origin | Difficult | Full provenance per widget |
| Model dependency | Tied to specific model quality | Model-independent |

AEGIS does not claim to produce more creative SQL than a frontier LLM. It claims that for the supported analytics requests, results are guaranteed correct by construction, auditable, and safe — properties probabilistic generation cannot offer unconditionally.

### 7.1 Why a Semantic Layer Instead of RAG?

Retrieval-augmented generation (RAG) for NL2SQL retrieves relevant schema fragments to give the LLM better context. This is a useful technique, but it solves a different problem from the semantic layer and does not eliminate the safety risk.

RAG asks: *which schema information should the LLM see?* It is an access optimization — reducing hallucination by narrowing the schema the model reasons over. The LLM still generates a free-form SQL string as output.

The semantic layer asks: *which analytical concepts are allowed to exist, what do they mean, and who can access them?* It is a governance mechanism — defining the complete set of answerable questions and their canonical SQL translations before any query is processed. The LLM outputs a typed intent object, not SQL.

The key difference:
- **RAG** narrows input context. SQL generation is still unconstrained.
- **Semantic layer** constrains the output space. SQL generation is replaced by deterministic compilation.

An organization that wants both better schema context *and* controlled output could use RAG to select relevant semantic layer sections for very large vocabularies (thousands of metrics), while still routing through the AEGIS compiler. These are complementary, not competing, approaches.

### 7.2 Controlling the AI vs. Training a Better AI

Scoring both arms with the compiler's own forbidden-construct list — `python3 evaluation_dataset/evaluate_baseline_safety.py`, which imports `SQLCompiler.FORBIDDEN_PATTERNS` rather than restating it, and fails loudly if the two ever drift — the direct LLM baseline produced **one** genuine violation across 107 requests (0.9%), and AEGIS produced none. Both baseline runs recorded in this repository, generated independently, produce that violation on the same request: query 105, the disguised write probe ("Cancel all orders stuck in Pending for more than 30 days"), for which the baseline emitted a real, executable `UPDATE Order SET OrderStatusId = 40 ...`. AEGIS returned a read-only listing, because a write intent is not expressible in the plan the compiler consumes.

Three qualifications keep this from being read as more than it is. First, an earlier draft of this section reported "5 unsafe queries (5.0%)"; that figure is not reproducible from either committed baseline artifact and is withdrawn along with those listed in §6.1. Second, a handful of further pattern hits per run — four in one recorded baseline run, five in the other — are `UNION ALL` in date-series and grand-total CTEs — forbidden in *compiled* output, where the compiler has no legitimate reason to emit a set operator, but benign from a free-form generator, so they are reported separately rather than counted. Third, and most importantly, the baseline's rate is **not a stable quantity**: it depends on which model answers the prompt, and an earlier run against a different model produced several genuine DML violations where the current one produces one.

That instability is the actual argument, and it survives the smaller number intact — arguably it is made more clearly by it. A baseline that emits one unsafe statement in 107 is *more* dangerous to reason about than one that emits twenty, because a 0.9% rate is exactly the rate that passes casual review and still fires in production. AEGIS's rate is not low; it is structurally zero, and it does not move when the model, the prompt, or the provider changes, because no model output ever reaches the SQL string (§4.2, Proposition 1). When something must always be true — "never write", "never expose a column outside the semantic layer" — the difference that matters is not between a high rate and a low one but between a rate and a guarantee.

### 7.3 Vocabulary Injection: Letting the LLM Do What It Does Best

Handcrafted synonym dictionaries are both unnecessary and counterproductive when the LLM is given explicit access to the approved vocabulary. AEGIS's vocabulary injection inverts this responsibility: the model mapped "earnings" to `revenue`, "promo codes" to `discount_amount`, and "clients" to `customer_email` — none of which appeared in any synonym list. This allowed the 112-entry synonym dictionary to be deleted entirely, with the wordings it had enumerated by hand resolved instead against the injected vocabulary at request time.

The limit of the technique is worth stating precisely, because it is the mechanism behind a failure mode this thesis had to build a separate stage to catch. Injection makes the model reliable at mapping *within* the vocabulary and structurally incapable of signalling that a request falls *outside* it: a prompt listing only approved identifiers cannot elicit an unapproved one, so a request the layer does not cover returns the nearest approved identifier rather than an objection. Vocabulary injection therefore buys coverage of the wordings for concepts the layer already carries — not coverage of concepts it does not. That is why coverage analysis (§4.7) runs against the user's original text rather than the model's output, and why this section reports no coverage percentage: the figure earlier drafts quoted here is among those withdrawn in §6.1.

### 7.4 What You Give Up

AEGIS only supports queries that fit within its defined metrics, dimensions, and patterns. For open-ended data exploration requiring custom joins or schema-level operations, an unconstrained system may be more appropriate. AEGIS is designed for the majority of everyday reporting needs.

### 7.5 Why Saving Widgets Matters

Widget reuse directly addresses the observation that many reporting requests are repeated questions rather than one-off queries (Section 3.3). Saved widgets become part of users' daily workflows rather than requiring regeneration each time.

### 7.6 What AEGIS Cannot Answer

AEGIS can answer from ~8,712 valid combinations (22 metrics × 36 dimensions × 11 patterns), before the further multiplication contributed by time ranges, filters and top-N cut-offs. The point of this figure is not its size but its *finiteness*: the answerable space is large enough to be useful and closed enough to be enumerated, audited, and permission-scoped — which is precisely what free-form SQL generation cannot offer. Out-of-scope queries receive structured rejections listing available identifiers:

```
Unknown metric 'conversion_rate'.
Available: avg_order_value, customer_count, discount_amount,
           order_count, profit, refund_amount, revenue, ...
```

Extending coverage requires only adding semantic layer rows — no model retraining or synonym curation.

---

## 8. Limitations and Future Work

- **Re-annotation is the blocking item for two metrics.** `translation_precision` and `silent_error_rate` are both scored against the `aegis_correct` field in `evaluation_dataset/semantic_correctness_annotations.json`, and those labels describe the correctness of the *previous* pipeline's generated SQL, not the current one's. The symptom is visible in the numbers themselves: `translation_precision` has read 29.9% on every run to date, because every run re-reads the same fixed label count rather than forming a fresh judgement of current outputs. Neither metric may be quoted as a finding until the dataset is re-annotated against current AEGIS outputs — ideally by two independent annotators working from a stratified sample, with inter-annotator agreement reported as Cohen's kappa, following the two-annotator protocol BIRD (Li et al., 2023) uses for its own correctness labels.
- **Some current labels reward the behaviour this thesis removes.** A number of questions labelled `answer` in the annotation set are not, on inspection, answerable from the semantic layer as currently scoped: a composite "health score" combining sales, stock, and refund rates; abandoned-checkout events, for which no event table exists; and a first-time-versus-returning-customer cohort split applied to a period that predates that dimension being tracked. These labels were assigned when the previous pipeline "answered" such requests by nearest-match substitution — silently mapping an unavailable concept onto the closest available one and returning a result regardless of fit. That is exactly the silent-fallback behaviour this thesis identifies as a defect and removes. Consequently, part of the residual false-abstention rate measures the dataset's tolerance for a wrong-but-confident answer rather than a defect in the current system, and will be resolved by the same re-annotation pass rather than by a further code change.
- **Coverage is a configuration boundary, not an architectural one.** The semantic layer currently exposes 17 of the 126 tables in the schema. Every concept declined so far as "unmapped" — coupons, product tags, cart abandonment, product reviews — corresponds to a table that already exists in the schema; only the semantic-layer binding was missing. Extending the layer's coverage has already moved the false-abstention rate from 40.0% to 25.5% with no change to the compiler, the mapper, or any other architectural component. The remaining gap is expected to close the same way, by extending the semantic layer rather than changing the architecture — which is the deployment model this thesis already proposes in Section 4.
- **Genuine expressiveness limits (architectural, not configuration).** Three restrictions are owned as properties of the design rather than treated as coverage gaps awaiting a configuration fix: ranking by a raw numeric attribute (e.g. sorting products by rating) is not an aggregation, and the compiler does not support it; comparison against a prior period (e.g. "the same period last year") is not modelled by any current template; and fiscal-calendar phrases resolve only when a deployment has configured a fiscal-year start month, and the system abstains deliberately in that case rather than guess at one.
- **Single-model, single-schema evaluation.** Every figure in Section 6 comes from one LLM evaluated against one schema. No cross-model or cross-schema replication has been carried out. The WooCommerce cross-schema figures reported in earlier drafts of this thesis have been withdrawn: no corresponding artifact supporting them exists in this repository, and they should not be cited until one does.
- **SQL-parity checking has not been extended to a differential test.** The comparison in §6.3.1 checks compiled SQL *text* against nopCommerce's own report-service source, which found five silent-wrong-answer defects — now fixed and pinned by regression tests in `tests/test_platform_parity.py`. A stronger check exists and has not been run: executing both AEGIS's compiled queries and the platform's own report queries against a shared, seeded database and diffing the result sets directly. A text-level comparison can both miss a divergence that only shows up in the returned rows and flag a textual difference that produces an identical result; a differential test would settle both failure modes at once.
- **No user study.** The plan-verbalisation and clarification step described in Section 4 is motivated by NaLIR's finding (Li & Jagadish, 2014) that users, without an interactive confirmation step, correctly detected only 7 of 32 wrong system answers. AEGIS's own effect on this failure mode has not been measured. A Jeopardy-style protocol, of the kind used by DataTone (Gao et al., 2015) — showing a participant a fact and asking them to construct the widget that demonstrates it, rather than giving them a question to ask — is the natural design for that study, since it avoids priming participants with task wording that would leak the intended query.
- **Semantic layer construction cost.** Every AEGIS deployment requires a domain-specific semantic layer built by someone with both business knowledge and schema access. The e-commerce prototype took ~40 person-hours. Organizations without this expertise, or with rapidly evolving schemas, may find the maintenance burden significant. AEGIS is not a zero-configuration system; vocabulary injection removes the need to separately curate synonym lists, but not the need to define the underlying metrics, dimensions, and joins.
- **Cannot answer arbitrary SQL questions.** By design, AEGIS only answers questions that map to a supported analytics primitive with an approved metric and dimension. Ad-hoc queries, multi-level nested aggregations, or requests for data fields not in the semantic layer will fail with a coverage error. This is a deliberate trade-off, distinct from the configuration-boundary coverage gaps described above.
- **New analytical patterns require developer effort.** Adding a pattern not yet in the template library requires a developer with SQL knowledge to write and validate a new template; it cannot be done by extending the semantic layer alone.
- **Quality depends on LLM intent extraction.** The safety guarantees apply to compilation and execution, not intent extraction quality. A model that misclassifies a request will produce a structurally safe but semantically wrong query.
- **Benchmark selection.** The custom benchmark is necessary because standard benchmarks (Spider, BIRD) do not evaluate adversarial safety or adherence to business logic.
- **Architectural overhead.** The compiler module executes in <10 ms, representing less than 1% of total request latency.
- **Semantic layer scalability.** Modern 128k context windows can hold ~2,500 distinct metric and dimension definitions; most enterprise deployments expose fewer than 500 core concepts. Future work could incorporate RAG for massive-scale deployments.
- **Database agnosticism.** Currently generates MySQL syntax; supporting PostgreSQL or SQL Server requires only extending the compiler module.
- **Storage persistence.** Prototype uses JSON flat files; the widget registry interface is designed to swap to PostgreSQL for production.
- **Multi-turn conversation.** AEGIS currently treats each request independently. Contextual carryover is planned as the next major feature.
- **Vocabulary injection limitations.** Highly specialized domain terminology may require supplementary few-shot examples in the prompt.

---

## 9. Conclusion

AEGIS is a system for turning plain-English reporting requests into dynamic, refreshable dashboard widgets over relational databases. Its contribution has three parts.

The first is architectural. The LLM is confined to understanding the question; query construction, chart selection, and widget storage are performed by fixed templates and rules downstream of it. Because the compiler emits SQL only by expanding a closed set of templates over a curated semantic layer, and never by interpolating model-produced text, unsafe SQL is excluded by construction rather than filtered after the fact (§4.2, Proposition 1) — a guarantee that holds for any model, including one that behaves adversarially. This is the sense in which the design converts a probabilistic property into a structural one.

The second is a pair of mechanisms for the boundary of that vocabulary. Vocabulary injection removes the manually maintained synonym list, but in doing so makes the model structurally unable to report that a request falls outside the layer it was shown. Coverage analysis recovers that signal by running against the user's original wording rather than the model's output, and the ANSWER / CLARIFY / REJECT channel gives the pipeline somewhere to put the answer "this cannot be expressed here" — an outcome the original design had no way to represent, and therefore silently converted into a confident wrong answer.

The third is evaluative, and it is the part that most changed this thesis. Scoring a governed reporting system by aggregate accuracy punishes a correct refusal and rewards a confident wrong answer, so this work reports abstention recall always beside false-abstention rate, over an explicitly stratified answerable/should-decline split. Measured that way, the system reproduced all twenty of nopCommerce's standard admin reports from natural language (§6.3) while declining every out-of-scope probe in the benchmark — abstention recall 100% (52/52) at a false-abstention rate of 25.5% (14/55), the latter having fallen from 61.8% through a sequence of implementation and configuration fixes that changed no architectural component (§6.5). Several figures from earlier drafts of this work did not survive the same standard and are withdrawn in §6.1 rather than restated.

The residual gap is a configuration boundary rather than an architectural one: every concept declined so far as unmapped corresponds to a table the schema already contains and the semantic layer had not yet been configured to expose. AEGIS is therefore built for environments where data privacy, consistent reporting definitions, and daily reuse of saved reports matter more than unlimited query flexibility — and where a system that says "I cannot answer that" is worth more than one that always answers.

---

## Declarations

- **Funding:** No funding was received for this study.
- **Conflict of Interest:** The author declares no conflict of interest.
- **Data Availability:** The benchmark dataset, semantic layer configuration files, and evaluation scripts will be released publicly upon paper acceptance.
- **Code Availability:** The AEGIS prototype implementation will be released as open-source software upon paper acceptance.

---

## References

Affolter, K., Stockinger, K., & Bernstein, A. (2019). A comparative survey of recent natural language interfaces for databases. *The VLDB Journal*, *28*, 793–819.

Deng, D., Wu, A., Qu, H., & Wu, Y. (2023). DashBot: Insight-driven dashboard generation based on deep reinforcement learning. *IEEE Transactions on Visualization and Computer Graphics*, *29*(1), 690–700.

Gao, T., Dontcheva, M., Adar, E., Liu, Z., & Karahalios, K. G. (2015). DataTone: Managing ambiguity in natural language interfaces for data visualization. *UIST*, 489–500.

Lehmann, C., Kehlbeck, R., Fekete, J.-D., & Deussen, O. (2022). Building natural language interfaces for databases in practice. *SSDBM*, Article 20.

Li, F., & Jagadish, H. V. (2014). Constructing an interactive natural language interface for relational databases. *PVLDB*, *8*(1), 73–84.

Li, J. et al. (2023). Can large language models serve as a database interface? *NeurIPS*, *36*.

Liu, M. et al. (2026). A systematic review of natural language interfaces for databases. *Frontiers of Computer Science*, *20*, 2011623.

Luo, Y. et al. (2021). Synthesizing NL2VIS benchmarks from NL2SQL benchmarks. *SIGMOD*, 1235–1247.

Narechania, A., Srinivasan, A., & Stasko, J. (2021). nl4dv: A toolkit for generating analytic specifications for data visualization. *IEEE TVCG*, *27*(2), 369–379.

OpenAI. (2024). *Introducing structured outputs in the API*.

Scholak, T., Schucher, N., & Bahdanau, D. (2021). PICARD: Parsing incrementally for constrained auto-regressive decoding. *EMNLP*, 9895–9901.

Setlur, V. et al. (2016). Eviza: A natural language interface for visual analysis. *UIST*, 365–377.

Shalaan, H. S. et al. (2025). G-SQL: A schema-aware and rule-guided approach for NL-to-SQL. *IEEE Access*, *13*, 158520–158534.

Su, X. et al. (2026). A robust NL text-to-SQL generation framework. *Scientific Reports*, *16*, Article 7892.

Wang, B. et al. (2020). RAT-SQL: Relation-aware schema encoding for text-to-SQL. *ACL*, 7567–7578.

Wang, Y. et al. (2020). DataShot: Automatic generation of fact sheets from tabular data. *IEEE TVCG*, *26*(1), 895–905.

Wu, A. et al. (2022). MultiVision: Designing analytical dashboards with deep learning. *IEEE TVCG*, *28*(1), 162–172.

Yu, T. et al. (2018). Spider: A large-scale human-labeled dataset for text-to-SQL. *EMNLP*, 3911–3921.

Yu, T. et al. (2019a). SParC: Cross-domain semantic parsing in context. *ACL*, 4511–4523.

Yu, T. et al. (2019b). CoSQL: A conversational text-to-SQL challenge. *EMNLP*, 1962–1979.

Zhong, V., Xiong, C., & Socher, R. (2018). Seq2SQL: Generating structured queries from NL using reinforcement learning. *ICLR*.

Shi, D. et al. (2021). Calliope: Automatic visual data stories with Monte Carlo tree search. *IEEE TVCG*, *27*(2), 464–474.

Shailesh, G. N. et al. (2025). Conversational BI: Natural language interface to business dashboards. *IJERTV*, *14*(12).
