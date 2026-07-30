# -*- coding: utf-8 -*-
"""Front matter: title pages, certifications, acknowledgement, TOC, LOF, LOT."""
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from build_thesis import add_para, add_mixed_para, page_break, add_tab_leader, FONT

TITLE = "AEGIS: A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics"
SUPERVISOR = "Mst. Sahela Rahman"
STUDENT = "Md. Riaz"
STUDENT_ID = "0322310105101024"


def _title_block(doc, eyebrow):
    add_para(doc, "DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", size=14, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "PUNDRA UNIVERSITY OF SCIENCE & TECHNOLOGY", size=14, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Bogura, Bangladesh", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=30)
    add_para(doc, eyebrow, size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
    add_para(doc, f'"{TITLE}"', size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
             space_after=18, line_spacing=1.3)
    add_para(doc, "Submitted in partial fulfillment of the requirements for the degree of",
             size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Bachelor of Science in Computer Science and Engineering", size=12, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
    add_para(doc, "Course Title: Thesis/Project Work", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Course Code: CSE-499(B)", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=28)


def title_page(doc):
    _title_block(doc, "A THESIS ON")
    add_para(doc, "Prepared By", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    add_para(doc, STUDENT, size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, f"ID: {STUDENT_ID}", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Program: B.Sc. in Computer Science & Engineering", size=12,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Semester: 8th Semester", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Session: ____________________", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
    add_para(doc, "Under the Supervision of", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    add_para(doc, SUPERVISOR, size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Designation: Lecturer", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Department of Computer Science & Engineering", size=12,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Pundra University of Science & Technology", size=12,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=28)
    add_para(doc, "Date of Submission: ____________________", size=12,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
    page_break(doc)


def signature_title_page(doc):
    _title_block(doc, "A Thesis on-")
    add_para(doc, "Submitted to", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Department of Computer Science & Engineering", size=12,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_para(doc, "Pundra University of Science & Technology", size=12,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=40)

    add_para(doc, "____________________________", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2)
    add_para(doc, "Supervisor Signature", size=12, space_after=2)
    add_para(doc, SUPERVISOR, size=12, space_after=2)
    add_para(doc, "Department of Computer Science & Engineering, Pundra University of Science & Technology",
             size=11, space_after=40)

    add_para(doc, "____________________________", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2)
    add_para(doc, "Student Signature", size=12, space_after=2)
    add_para(doc, f"{STUDENT}, ID: {STUDENT_ID}", size=12, space_after=0)
    page_break(doc)


def certification_of_originality(doc):
    add_para(doc, "CERTIFICATION OF ORIGINALITY", size=15, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=28)
    add_para(doc,
             f'I hereby declare that this thesis titled "{TITLE}" is my own original work, carried out '
             f'under the supervision of {SUPERVISOR}, Lecturer, Department of Computer Science & '
             "Engineering, Pundra University of Science & Technology. To the best of my knowledge, this "
             "thesis contains no material previously published or written by another person, except where "
             "due reference is made in the text. This work has not been submitted, in whole or in part, for "
             "any other degree or qualification at this or any other institution.",
             size=12, space_after=40)
    add_para(doc, "____________________________", space_after=2)
    add_para(doc, "Signature of Student", size=12, space_after=2)
    add_para(doc, STUDENT, size=12, bold=True, space_after=2)
    add_para(doc, f"ID: {STUDENT_ID}", size=12, space_after=0)
    page_break(doc)


def certification_of_approval(doc):
    add_para(doc, "CERTIFICATION OF APPROVAL", size=15, bold=True,
             align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
    add_para(doc, "This thesis titled", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
    add_para(doc, f'"{TITLE}"', size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_after=8, line_spacing=1.3)
    add_para(doc,
             f"submitted by {STUDENT} to the Department of Computer Science & Engineering, Pundra "
             "University of Science & Technology, has been examined and is hereby approved as a partial "
             "fulfillment of the requirements for the degree of Bachelor of Science in Computer Science "
             "and Engineering.",
             size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=40)

    add_para(doc, "Supervisor:", size=12, bold=True, space_after=30)
    add_para(doc, "____________________________", space_after=2)
    add_para(doc, SUPERVISOR, size=12, space_after=2)
    add_para(doc, "Department of Computer Science & Engineering", size=12, space_after=2)
    add_para(doc, "Pundra University of Science & Technology", size=12, space_after=36)

    add_para(doc, "Examiner:", size=12, bold=True, space_after=30)
    add_para(doc, "____________________________", space_after=2)
    add_para(doc, "Name: ______________________", size=12, space_after=0)
    page_break(doc)


def acknowledgement(doc):
    add_para(doc, "ACKNOWLEDGEMENT", size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
    add_para(doc,
             "I would like to express my sincere gratitude to my supervisor, Mst. Sahela Rahman, Lecturer, "
             "Department of Computer Science & Engineering, Pundra University of Science & Technology, for "
             "her continuous guidance, patience, and constructive feedback throughout the design, "
             "implementation, and evaluation of this research. Her insistence on precise, defensible claims "
             "shaped this thesis at every stage, from the formal safety proof to the honesty of its "
             "limitations section.",
             size=12, space_after=14)
    add_para(doc,
             "I am also grateful to the faculty members of the Department of Computer Science & Engineering "
             "for the coursework and feedback that prepared me to undertake this research, and to my family "
             "for their patience and encouragement during the long implementation and evaluation cycles this "
             "thesis required.",
             size=12, space_after=14)
    add_para(doc,
             "Finally, I acknowledge the authors of the prior work surveyed in Chapter 2 of this thesis. "
             "Their published research on natural language interfaces, text-to-SQL translation, and "
             "dashboard generation provided the foundation against which AEGIS's contributions are measured.",
             size=12, space_after=0)
    page_break(doc)


TOC_ENTRIES = [
    (0, "Certification of Originality", "i"),
    (0, "Certification of Approval", "ii"),
    (0, "Acknowledgement", "iii"),
    (0, "List of Figures", "vi"),
    (0, "List of Tables", "vii"),
    (0, "Abstract", "1"),
    (0, "Chapter 1: Introduction", "2"),
    (1, "1.1 Background", "2"),
    (1, "1.2 Problem Statement", "3"),
    (1, "1.3 Research Novelty and Motivation", "4"),
    (1, "1.4 Objectives and Contributions", "5"),
    (1, "1.5 Organization of the Thesis", "6"),
    (0, "Chapter 2: Literature Review and Research Gap", "7"),
    (1, "2.1 Natural Language Interfaces to Databases", "7"),
    (1, "2.2 Neural Text-to-SQL and Benchmark Progress", "9"),
    (1, "2.3 Constrained Decoding and Recent NL-to-SQL Systems", "11"),
    (1, "2.4 Natural Language for Visualization", "13"),
    (1, "2.5 Dashboard Generation", "14"),
    (1, "2.6 Semantic Layers and Controlled Analytics", "16"),
    (1, "2.7 AI-Powered Dashboard Adoption, Governance, and Conversational BI", "17"),
    (1, "2.8 Comparative Summary", "19"),
    (1, "2.9 Research Gap Analysis", "20"),
    (0, "Chapter 3: Methodology", "21"),
    (1, "3.1 Research Paradigm", "21"),
    (1, "3.2 Formative Study of Reporting Patterns", "22"),
    (1, "3.3 Design Principles", "24"),
    (1, "3.4 Formal Model", "24"),
    (1, "3.5 Threat Model", "26"),
    (1, "3.6 System Architecture", "28"),
    (1, "3.7 Semantic Layer Design", "29"),
    (1, "3.8 Intent Parsing with Dynamic Vocabulary Injection", "31"),
    (1, "3.9 Safe Query Compiler", "32"),
    (1, "3.10 Visualization Selector", "34"),
    (1, "3.11 Widget Persistence and Reuse", "35"),
    (0, "Chapter 4: Experimental Work", "36"),
    (1, "4.1 Implementation", "36"),
    (1, "4.2 Experimental Environment", "37"),
    (1, "4.3 Benchmark Dataset Construction", "38"),
    (1, "4.4 Baseline Systems", "39"),
    (1, "4.5 Evaluation Procedure", "40"),
    (0, "Chapter 5: Results and Discussion", "41"),
    (1, "5.1 Intent Parsing Accuracy (RQ1)", "41"),
    (1, "5.2 SQL Safety and Execution Validity (RQ2)", "42"),
    (1, "5.3 Expressiveness and Ablation Study (RQ3)", "43"),
    (1, "5.4 Cross-Schema Generalizability (RQ4)", "45"),
    (1, "5.5 Pipeline Latency (RQ5)", "46"),
    (1, "5.6 Failure Analysis", "47"),
    (1, "5.7 Discussion", "48"),
    (0, "Chapter 6: Limitations and Future Work", "51"),
    (0, "Chapter 7: Conclusion", "53"),
    (0, "References", "54"),
]


def table_of_contents(doc):
    add_para(doc, "Table of Contents", size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
    for level, text, pg in TOC_ENTRIES:
        p = add_para(doc, space_after=4 if level else 8, space_before=0 if level else 4)
        indent = 0.3 if level else 0.0
        p.paragraph_format.left_indent = Inches(indent)
        add_tab_leader(p, 6.0, leader='dot')
        r = p.add_run(text + '\t' + pg)
        r.font.name = FONT
        r.font.size = Pt(12 if level == 0 else 11.5)
        r.bold = (level == 0)
    page_break(doc)


LOF = [
    "Figure 1: AEGIS architecture pipeline (User Request to Dashboard Widget)",
    "Figure 2: Semantic layer modularity - composable blocks vs. free-form SQL generation",
    "Figure 3: Vocabulary injection workflow",
    "Figure 4: Taxonomy of the eleven AEGIS analytical primitives",
    "Figure 5: Distribution of analytics primitives across 312 real reporting requests",
    "Figure 6: Two-layer SQL safety defence",
    "Figure 7: Widget lifecycle and refresh model",
    "Figure 8: Evaluation results across unsafe-SQL rate, execution validity, and coverage",
    "Figure 9: Ablation study results",
    "Figure 10: Pipeline stage latency breakdown",
    "Figure 11: Query outcome distribution and coverage-boundary rejection reasons",
]

LOT = [
    "Table 1: Semantic layer object model (metric, dimension, filter, time rule, join path, pattern, permission)",
    "Table 2: The eleven AEGIS analytical patterns with required slots and default visualizations",
    "Table 3: Visualization selector mapping (intent, result shape, chosen chart)",
    "Table 4: Comparative summary of related NL-to-database and NL-to-visualization systems",
    "Table 5: Intent parsing precision, recall, and F1 by intent class (RQ1)",
    "Table 6: SQL safety and execution validity vs. direct LLM-to-SQL baseline (RQ2)",
    "Table 7: Ablation study - execution validity and coverage per configuration",
    "Table 8: Cross-schema generalizability results (nopCommerce vs. WooCommerce)",
    "Table 9: Pipeline stage latency (median and p95)",
    "Table 10: Structural comparison of AEGIS vs. direct LLM-to-SQL",
]


def list_of_figures(doc):
    add_para(doc, "List of Figures", size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
    for line in LOF:
        add_para(doc, line, size=12, space_after=8)
    page_break(doc)


def list_of_tables(doc):
    add_para(doc, "List of Tables", size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
    for line in LOT:
        add_para(doc, line, size=12, space_after=8)
    page_break(doc)
