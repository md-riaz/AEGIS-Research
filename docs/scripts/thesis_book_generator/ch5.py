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
        "This chapter reports the current AEGIS prototype evaluation using static "
        "nopCommerce datasets committed with the repository. The evaluation separates "
        "four questions that are often mixed together: whether the system can parse a "
        "natural-language request, whether the request is covered by the semantic layer, "
        "whether the compiled SQL executes, and whether the returned result matches the "
        "expected business answer.",
        space_after=10,
    )
    add_para(
        doc,
        "The results should not be read as a claim that AEGIS is a perfect analytics "
        "system. A perfect score on every table would be suspicious for a prototype. "
        "Instead, the evaluation shows where the architecture is strong, where the "
        "current nopCommerce implementation is already useful, and where a visible "
        "implementation gap remains.",
        space_after=0,
    )

    add_section_heading(doc, "5.1", "Evaluation Overview")
    add_table_with_caption(
        doc,
        "Table 5.1: Current evaluation artifacts.",
        ["Artifact", "Purpose", "Status"],
        [
            [
                "500-question natural-language dataset",
                "Tests broad user-facing e-commerce questions over the implemented semantic layer.",
                "425 supported requests and 75 realistic boundary requests.",
            ],
            [
                "Admin analytics oracles",
                "Compares AEGIS outputs with source-derived nopCommerce Admin reporting logic.",
                "16 oracle tasks.",
            ],
            [
                "Admin-fidelity phrasings",
                "Checks whether the same Admin task can be requested in multiple natural phrasings.",
                "80 prompts, five per oracle task.",
            ],
            [
                "Focused semantic coverage suite",
                "Checks representative metric, dimension, trend, ranking, exception, and boundary cases.",
                "20 supported and 5 boundary checks.",
            ],
        ],
        font_size=8.8,
        col_widths=[1.65, 3.15, 1.4],
    )
    add_para(
        doc,
        "These datasets are static research artifacts, not generated at evaluation time. "
        "This matters because a thesis result must be reproducible: another reader should "
        "be able to inspect the exact questions, oracle definitions, scripts, and result "
        "files used for the reported claims.",
        space_after=0,
    )

    add_section_heading(doc, "5.2", "500-Question Natural-Language Benchmark")
    add_para(
        doc,
        "The main breadth benchmark contains natural-language questions that a store owner "
        "or administrator might ask about orders, revenue, customers, products, refunds, "
        "inventory, stores, countries, payment status, shipping, and search terms. The "
        "dataset intentionally includes unsupported questions as well, because a Approved "
        "analytics system must know when not to answer.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.2: 500-question live benchmark results.",
        ["Metric", "Result", "Interpretation"],
        [
            ["Parser success", "498/500 (99.6%)", "The LLM API usually returned a valid typed intent."],
            [
                "Supported intent exact match",
                "345/425 (81.2%)",
                "Many prompts were parsed exactly; remaining supported prompts often still compiled to a valid answer.",
            ],
            [
                "Supported answer rate",
                "422/425 (99.3%)",
                "AEGIS answered almost all requests that were inside the semantic layer.",
            ],
            [
                "Supported execution validity",
                "422/425 (99.3%)",
                "The answered supported requests also executed successfully.",
            ],
            [
                "Boundary rejection accuracy",
                "74/75 (98.7%)",
                "Most realistic e-commerce questions outside the semantic layer were rejected or clarified.",
            ],
        ],
        font_size=8.9,
        col_widths=[1.55, 1.25, 3.4],
    )
    add_para(
        doc,
        "This result supports the bounded-system claim. AEGIS is not trying to answer "
        "infinite arbitrary SQL questions. It is trying to answer a large, useful set of "
        "questions made available by the semantic layer and to avoid silently inventing "
        "answers for unavailable concepts.",
        space_after=0,
    )

    add_section_heading(doc, "5.3", "Admin Fidelity Benchmark")
    add_para(
        doc,
        "The Admin fidelity benchmark is stricter than asking whether AEGIS can produce "
        "some chartable SQL. It extracts reporting expectations from nopCommerce Admin "
        "analytics and compares the returned shape and values against those source-derived "
        "oracles. Exact SQL text is not required; the important question is whether the "
        "answer has the correct business meaning.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.3: Admin analytics oracle benchmark.",
        ["Metric", "Result", "Interpretation"],
        [
            ["Execution validity", "16/16 (100.0%)", "Every Admin oracle task produced executable SQL."],
            ["Shape accuracy", "16/16 (100.0%)", "Every output used the expected row/column structure."],
            [
                "Result accuracy",
                "15/16 (93.8%)",
                "One dashboard order-average matrix still differs from nopCommerce.",
            ],
        ],
        col_widths=[1.55, 1.35, 3.3],
    )
    add_para(
        doc,
        "The remaining mismatch is useful evidence rather than an embarrassment. It shows "
        "that the benchmark is capable of finding a real gap. The gap should be fixed by "
        "adding a general multi-period matrix-summary primitive to the compiler, not by "
        "hardcoding a nopCommerce report shortcut.",
        space_after=0,
    )

    add_section_heading(doc, "5.4", "Focused Semantic Coverage")
    add_table_with_caption(
        doc,
        "Table 5.4: Focused semantic coverage results.",
        ["Metric", "Result", "Interpretation"],
        [
            ["Supported execution validity", "20/20 (100.0%)", "Representative supported requests executed."],
            ["Supported shape accuracy", "20/20 (100.0%)", "Outputs matched the expected widget form."],
            ["Supported result accuracy", "20/20 (100.0%)", "Focused supported cases matched expected values."],
            ["Boundary rejection accuracy", "5/5 (100.0%)", "Focused unsupported cases were rejected."],
        ],
        col_widths=[1.75, 1.35, 3.1],
    )
    add_para(
        doc,
        "This small suite is not presented as proof of perfection. It is a regression and "
        "coverage check over representative semantic-layer combinations. The broader "
        "500-question benchmark and the Admin oracle mismatch are what keep the evaluation "
        "honest.",
        space_after=0,
    )

    add_section_heading(doc, "5.5", "Safety Evaluation")
    add_para(
        doc,
        "The central architectural safety property is that the language model does not "
        "write SQL. It returns a typed intent object. SQL is then produced by deterministic "
        "templates over approved semantic-layer definitions and checked before execution. "
        "Therefore, prompt text from the user is not interpolated into executable SQL.",
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
                "The structured intent must bind to approved semantic-layer definitions.",
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

    add_section_heading(doc, "5.6", "Comparison With Direct LLM-to-SQL")
    add_para(
        doc,
        "A direct LLM-to-SQL baseline can appear attractive because it can always try to "
        "write a SELECT statement. However, allowing the model to author SQL moves business "
        "definitions, join choices, security behavior, and dialect correctness into a "
        "probabilistic component. AEGIS deliberately gives up unlimited query flexibility in "
        "exchange for Approved definitions, deterministic compilation, and an explicit refusal "
        "path.",
        space_after=10,
    )
    add_table_with_caption(
        doc,
        "Table 5.6: Structural comparison.",
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
        "The evaluation supports three conclusions. First, a semantic-layer architecture can "
        "cover a broad set of natural e-commerce analytics questions without exposing users "
        "to raw SQL. Second, refusal is part of correctness: a system that answers an "
        "unsupported question with a plausible but wrong query is less trustworthy than one "
        "that declines. Third, the remaining Admin fidelity gap is an implementation gap in "
        "the current compiler, not evidence that the architecture must be replaced.",
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
