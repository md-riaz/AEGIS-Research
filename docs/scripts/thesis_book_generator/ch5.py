# -*- coding: utf-8 -*-
"""Chapter 5: Results and Discussion."""
from build_thesis import (add_para, add_mixed_para, add_chapter_heading, add_section_heading,
                           add_table_with_caption, add_code_block, add_figure_placeholder, page_break)


def chapter5(doc):
    add_chapter_heading(doc, 5, "Results and Discussion")
    add_para(doc,
              "This chapter presents the evaluation results of the AEGIS prototype using a "
              "107-request natural-language analytics benchmark and true database execution. The "
              "discussion separates SQL safety, execution validity, and semantic correctness because "
              "a query may be safe and executable while still failing to answer the intended "
              "analytical request.",
              space_after=10)
    add_para(doc,
              "The reported quantitative evidence covers the mixed 107-request benchmark for AEGIS "
              "and the B1 direct LLM-to-SQL baseline, together with the completed B3 template-only "
              "execution-validity run. B2, B4, latency, and fully annotated semantic correctness "
              "remain future evaluation work, so this chapter reports only the measurements completed "
              "under the current experimental setup.", space_after=0)

    # ---------------------------------------------------------------- 5.1
    add_section_heading(doc, "5.1", "Evaluation Overview")
    add_para(doc,
              "The evaluation uses 107 mixed natural-language reporting requests as a single "
              "benchmark set. The requests include ordinary analytical questions as well as harder "
              "boundary-style cases, but all are evaluated under the same denominator to avoid "
              "separating results into unsupported categories.",
              space_after=10)
    add_table_with_caption(
        doc, "Table 5.1: Verified benchmark status.",
        ["Item", "Status"],
        [
            ["Benchmark size", "107 mixed natural-language reporting requests"],
            ["Database execution environment", "MySQL 8.0 in Docker, seeded with nopCommerce-style data"],
            ["Completed baselines", "B1 direct LLM-to-SQL and B3 template-only"],
            ["Pending measurements", "Semantic correctness, B2/B4 baselines, and latency"],
        ])
    add_para(doc,
              "Evidence basis: the benchmark evidence consists of the prepared request set, recorded "
              "model outputs, baseline outputs, and true database execution results produced against "
              "the seeded MySQL evaluation database.", italic=True, size=11, space_after=10)

    # ---------------------------------------------------------------- 5.2
    add_section_heading(doc, "5.2", "SQL Safety and True Database Execution Validity")
    add_para(doc,
              "Unsafe Query Execution Rate measures whether a generated SQL statement contains a "
              "genuine unsafe operation such as a write or schema-changing command. Query Execution "
              "Validity measures whether the SQL actually runs against the seeded MySQL database. These "
              "are different measurements: safety is about what the query is allowed to do, while true "
              "execution validity is about whether the database accepts and executes the statement.",
              space_after=10)
    add_table_with_caption(
        doc, "Table 5.2: SQL safety and true execution validity on the 107-query benchmark.",
        ["System", "Unsafe SQL", "True execution validity"],
        [
            ["Baseline B1 (Direct LLM-to-SQL)", "1 genuine unsafe statement in 107",
             "27 of 107 executed successfully (25.2%)"],
            ["AEGIS", "0 unsafe statements in 107",
             "100 of 107 executed successfully (93.5%)"],
            ["B3 Template-only", "Not used as the primary safety baseline in this chapter",
             "104 of 107 executed successfully (97.2%)"],
        ])
    add_para(doc,
              "Baseline B1 mostly failed because of hallucinated columns, invalid table references, or "
              "dialect errors. AEGIS had no unsafe SQL, but seven generated statements still failed due "
              "to implementation defects diagnosed below. B3 is included as a compiler-behavior "
              "comparison, not as a semantic-correctness result.", space_after=8)
    add_para(doc,
              "The strongest safety example is the disguised write request asking to cancel orders stuck "
              "in Pending for more than 30 days. Baseline B1 produced an executable UPDATE statement. "
              "AEGIS cannot express a write intent in its intent object or compiler templates, so it did "
              "not emit write SQL. This is the central safety result: AEGIS prevents this class of unsafe "
              "execution structurally rather than hoping the model follows an instruction not to write "
              "dangerous SQL.", space_after=0)
    add_figure_placeholder(doc, 8,
        "Verified safety and execution-validity comparison",
        "A grouped bar chart comparing B1, AEGIS, and B3 where available. Show unsafe SQL as counts "
        "and true execution validity as successful executions out of 107. Do not plot semantic "
        "correctness here; correctness is a separate annotated benchmark.")

    # ---------------------------------------------------------------- 5.3
    add_section_heading(doc, "5.3", "Execution Failure Analysis")
    add_para(doc,
              "The seven AEGIS execution failures identify the remaining implementation limitations "
              "of the prototype. These failures are not safety violations; they are executable-query "
              "construction issues observed when the generated SQL was tested against the evaluation "
              "database.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.3: AEGIS true-execution failures diagnosed from MySQL execution.",
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

    # ---------------------------------------------------------------- 5.4
    add_section_heading(doc, "5.4", "Semantic Correctness and Accuracy")
    add_para(doc,
              "Correctness or accuracy must be treated separately from execution validity. The "
              "current results show that AEGIS often generates SQL that executes successfully and "
              "avoids unsafe operations, but they do not establish that every executable result "
              "matches the user's intended analytical meaning.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.4: Distinguishing the evaluation metrics.",
        ["Metric", "What it answers", "Current status"],
        [
            ["SQL safety", "Did the generated SQL avoid unsafe write or schema-changing behavior?",
             "Verified for B1 and AEGIS on all 107 requests."],
            ["True execution validity", "Did the generated SQL run against the seeded MySQL database?",
             "Verified for B1, AEGIS, and B3."],
            ["Semantic correctness / accuracy", "Did the answer match the user's intended reporting need?",
             "Not yet numerically scored; requires annotated expected outputs or labels."],
            ["Scope handling", "Did the system clarify or reject unsupported requests instead of guessing?",
             "Observed as a limitation; needs a separate annotated evaluation."],
            ["Latency", "How long each stage takes end to end?",
             "Not yet instrumented."],
        ])
    add_para(doc,
              "This distinction is important for the thesis argument. AEGIS maintained SQL safety even "
              "under harder boundary cases, but the scope-detection mechanism was incomplete: several "
              "unsupported or underspecified requests were mapped to safe but semantically wrong in-scope "
              "queries instead of being rejected or clarified. That behavior should be reported as a "
              "correctness and clarification limitation, not hidden inside the safety metric.",
              space_after=0)

    # ---------------------------------------------------------------- 5.5
    add_section_heading(doc, "5.5", "B3 Template-Only Baseline")
    add_para(doc,
              "The B3 template-only baseline is useful because it separates the deterministic compiler "
              "from the LLM intent parser. B3 uses keyword matching to create an intent object, then "
              "hands that intent to the same downstream semantic mapping and compiler path. Its high "
              "execution-validity result shows that many database errors are triggered by particular "
              "intent choices and time phrases, not by the compiler alone.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.5: B3 execution-validity summary.",
        ["System", "Execution result", "Interpretation"],
        [
            ["B3 Template-only", "104 of 107 executed successfully (97.2%)",
             "Higher execution validity than AEGIS on this run, but not evidence of higher semantic correctness."],
            ["B3 failures", "3 database execution failures",
             "Two compiler or join-path issues and one date-value issue were observed."],
        ])
    add_para(doc,
              "B3's result should be interpreted carefully. A keyword-only classifier may choose a query "
              "shape that runs successfully while answering the wrong question. Therefore B3 belongs in "
              "the execution-validity comparison, but it should not be used to claim semantic accuracy "
              "until the same annotated correctness benchmark is applied to all systems.", space_after=0)

    # ---------------------------------------------------------------- 5.6
    add_section_heading(doc, "5.6", "Discussion")
    add_section_heading(doc, "5.6.1", "AEGIS vs. Direct LLM-to-SQL", level=3)
    add_para(doc,
              "The B1 baseline exposes the central risk of direct SQL generation. The same model that "
              "can produce useful analytical SQL can also hallucinate schema objects, mix SQL dialects, "
              "and generate a real write statement when a business-looking request implies a write "
              "operation. AEGIS narrows the model's role to intent extraction, so these risks do not "
              "enter the SQL construction stage in the same way.", space_after=10)
    add_table_with_caption(
        doc, "Table 5.6: Structural comparison of AEGIS vs. direct LLM-to-SQL.",
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
    add_section_heading(doc, "5.6.2", "Semantic Layer versus Retrieval-Augmented Generation", level=3)
    add_para(doc,
              "Retrieval-augmented generation can help an LLM find relevant schema fragments, but it "
              "does not remove the model's authority to write SQL. AEGIS uses the semantic layer for a "
              "different purpose: it defines which business concepts are allowed to exist and how they "
              "compile into SQL. RAG may still be useful in a future large deployment to select relevant "
              "semantic-layer entries, but the final SQL should still be compiled by the deterministic "
              "AEGIS compiler.", space_after=10)
    add_section_heading(doc, "5.6.3", "Scope Boundary", level=3)
    add_para(doc,
              "AEGIS currently supports a bounded set of approved metrics, dimensions, analytical "
              "patterns, and join paths. This is the source of its safety, but also the source of its "
              "main limitation. If a user asks for something not represented in the semantic layer, the "
              "system should reject or clarify the request. The current prototype does not always do "
              "that reliably; improving scope detection is therefore a priority in future work.",
              space_after=0)
    page_break(doc)

