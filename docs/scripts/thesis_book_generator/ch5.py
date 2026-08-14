# -*- coding: utf-8 -*-
"""Chapter 5: Results and Discussion."""
from pathlib import Path
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_table_with_caption, add_code_block, add_figure_image, page_break)
from refs import cite

FIG_DIR = Path(__file__).with_name("figures")


def chapter5(doc):
    add_chapter_heading(doc, 5, "Results and Discussion")
    add_para(doc,
              "The results discussion presents the evaluation results of the AEGIS prototype using a "
              "107-request natural-language analytics benchmark and true database execution. The "
              "discussion separates SQL safety, execution validity, and semantic correctness because "
              "a query may be safe and executable while still failing to answer the intended "
              "analytical request.",
              space_after=10)
    add_para(doc,
              "The reported quantitative evidence covers AEGIS and three completed baselines: B1 "
              "direct LLM-to-SQL, B2 decomposed LLM-to-SQL, and B3 template-only. It also includes "
              "a machine-assisted first-pass semantic-correctness annotation and runtime evidence "
              "from the live LLM gateway and Docker MySQL execution.", space_after=0)

    # ---------------------------------------------------------------- 5.1
    add_section_heading(doc, "5.1", "Evaluation Overview")
    add_para(doc,
              "The evaluation uses 107 mixed natural-language reporting requests as a single "
              "benchmark set. The requests include ordinary analytical questions as well as harder "
              "boundary-style cases, but all are evaluated under the same denominator to avoid "
              "separating results into unsupported categories.",
              space_after=10)
    add_table_with_caption(
        doc, "Table 5.1: Evaluation benchmark status.",
        ["Item", "Status"],
        [
            ["Benchmark size", "107 mixed natural-language reporting requests"],
            ["Database execution environment", "MySQL 8.0 in Docker, seeded with nopCommerce-style data"],
            ["Completed baselines", "B1 direct LLM-to-SQL, B2 decomposed LLM-to-SQL, and B3 template-only"],
            ["Correctness annotation", "Machine-assisted first pass over all 107 requests"],
            ["Runtime evidence", "LLM gateway responses observed around 12-30 seconds; SQL replay measured in milliseconds"],
            ["Remaining manual step", "Human spot-checking of semantic-correctness annotations before final submission"],
        ])
    add_para(doc,
              "The benchmark evidence consists of the prepared request set, recorded model outputs, "
              "baseline outputs, and true database execution results produced against the seeded MySQL "
              "evaluation database.", italic=True, size=11, space_after=10)

    # ---------------------------------------------------------------- 5.2
    add_section_heading(doc, "5.2", "Main Result Summary")
    add_para(doc,
              "Reference text-to-SQL papers commonly present a compact result table before detailed "
              "analysis. Following that pattern, Table 5.2 summarizes the completed AEGIS measurements "
              "and separates them from measurements that remain pending.",
              space_after=10)
    add_table_with_caption(
        doc, "Table 5.2: Main evaluation result summary.",
        ["Metric", "AEGIS result", "Baseline result", "Interpretation", "Status"],
        [
            ["SQL safety", "0 unsafe statements in 107", "B1 produced 1 unsafe statement in 107",
             "AEGIS blocked the observed unsafe-write case", "Measured"],
            ["True execution validity", "100 of 107 executed successfully (93.5%)",
             "B1: 27 of 107; B2: 33 of 107; B3: 104 of 107",
             "AEGIS greatly improved execution validity over LLM-to-SQL baselines", "Measured"],
            ["Failure analysis", "7 AEGIS execution failures", "B1 failures were broader and more frequent",
             "Remaining AEGIS failures are implementation issues, not safety violations", "Measured"],
            ["Semantic correctness", "32 of 107 overall; 32 of 54 answerable requests",
             "B1: 16; B2: 19; B3: 21 correct overall",
             "AEGIS had the strongest answerable-request correctness in the annotation", "First-pass"],
            ["Runtime", "SQL replay mean 13.22 ms; live LLM responses commonly 12-30 s",
             "B2 requires two LLM calls per request",
             "LLM response time dominates user-visible latency", "Measured / observed"],
        ],
        font_size=8.7,
        col_widths=[1.15, 1.28, 1.45, 1.9, 0.75])
    add_para(doc,
              "The execution-validity and semantic-correctness rows above were measured against the "
              "pipeline version in place before the three abstention-focused interventions described in "
              "Section 5.9, and have not been re-measured under the current configuration; they are "
              "reported here as the baseline against which Section 5.9 states its improvement. The "
              "abstention-aware metrics in Section 5.9 are current.", italic=True, size=11, space_after=0)

    # ---------------------------------------------------------------- 5.3
    add_section_heading(doc, "5.3", "SQL Safety")
    add_para(doc,
              "Unsafe Query Execution Rate measures whether a generated SQL statement contains a "
              "genuine unsafe operation such as a write or schema-changing command. This metric is "
              "different from execution validity because a statement can be syntactically valid while "
              "still being unsafe for an analytics-only system.",
              space_after=10)
    add_table_with_caption(
        doc, "Table 5.3: SQL safety on the 107-request benchmark.",
        ["System", "Unsafe SQL", "Interpretation"],
        [
            ["Baseline B1 (Direct LLM-to-SQL)", "1 genuine unsafe statement in 107",
             "The model generated one write operation when prompted with a business-looking request."],
            ["AEGIS", "0 unsafe statements in 107",
             "The intent schema and compiler templates did not allow write SQL to be emitted."],
        ],
        col_widths=[1.7, 1.35, 3.15])
    add_para(doc,
              "The strongest safety example is the disguised write request asking to cancel orders stuck "
              "in Pending for more than 30 days. Baseline B1 produced an executable UPDATE statement. "
              "AEGIS cannot express a write intent in its intent object or compiler templates, so it did "
              "not emit write SQL. This is the central safety result: AEGIS prevents this class of unsafe "
              "execution structurally rather than hoping the model follows an instruction not to write "
              "dangerous SQL.", space_after=0)
    add_figure_image(doc, 9,
        "Verified safety and execution-validity comparison",
        FIG_DIR / "figure-09-safety-execution-results.png", width_in=5.85)

    # ---------------------------------------------------------------- 5.4
    add_section_heading(doc, "5.4", "True Database Execution Validity")
    add_para(doc,
              "True database execution validity measures whether the generated SQL actually runs "
              "against the seeded MySQL database. This check is stricter than string inspection or "
              "application-level compilation because it exposes missing columns, invalid joins, dialect "
              "errors, and invalid literal values.",
              space_after=10)
    add_para(doc,
              "The results in this section are the earlier baseline pipeline run: the same run "
              "referenced in Table 5.2. Re-running true database execution against the current "
              "pipeline, after the interventions described in Section 5.9, is outstanding work.",
              italic=True, size=11, space_after=10)
    add_table_with_caption(
        doc, "Table 5.4: True execution validity on the 107-request benchmark.",
        ["System", "Execution result", "Interpretation"],
        [
            ["Baseline B1 (Direct LLM-to-SQL)", "27 of 107 executed successfully (25.2%)",
             "Most failures came from hallucinated columns, invalid table references, or dialect errors."],
            ["Baseline B2 (Decomposed LLM)", "33 of 107 executed successfully (30.8%)",
             "Decomposition improved slightly over B1, but many SQL errors remained."],
            ["AEGIS", "100 of 107 executed successfully (93.5%)",
             "The deterministic pipeline removed many free-form SQL errors, but seven issues remained."],
            ["B3 Template-only", "104 of 107 executed successfully (97.2%)",
             "High execution validity, but not evidence of higher semantic correctness."],
        ],
        col_widths=[1.75, 1.55, 2.9])

    # ---------------------------------------------------------------- 5.5
    add_section_heading(doc, "5.5", "Execution Failure Analysis")
    add_para(doc,
              "The seven AEGIS execution failures identify the remaining implementation limitations "
              "of the prototype. These failures are not safety violations; they are executable-query "
              "construction issues observed when the generated SQL was tested against the evaluation "
              "database.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.5: AEGIS true-execution failures diagnosed from MySQL execution.",
        ["Query ID", "Failure class", "Observed database error"],
        [
            ["5", "Relative-date normalization", "Incorrect DATETIME value: 'this morning'"],
            ["13", "Compiler syntax edge case", "MySQL syntax error near generated SQL fragment"],
            ["19", "Join-path or alias defect", "Unknown column 'o.Id' in ON clause"],
            ["46", "Relative-date normalization", "Incorrect DATETIME value: 'last 90 days'"],
            ["72", "Relative-date normalization", "Incorrect DATETIME value: 'this quarter'"],
            ["80", "Compiler syntax edge case", "MySQL syntax error near generated SQL fragment"],
            ["84", "Compiler syntax edge case", "MySQL syntax error near generated SQL fragment"],
        ])
    add_para(doc,
              "The failure pattern is narrow. Three failures are date-normalization bugs, three are "
              "compiler syntax edge cases, and one is a join or alias construction defect. These are "
              "concrete implementation bugs, not evidence that the safety boundary failed. They should "
              "be fixed in future work and then re-measured using the same true database execution "
              "procedure.", space_after=0)

    # ---------------------------------------------------------------- 5.6
    add_section_heading(doc, "5.6", "Semantic Correctness and Scope Handling")
    add_para(doc,
              "Correctness or accuracy must be treated separately from execution validity. A "
              "machine-assisted annotation pass was therefore added after the supervisor review. "
              "Each row was checked against the expected metric, grouping, time or filter, and "
              "required behavior. This annotation is a first pass and should be manually spot-checked "
              "before final submission, but it gives the thesis a concrete correctness measurement "
              "instead of relying only on SQL execution.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.6: Semantic-correctness annotation summary.",
        ["System", "Overall correctness", "Answerable requests", "Scope/write handling"],
        [
            ["AEGIS", "32 of 107 (29.9%)", "32 of 54 (59.3%)", "0 of 52"],
            ["B1 Direct LLM-to-SQL", "16 of 107 (15.0%)", "15 of 54 (27.8%)", "0 of 52"],
            ["B2 Decomposed LLM", "19 of 107 (17.8%)", "18 of 54 (33.3%)", "0 of 52"],
            ["B3 Template-only", "21 of 107 (19.6%)", "21 of 54 (38.9%)", "0 of 52"],
        ],
        col_widths=[1.75, 1.4, 1.45, 1.4])
    add_para(doc,
              "The annotation shows two findings. For answerable requests, AEGIS scored higher than "
              "the LLM-to-SQL and template-only baselines. For unsupported, vague, compound, or "
              "write-style requests, none of the evaluated systems handled the scope boundary "
              "correctly in this first pass. AEGIS still maintained SQL safety, but it often mapped "
              "unsupported requests to safe but semantically wrong in-scope queries. This is a "
              "correctness and robustness limitation, not a SQL-safety failure.",
              space_after=0)
    add_para(doc,
              "This annotation is the same 32-of-107 figure reported as translation precision in "
              "Section 5.9. It is scored against aegis_correct labels that describe the SQL produced by "
              "the pipeline version that existed before the abstention interventions in Section 5.9, so "
              "the same count is being re-read rather than re-measured. Section 5.9 marks it accordingly "
              "and states which of this chapter's metrics remain quotable.",
              italic=True, size=11, space_after=10)

    # ---------------------------------------------------------------- 5.7
    add_section_heading(doc, "5.7", "Baseline and Runtime Analysis")
    add_para(doc,
              "The completed baselines show different failure modes. B1 and B2 rely on unconstrained "
              "LLM-written SQL and therefore suffer from dialect errors, missing tables, hallucinated "
              "columns, and unsafe write behavior. B3 removes the LLM and uses keyword templates, so "
              "it produces highly executable SQL but often misses the user's intended meaning.",
              space_after=10)
    add_table_with_caption(
        doc, "Table 5.7: Completed baseline comparison.",
        ["System", "True execution validity", "Semantic correctness", "Main observation"],
        [
            ["B1 Direct LLM-to-SQL", "27 of 107 (25.2%)", "16 of 107 (15.0%)",
             "Lowest execution validity and one unsafe write statement."],
            ["B2 Decomposed LLM", "33 of 107 (30.8%)", "19 of 107 (17.8%)",
             "Two-step prompting improved execution slightly but did not solve schema errors."],
            ["B3 Template-only", "104 of 107 (97.2%)", "21 of 107 (19.6%)",
             "SQL often runs, but keyword intent selection is semantically brittle."],
            ["AEGIS", "100 of 107 (93.5%)", "32 of 107 (29.9%)",
             "Best correctness among evaluated systems while preserving SQL safety."],
        ],
        font_size=8.7,
        col_widths=[1.45, 1.25, 1.25, 2.25])
    add_para(doc,
              "As in Section 5.4, the AEGIS execution-validity and semantic-correctness figures above "
              "are the earlier baseline pipeline run and are superseded, for the abstention-handling "
              "behavior specifically, by the current measurements in Section 5.9.",
              italic=True, size=11, space_after=10)
    add_table_with_caption(
        doc, "Table 5.8: Runtime evidence from benchmark replay and live LLM gateway.",
        ["Measurement", "Observed result", "Interpretation"],
        [
            ["AEGIS SQL replay", "Mean 13.22 ms; median 2.59 ms; p95 72.55 ms",
             "Database execution and deterministic post-LLM stages are fast."],
            ["B2 SQL replay", "Mean 6.88 ms; median 0.74 ms; p95 28.55 ms",
             "SQL execution time is small compared with LLM response time."],
            ["B3 pipeline replay", "Mean 13.66 ms; median 3.80 ms; p95 59.17 ms",
             "Template-only classification, mapping, compilation, and execution are lightweight."],
            ["Live LLM response", "Observed around 12-30 seconds per request in the gateway screenshot",
             "User-visible runtime is dominated by model response duration."],
        ],
        font_size=8.9,
        col_widths=[1.45, 1.9, 2.85])
    add_para(doc,
              "The runtime results show why end-to-end latency must be discussed separately from SQL "
              "execution time. Once the intent or SQL text exists, database replay takes milliseconds. "
              "The visible delay comes mainly from LLM calls. B2 is especially costly because each "
              "benchmark request uses two model calls: one for reasoning and one for SQL generation.",
              space_after=0)

    # ---------------------------------------------------------------- 5.8
    add_section_heading(doc, "5.8", "Comparative Discussion and Robustness")
    add_section_heading(doc, "5.8.1", "AEGIS vs. Direct LLM-to-SQL", level=3)
    add_para(doc,
              "The B1 baseline exposes the central risk of direct SQL generation. The same model that "
              "can produce useful analytical SQL can also hallucinate schema objects, mix SQL dialects, "
              "and generate a real write statement when a business-looking request implies a write "
              "operation. AEGIS narrows the model's role to intent extraction, so these risks do not "
              "enter the SQL construction stage in the same way.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.9: Structural comparison of AEGIS vs. direct LLM-to-SQL.",
        ["Property", "Direct LLM-to-SQL", "AEGIS"],
        [
            ["SQL generation", "Model-generated free-form text", "Deterministic compiler"],
            ["Schema exposure to LLM", "Requires tables, columns, and relationships", "Uses approved business labels"],
            ["Business metric definitions", "Inferred from prompt and schema names", "Defined in the semantic layer"],
            ["SQL injection prevention", "Prompt-level instruction and post-checking", "Structural prevention through intent schema and templates"],
            ["Permission enforcement", "External or absent", "Applied after intent extraction by deterministic code"],
            ["Dashboard widget persistence", "Not provided by default", "First-class saved artifact"],
            ["Model dependency", "Strongly tied to model quality", "Compiler and safety scanner are model-independent"],
        ])
    add_section_heading(doc, "5.8.2", "Semantic Layer versus Retrieval-Augmented Generation", level=3)
    add_para(doc,
              "Retrieval-augmented generation can help an LLM find relevant schema fragments, but it "
              "does not remove the model's authority to write SQL. AEGIS uses the semantic layer for a "
              "different purpose: it defines which business concepts are allowed to exist and how they "
              "compile into SQL. RAG may still be useful in a future large deployment to select relevant "
              "semantic-layer entries, but the final SQL should still be compiled by the deterministic "
              "AEGIS compiler.", space_after=10)
    add_section_heading(doc, "5.8.3", "Scope Boundary", level=3)
    add_para(doc,
              "AEGIS currently supports a bounded set of approved metrics, dimensions, analytical "
              "patterns, and join paths. This is the source of its safety, but also the source of its "
              "main limitation. If a user asks for something not represented in the semantic layer, the "
              "system should reject or clarify the request. The current prototype does not always do "
              "that reliably; improving scope detection is therefore a priority in future work.",
              space_after=0)

    # ---------------------------------------------------------------- 5.9
    add_section_heading(doc, "5.9", "Abstention-Aware Evaluation")
    add_para(doc,
              "Sections 5.4 through 5.7 score every request against a single pass/fail outcome. On this "
              "benchmark roughly half of the requests should not be answered at all: they are "
              "unsupported, vague, compound, or write-style, and the correct system behavior is to "
              "decline or ask for clarification rather than to produce an answer. A single aggregate "
              "accuracy figure over a set built this way is misleading in both directions: it counts a "
              "correct refusal as a failure, and it counts a confident wrong answer as a success. This "
              "section reports the refusal channel on its own terms, over the 55 requests that should "
              "be answered and the 52 that should be declined.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.10: Abstention-aware evaluation metrics.",
        ["Metric", "Result", "Definition", "Status"],
        [
            ["Translatability", "37.4% (40/107)",
             "Produced executable SQL, over all requests", "Measured"],
            ["Translation precision", "29.9% (32/107)",
             "Produced the expected result, over labelled requests", "Not yet valid — requires re-annotation"],
            ["Abstention recall", "100.0% (52/52)",
             "Correctly declined, over requests that should be declined", "Measured"],
            ["False abstention rate", "25.5% (14/55)",
             "Wrongly declined, over requests that should be answered", "Measured"],
            ["Silent error rate", "11.2% (12/107)",
             "Answered confidently and wrongly, with no error raised", "Not yet valid — requires re-annotation"],
        ],
        font_size=9.0,
        col_widths=[1.3, 1.15, 2.55, 1.3])
    add_mixed_para(doc, [
        ("Translatability and translation precision follow ", False, False),
        (cite('liu_xu25'), False, False),
        (" canonicalisation of these metrics for natural-language database interfaces: translatability "
         "asks whether a request produced any executable artefact, and translation precision asks "
         "whether that artefact produced the expected result. High translatability with low precision "
         "is the signature of a system that always answers regardless of whether the answer is right.",
         False, False),
    ], space_after=10)
    add_mixed_para(doc, [
        ("Silent error rate matters because an unnoticed wrong answer is more damaging than a visible "
         "refusal. ", False, False),
        (cite('li_jagadish14'), False, False),
        (", in the NaLIR user study, found that of 32 wrong answers produced without an interactive "
         "confirmation step, participants detected only 7 unaided. A governed reporting system that "
         "answers confidently and wrongly is therefore not a safe default merely because it avoids "
         "refusing; it is a failure mode that the person reading the report has little chance of "
         "catching without an independent check.", False, False),
    ], space_after=10)
    add_para(doc,
              "One further caveat applies to every figure in Table 5.10: each is a single run. An "
              "earlier measurement of the same pipeline reported false abstention at 23.6% (13/55) "
              "and silent error rate at 13.1% (14/107), against 25.5% and 11.2% here. The totals "
              "barely moved, but the underlying sets churned more than the totals suggest — two "
              "question ids left the wrongly-declined list while three joined it, and one id moved "
              "from wrongly-declined into silent errors while another moved the opposite way. The two "
              "runs are not cleanly comparable, because the earlier one was competing with a "
              "concurrent copy of itself for a rate-limited model endpoint and its timeouts could "
              "themselves have shifted outcomes; the figures reported here come from a clean run with "
              "no rate limiting and no failed requests. The honest reading is that a single-run figure "
              "on this benchmark carries a wobble of a question or two even at fixed temperature. "
              "Reporting a mean over repeated runs with its spread would be the stronger method, and "
              "it has not been done.", space_after=10)
    add_para(doc,
              "Abstention recall is reported here only beside false abstention rate, and this pairing "
              "is not optional. A system that refuses every request scores 100% on abstention recall "
              "alone, which would make the metric worthless on its own. No system in the reference "
              "corpus reviewed in Chapter 2 measures the refusal channel this way; reporting the two "
              "figures together, rather than the first in isolation, is the methodological contribution "
              "of this section.", space_after=10)
    add_para(doc,
              "Translation precision and silent error rate are not quotable as findings in this thesis. "
              "Both are scored against the aegis_correct labels in the semantic-correctness annotation "
              "file, and those labels describe the SQL produced by the pipeline version that existed "
              "before the interventions described below, not the current pipeline. The tell is that "
              "translation precision has read exactly 29.9% on every run: it is the same 32-of-107 label "
              "count being re-read rather than a fresh measurement of the current system. Both metrics "
              "are marked \"Not yet valid — requires re-annotation\" in Table 5.10 rather than reported "
              "as results, and re-annotating them against the current pipeline's SQL is listed as future "
              "work in Chapter 6.", space_after=0)

    add_section_heading(doc, "5.9.1", "The Abstention Improvement Trajectory", level=3)
    add_para(doc,
              "False abstention rate is the metric this project moved deliberately, and it is the "
              "central result of this section. Across three measured stages, false abstention fell from "
              "61.8% to 40.0% to the current 25.5%, while abstention recall held at 100.0% throughout. "
              "No architectural change was required at any step: every improvement came from fixing an "
              "implementation defect or extending a configuration, not from redesigning the pipeline.",
              space_after=10)
    add_table_with_caption(
        doc, "Table 5.11: False-abstention improvement trajectory.",
        ["Stage", "False abstention rate", "Abstention recall", "Intervention applied"],
        [
            ["Initial measured run", "61.8%", "100.0%",
             "— (baseline instrumentation)"],
            ["After validating unmapped terms", "40.0%", "100.0%",
             "Validated the model's self-reported unmapped terms instead of trusting them"],
            ["Current", "25.5%", "100.0%",
             "Separated time granularity from time filtering; extended the semantic layer from 12 to "
             "17 of the 126 available schema tables"],
        ],
        font_size=9.3,
        col_widths=[1.3, 1.15, 1.05, 2.8])
    add_para(doc,
              "The interventions were configuration and implementation changes, not architectural ones: "
              "no new component was added to the pipeline, and the LLM's role remained restricted to "
              "intent extraction throughout. This supports the interpretation that semantic accuracy in "
              "this architecture is an implementation and configuration property rather than an "
              "architectural one — the ceiling is set by how much of the schema and vocabulary is "
              "exposed and how carefully the model's self-reported signals are checked, not by the "
              "constraint-based design itself.", space_after=0)

    add_section_heading(doc, "5.9.2", "Residual Analysis", level=3)
    add_para(doc,
              "Part of the remaining 25.5% false abstention rate is label error rather than system "
              "error. Several requests labelled \"answer\" in the annotation file are not, on inspection, "
              "answerable against the current semantic layer: a composite \"health score\" combining "
              "sales, stock levels, and refund rates into one number (request 53), abandoned-checkout "
              "events (request 96), and first-time-versus-returning customer cohorts as a dimension "
              "before that dimension existed in the semantic layer. These labels were assigned when the "
              "previous pipeline answered the corresponding requests by nearest-match substitution "
              "against an unrelated metric, so the annotation records that a query executed, not that "
              "the request was genuinely answerable. Correcting these labels is part of the "
              "re-annotation work noted above, and would place the true false-abstention rate somewhat "
              "below 25.5%.", space_after=0)

    # ---------------------------------------------------------------- 5.10
    add_section_heading(doc, "5.10", "Coverage Against the Platform's Native Report Suite")
    add_para(doc,
              "The 107-request benchmark used in the rest of this chapter was authored for this thesis, "
              "which raises an unavoidable question of annotation bias: a benchmark's author can, even "
              "unintentionally, phrase requests toward the system's known strengths. A benchmark whose "
              "question list is fixed by an outside party avoids this. nopCommerce, the e-commerce "
              "platform whose schema underlies the evaluation database, ships a fixed set of standard "
              "admin reports as a built-in reporting surface. AEGIS reproduces all 20 of these reports "
              "from natural-language requests, each producing compiled SQL and an automatically "
              "selected chart type.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.12: Coverage of nopCommerce's standard admin reports (20 of 20).",
        ["#", "Report", "#", "Report"],
        [
            ["1", "Sales summary by month", "11", "Order status breakdown"],
            ["2", "Sales summary today", "12", "Incomplete orders"],
            ["3", "Bestsellers by quantity", "13", "Latest orders"],
            ["4", "Bestsellers by amount", "14", "Sales by category"],
            ["5", "Products never purchased", "15", "Sales by manufacturer"],
            ["6", "Country sales", "16", "Average order value"],
            ["7", "Best customers by order total", "17", "Shipment count"],
            ["8", "Best customers by order count", "18", "Refund totals"],
            ["9", "Registered customers", "19", "Tax collected"],
            ["10", "Low stock", "20", "Daily revenue trend"],
        ],
        font_size=9.5,
        col_widths=[0.35, 2.55, 0.35, 2.55])
    add_para(doc,
              "This is a stronger evaluation than the self-authored question set for a specific reason: "
              "the report list is defined by the host platform rather than by the thesis author, so "
              "there is no annotation bias in which requests were chosen, and reproducing it answers a "
              "direct question — can natural language reproduce the platform's own built-in reporting "
              "surface? — rather than a question shaped by the evaluator. AEGIS additionally supports "
              "parameterised variation of these reports, such as arbitrary date ranges, category "
              "filters, or customer segments, that the fixed admin panel screens have no control for.",
              space_after=0)
    page_break(doc)

