# -*- coding: utf-8 -*-
"""Generate AEGIS_Thesis_Supervisor_Briefing.pdf using reportlab.

Rebuilds the pre-defense supervisor briefing with the literature review
synced to the corrected, expanded 31-source review from the thesis book
(docs/scripts/thesis_book_generator/). Sections 2-5 (Methodology, Novelty,
Practical Use Case, Defense Q&A) are carried over from the original
briefing essentially unchanged; only Section 1 (Research Gap Analysis)
and a few paper-count references elsewhere are updated.
"""
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                 PageBreak, KeepTogether)

NAVY = colors.HexColor('#0F3854')
GOLD = colors.HexColor('#D99A3E')
LIGHTBG = colors.HexColor('#EEF3F7')
DARK = colors.HexColor('#1A1A1A')
BORDER = colors.HexColor('#CBD5E0')
GREY = colors.HexColor('#5A6672')

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Heading1'], textColor=NAVY, fontSize=17,
                     spaceBefore=6, spaceAfter=10, fontName='Helvetica-Bold')
H2 = ParagraphStyle('H2', parent=styles['Heading2'], textColor=NAVY, fontSize=12.5,
                     spaceBefore=10, spaceAfter=6, fontName='Helvetica-Bold')
BODY = ParagraphStyle('Body', parent=styles['BodyText'], fontSize=9.7, leading=13.5,
                       spaceAfter=6, alignment=TA_LEFT, fontName='Helvetica')
BOLD_LEAD = ParagraphStyle('BoldLead', parent=BODY, fontName='Helvetica-Bold')
ITAL = ParagraphStyle('Ital', parent=BODY, fontName='Helvetica-Oblique')
CELL = ParagraphStyle('Cell', parent=BODY, fontSize=8.7, leading=11.5, spaceAfter=0)
CELL_HDR = ParagraphStyle('CellHdr', parent=CELL, textColor=colors.white, fontName='Helvetica-Bold')
QLABEL = ParagraphStyle('QLabel', parent=BODY, fontName='Helvetica-Bold', textColor=NAVY,
                         fontSize=9.7, spaceBefore=8, spaceAfter=2)


def callout(text, border=GOLD):
    t = Table([[Paragraph(text, ITAL)]], colWidths=[6.6 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHTBG),
        ('LINEBEFORE', (0, 0), (0, -1), 4, border),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    return t


def make_table(headers, rows, col_widths):
    data = [[Paragraph(h, CELL_HDR) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), CELL) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), LIGHTBG))
    t.setStyle(TableStyle(style))
    return t


def h1(text):
    return Paragraph(text, H1)


def h2(text):
    return Paragraph(text, H2)


def p(text, style=BODY):
    return Paragraph(text, style)


def gap_box(title, text):
    inner = Table([[Paragraph(f"<b>{title}</b><br/>{text}", BODY)]], colWidths=[6.6 * inch])
    inner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER),
        ('LINEBEFORE', (0, 0), (0, -1), 4, GOLD),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    return inner


