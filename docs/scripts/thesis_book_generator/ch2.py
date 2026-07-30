# -*- coding: utf-8 -*-
"""Chapter 2: Literature Review and Research Gap."""
from build_thesis import (add_para, add_chapter_heading, add_section_heading,
                           add_table_with_caption, page_break)
from refs import cite


def chapter2(doc):
    add_chapter_heading(doc, 2, "Literature Review and Research Gap")

    add_para(doc,
              "This chapter surveys prior work across six areas that bear on AEGIS's design: "
              "natural language interfaces to databases, neural text-to-SQL and its benchmarks, "
              "constrained decoding and recent hybrid NL-to-SQL systems, natural language for "
              "visualization, dashboard generation, and semantic layers for controlled analytics. It "
              "closes with a review of recent practitioner and adoption-focused literature on "
              "AI-powered dashboards, a comparative summary table, and an explicit research gap "
              "analysis. Twenty-nine sources are reviewed. Two citations present in an earlier draft "
              "of this work could not be verified against any locally held source document and have "
              "been removed; the corresponding source files are instead cited under their true, "
              "verified titles and authors, which is disclosed at the relevant point in Sections 2.3 "
              "and 2.7.", space_after=0)

    # ---------------------------------------------------------------- 2.1
    add_section_heading(doc, "2.1", "Natural Language Interfaces to Databases")
    add_para(doc,
              "Natural language database interfaces have been studied for over four decades. Early "
              "systems such as LUNAR and TEAM used hand-crafted grammars and domain-specific "
              "ontologies to parse queries. These systems were brittle under vocabulary variation, but "
              "they established the core insight that query understanding requires an explicit bridge "
              "between natural language and schema semantics, rather than treating the schema as "
              "implicit context for a general-purpose language model.", space_after=10)
    add_para(doc,
              f"Affolter et al. {cite('affolter19')} provide the most systematic comparison of this "
              "literature to date. They define a ten-question benchmark of increasing complexity "
              "(joins, filters, aggregation, negation, subqueries) and evaluate 24 NLIDBs across four "
              "architectural classes: keyword-based, pattern-based, parsing-based, and grammar-based. "
              "Keyword-based systems answer only simple filter queries and fail on aggregation or "
              "subqueries; grammar-based systems such as SQUALL and SPARKLIS achieve the broadest "
              "coverage but require users to learn a constrained query vocabulary; parsing-based, "
              "ontology-driven systems handle free natural language well but stumble on negation and "
              "multi-level subqueries. Their survey never evaluates SQL injection, hallucination, or "
              "adversarial safety, a gap this thesis addresses directly.", space_after=10)
    add_para(doc,
              f"NaLIR {cite('li_jagadish14')} is an important modern NLIDB because it treats ambiguity "
              "as a problem to expose rather than to silently resolve. NaLIR parses a query into a "
              "grammar-constrained intermediate “query tree” that maps deterministically to "
              "SQL, and when parsing is ambiguous it presents the user with a short multiple-choice "
              "interaction rather than guessing. In a user study on the Microsoft Academic Search "
              "dataset, users with NaLIR's interactive step correctly completed 88 of 98 tasks, "
              "versus 56 of 98 using MAS's native faceted-search interface, and only about 68 of 98 "
              "without the interactive step. Without interaction, most wrong answers went undetected "
              "by users. NaLIR anticipates AEGIS's separation of language understanding from SQL "
              "construction, but its correctness still depends on the user actively catching and "
              "correcting ambiguous parses; AEGIS instead restricts the LLM to a fixed, pre-approved "
              "vocabulary so that incorrect or unsafe SQL is structurally harder to produce in the "
              "first place, and it persists results as reusable widgets, which NaLIR does not.",
              space_after=10)
    add_para(doc,
              "Lehmann et al. describe Veezoo, a commercial analytics platform built around an "
              "auto-generated, user-editable Knowledge Graph that matches keywords to database "
              "concepts, combined with entity linking, relation extraction, and an ML-based ranking "
              "model over candidate logical forms. A controlled experiment with 16 users and an "
              "adversarially unoptimized configuration found a median of two query reformulations "
              "needed to reach a correct answer. Veezoo's Knowledge Graph is structurally analogous to "
              f"AEGIS's semantic layer {cite('lehmann22')}, but Veezoo still compiles candidate logical "
              "forms into open-ended SQL and relies on iterative dialogue to recover from wrong "
              "answers, a generate-fail-retry interaction pattern. AEGIS instead aims to prevent "
              "incorrect or unsafe generation up front through a fixed template library.", space_after=10)
    add_para(doc,
              f"Liu and Xu {cite('liu_xu25')} provide the most recent systematic review, organizing "
              "NLIDB research around a three-stage pipeline of preprocessing, understanding, and "
              "translation. Their review is the only one of the reviewed surveys to document empirical "
              "SQL-injection risk directly: it discusses TrojanSQL, a backdoor-based injection attack "
              "framework against text-to-SQL systems that the authors report achieves a high attack "
              "success rate and is difficult to defend against. Their recommended mitigations, chiefly "
              "vetted training data and “additional layers of security or filtering,” are "
              "general and non-constructive. AEGIS operationalizes exactly this recommendation: by "
              "never allowing the LLM to generate SQL text and compiling every query deterministically "
              "from a fixed template library, the class of attack Liu and Xu describe cannot reach the "
              "SQL layer regardless of what the LLM outputs.", space_after=0)

    # ---------------------------------------------------------------- 2.2
    add_section_heading(doc, "2.2", "Neural Text-to-SQL and Benchmark Progress")
    add_para(doc,
              f"The field shifted decisively toward neural approaches with Seq2SQL {cite('zhong18')}, "
              "which combined a SQL-structured decoder (aggregation classifier, SELECT-column pointer, "
              "WHERE-clause pointer) with reinforcement learning driven by in-the-loop query execution, "
              "and released WikiSQL, 80,654 question-SQL-table triples restricted to single-table "
              "SELECT/aggregation/WHERE queries. Seq2SQL reached 59.4% execution accuracy on WikiSQL "
              "and reduced invalid-SQL generation from roughly 7.9% to 4.8% relative to a prior "
              "sequence-to-sequence baseline, demonstrating that constraining a model's output "
              "structure improves both accuracy and validity. AEGIS extends this same insight to its "
              "logical conclusion: rather than a network that still emits SQL tokens with residual "
              "freedom to hallucinate columns, AEGIS removes SQL emission from the model entirely.",
              space_after=10)
    add_para(doc,
              f"Spider {cite('yu_spider18')} exposed how far this problem remained from solved. Its "
              "10,181 questions and 5,693 unique SQL queries span 200 multi-table databases with a "
              "strict train/test database split, forcing genuine generalization to unseen schemas. The "
              "best baseline of the time reached only 12.4% exact-match accuracy under this "
              "cross-domain setting, and accuracy degraded further as the number of foreign keys grew. "
              f"SParC {cite('yu_sparc19')} and CoSQL {cite('yu_cosql19')} extended Spider's databases to "
              "conversational, multi-turn settings: SParC's best model reached only 20.2% exact-match "
              "accuracy over individual questions in a sequence, dropping sharply with turn number, and "
              "CoSQL found that roughly 40% of realistic user questions could not be directly converted "
              "to SQL at all, requiring clarification, inference, or a coverage rejection. AEGIS's "
              "semantic layer effectively hard-codes the ambiguous-or-unanswerable detection that "
              "CoSQL's models struggle to learn, by rejecting or clarifying any intent that does not "
              "map onto its approved vocabulary rather than attempting to freely interpret and generate "
              "SQL for arbitrary questions.", space_after=10)
    add_para(doc,
              f"BIRD {cite('li_bird23')} closed the gap between academic benchmarks and production "
              "conditions by testing 95 real, large databases (up to 33.4 GB) with expert-written "
              "domain-knowledge annotations. Even the best evaluated model, GPT-4 combined with "
              "DIN-SQL prompting, reached only 55.9% execution accuracy against a 92.96% human-expert "
              "ceiling, and the dominant failure modes were wrong schema linking (41.6% of errors) and "
              "misunderstanding database content or values (40.8%). This is the strongest available "
              "evidence for AEGIS's core motivating claim: even frontier LLMs generating free-form SQL "
              "against real, large schemas hallucinate schema elements and misinterpret values in "
              "roughly two out of every five cases. AEGIS avoids this failure class by never asking the "
              "LLM to resolve schema, joins, or literal values at all; it only classifies a request into "
              "a fixed, pre-vetted vocabulary, after which a deterministic compiler resolves every join "
              "and expression.", space_after=10)
    add_para(doc,
              f"RAT-SQL {cite('wang_rat20')} is the most sophisticated attempt within the free-form "
              "generation paradigm to solve schema linking directly, using relation-aware self-attention "
              "over a typed schema graph and a grammar-constrained decoder, reaching 57.2% exact-match "
              "accuracy on Spider (65.6% with BERT augmentation). Even so, oracle analysis attributed "
              "72-81% of its remaining errors to wrong column or table selection or wrong SQL structure. "
              "RAT-SQL's schema graph plays a role analogous to AEGIS's semantic layer, but is used to "
              "guide free SQL token generation rather than to constrain a bounded classification space; "
              "its grammar constraint guarantees syntactic validity only, not semantic correctness, "
              "safety, or injection-proofing, which remain unaddressed by any paper in this section.",
              space_after=0)

    # ---------------------------------------------------------------- 2.3
    add_section_heading(doc, "2.3", "Constrained Decoding and Recent NL-to-SQL Systems")
    add_para(doc,
              f"PICARD {cite('scholak21')} is the closest prior technique to AEGIS's philosophy of "
              "restricting model output, and the most important contrast case for this thesis. It is "
              "an inference-time, model-agnostic constrained-decoding method that uses incremental "
              "parsing during beam search to reject any candidate token that would make the partial SQL "
              "output invalid against a grammar and the target schema. Applied to T5-3B, PICARD reduced "
              "the invalid-SQL rate on the Spider development set from roughly 12% to 2% and raised "
              "execution accuracy to a then state-of-the-art 79.3%. Even at its strictest setting, "
              "however, PICARD does not eliminate invalid SQL, and because the LLM still writes every "
              "character of the SQL string, any semantic bug not caught by the grammar or schema check "
              "(a wrong join, a wrong aggregation, a wrong business definition of a metric) can pass "
              "through as syntactically valid but analytically wrong SQL. PICARD constrains what tokens "
              "the LLM may emit while it writes SQL; AEGIS removes SQL-writing from the LLM's role "
              "entirely, which is a categorically stronger guarantee because it eliminates an entire "
              "failure class rather than reducing its probability at the token level.", space_after=10)
    add_para(doc,
              f"G-SQL {cite('shalaan25')} is the closest architectural precedent to AEGIS among the "
              "reviewed systems: a rule-based, template-driven SQL generator built on a structured, "
              "curated schema representation and a domain-specific synonym dictionary, deliberately "
              "avoiding a neural component that writes SQL directly. On the IMDB, Yelp, and MAS "
              "benchmarks it achieved 100% execution accuracy on easy queries across all three, but "
              "accuracy fell to 45-55% on extra-hard queries requiring nested reasoning. AEGIS builds on "
              "the same core insight, that a curated vocabulary plus deterministic clause assembly "
              "yields much higher executability than free-form generation, but replaces G-SQL's "
              "classical NLP pipeline (dependency parsing, GloVe embeddings) with an LLM-based intent "
              "extractor, and adds a persisted, reusable dashboard-widget layer that G-SQL does not "
              "have.", space_after=10)
    add_para(doc,
              f"A generative-AI-based conversion system by Jha et al. {cite('jha25')} illustrates the "
              "pattern this thesis argues against: a sequence-to-sequence model directly emits SQL text "
              "from unconstrained natural language, with a rule-based module added afterward only to "
              "produce a plain-language explanation of whatever SQL the generator happened to produce. "
              "No accuracy or robustness evaluation is reported for the system. The explanation module "
              "is a post-hoc rationalization, not a safety mechanism, and cannot prevent a hallucinated "
              "table name or an injection-prone output; it exemplifies a broader gap in practitioner "
              "literature, where generative NL-to-SQL tools are shipped without a rigorous safety or "
              "correctness evaluation.", space_after=10)
    add_para(doc,
              "A note on evaluation methodology is warranted here. During the preparation of this "
              "thesis, a source file in the project's reference collection previously catalogued as "
              "“Su et al. (2026), a robust natural language text-to-SQL generation framework” "
              "was found on inspection to actually contain a different, unrelated paper. The true "
              f"content of that file is Pinna et al. {cite('pinna25')}, which proposes the Query "
              "Affinity Score, a continuous metric combining code-embedding similarity and executed-"
              "result-table similarity, arguing that binary exact-match and execution-accuracy metrics "
              "hide partial correctness (for example, a dropped DISTINCT keyword or a reversed sort "
              "order can score as completely wrong under a binary metric despite near-identical SQL "
              "text). This citation has been corrected accordingly and is retained here because it is "
              "a genuinely useful caution for Chapter 5's evaluation design: AEGIS's own safety property "
              "makes most of the failure modes Pinna et al. study architecturally impossible in the "
              "first place, since clauses come from vetted templates rather than free generation, but "
              "their semantic-versus-structural distinction is a useful frame for grading intent "
              "extraction accuracy rather than treating it as pass or fail.", space_after=0)

    # ---------------------------------------------------------------- 2.4
    add_section_heading(doc, "2.4", "Natural Language for Visualization")
    add_para(doc,
              f"A parallel research stream targets chart generation rather than SQL generation. nl4dv "
              f"{cite('narechania21')} is the closest visualization-side precedent to AEGIS's design: a "
              "toolkit that maps natural language queries to a small, fixed set of five analytic tasks "
              "and a rule-based attribute-task-visualization mapping table, returning a structured JSON "
              "specification rather than free-form chart code. It reports response times of 1-18 "
              "seconds on small in-memory datasets, but conducts no formal accuracy benchmark, has no "
              "SQL-safety or database-permission layer at all (it operates purely on an in-memory "
              "dataset, never a live relational schema), and produces one-off specifications with no "
              "notion of a persistent, refreshable dashboard object.", space_after=10)
    add_para(doc,
              f"DataTone {cite('gao15')} established the alternative philosophy of surfacing ambiguity "
              "to the user through interactive “ambiguity widgets” rather than silently "
              "resolving it, covering six decision points from attribute recognition to chart-type "
              "choice. In a comparative study against IBM Watson Analytics, participants completed "
              "significantly more correct facts with DataTone (5.43 versus 2.00 facts, p < 0.01). AEGIS "
              "and DataTone address the same underlying ambiguity problem with opposite strategies: "
              "DataTone generates many candidate interpretations and lets the user disambiguate "
              "after the fact, while AEGIS restricts the LLM's extraction target to a small curated "
              "vocabulary up front, preventing many classes of ambiguity from arising at all. DataTone "
              "is also explicitly limited to single-table, non-relational data and offers no "
              "persistence mechanism.", space_after=10)
    add_para(doc,
              f"nvBench {cite('luo21')} demonstrates the risk of the opposite extreme: it synthesizes a "
              "25,750-pair benchmark from Spider's SQL queries and trains ncNet, a Transformer that "
              "translates natural language directly, end to end, into a Vega-Zero visualization "
              "specification with no deterministic or auditable compilation step in between. "
              "Correctness depends entirely on the trained model's generalization, with no template-"
              "based guarantee against a malformed or unsafe query, and the output is a single static "
              "chart per query rather than a persisted artifact. Eviza extended natural language "
              "interaction to already-rendered visualizations, allowing conversational refinement of an "
              f"existing chart {cite('setlur16')}, a concept AEGIS's clarification model draws on when "
              "a request is ambiguous. Kavaz et al.'s scoping review of chatbot-based visualization "
              f"interfaces {cite('kavaz23')} found that across 20 surveyed systems, 90% supported only "
              "low-level queries, half used fixed rather than adaptive visual mapping, and only 4 of 20 "
              "supported any follow-up or conversational interaction, confirming that most systems in "
              "this space regenerate a visualization each time rather than treating a validated "
              "query-chart pairing as a durable, reusable object, precisely the gap AEGIS's widget "
              "persistence model closes.", space_after=0)

    # ---------------------------------------------------------------- 2.5
    add_section_heading(doc, "2.5", "Dashboard Generation")
    add_para(doc,
              f"Dashboard generation as an automated design problem has attracted growing attention. "
              f"DashBot {cite('deng23')} formulates dashboard construction as a Markov decision process "
              "solved with deep reinforcement learning (A3C), using a preliminary study of 90 real "
              "Tableau and Power BI dashboards to define reward functions for presentation quality "
              "(diversity, parsimony) and statistical insight (trend, correlation, comparison). A user "
              "study found DashBot preferred over a prior deep-learning dashboard generator, MultiVision "
              f"{cite('wu22')}, on 76-88% of quality dimensions. Both systems, however, operate without "
              "any natural language input or intent layer: a user cannot ask a question in English; the "
              "agent instead explores a dataset unprompted. Neither faces an LLM-generated-SQL attack "
              "surface at all, because neither generates SQL from user language, which is precisely the "
              "problem AEGIS's semantic layer and compiler are built to solve and that DashBot's "
              f"architecture never encounters. DataShot {cite('wang_datashot20')} and Calliope "
              f"{cite('shi21')} used statistical fact extraction followed by template-based layout to "
              "generate narrative data documents, again illustrating that rule-based, non-AI logic is a "
              "well-precedented and reliable way to drive downstream presentation once the underlying "
              "facts are established, reinforcing AEGIS's own decision to use a deterministic, "
              "rule-based visualization selector rather than a learned one.", space_after=0)

    # ---------------------------------------------------------------- 2.6
    add_section_heading(doc, "2.6", "Semantic Layers and Controlled Analytics")
    add_para(doc,
              "A semantic layer is a business-logic abstraction that maps business concepts to the "
              "actual database tables and columns. Commercial tools such as dbt Metrics, Looker LookML, "
              "and Apache Superset implement semantic layers in different ways, but the research "
              "literature has treated the semantic layer primarily as a convenience for query authoring "
              f"rather than as a safety mechanism. Lehmann et al.'s Veezoo {cite('lehmann22')}, already "
              "discussed in Section 2.1, is the clearest exception, and even there the Knowledge Graph "
              "constrains matching rather than replacing SQL generation outright. Structured output "
              f"enforcement for LLMs {cite('openai24')} has been shown to improve the reliability of "
              "typed object generation, which AEGIS relies on for intent extraction: the LLM's output is "
              "constrained to a fixed JSON schema before any downstream validation occurs. No prior work "
              "reviewed in this chapter uses a semantic layer as the primary safety mechanism for an "
              "LLM-assisted reporting system, in the specific sense of replacing SQL generation with "
              "deterministic compilation from a governed vocabulary; this is the gap AEGIS's "
              "architecture is built to close.", space_after=0)

    # ---------------------------------------------------------------- 2.7
    add_section_heading(doc, "2.7", "AI-Powered Dashboard Adoption, Governance, and Conversational BI")
    add_para(doc,
              "Beyond the technical NL-to-SQL and NL-to-visualization literature, a body of recent "
              "practitioner-oriented and management-focused work addresses the adoption, governance, "
              "and business impact of AI-powered dashboards. This literature is reviewed here because it "
              "was identified through a systematic re-examination of this thesis's full reference "
              "collection, and because it usefully situates AEGIS's technical contribution within the "
              "broader question of why organizations want AI-assisted analytics in the first place.",
              space_after=10)
    add_para(doc,
              f"Häikiö {cite('haikio24')} examines how organizations should govern AI-powered executive "
              "dashboards, concluding that no mature, comprehensive AI-governance framework yet exists "
              "and proposing adapted IT-governance processes (drawing on COBIT 2019 and the Technology-"
              f"Organization-Environment model) as an interim approach. Saidur {cite('saidur25')} "
              "reports a large-sample quantitative study of 150 U.S. enterprises, finding that "
              "AI-enhanced BI dashboards correlated with substantial gains in forecast accuracy (78.1% "
              "to 91.2%) and marketing return on investment (124% to 168%) over a 24-month period. "
              "Neither paper addresses natural-language query translation, SQL generation, or injection "
              "safety; their relevance to AEGIS is limited to the shared premise that persistent "
              "dashboards, rather than one-off chat answers, are the effective vehicle for delivering "
              "AI-derived insight to decision-makers, which is one motivation for AEGIS's widget-"
              "persistence design.", space_after=10)
    add_para(doc,
              f"Mujeeb et al. {cite('mujeeb25')} propose, at the conceptual level, a four-layer "
              "conversational business-intelligence architecture whose query-planning layer explicitly "
              "combines “template-based SQL generation” for predictable requests with "
              "“transformer-based synthesis” for complex ones, followed by a separate "
              "governance layer that validates queries after generation. The authors state plainly that "
              "the architecture has not been implemented or validated. This is a useful reference point "
              "precisely because it shows the field converging on a hybrid template-plus-generation "
              "idea without committing to it or testing it: AEGIS's contribution is to commit fully to "
              "the deterministic-compilation path for every query expressible in its semantic layer, "
              "removing the free-generation fallback entirely and, with it, the need for a downstream "
              "governance layer to catch what the LLM might have produced incorrectly.", space_after=10)
    add_para(doc,
              "A second file-naming discrepancy was found in this reference collection: a source "
              "catalogued as “Shailesh, G. N. et al. (2025), Conversational BI: Natural language "
              "interface to business dashboards” was found on inspection to actually be a different "
              f"work, Valkenburgh's master's thesis {cite('valkenburgh24')} on explanatory analytics. "
              "This citation is corrected accordingly, and the underlying paper turns out to be one of "
              "the most architecturally relevant sources in this collection: Valkenburgh's prototype "
              "computes causal-influence explanations for business metrics using a deterministic, "
              "non-AI formalism, and only afterward asks an LLM to narrate the already-correct "
              "structured result in natural language, never allowing the LLM to perform the underlying "
              "computation itself. A pre-study surveying ten commercial AI-BI products (including Power "
              "BI and Tableau) found that all of them could answer simple descriptive queries but none "
              "could correctly answer explanatory, “why is X high” queries without manual "
              "pre-configuration, direct evidence that unconstrained LLM reasoning fails at exactly the "
              "class of task AEGIS targets. Valkenburgh's design and AEGIS arrive at the same governing "
              "principle independently: do not trust the model to perform the analytical computation; "
              "let a deterministic algorithm compute the correct result, and restrict the model's role "
              "to a bounded, downstream task. Valkenburgh's deterministic layer operates on a single "
              "pre-loaded spreadsheet rather than a live relational database, so it has no SQL-injection "
              "surface and produces one-off, non-persistent text answers rather than stored, refreshable "
              "widgets, both of which AEGIS's architecture addresses.", space_after=10)
    add_para(doc,
              f"Finally, Chinnappaiyan {cite('chinnappaiyan25')} surveys “conversational "
              "analytics” as a general architectural pattern (natural language understanding, "
              "semantic layer, query generation, response generation) and identifies fine-grained "
              "access control versus conversational fluency as an unresolved tension in current systems, "
              "without proposing or evaluating a concrete mechanism to resolve it. This is precisely the "
              "gap AEGIS's design closes by construction: the Permission Rewriter (Chapter 3) enforces "
              "row-level access control after the LLM has already produced its intent, so conversational "
              "fluency and access control are not in tension because the LLM never has an opportunity to "
              "influence the permission predicate.", space_after=0)

    # ---------------------------------------------------------------- 2.8
    add_section_heading(doc, "2.8", "Comparative Summary")
    add_para(doc,
              "Table 4 positions AEGIS against the systems most central to Sections 2.1-2.6 across "
              "seven properties: whether the system parses natural language at all, whether it defines "
              "an explicit semantic layer, whether SQL generation is structurally safe rather than "
              "merely accuracy-optimized, whether it selects or generates a visualization, whether "
              "results persist as reusable widgets, whether unanswerable requests are explicitly "
              "validated against a coverage boundary, and the nature of its evaluation.", space_after=10)
    add_table_with_caption(
        doc, "Table 4: Comparative summary of related NL-to-database and NL-to-visualization systems.",
        ["System", "NL Parsing", "Semantic Layer", "Safe SQL", "Visualization",
         "Widget Persistence", "Coverage Validation", "Evaluation"],
        [
            ["Spider / BIRD / Seq2SQL", "Yes", "-", "-", "-", "-", "-", "Benchmark only"],
            ["RAT-SQL / PICARD", "Yes", "-", "Partial", "-", "-", "-", "Benchmark only"],
            ["NaLIR", "Yes", "-", "-", "-", "-", "-", "User study"],
            ["Veezoo (Lehmann et al.)", "Yes", "Yes", "-", "-", "-", "-", "User study"],
            ["G-SQL", "Yes", "Partial", "Partial", "-", "-", "-", "Benchmark only"],
            ["nl4dv", "Yes", "-", "-", "Yes", "-", "-", "In-memory data"],
            ["DataTone", "Yes", "-", "-", "Yes", "-", "-", "User study"],
            ["DashBot / MultiVision", "-", "-", "-", "Yes", "Partial", "-", "Synthetic / user study"],
            ["AEGIS (this thesis)", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Production (nopCommerce)"],
        ])
    page_break(doc)

    # ---------------------------------------------------------------- 2.9
    add_section_heading(doc, "2.9", "Research Gap Analysis")
    add_para(doc,
              "Three consistent gaps emerge from this review, and each maps directly onto a design "
              "decision made in Chapter 3.", space_after=10)
    add_para(doc,
              "First, no system reviewed in Sections 2.1-2.3 treats SQL-generation safety as a "
              "structural property rather than an accuracy metric. Every neural text-to-SQL system, "
              "from Seq2SQL through RAT-SQL and PICARD, is evaluated purely on exact-match or execution "
              "accuracy against a benchmark; none reports an injection rate, and only Liu and Xu's "
              "review even discusses adversarial SQL injection as a named threat, without proposing an "
              "architectural defense. AEGIS closes this gap by removing SQL generation from the LLM's "
              "output space entirely (Section 3.4) and evaluating an explicit unsafe-SQL rate against a "
              "direct LLM-to-SQL baseline (Chapter 5), rather than relying on accuracy as a proxy for "
              "safety.", space_after=10)
    add_para(doc,
              "Second, no system in Sections 2.1, 2.4, or 2.5 combines a governed semantic vocabulary "
              "with persistent, refreshable output. Veezoo and G-SQL define curated vocabularies but "
              "produce one-off answers; nl4dv, DataTone, and nvBench produce one-off visualizations; "
              "DashBot and MultiVision generate multi-chart dashboards but with no natural-language "
              "input and no notion of a saved, reusable artifact tied to a specific user question. "
              "AEGIS's widget engine (Section 3.11) closes this gap directly, motivated by the "
              "formative-study finding that 61% of real reporting requests are recurring (Section 3.2).",
              space_after=10)
    add_para(doc,
              "Third, the practitioner and adoption-focused literature reviewed in Section 2.7 "
              "recognizes the tension between conversational flexibility and governed access control "
              "(Chinnappaiyan) and gestures at hybrid template-plus-generation designs (Mujeeb et al.) "
              "without building or evaluating a fully deterministic alternative. Valkenburgh's "
              "independent arrival at the same “let a deterministic layer compute the answer, let "
              "the model only narrate it” principle, in an unrelated domain (spreadsheet-based "
              "explanatory analytics rather than relational-database reporting), is the strongest "
              "external corroboration available in this review that AEGIS's central design decision is "
              "not idiosyncratic to this thesis but reflects a pattern independently discovered wherever "
              "researchers have taken LLM reliability seriously as an engineering constraint rather than "
              "an accuracy target to be improved.", space_after=0)
    page_break(doc)
