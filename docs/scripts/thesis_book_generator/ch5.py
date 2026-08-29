# -*- coding: utf-8 -*-
"""Chapter 5: Results and Discussion."""
from build_thesis import (
    add_para,
    add_mixed_para,
    add_chapter_heading,
    add_section_heading,
    add_table_with_caption,
    page_break,
)
from refs import cite


def chapter5(doc):
    add_chapter_heading(doc, 5, "Results and Discussion")
    add_para(
        doc,
        "This chapter reports the AEGIS prototype evaluation using static "
        "nopCommerce artifacts committed with the repository. The evaluation separates "
        "four questions that are often mixed together. Can the system parse the "
        "request? Is the request inside the semantic layer? Does the compiled SQL run? "
        "Does the result match the expected business answer?",
        space_after=10,
    )
    add_para(
        doc,
        "The results are not a claim that AEGIS is perfect. A perfect score on every "
        "table would be suspicious for a prototype. The evaluation shows where the "
        "architecture is strong, where the nopCommerce implementation works well, and "
        "where real gaps remain.",
        space_after=0,
    )

    add_section_heading(doc, "5.1", "Evaluation Overview")
    add_table_with_caption(
        doc,
        "Table 5.1: Evaluation artifacts.",
        ["Artifact", "Purpose", "Status"],
        [
            [
                "500-question natural-language dataset",
                "Tests broad user-facing e-commerce questions over the implemented semantic layer.",
                "425 supported requests and 75 realistic boundary requests.",
            ],
            [
                "nopCommerce standard admin reports",
                "Compares AEGIS output with the platform's own shipped report implementations.",
                "20 reports, with source-derived semantics and oracle queries.",
            ],
            [
                "Direct LLM-to-SQL baseline",
                "Runs the same model on the same questions with no semantic layer between it and the SQL.",
                "500 questions, same gateway and database.",
            ],
        ],
        font_size=8.8,
        col_widths=[1.65, 3.15, 1.4],
    )
    add_para(
        doc,
        "These artifacts are static, not generated at evaluation time, so another reader "
        "can inspect the exact questions, oracle definitions, scripts, and result files "
        "behind every reported claim. The two evidence tracks differ in who chose them. "
        "The 500 questions were written for this study. The 20 reports were not: the list "
        "is nopCommerce's own admin menu and the comparison target is nopCommerce's own "
        "service-layer code, which removes the risk of an expected-answer set that happens "
        "to agree with the system under test because the same person wrote both.",
        space_after=0,
    )

    add_section_heading(doc, "5.2", "500-Question Natural-Language Benchmark")
    add_para(
        doc,
        "The main breadth benchmark contains natural-language questions that a store owner "
        "or administrator might ask about orders, revenue, customers, products, refunds, "
        "inventory, stores, countries, payment status, shipping, and search terms. The "
        "dataset intentionally includes unsupported questions as well, because an approved "
        "analytics system must know when not to answer.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.2: 500-question live benchmark results.",
        ["Metric", "Result", "Interpretation"],
        [
            ["Parser success", "499/500 (99.8%)", "The gateway returned a valid Intent Object for all but one prompt."],
            [
                "Supported intent exact match",
                "313/425 (73.6%)",
                "Strictest measure; a prompt parsed differently from the annotation often still compiled to a valid answer.",
            ],
            [
                "Supported answer rate",
                "423/425 (99.5%)",
                "AEGIS answered almost every request inside the semantic layer.",
            ],
            [
                "Supported execution validity",
                "422/425 (99.3%)",
                "The answered supported requests also executed against MySQL.",
            ],
            [
                "Boundary rejection accuracy",
                "72/75 (96.0%)",
                "Most realistic e-commerce questions outside the semantic layer were declined or clarified.",
            ],
        ],
        font_size=8.9,
        col_widths=[1.55, 1.25, 3.4],
    )
    add_para(
        doc,
        "An initial pass lost 29 questions to a consecutive block of HTTP 502 responses "
        "from the model gateway, which reduced the supported answer rate to 92.9 per cent. "
        "Those questions were retried and 28 answered on the second attempt. Both passes "
        "are recorded rather than only the better one: reporting only the retry would "
        "present a provider outage as though it had not happened, and reporting only the "
        "first pass would attribute that outage to the architecture.",
        space_after=10,
    )
    add_para(
        doc,
        "Two supported questions were refused, and both refusals are correct. Each asks to "
        "break refunds down by payment method without naming a measure, and a segment "
        "report cannot be built without one. Choosing a measure on the user's behalf is "
        "exactly the silent substitution the resolver was built to remove.",
        space_after=10,
    )
    add_para(
        doc,
        "Three boundary questions were answered instead of declined. One was a malformed "
        "model reply, which is a parse failure rather than a decision the system made. The "
        "other two are the same question phrased twice, asking to compare two named "
        "shipping carriers. The model reported both carrier names as unmapped, and the "
        "resolver answered by shipping method regardless. That is deliberate: a "
        "model-reported gap is treated as evidence rather than a verdict, because treating "
        "it as a verdict caused a high rate of false refusals. These two questions are what "
        "that choice costs, and stating the cost is more useful than tuning it away.",
        space_after=10,
    )
    add_para(
        doc,
        "The same corpus is also run with the model removed, by feeding each question's "
        "committed intent annotation straight to the resolver. That configuration resolves, "
        "compiles and executes 425 of 425 supported questions and labels 75 of 75 boundary "
        "questions correctly. It is a regression gate on the resolver and compiler only. "
        "Because no model participates, it is not an end-to-end result and is never quoted "
        "as one.",
        space_after=0,
    )

    add_section_heading(doc, "5.3", "Fidelity Against nopCommerce's Own Report Logic")
    add_para(
        doc,
        "Each of nopCommerce's twenty standard admin reports is requested in ordinary "
        "business phrasing. Two checks are applied. The first asks whether the request "
        "reaches an answer and compiles to SQL. The second executes that SQL and the "
        "platform's own query against the same seeded database and compares the rows "
        "returned. Exact SQL text is not required; the question is whether the answer "
        "carries the same business meaning.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.3: nopCommerce standard admin report fidelity.",
        ["Check", "Result", "Interpretation"],
        [
            [
                "Reached an answer and compiled",
                "20/20",
                "Every standard report can be requested in ordinary language.",
            ],
            [
                "Result set matched the platform",
                "15/20 (75.0%)",
                "The check that tests the claim: same database, same rows, same values.",
            ],
            [
                "Reports differing in value",
                "0/20",
                "The five mismatches differ in row count or label column, never in a number.",
            ],
        ],
        col_widths=[1.75, 1.15, 3.3],
    )
    add_para(
        doc,
        "Only the second check tests the claim. The first is satisfied by any query that "
        "compiles, and several of these twenty once passed it while being silently wrong: "
        "an order-level revenue sum fanned out across item-level joins, a missing "
        "soft-delete filter, a customer breakdown grouped by display name. Each returned a "
        "plausible, chartable number, so nothing downstream could tell it from a correct "
        "answer. That is the reason this thesis treats a compile-only check as a proxy "
        "rather than a result.",
        space_after=10,
    )
    add_para(
        doc,
        "The five reports that did not match agree with the platform on every value in "
        "every overlapping row. Four differ in result-set size, because nopCommerce's own "
        "reports carry their own limits of five, fifteen or one hundred rows. Two differ in "
        "the label column, returning a customer name where the platform labels by email "
        "address. Matching them exactly would require per-report presets, which is the "
        "report-specific special-casing the semantic layer exists to avoid.",
        space_after=0,
    )

    add_section_heading(doc, "5.4", "Latency")
    add_para(
        doc,
        "Per-stage timings were recorded for every supported question in the live "
        "benchmark. The split between the model stage and the deterministic stages matters "
        "more than the totals, because it is the same boundary the safety argument rests "
        "on.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.4: Per-stage latency over 425 supported questions.",
        ["Stage", "Median", "95th percentile"],
        [
            ["Intent extraction (model)", "9,029.89 ms", "19,460.15 ms"],
            ["Semantic resolution", "0.89 ms", "1.25 ms"],
            ["SQL compilation", "0.13 ms", "0.21 ms"],
            ["Database execution", "2.54 ms", "12.87 ms"],
            ["All stages after the model", "3.62 ms", "14.02 ms"],
        ],
        col_widths=[2.4, 1.4, 1.4],
    )
    add_para(
        doc,
        "Substantially all of the wall clock is the model reading the question. The stages "
        "that resolve business concepts, choose the join path, emit SQL and execute it take "
        "a few milliseconds together, and the model has no influence over any of them. The "
        "model figure is a property of the gateway used here and would change with the "
        "provider; the deterministic figures are properties of the architecture and would "
        "follow it to another deployment. The direct baseline's generation stage has a "
        "comparable median of 9,154.02 ms, so the constrained pipeline pays no latency "
        "premium for its safety.",
        space_after=0,
    )

    add_section_heading(doc, "5.5", "Safety Evaluation")
    add_para(
        doc,
        "The central architectural safety property is that the language model does not "
        "write SQL. It returns an Intent Object. Deterministic templates then produce "
        "SQL from approved semantic-layer definitions and check the query before execution. "
        "User prompt text is not inserted into executable SQL. The claim is therefore "
        "structural rather than statistical: no rate of successful defence is asserted, "
        "because there is no path from a prompt to a query the templates do not generate.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.5: Safety interpretation.",
        ["Risk", "AEGIS control", "Remaining boundary"],
        [
            [
                "User asks for a write operation",
                "Intent schema and compiler templates do not include write primitives.",
                "The system must still explain refusal clearly to the user.",
            ],
            [
                "User uses unsupported business terms",
                "The Intent Object must bind to approved semantic-layer definitions.",
                "Intent extraction can still misread vague language; debug traces and clarification reduce this risk.",
            ],
            [
                "LLM misunderstands the request",
                "Compiled SQL remains structurally safe.",
                "The answer may still be semantically wrong if intent extraction is wrong.",
            ],
        ],
        font_size=8.8,
        col_widths=[1.65, 2.55, 2.0],
    )
    add_para(
        doc,
        "The baseline arm gives this structural claim an empirical counterpart. Both arms "
        "were scanned with the same forbidden-pattern set, imported from the compiler "
        "rather than restated, so neither is judged by a more lenient rule. The "
        "unconstrained arm produced two queries containing a forbidden construct, both "
        "attempts to classify review text by keyword matching joined with UNION. The "
        "constrained arm produced none.",
        space_after=0,
    )

    add_section_heading(doc, "5.6", "Comparison With Direct LLM-to-SQL")
    add_para(
        doc,
        "A direct LLM-to-SQL baseline can appear attractive because it can always try to "
        "write a SELECT statement. However, allowing the model to author SQL moves business "
        "definitions, join choices, security behavior, and dialect correctness into a "
        "probabilistic component. To measure that rather than assert it, the same model was "
        "run through the same gateway on the same 500 questions against the same database, "
        "with no semantic layer in between. The arms differ only in whether the model "
        "authors the query.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.6: Measured comparison over the same 500 questions.",
        ["Measure", "AEGIS", "Direct LLM-to-SQL"],
        [
            ["Supported execution validity", "422/425 (99.3%)", "365/425 (85.9%)"],
            ["Out-of-scope questions answered", "3/75 (4.0%)", "25/75 (33.3%)"],
            ["Queries with a forbidden construct", "0", "2/500"],
        ],
        col_widths=[2.4, 1.4, 1.4],
    )
    add_para(
        doc,
        "The middle row carries the finding. A third of the questions the semantic layer "
        "cannot express were answered by the unconstrained model with confident, executable "
        "SQL. Asked to forecast next month's sales, it returned a query summing past "
        "months, which runs, returns a number, and forecasts nothing. Asked which customers "
        "are likely to churn, it returned a query counting each customer's past orders. "
        "Asked what customers say about delivery speed, it returned raw review rows. Each "
        "answer is plausible, chartable, and addresses a different question than the one "
        "asked. AEGIS cannot produce these because none of the requests binds to anything "
        "in the semantic layer.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.7: Structural comparison.",
        ["Property", "Direct LLM-to-SQL", "AEGIS"],
        [
            ["SQL generation", "Model writes SQL text", "Compiler expands approved templates"],
            ["Business definitions", "Inferred from prompt/schema names", "Declared in semantic layer"],
            ["Unsupported requests", "Often answered by nearest plausible SQL", "Rejected or clarified when outside coverage"],
            ["Dashboard output", "Usually one-off query result", "Saved, refreshable widget artifact"],
            ["Safety basis", "Prompt instruction and filtering", "No model-authored SQL execution path"],
        ],
        font_size=8.8,
        col_widths=[1.35, 2.25, 2.6],
    )

    add_section_heading(doc, "5.7", "Interpretation")
    add_para(
        doc,
        "The evaluation supports three conclusions. First, a semantic-layer architecture "
        "can cover a broad set of natural e-commerce analytics questions without exposing "
        "users to raw SQL. Second, refusal is part of correctness: the same model without "
        "the semantic layer answered a third of the unanswerable questions anyway, and a "
        "system that answers an unsupported question with a plausible but wrong query is "
        "less trustworthy than one that declines. Third, the differences that remain "
        "against nopCommerce's own reports are presentational rather than numerical, which "
        "locates the gap in row limits and label choices rather than in the compiled "
        "semantics.",
        space_after=10,
    )
    add_para(
        doc,
        "Two limitations are worth stating alongside those conclusions. Value-level "
        "verification covers the twenty reports, not all 425 supported questions; for the "
        "latter the evidence is that the compiled SQL resolves and executes, not that every "
        "answer is the intended one. And the gateway used for intent extraction resolved a "
        "routing alias per request, so the reported run spans two models. Each result row "
        "records the model that served it, but a single-model run is needed before "
        "parser-dependent figures can be attributed to one system.",
        space_after=10,
    )
    add_mixed_para(
        doc,
        [
            ("This interpretation is consistent with mixed-initiative NLIDB work such as ", False, False),
            (cite("li_jagadish14"), False, False),
            (
                ", which showed that users do not reliably detect wrong system answers without "
                "help. In a reporting context, a visible refusal or clarification is therefore "
                "often safer than a confident wrong chart.",
                False,
                False,
            ),
        ],
        space_after=0,
    )
    page_break(doc)