def build():
    out_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..',
                                               'AEGIS_Thesis_Supervisor_Briefing.pdf'))
    doc = SimpleDocTemplate(out_path, pagesize=LETTER,
                             topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                             leftMargin=0.9 * inch, rightMargin=0.9 * inch)
    story = []

    # ---------------------------------------------------------------- Title page
    title_bg = Table([[Paragraph(
        "<font color='white' size=9><b>PRE-DEFENSE SUPERVISOR BRIEFING</b></font>", BODY)]],
        colWidths=[6.6 * inch])
    title_bg.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), GOLD),
                                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                   ('TOPPADDING', (0, 0), (-1, -1), 6),
                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    story.append(Spacer(1, 2.4 * inch))
    story.append(title_bg)
    story.append(Spacer(1, 0.25 * inch))
    title_style = ParagraphStyle('Title', parent=styles['Title'], textColor=NAVY, fontSize=22,
                                  alignment=TA_CENTER, leading=27)
    story.append(Paragraph(
        "AEGIS: A Constraint-Based Architecture for Safe Natural-Language Database Reporting",
        title_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Research Gap &middot; Methodology &middot; Novelty &middot; Defense Q&amp;A Preparation",
                            ParagraphStyle('Sub', parent=BODY, alignment=TA_CENTER, fontSize=11, textColor=GREY)))
    story.append(Spacer(1, 0.4 * inch))
    info_style = ParagraphStyle('Info', parent=BODY, alignment=TA_CENTER, fontSize=9.5, textColor=colors.white,
                                 spaceAfter=4)
    info_box = Table([[Paragraph(
        "<b>Prepared by:</b> Md. Riaz<br/>"
        "<b>Programme:</b> B.Sc. in CSE, Pundra University of Science and Technology<br/>"
        "<b>Purpose:</b> Briefing document for thesis supervisor ahead of the thesis defense<br/>"
        "<b>Repository:</b> github.com/md-riaz/AEGIS-Research<br/>"
        "<b>Date:</b> July 2026 (revised to reflect a 31-source literature review)",
        info_style)]], colWidths=[5.2 * inch])
    info_box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NAVY),
                                   ('TOPPADDING', (0, 0), (-1, -1), 12),
                                   ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 16),
                                   ('RIGHTPADDING', (0, 0), (-1, -1), 16),
                                   ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(Table([[info_box]], colWidths=[6.6 * inch],
                        style=[('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(PageBreak())

    # ---------------------------------------------------------------- How to read
    story.append(h1("How to Read This Document"))
    story.append(p(
        "This briefing is written for you, my supervisor, to review before the defense. It is "
        "deliberately organized the way a defense board expects to see a thesis explained: what "
        "was missing in prior work, what was actually studied and how, what is genuinely new, and "
        "&mdash; because the board will ask hard questions &mdash; a rehearsal set of likely "
        "questions with the answers I plan to give."))
    story.append(p(
        "It does not describe the software prototype step by step. The prototype is only the "
        "instrument I built to test a research idea; the five sections below describe the research "
        "itself."))
    story.append(make_table(
        ["Section", "What it answers"],
        [
            ["1. Research Gap", "What did 31 related sources already solve, and what did none of them solve?"],
            ["2. Methodology", "What did I actually investigate, and how was the investigation carried out?"],
            ["3. Novelty", "What is genuinely new about the way I framed and answered the question?"],
            ["4. Practical Use Case", "Who actually uses this after deployment, and what does it look like day to day?"],
            ["5. Defense Q&amp;A Prep", "What is the committee likely to ask, and how do I answer without overclaiming?"],
        ], [1.7 * inch, 4.9 * inch]))
    story.append(PageBreak())

    # ---------------------------------------------------------------- Section 1
    story.append(h1("1. Research Gap Analysis"))
    story.append(h2("1.1 What the existing literature already covers"))
    story.append(p(
        "A systematic re-check of this thesis's full reference collection against the source PDFs "
        "(undertaken while drafting the thesis book's literature review chapter) found that this "
        "briefing's earlier count of 21 papers undercounted the collection, and that two files had "
        "been filed under the wrong name. The corrected, expanded review now covers <b>31 sources</b> "
        "spanning six research clusters: traditional natural-language database interfaces, neural and "
        "LLM-based text-to-SQL, conversational/contextual querying, applied conversational business "
        "intelligence, natural-language-to-visualization/dashboard generation, and AI-dashboard "
        "adoption &amp; control. Two citations are corrected from the earlier draft: the file "
        "labeled &ldquo;Su et al.&rdquo; is the genuine TriSQL paper (Su et al., 2026, Scientific "
        "Reports 16:7892), and the file labeled &ldquo;Shailesh et al.&rdquo; is the genuine "
        "Conversational BI paper (Shailesh et al., 2025, IJERT 14(12)) &mdash; both were re-verified "
        "directly against the source PDFs and are cited below under their correct content."))
    story.append(make_table(
        ["Cluster", "Representative work", "What it contributes / where it stops"],
        [
            ["NLIDB surveys &amp; practice",
             "Affolter et al.; Li &amp; Jagadish (NaLIR); Lehmann et al.; Liu &amp; Xu (2025 review)",
             "Compare or design interaction methods for query expressiveness; Liu &amp; Xu is the only "
             "one to name SQL-injection risk (TrojanSQL) directly, without proposing an architectural "
             "defense."],
            ["Neural / LLM text-to-SQL",
             "Seq2SQL; RAT-SQL; PICARD; G-SQL; TriSQL; Spider; BIRD; Jha &amp; Anand (2025); Pinna et al. "
             "(2025, evaluation metrics)",
             "Improve SQL accuracy, schema linking, or syntactic validity &mdash; but the model still "
             "authors the executable query. TriSQL (2026) is the current state of the art (82.2% "
             "execution accuracy on Spider) and still has the LLM produce the final SQL directly, with "
             "no reported safety evaluation."],
            ["Conversational / contextual", "SParC; CoSQL",
             "Handle ambiguity and follow-up turns, but still target generated SQL as the end product, "
             "with no persistence layer."],
            ["Applied conversational BI",
             "Shailesh et al. (2025); Mujeeb et al. (2025); Chinnappaiyan (2025)",
             "Closest real-world comparisons. Shailesh et al. is a working Groq/LangChain assistant "
             "that gives the LLM direct SQL execution tools and a self-correction loop &mdash; a live "
             "example of the exact attack surface this thesis's threat model closes. None define a "
             "formal threat model, a deterministic compiler, or a closed business vocabulary."],
            ["NL-to-visualization / dashboards",
             "DataTone; NL4DV; nvBench; DashBot; Kavaz et al. (2023)",
             "Solve chart selection or dashboard composition (or survey that sub-field) assuming the "
             "data access problem is already solved elsewhere."],
            ["AI-dashboard adoption &amp; control",
             "H&auml;iki&ouml; (2024); Saidur (2025); Valkenburgh (2024)",
             "Business/IS-control and adoption literature, mostly adjacent to the technical "
             "contribution. Valkenburgh is the exception: an independently-arrived-at &ldquo;let a "
             "deterministic layer compute the answer, let the model only narrate it&rdquo; design, in "
             "an unrelated domain (spreadsheet-based explanatory analytics)."],
        ], [1.5 * inch, 2.1 * inch, 3.0 * inch]))

    story.append(h2("1.2 The five gaps that remain unresolved"))
    story.append(gap_box(
        "Gap 1 &mdash; The language model still authors executable SQL",
        "Even constrained-decoding methods like PICARD, or schema-aware methods like RAT-SQL, G-SQL "
        "and the state-of-the-art TriSQL (2026), only make model-generated SQL more accurate or "
        "syntactically valid. The probabilistic model is still the one constructing the query, so a "
        "syntactically perfect statement can still use the wrong business formula, touch an "
        "unapproved join, or return unauthorized rows."))
    story.append(Spacer(1, 6))
    story.append(gap_box(
        "Gap 2 &mdash; A database schema does not encode business meaning",
        "Schema-linking work connects words to tables and columns, but terms like &ldquo;revenue,&rdquo; "
        "&ldquo;active customer,&rdquo; or &ldquo;refund rate&rdquo; are organization-specific "
        "definitions, not schema facts. No reviewed system inserts an explicit, administrator-approved "
        "semantic layer between language understanding and query compilation."))
    story.append(Spacer(1, 6))
    story.append(gap_box(
        "Gap 3 &mdash; Safety is checked after the SQL already exists, not before",
        "None of the reviewed systems treat the authenticated user's role as an input to query "
        "construction, or define a formal family of permitted queries per role. Shailesh et al.'s "
        "deployed assistant illustrates this concretely: it gives the LLM a SQL-execution tool and a "
        "self-correction loop, with no reported adversarial evaluation. Benchmark execution accuracy "
        "therefore cannot be read as evidence of authorized access."))
    story.append(Spacer(1, 6))
    story.append(gap_box(
        "Gap 4 &mdash; No single architecture connects all the pipeline stages",
        "Text-to-SQL systems stop at SQL. NL4DV, DataTone and nvBench stop at a chart specification. "
        "DashBot stops at dashboard layout. Nothing in the literature connects intent understanding, "
        "business-semantic mapping, authorized compilation, visualization choice, and artifact "
        "persistence in one controlled pipeline."))
    story.append(Spacer(1, 6))
    story.append(gap_box(
        "Gap 5 &mdash; Every request is treated as disposable",
        "Almost all reviewed systems answer a question once and discard the analysis. None convert a "
        "recognized, recurring reporting need into a versioned, refreshable, access-controlled widget."))

    story.append(h2("1.3 Gap statement"))
    story.append(callout(
        "Existing natural-language database research focuses on making model-generated SQL more "
        "accurate or more syntactically valid &mdash; including the most recent state-of-the-art "
        "systems. It does not investigate an alternative in which the language model is prevented "
        "from generating executable SQL altogether &mdash; where the LLM is restricted to "
        "analytical-intent extraction, and business definitions, authorization rules, and executable "
        "SQL are all produced deterministically by a compiler operating over an administrator-approved "
        "semantic layer."))
    story.append(PageBreak())

    # ---------------------------------------------------------------- Section 2 (unchanged content)
    story.append(h1("2. Research Methodology"))
    story.append(h2("2.1 What is actually being investigated"))
    story.append(p(
        "This is not a study about building a better text-to-SQL tool. It is a study of one "
        "architectural decision and its consequences: who is allowed to author the executable SQL "
        "&mdash; the language model, or a deterministic compiler?"))
    story.append(make_table(
        ["Element", "Description"],
        [
            ["Independent variable", "Who authors the SQL &mdash; the LLM (baseline) or a deterministic compiler (proposed method)"],
            ["Dependent variables", "Unsafe-query rate, execution validity, intent accuracy, business-metric correctness, join correctness, authorization correctness, request coverage, latency"],
            ["Research question", "Does separating probabilistic language understanding from deterministic SQL compilation improve safety and semantic consistency compared with direct LLM-to-SQL generation?"],
            ["Hypothesis", "Restricting the LLM to intent extraction and generating SQL deterministically from an approved semantic layer reduces unsafe and semantically incorrect queries relative to direct LLM-to-SQL generation."],
        ], [1.5 * inch, 5.1 * inch]))

    story.append(h2("2.2 The two architectures under comparison"))
    story.append(p(
        "Both conditions use the same model, the same database, and the same benchmark questions "
        "&mdash; only the location of SQL authorship changes. <b>Approach A (baseline):</b> NL question "
        "&rarr; LLM understands request and generates SQL itself &rarr; Database &rarr; Query result. "
        "<b>Approach B (proposed):</b> NL question &rarr; LLM extracts analytical intent only &rarr; "
        "Validate against approved concepts &rarr; Deterministic compiler writes the SQL &rarr; "
        "Database &rarr; Result + chart + widget."))
    story.append(p(
        "The only structural difference is who is permitted to touch the SQL. In Approach A, natural "
        "language can influence the executable query's structure directly. In Approach B, natural "
        "language can influence only a typed intent object built from a closed vocabulary; the SQL "
        "structure, joins, and permission predicates all come from trusted, administrator-controlled "
        "definitions."))

    story.append(h2("2.3 The seven-stage AEGIS pipeline (proposed method)"))
    for line in [
        "1. Intent extraction &mdash; LLM converts NL request into typed JSON",
        "2. Validation &mdash; reject identifiers outside approved vocabulary",
        "3. Semantic mapping &mdash; business terms &rarr; approved SQL definitions",
        "4. Permission rewriting &mdash; role predicates added outside LLM control",
        "5. Deterministic compilation &mdash; parameterized read-only SQL is built",
        "6. Visualization selection &mdash; chart chosen from intent + result shape",
        "7. Widget persistence &mdash; plan, query identity &amp; policy saved for reuse",
    ]:
        story.append(p(line))
    story.append(p(
        "A post-compilation validator additionally accepts only a single read-only SELECT statement "
        "and rejects any forbidden construct. The threat boundary explicitly assumes the "
        "semantic-layer definitions, permission rules, and compiler templates themselves are trusted, "
        "administrator-controlled resources &mdash; this is stated up front rather than left implicit, "
        "because a committee member may otherwise assume the architecture claims to defend against a "
        "malicious administrator, which it does not."))

    story.append(h2("2.4 One request, start to finish"))
    story.append(p(
        "Trace for &ldquo;Show revenue by category this month&rdquo;: <b>Stage 1</b> &mdash; LLM "
        "returns {intent_class: ranking, metric_term: revenue, dimension_term: category, time_term: "
        "this month, sort: desc, limit: 10} with no SQL field. <b>Stage 2</b> &mdash; both terms "
        "resolve against the approved vocabulary. <b>Stage 3</b> &mdash; revenue &rarr; "
        "SUM(oi.UnitPriceExclTax * oi.Quantity); category &rarr; c.Name, with their required join "
        "tables. <b>Stage 4</b> &mdash; a role predicate is appended using the session, never anything "
        "the user typed. <b>Stage 5</b> &mdash; BFS finds the shortest join path (Order &rarr; "
        "OrderItem &rarr; Product &rarr; Product_Category_Mapping &rarr; Category); a safety scan runs "
        "before execution. <b>Stage 6</b> &mdash; ranking + descending sort &rarr; horizontal bar "
        "chart. <b>Stage 7</b> &mdash; the plan is hashed (SHA-256) and saved as a refreshable widget. "
        "The words the user actually typed never appear in the compiled SQL string."))

    story.append(h2("2.5 Three linked studies, not one"))
    story.append(make_table(
        ["Study", "What it investigates", "Purpose"],
        [
            ["Study 1 &mdash; Reporting-pattern analysis",
             "Whether common organizational reporting requests can be represented by a small, finite "
             "set of analytical patterns (KPI, ranking, trend, comparison, exception, summary, "
             "segment, funnel, cohort, correlation, tabular)",
             "Establishes that a bounded vocabulary is a reasonable design choice, not an arbitrary "
             "restriction"],
            ["Study 2 &mdash; Architectural comparison",
             "Direct LLM-to-SQL vs. AEGIS's constraint-based compilation, same model &amp; database, "
             "on a 100-question benchmark covering supported, paraphrased, unsupported, and "
             "adversarial requests",
             "Tests the central hypothesis: does removing SQL authorship from the LLM measurably "
             "reduce unsafe/incorrect queries?"],
            ["Study 3 &mdash; Cross-schema transfer",
             "The same architecture reconfigured for a second schema (WooCommerce) by replacing only "
             "the semantic-layer definitions, evaluated on a second question set",
             "Tests whether the contribution is a general method or a one-off solution tied to a "
             "single database"],
        ], [1.7 * inch, 3.0 * inch, 1.9 * inch]))

    story.append(h2("2.6 Evaluation metrics"))
    story.append(make_table(
        ["Dimension", "Metric"],
        [
            ["Intent understanding", "Precision, recall, F1, exact slot accuracy"],
            ["Semantic correctness", "Agreement with the approved metric formula and join path"],
            ["Execution", "Executable-query rate, result equivalence"],
            ["Safety", "Unsafe-query rate, adversarial rejection rate"],
            ["Authorization", "Forbidden-table / column / row access rate"],
            ["Coverage", "Direct / clarified / extended / rejected proportions"],
            ["Visualization", "Agreement with expert-approved chart choice"],
            ["Portability", "Configuration time and code changes for the second schema"],
            ["Performance", "Median / p95 latency per pipeline stage"],
        ], [1.6 * inch, 5.0 * inch]))
    story.append(p(
        "Safety and authorization are scored separately, deliberately: a query can be syntactically "
        "safe and still violate a role's access policy, or compute the wrong business number while "
        "executing without error.", ITAL))
    story.append(PageBreak())

    # ---------------------------------------------------------------- Section 3
    story.append(h1("3. Research Novelty"))
    story.append(p(
        "AEGIS does not introduce a new LLM, SQL parser, charting library, or database engine. The "
        "contribution is the research formulation and the architectural boundary &mdash; and the "
        "evaluation of whether that boundary helps."))
    for title, body in [
        ("Novelty 1 &mdash; Reformulating the target problem",
         "Prior work treats the problem as Natural Language &rarr; SQL. This research reframes it as "
         "Natural Language &rarr; Approved Analytical Intent &rarr; Deterministically Compiled Report. "
         "The object being generated by the model changes from an executable instruction to a bounded, "
         "checkable description of intent."),
        ("Novelty 2 &mdash; Testing whether a bounded reporting vocabulary is viable",
         "Instead of assuming organizational reporting needs unrestricted SQL expressiveness, the "
         "research empirically tests whether a small, finite set of analytical patterns can cover most "
         "real reporting requests &mdash; trading some expressiveness for safety, consistency, and "
         "auditability."),
        ("Novelty 3 &mdash; A hard boundary between probabilistic and deterministic responsibility",
         "LLM-controlled: interpreting user intent, identifying the reporting pattern, extracting "
         "filter values, flagging ambiguity. System-controlled: business metric &amp; dimension "
         "definitions, table and join selection, permission/role predicates, final SQL structure. "
         "This is different from prompting an LLM to &ldquo;please generate only safe SQL.&rdquo; "
         "Here, safety is a property of the architecture, not an expectation about model behavior."),
        ("Novelty 4 &mdash; A formal, role-dependent safe query space",
         "q &isin; Q_safe(L, r), where L is the approved semantic-layer definitions and r is the "
         "authenticated user's role. A generated query is only accepted if it uses an approved "
         "analytical pattern and metric/dimension, follows an approved join path, includes the "
         "required permission restriction, performs only read operations, and passes literal values as "
         "bound parameters &mdash; not if it merely executes without error."),
        ("Novelty 5 &mdash; Separating &ldquo;SQL correctness&rdquo; from &ldquo;business correctness&rdquo;",
         "A query can execute successfully and still be wrong: it might use an unapproved revenue "
         "formula, include cancelled orders it shouldn't, or expose rows outside the requester's "
         "permission. This research treats business-semantic correctness as a distinct, separately "
         "measured property rather than folding it into execution accuracy."),
        ("Novelty 6 &mdash; Turning one-off questions into reusable artifacts",
         "Differently worded requests that mean the same analysis are converted into the same "
         "standard definition and stored as a refreshable widget, rather than being answered and "
         "discarded each time."),
    ]:
        story.append(p(f"<b>{title}</b><br/>{body}"))

    story.append(h2("One-paragraph novelty summary for slides"))
    story.append(callout(
        "The contribution is not another text-to-SQL system. It is the reformulation of "
        "natural-language reporting as intent-to-report compilation, and the empirical test of "
        "whether structurally removing SQL authorship from the language model &mdash; while keeping "
        "business definitions, permissions, and query structure under deterministic control &mdash; "
        "produces safer and more semantically consistent reporting than direct LLM-to-SQL generation, "
        "without an unacceptable loss of coverage."))

    story.append(h2("One-minute spoken explanation"))
    story.append(callout(
        "&ldquo;My research investigates an architectural question in natural-language database "
        "reporting. Existing work mainly improves the accuracy or syntax of SQL generated by language "
        "models &mdash; including the current state of the art. I investigated whether the model "
        "could instead be restricted to understanding the user's analytical intention only, while "
        "executable SQL is produced deterministically from approved business definitions and "
        "authorization rules. I compared this constraint-based architecture against direct "
        "LLM-to-SQL under the same model, database, and questions, measuring safety, semantic "
        "correctness, authorization, coverage, and latency. The contribution is not the prototype "
        "&mdash; it is the formulation and evaluation of intent-to-report compilation as an "
        "alternative to direct LLM-generated SQL.&rdquo;", border=NAVY))
    story.append(PageBreak())

    # ---------------------------------------------------------------- Section 4
    story.append(h1("4. Practical Use Case &mdash; Life After Deployment"))
    story.append(p(
        "A defense committee will eventually ask &ldquo;who actually uses this, and why does it "
        "matter?&rdquo; The answer is that the permission model already built into AEGIS &mdash; five "
        "roles enforced at the compiler stage &mdash; maps directly onto how a real retail or "
        "e-commerce organization is structured."))
    story.append(make_table(
        ["AEGIS role", "Typical job title", "Typical question asked", "What they actually see"],
        [
            ["store_manager", "Store / branch manager", "“How much did we sell today?”",
             "Only rows belonging to their own store &mdash; a permission predicate is appended after "
             "the LLM, using their session, not their wording."],
            ["regional_manager", "Area / regional manager", "“Compare revenue across my stores this month”",
             "Rows for every store in their region &mdash; a wider but still bounded slice of the same data."],
            ["analyst", "Business / data analyst", "“Refund rate by category last quarter”",
             "Broad read access across the analytics domain, still limited to the approved metric and "
             "dimension vocabulary."],
            ["read_only", "Executive / internal auditor", "Opens existing saved dashboards",
             "Can view and refresh saved widgets but cannot trigger new query compilation."],
            ["public", "Unauthenticated / demo user", "Sample questions during a demo",
             "Only non-sensitive, pre-approved aggregate metrics."],
        ], [1.15 * inch, 1.4 * inch, 1.85 * inch, 2.2 * inch]))

    story.append(h2("4.1 A day in the life"))
    story.append(p(
        "A store manager opens the dashboard each morning and asks &ldquo;How did we do "
        "yesterday?&rdquo; &mdash; this becomes a saved KPI widget that refreshes automatically every "
        "morning. A regional manager asks a related but broader question and gets a ranking widget "
        "scoped to their whole region, from the same semantic layer and compiler, just a different "
        "permission scope. An analyst investigating a margin drop builds a deeper correlation widget "
        "that the rest of the team reuses instead of rebuilding. None of these three people write SQL, "
        "touch a shared query editor, or can see another role's data by construction rather than by "
        "convention."))

    story.append(h2("4.2 Why this matters for the thesis argument"))
    story.append(p(
        "This isn't a feature bolted on after the fact &mdash; it's the same permission-rewriting "
        "stage (Stage 4) and the same widget-persistence stage (Stage 7) already evaluated in the "
        "manuscript. The practical value of &ldquo;safe by construction&rdquo; and &ldquo;reusable by "
        "default&rdquo; is that an organization's existing reporting hierarchy &mdash; store, region, "
        "head office &mdash; maps onto AEGIS roles without any custom development."))
    story.append(PageBreak())

    # ---------------------------------------------------------------- Section 5
    story.append(h1("5. Defense Q&amp;A Preparation"))
    story.append(p("Grouped by the angle a committee member is likely to attack from. My planned "
                    "answers are underneath each question.", ITAL))

    qa_groups = [
        ("On the research gap", [
            ("Isn't this just adding a permission check on top of existing text-to-SQL systems?",
             "No. A permission check that runs after SQL is generated is a filter on an "
             "already-untrusted artifact. AEGIS never lets the LLM produce SQL in the first place "
             "&mdash; the permission rule is inserted during deterministic compilation, using the "
             "authenticated session, not anything derived from the user's wording."),
            ("PICARD (or TriSQL) already constrains SQL generation &mdash; how is this different?",
             "PICARD rejects syntactically invalid tokens during decoding; TriSQL adds schema "
             "selection, skeleton-first decoding, and an LLM refinement loop. Both raise accuracy, "
             "but the LLM still writes the final SQL string in both cases, with no reported "
             "safety/injection evaluation. AEGIS removes SQL authorship from the model entirely, so "
             "the question of what the model might write does not arise the same way."),
            ("Why not just fine-tune or prompt-engineer the LLM to always generate safe SQL?",
             "Because that makes safety a property of model behavior, which is probabilistic and "
             "cannot be exhaustively verified. AEGIS makes safety a property of the architecture: the "
             "LLM structurally cannot emit SQL tokens, tables, or joins &mdash; its output is a typed "
             "object with no SQL field."),
        ]),
        ("On methodology and evidence", [
            ("Why only compare against direct LLM-to-SQL? What about other baselines?",
             "The design also defines decomposed LLM-to-SQL, keyword-to-template matching, and four "
             "AEGIS ablations (no vocabulary injection, no semantic layer, no permission rewriting, no "
             "post-compilation validation) as comparison points, to show which component is "
             "responsible for which improvement."),
            ("Isn't a 100-question benchmark small?",
             "It is intentionally exhaustive rather than large: constructed to cover every supported "
             "analytical pattern plus paraphrases, unsupported requests, and adversarial/unauthorized "
             "requests, so safety and rejection behavior can be measured on purpose-built cases."),
            ("How do you know the improvement isn't just a better prompt for the baseline?",
             "Both conditions use the same underlying model, the same database snapshot, and the same "
             "benchmark questions; only the location of SQL authorship changes."),
        ]),
        ("On the architecture itself", [
            ("What happens if the semantic layer itself is wrong or misconfigured?",
             "The threat boundary explicitly assumes the semantic layer, permission rules, and "
             "compiler templates are trusted, administrator-controlled resources &mdash; that is a "
             "stated limitation, not a hidden one."),
            ("What if the LLM's intent extraction is wrong &mdash; doesn't that still cause an "
             "incorrect report?",
             "Yes, and that is why intent accuracy is measured as its own metric rather than assumed. "
             "A wrong intent produces a wrong-but-safe report; it will never produce an unauthorized "
             "or structurally unsafe one."),
            ("Does the constrained vocabulary mean AEGIS can't answer many real questions?",
             "Coverage is measured explicitly, with four categories: answered directly, answered "
             "after clarification, answered via an extended pattern, or explicitly rejected."),
        ]),
        ("On practical use", [
            ("Who would actually use this after deployment?",
             "The five roles already enforced by the permission-rewriting stage map directly onto a "
             "real organizational hierarchy: store manager, regional manager, analyst, read-only, and "
             "public."),
        ]),
        ("On generalization", [
            ("Is this only built for nopCommerce?",
             "The cross-schema study reconfigures the same architecture for WooCommerce by replacing "
             "only the semantic-layer definitions, keeping the intent model, pattern taxonomy, and "
             "safety mechanism unchanged."),
        ]),
        ("On novelty", [
            ("Isn't &ldquo;don't let the AI write SQL&rdquo; an obvious idea?",
             "The idea of constraining an LLM is not new by itself &mdash; PICARD, G-SQL, and the "
             "state-of-the-art TriSQL all constrain the LLM's output in some way. What is new here is "
             "going further: removing SQL authorship from the LLM entirely, clearly defining the "
             "resulting safe query space as a function of the semantic layer and the user's role, and "
             "empirically testing whether that stricter boundary is viable for real reporting "
             "workloads without collapsing coverage."),
            ("What is the single sentence I should say if I only get one chance?",
             "&ldquo;I reformulated natural-language reporting from &lsquo;language model generates "
             "SQL&rsquo; to &lsquo;language model extracts intent, deterministic compiler generates "
             "SQL,&rsquo; and I tested whether that boundary improves safety and semantic correctness "
             "without an unacceptable loss of coverage.&rdquo;"),
        ]),
    ]
    for group_title, qas in qa_groups:
        story.append(h2(group_title))
        for q, a in qas:
            story.append(p(f"<b>Q: {q}</b>", QLABEL))
            story.append(p(a))

    story.append(Spacer(1, 10))
    story.append(p(
        "Prepared as a study aid ahead of the defense. All figures and dataset sizes referenced here "
        "should be reconciled with the final manuscript before submission.", ITAL))

    doc.build(story)
    print(f"Saved: {out_path}")


if __name__ == '__main__':
    build()
