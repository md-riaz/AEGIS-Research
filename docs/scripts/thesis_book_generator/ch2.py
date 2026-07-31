# -*- coding: utf-8 -*-
"""Chapter 2: Literature Review and Research Gap."""
from build_thesis import (add_para, add_chapter_heading, add_section_heading,
                           add_table_with_caption, page_break)
from refs import cite


def chapter2(doc):
    add_chapter_heading(doc, 2, "Literature Review and Research Gap")

    add_para(doc,
              "This chapter reviews the sources most directly comparable to AEGIS, grouped by theme: "
              "natural language interfaces to databases, neural and LLM-based text-to-SQL, natural "
              "language for visualization and dashboards, and applied conversational business "
              "intelligence. Closely related sources are discussed together rather than one at a time "
              "where they make the same architectural point. Sources only loosely adjacent to AEGIS's "
              "technical contribution (general business-adoption surveys, dashboard-governance "
              "literature, evaluation-methodology papers unrelated to safety) are outside this review's "
              "scope.", space_after=0)

    # ---------------------------------------------------------------- 2.1
    add_section_heading(doc, "2.1", "Natural Language Interfaces to Databases")
    add_para(doc,
              f"Two systematic surveys frame this literature. Affolter et al. {cite('affolter19')} "
              "benchmark 24 NLIDBs against ten questions of increasing complexity across four "
              "architectural classes (keyword, pattern, parsing, grammar-based); grammar-based systems "
              "achieve the broadest coverage but require users to learn a constrained vocabulary. Liu "
              f"and Xu's more recent review {cite('liu_xu25')} is the only one to name SQL-injection "
              "risk directly, discussing TrojanSQL, a backdoor injection attack the authors report is "
              "difficult to defend against, yet their only recommended mitigation is generic "
              "(“additional layers of security or filtering”), with no architectural defense "
              "proposed. Neither survey finds a system that treats safety as a structural property.",
              space_after=8)
    add_para(doc,
              f"NaLIR {cite('li_jagadish14')} and Veezoo {cite('lehmann22')} are the closest prior "
              "systems to AEGIS's use of a curated vocabulary. NaLIR parses a query into a "
              "grammar-constrained intermediate “query tree” and surfaces ambiguity to the user "
              "through a short multiple-choice interaction rather than guessing, correctly completing "
              "88 of 98 tasks versus 56 of 98 without this step. Veezoo constrains matching with an "
              "editable Knowledge Graph structurally analogous to a semantic layer, needing a median of "
              "two reformulations to reach a correct answer in a controlled study. Both, however, still "
              "compile into open-ended SQL and depend on user-facing dialogue to recover from a wrong "
              "query rather than preventing an unsafe one up front, and both produce one-off answers "
              "with no persistence.", space_after=0)

    # ---------------------------------------------------------------- 2.2
    add_section_heading(doc, "2.2", "Neural and LLM-Based Text-to-SQL")
    add_para(doc,
              f"Spider {cite('yu_spider18')} and BIRD {cite('li_bird23')} provide the clearest evidence "
              "that free-form generation is unreliable at scale. Spider's strict cross-domain "
              "train/test split found the best contemporary baseline reached only 12.4% exact-match "
              "accuracy on unseen schemas. BIRD went further, testing 95 real, large databases with "
              "expert-annotated domain knowledge: even GPT-4 combined with DIN-SQL prompting reached "
              "only 55.9% execution accuracy against a 92.96% human-expert ceiling, with wrong schema "
              "linking (41.6%) and misunderstood database values (40.8%) as the dominant failure modes.",
              space_after=8)
    add_para(doc,
              f"RAT-SQL {cite('wang_rat20')} and PICARD {cite('scholak21')} each constrain the same "
              "underlying generation approach without changing who authors the SQL. RAT-SQL encodes "
              "the schema as a relational graph via relation-aware self-attention, reaching 57.2% "
              "exact-match on Spider, yet oracle analysis attributes 72-81% of its remaining errors to "
              "wrong column or table selection. PICARD instead constrains decoding at the token level, "
              "cutting invalid SQL on Spider from roughly 12% to 2% — but the LLM still writes every "
              "character of the SQL string, so a semantic bug invisible to the grammar check (a wrong "
              "join, a wrong business formula) can still pass through as syntactically valid SQL.",
              space_after=8)
    add_para(doc,
              f"G-SQL {cite('shalaan25')} and TriSQL {cite('su_trisql26')} sit at opposite ends of the "
              "same spectrum and are the two closest points of comparison for AEGIS. G-SQL is "
              "rule-based and template-driven over a curated schema representation, deliberately "
              "avoiding a neural component that writes SQL directly; it reaches 100% execution accuracy "
              "on easy queries but falls to 45-55% on extra-hard ones. TriSQL is, at the time of "
              "writing, the state of the art: a three-stage LLM pipeline (schema selection, "
              "skeleton-first generation, complexity-aware refinement) reaching 82.2% execution "
              "accuracy on Spider. It is the sharpest possible contrast to AEGIS, precisely because it "
              "is state of the art and still has the LLM produce the final executable SQL directly, "
              "with no semantic layer and no reported safety evaluation.", space_after=0)

    # ---------------------------------------------------------------- 2.3
    add_section_heading(doc, "2.3", "Natural Language for Visualization and Dashboards")
    add_para(doc,
              f"nl4dv {cite('narechania21')} and DataTone {cite('gao15')} are the closest "
              "visualization-side precedents. nl4dv maps natural language to a small, fixed set of five "
              "analytic tasks via a rule-based mapping table, closely analogous to AEGIS's "
              "bounded-vocabulary design, but has no SQL-safety or permission layer at all since it "
              "operates only on an in-memory dataset, and produces a one-off specification with no "
              "persistence. DataTone instead surfaces ambiguity through interactive widgets rather than "
              "resolving it silently, significantly outperforming IBM Watson Analytics in a comparative "
              "study (5.43 vs. 2.00 correct facts, p < 0.01), but is limited to single-table data with "
              "no persistence mechanism.", space_after=8)
    add_para(doc,
              f"DashBot {cite('deng23')} composes multi-chart dashboards with deep reinforcement "
              "learning guided by design rules (diversity, parsimony) drawn from a study of 90 real "
              "dashboards. It has no natural-language input at all, and because it never generates SQL "
              "from user language, it never encounters the safety problem AEGIS is built to solve.",
              space_after=0)

    # ---------------------------------------------------------------- 2.4
    add_section_heading(doc, "2.4", "Applied Conversational Business Intelligence")
    add_para(doc,
              f"Two recent applied studies bookend AEGIS's design choice. Shailesh et al. "
              f"{cite('shailesh25')} describe a deployed Groq/LangChain assistant that gives an LLM "
              "direct SQL-execution tools and a self-correction retry loop — a live, working example of "
              "exactly the attack surface AEGIS's threat model closes (Section 3.5), with no reported "
              f"adversarial evaluation. Valkenburgh {cite('valkenburgh24')}, by contrast, independently "
              "arrives at AEGIS's central design principle in an unrelated domain: a deterministic, "
              "non-AI formalism computes a business explanation, and an LLM is used only to narrate the "
              "already-correct result. A pre-study in the same thesis found that ten commercial AI-BI "
              "products could all answer simple descriptive queries but none could correctly answer "
              "explanatory ones without manual reconfiguration — direct evidence that unconstrained LLM "
              "reasoning fails at exactly the class of task AEGIS targets.", space_after=0)

    # ---------------------------------------------------------------- 2.5
    add_section_heading(doc, "2.5", "Comparative Summary")
    add_table_with_caption(
        doc, "Table 4: Comparative summary of the most closely related systems.",
        ["System", "NL Parsing", "Semantic Layer", "Safe SQL", "Visualization",
         "Widget Persistence", "Coverage Validation", "Evaluation"],
        [
            ["Spider / BIRD", "Yes", "-", "-", "-", "-", "-", "Benchmark only"],
            ["RAT-SQL / PICARD", "Yes", "-", "Partial", "-", "-", "-", "Benchmark only"],
            ["G-SQL / TriSQL", "Yes", "Partial", "Partial", "-", "-", "-", "Benchmark only"],
            ["NaLIR", "Yes", "-", "-", "-", "-", "-", "User study"],
            ["Veezoo (Lehmann et al.)", "Yes", "Yes", "-", "-", "-", "-", "User study"],
            ["nl4dv / DataTone", "Yes", "-", "-", "Yes", "-", "-", "In-memory / user study"],
            ["DashBot", "-", "-", "-", "Yes", "Partial", "-", "Synthetic study"],
            ["Conversational BI Assistant\n(Shailesh et al.)", "Yes", "-", "-", "Yes", "-", "-",
             "Prototype demo"],
            ["AEGIS (this thesis)", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Production (nopCommerce)"],
        ])
    page_break(doc)

    # ---------------------------------------------------------------- 2.6
    add_section_heading(doc, "2.6", "Research Gap Analysis")
    add_para(doc,
              "Two gaps recur across every source reviewed above, including the state of the art. "
              "First, no system treats SQL-generation safety as a structural property rather than an "
              "accuracy metric: Spider, BIRD, RAT-SQL, PICARD, G-SQL, and TriSQL are all evaluated "
              "purely on exact-match or execution accuracy, and Shailesh et al.'s deployed assistant "
              "reports no adversarial evaluation at all despite giving an LLM direct database access. "
              "AEGIS closes this gap by removing SQL generation from the LLM's output space entirely "
              "(Section 3.4) and evaluating an explicit unsafe-SQL rate against a direct LLM-to-SQL "
              "baseline (Chapter 5), rather than relying on accuracy as a proxy for safety.",
              space_after=10)
    add_para(doc,
              "Second, no system combines a governed semantic vocabulary with persistent, refreshable "
              "output: NaLIR and Veezoo produce one-off answers, nl4dv and DataTone produce one-off "
              "visualizations, and DashBot has no natural-language input at all. AEGIS's widget engine "
              "(Section 3.11) closes this gap, motivated by the design-time observation that real "
              "reporting requests are often recurring rather than one-off (Section 3.2). Valkenburgh's "
              "independent arrival at "
              "AEGIS's “let a deterministic layer compute the answer” principle, in an unrelated "
              "domain, is the strongest external corroboration that this design decision reflects a "
              "pattern discovered wherever LLM reliability is treated as an engineering constraint "
              "rather than an accuracy target.", space_after=0)
    page_break(doc)
