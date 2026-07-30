import os
import re
import copy
import io
from datetime import datetime
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

TEMPLATE_FONT = 'Times New Roman'  # matches university template typography throughout
ACCENT_GREEN = RGBColor(0x70, 0xAD, 0x47)  # theme accent6 - matches template's actual brand palette
HEADER_COLOR = RGBColor(0, 51, 102)
BODY_COLOR = RGBColor(51, 51, 51)
SUBDETAIL_COLOR = RGBColor(95, 95, 95)
CODE_COLOR = RGBColor(80, 80, 80)


def _split_label(content):
    """Split 'Label: description' into a bold lead-in and a normal remainder.
    Returns (label_incl_colon, rest_incl_leading_space) or (None, content) if no label pattern exists."""
    if content.endswith(':'):
        return content, ''
    if ': ' in content:
        label, rest = content.split(': ', 1)
        return label + ':', ' ' + rest
    return None, content


def _set_hanging_indent(paragraph, marL_inches, indent_inches):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set('marL', str(int(Inches(marL_inches))))
    pPr.set('indent', str(int(Inches(indent_inches))))


def add_bullet_text(slide, text, left, top, width, height, font_size=18, header_color=None):
    """Render a structured block of text with real typographic hierarchy:
    - lines ending in ':' or plain framing statements -> bold section headers
    - lines starting with '•' or 'N. ' -> hanging-indent bullets, with an optional
      bold 'Label:' lead-in split from the rest of the sentence
    - indented lines -> italic sub-detail/description text
    - lines that are '{', '}', or indented quoted JSON fields -> small monospace code text
    """
    if header_color is None:
        header_color = HEADER_COLOR

    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = 0
    tf.margin_top = 0
    tf.margin_right = 0

    first_para = [True]

    def next_paragraph():
        if first_para[0]:
            first_para[0] = False
            return tf.paragraphs[0]
        return tf.add_paragraph()

    for raw in text.split('\n'):
        stripped = raw.strip()
        if not stripped:
            continue

        leading_spaces = len(raw) - len(raw.lstrip(' '))
        is_indented = leading_spaces >= 1
        is_bullet = stripped.startswith('•')
        is_numbered = bool(re.match(r'^\d+\.\s', stripped)) and not is_indented
        is_sql_line = bool(re.match(r'^(SELECT|FROM|WHERE|GROUP BY|ORDER BY|LIMIT|LEFT JOIN|JOIN|AND)\b', stripped))
        is_code = stripped in ('{', '}') or (is_indented and (stripped.startswith('"') or is_sql_line))

        p = next_paragraph()
        p.line_spacing = 1.08

        if is_code:
            run = p.add_run()
            run.text = stripped
            run.font.name = 'Consolas'
            run.font.size = Pt(max(font_size - 3, 11))
            run.font.color.rgb = CODE_COLOR
            _set_hanging_indent(p, 0.4, 0)
            p.space_before = Pt(0)
            p.space_after = Pt(0)
            continue

        if is_bullet or is_numbered:
            content = stripped[1:].strip() if is_bullet else stripped
            label, rest = _split_label(content)
            marker = '• ' if is_bullet else ''
            if label is not None:
                r1 = p.add_run()
                r1.text = marker + label
                r1.font.bold = True
                r1.font.name = TEMPLATE_FONT
                r1.font.size = Pt(font_size)
                r1.font.color.rgb = header_color
                if rest:
                    r2 = p.add_run()
                    r2.text = rest
                    r2.font.name = TEMPLATE_FONT
                    r2.font.size = Pt(font_size)
                    r2.font.color.rgb = BODY_COLOR
            else:
                run = p.add_run()
                run.text = marker + content
                run.font.name = TEMPLATE_FONT
                run.font.size = Pt(font_size)
                run.font.color.rgb = BODY_COLOR
            _set_hanging_indent(p, 0.28, -0.28)
            p.space_before = Pt(3)
            p.space_after = Pt(7)
            continue

        if is_indented:
            run = p.add_run()
            run.text = stripped
            run.font.italic = True
            run.font.name = TEMPLATE_FONT
            run.font.size = Pt(max(font_size - 2, 12))
            run.font.color.rgb = SUBDETAIL_COLOR
            _set_hanging_indent(p, 0.5, 0)
            p.space_before = Pt(0)
            p.space_after = Pt(8)
            continue

        # Section header / framing statement. A bare "Heading:" gets the full
        # bold treatment; a "Label: narrative sentence" gets a bold lead-in
        # plus a normal-weight continuation so it doesn't read as a wall of bold text.
        label, rest = _split_label(stripped)
        r1 = p.add_run()
        if label is not None:
            r1.text = label
            r1.font.size = Pt(font_size + (3 if not rest else 1))
            if rest:
                r2 = p.add_run()
                r2.text = rest
                r2.font.name = TEMPLATE_FONT
                r2.font.size = Pt(font_size)
                r2.font.color.rgb = BODY_COLOR
        else:
            r1.text = stripped
            r1.font.size = Pt(font_size + 3)
        r1.font.bold = True
        r1.font.name = TEMPLATE_FONT
        r1.font.color.rgb = header_color
        _set_hanging_indent(p, 0, 0)
        p.space_before = Pt(12)
        p.space_after = Pt(5)

    return txBox


def style_table(table, header_rows=1, zebra_color=RGBColor(0xF2, 0xF4, 0xF8)):
    """Vertically center cell text, add breathing-room margins, and zebra-stripe body rows."""
    for r_idx, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.1)
            cell.margin_right = Inches(0.1)
            cell.margin_top = Inches(0.05)
            cell.margin_bottom = Inches(0.05)
            if r_idx >= header_rows and (r_idx - header_rows) % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = zebra_color

def create_presentation():
    output_path = r'D:\Development\Personal\research\docs\scripts\Md_Riaz_Mid_Defense_Final_0322310105101024.pptx'
    template_path = r'D:\Development\Personal\research\Md.Mominur Rahaman spring2022 Batch 14th Id 0322210105101511.pptx'
    
    prs = pptx.Presentation(template_path)
    orig_s1, orig_s2 = list(prs.slides)[:2]

    # Extract logo blob and branding shapes from original template slides
    logo_blob_s1 = [s for s in orig_s1.shapes if s.name == 'Picture 9'][0].image.blob
    logo_blob_s2 = [s for s in orig_s2.shapes if s.name == 'Picture 9'][0].image.blob

    pic_s1 = [s for s in orig_s1.shapes if s.name == 'Picture 9'][0]
    pic_s2 = [s for s in orig_s2.shapes if s.name == 'Picture 9'][0]

    # Required footer placeholders (date / department footer / slide number), taken
    # verbatim from the template so position, size and formatting match exactly.
    footer_placeholders = [sh for sh in orig_s2.shapes
                            if sh.name in ('Date Placeholder 3', 'Footer Placeholder 4', 'Slide Number Placeholder 5')]
    # Department + university affiliation line shown under the title on slide 1.
    dept_textbox = [sh for sh in orig_s1.shapes if sh.name == 'TextBox 14'][0]

    today_str = datetime.now().strftime('%A, %B %d, %Y')

    # Safely clear old slides to rebuild using template layout masters
    for s in list(prs.slides._sldIdLst):
        prs.part.drop_rel(s.rId)
    prs.slides._sldIdLst.clear()

    primary_color = RGBColor(0, 51, 102) # Dark Navy

    def apply_title_slide_branding(s):
        for sh in orig_s1.shapes:
            if sh.name in ['Rectangle 2', 'Rectangle 6']:
                s.shapes._spTree.insert(2, copy.deepcopy(sh._element))
        s.shapes.add_picture(io.BytesIO(logo_blob_s1), pic_s1.left, pic_s1.top, pic_s1.width, pic_s1.height)
        s.shapes._spTree.append(copy.deepcopy(dept_textbox._element))

    def apply_content_slide_branding(s, slide_number):
        for sh in orig_s2.shapes:
            if sh.name in ['Rectangle 2', 'Rectangle 6', 'Rectangle 10']:
                s.shapes._spTree.insert(2, copy.deepcopy(sh._element))
        s.shapes.add_picture(io.BytesIO(logo_blob_s2), pic_s2.left, pic_s2.top, pic_s2.width, pic_s2.height)

        for sh in footer_placeholders:
            s.shapes._spTree.append(copy.deepcopy(sh._element))
        for ph in s.placeholders:
            ph_type = str(ph.placeholder_format.type)
            if ph_type.startswith('DATE'):
                ph.text_frame.text = today_str
            elif ph_type.startswith('FOOTER'):
                ph.text_frame.text = "Department of Computer Science & Engineering, PUB"
            elif ph_type.startswith('SLIDE_NUMBER'):
                ph.text_frame.text = str(slide_number)
            for p in ph.text_frame.paragraphs:
                p.font.name = TEMPLATE_FONT

    def add_title_slide(notes=""):
        s = prs.slides.add_slide(prs.slide_layouts[0])
        apply_title_slide_branding(s)

        # Eyebrow line above the title, mirroring the template's "Presentation on" pattern
        eyebrow = s.shapes.add_textbox(Inches(1.0), Inches(1.62), Inches(11.33), Inches(0.4))
        etf = eyebrow.text_frame
        etf.word_wrap = True
        ep = etf.paragraphs[0]
        ep.text = "Mid-Defense Research Presentation"
        ep.alignment = PP_ALIGN.CENTER
        ep.font.size = Pt(18)
        ep.font.name = TEMPLATE_FONT
        ep.font.italic = True
        ep.font.color.rgb = RGBColor(70, 70, 70)

        title_shape = s.placeholders[0]
        title_shape.left = Inches(1.0)
        title_shape.top = Inches(2.05)
        title_shape.width = Inches(11.33)
        title_shape.height = Inches(1.75)
        title_shape.text = "AEGIS: A Constraint-Based Architecture for Safe\nLLM-Assisted Natural Language Analytics"
        for p in title_shape.text_frame.paragraphs:
            p.font.color.rgb = primary_color
            p.font.bold = True
            p.font.size = Pt(28)
            p.font.name = TEMPLATE_FONT
            p.alignment = PP_ALIGN.CENTER
            p.line_spacing = 1.15

        # Presenter block sits in the white space below the header band (matches the
        # template's separated, vertically-centered presenter block).
        subtitle_shape = s.placeholders[1]
        subtitle_shape.left = Inches(1.67)
        subtitle_shape.top = Inches(4.55)
        subtitle_shape.width = Inches(10.0)
        subtitle_shape.height = Inches(1.55)
        stf = subtitle_shape.text_frame
        stf.word_wrap = True
        presenter_lines = [
            ("Presenter: Md. Riaz", 18, True),
            ("Program: B.Sc. in CSE  |  ID: 0322310105101024", 15, False),
            ("Supervisor: Mst. Sahela Rahman, Lecturer, Dept. of CSE, PUB", 15, False),
        ]
        for i, (line_text, size, bold) in enumerate(presenter_lines):
            p = stf.paragraphs[0] if i == 0 else stf.add_paragraph()
            p.text = line_text
            p.font.size = Pt(size)
            p.font.name = TEMPLATE_FONT
            p.font.bold = bold
            p.font.color.rgb = primary_color if bold else RGBColor(70, 70, 70)
            p.alignment = PP_ALIGN.CENTER
            p.space_after = Pt(6)

        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s


    content_slide_count = [1]  # slide 1 is the title slide; content slides start at 2

    def add_content_slide(title_text, notes=""):
        s = prs.slides.add_slide(prs.slide_layouts[5])
        content_slide_count[0] += 1
        apply_content_slide_branding(s, content_slide_count[0])

        if len(s.placeholders) > 0:
            title_shape = s.placeholders[0]
            title_shape.left = Inches(1.3)
            title_shape.top = Inches(0.4)
            title_shape.width = Inches(10.5)
            title_shape.height = Inches(0.8)
            title_shape.text = title_text
            for p in title_shape.text_frame.paragraphs:
                p.font.color.rgb = primary_color
                p.font.bold = True
                p.font.size = Pt(24)
                p.font.name = TEMPLATE_FONT
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    # -------------------------------------------------------------
    # SLIDE 1: Title
    # -------------------------------------------------------------
    add_title_slide(
        notes="Honorable Chairman, respected committee members, and distinguished faculty. Welcome to my mid-defense presentation. Today, I present AEGIS—a research investigation into a constraint-based architecture designed to separate probabilistic language understanding from deterministic database execution in natural language analytics."
    )

    # -------------------------------------------------------------
    # SLIDE 2: Research Background
    # -------------------------------------------------------------
    s2 = add_content_slide(
        "Research Background & Context",
        notes="While natural language database querying expands data access, existing systems rely on generative LLMs writing raw SQL strings directly. Entrusting a neural model with direct query generation compromises database governance and execution safety."
    )
    add_bullet_text(s2, "The Natural Language Interface Imperative:\n• Translating natural language questions directly into analytical insights democratizes access to complex relational databases.\n\nThe Direct Execution Paradigm & Its Paradox:\n• Contemporary approaches rely on Generative LLMs emitting executable SQL statements directly.\n• The Research Paradox: Allowing a neural language model to directly write executable queries introduces non-deterministic execution risks and violates the Principle of Least Privilege in database security.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 3: Problem Statement
    # -------------------------------------------------------------
    s3 = add_content_slide(
        "Problem Statement & Vulnerability Taxonomy",
        notes="Our problem statement highlights three core vulnerability classes in current systems: Structural Injection, Schema Hallucination, and Access Control Bypass. We investigate how structural constraints can mitigate these risks without sacrificing natural language flexibility."
    )
    add_bullet_text(s3, "Current Generative NL2SQL approaches have 3 structural vulnerability classes:\n\n1. Vulnerability Class I: Structural Injection Risk\n   Adversarial prompt manipulation can bypass model instructions, causing neural models to output data-modifying DML/DDL statements (DROP, DELETE, UPDATE).\n2. Vulnerability Class II: Unbounded Schema Hallucination\n   Probabilistic token generation leads to hallucinated table joins, non-existent entity relations, and invalid column attributes.\n3. Vulnerability Class III: Access Control & Context Bypass\n   Direct query generation bypasses application-level multi-tenant boundaries and row-level security scopes.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=16)

    # -------------------------------------------------------------
    # SLIDE 4: Literature Review
    # -------------------------------------------------------------
    s4 = add_content_slide(
        "Literature Review & Existing Analysis",
        notes="In our review of existing work—such as RAT-SQL, RESDSQL, and DIN-SQL—the research focus has been almost exclusively on improving parsing accuracy, while database execution safety, schema isolation, and structural governance remain unaddressed."
    )
    table_shape = s4.shapes.add_table(6, 4, Inches(0.5), Inches(1.6), Inches(12.3), Inches(4.8))
    table = table_shape.table
    table.columns[0].width = Inches(2.8)
    table.columns[1].width = Inches(2.5)
    table.columns[2].width = Inches(3.5)
    table.columns[3].width = Inches(3.5)
    headers = ["Author(s) [Year]", "Methodology", "Focus & Approach", "Methodological Limitation"]
    for i in range(4):
        cell = table.cell(0, i)
        cell.text = headers[i]
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(14)
            p.font.name = TEMPLATE_FONT
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color

    data = [
        ["Wang et al. (2020) [RAT-SQL]", "Transformer", "Relation-aware schema encoding", "Emits raw SQL strings; vulnerable to prompt injection & hallucinations"],
        ["Li et al. (2023) [RESDSQL]", "Fine-Tuned LLM", "Decoupled schema linking & SQL skeleton", "Requires specialized fine-tuning; lacks structural execution guardrails"],
        ["Pourreza et al. (2024) [DIN-SQL]", "Multi-Step Prompting", "Decomposed prompting with GPT-4", "High inference latency & cost; prompt guardrails can be bypassed by injection"],
        ["Sun et al. (2023) [SQL-PaLM]", "LLM Fine-Tuning", "Direct natural language to SQL translation", "Opaque query execution; direct DB execution risks state-modifying DML/DDL"],
        ["Guo et al. (2022) [Robust Parsing]", "Semantic Parsing", "Domain-shift robust semantic parsing", "Exposes full raw database schema directly to neural network layers"]
    ]
    for r_idx, row_data in enumerate(data):
        for c_idx, cell_data in enumerate(row_data):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(12)
                p.font.name = TEMPLATE_FONT
    style_table(table)

    # -------------------------------------------------------------
    # SLIDE 5: Identified Research Gaps
    # -------------------------------------------------------------
    s5 = add_content_slide(
        "Identified Research Gaps",
        notes="From our literature review, we identify three critical research gaps: the lack of execution safety guarantees, the over-exposure of internal database schemas, and the tight coupling of language understanding with query string generation."
    )
    add_bullet_text(s5, "Methodological Gaps in Current Literature:\n\n• Gap 1: Absence of Execution Safety Guarantees\n  Existing models rely on prompt engineering or model fine-tuning, leaving systems vulnerable to adversarial prompt injection attacks.\n\n• Gap 2: Over-Exposure of Database Schemas\n  Current architectures expose raw database table definitions directly to untrusted neural models, exposing internal system metadata.\n\n• Gap 3: Entanglement of Language Understanding & Query Synthesis\n  Coupling natural language parsing with SQL string generation causes non-deterministic query execution.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 6: Research Questions
    # -------------------------------------------------------------
    s6 = add_content_slide(
        "Research Questions",
        notes="Our research is guided by three formal research questions: First, can LLMs support natural language analytics without generating executable SQL? Second, can deterministic compilation improve safety and governance? And third, can semantic constraints maintain analytical usefulness?"
    )
    add_bullet_text(s6, "This thesis investigates 3 primary research questions:\n\n• Research Question 1 (RQ1):\n  Can Large Language Models support natural language analytics without generating executable SQL code?\n\n• Research Question 2 (RQ2):\n  Can deterministic query compilation improve database safety and execution governance compared to generative baselines?\n\n• Research Question 3 (RQ3):\n  Can closed-vocabulary semantic constraints maintain analytical usefulness while reducing execution risks?", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 7: Objectives & Contributions
    # -------------------------------------------------------------
    s7 = add_content_slide(
        "Research Objectives & Contributions",
        notes="Our objective is to investigate the separation of probabilistic language parsing from deterministic query compilation. We aim to contribute a closed-vocabulary abstraction layer, a deterministic AST compiler, a dual-layer verification engine, and empirical benchmark findings."
    )
    add_bullet_text(s7, "Primary Research Objective:\n• To propose, formalize, and evaluate AEGIS—a constraint-based architecture that investigates whether separating language understanding from database execution improves safety and governance in natural language analytics.\n\nExpected Research Contributions:\n1. Closed-Vocabulary Semantic Abstraction: A formal mapping restricting LLM emission space.\n2. Decoupled AST Query Compilation Engine: Graph-based BFS AST compilation replacing AI generation.\n3. Dual-Layer Verification Architecture: Structural prevention of unsafe SQL execution via static AST scanning.\n4. Comparative Empirical Evaluation: Benchmark evaluation against baseline Generative models.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=16)

    # -------------------------------------------------------------
    # SLIDE 8: Research Methodology Paradigm
    # -------------------------------------------------------------
    s8 = add_content_slide(
        "Research Methodology Paradigm",
        notes="The theoretical core of AEGIS is shifting from query generation to deterministic compilation. The LLM acts purely as an intent classifier emitting JSON. The actual SQL construction is handled by a deterministic compiler."
    )
    add_bullet_text(s8, "Paradigm Shift: From AI Query Generation to Deterministic Compilation\n\n• Generative Paradigm: NL  -->  LLM (Untrusted String Generator)  -->  Raw SQL  -->  Database Execution\n• AEGIS Architecture: NL  -->  LLM (Bounded Intent Classifier)  -->  JSON  -->  Deterministic Compiler  -->  Safe SQL\n\n• LLM Function: Restricted strictly to Intent Classification (extracting metric/dimension tokens).\n• Compiler Function: Resolves relational join paths via Breadth-First Search (BFS) graph traversal.\n• Central Research Argument: Most NL-to-SQL systems try to make LLMs generate better SQL; AEGIS redefines the problem by removing SQL generation responsibility from the LLM.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=16)

    # -------------------------------------------------------------
    # SLIDE 9: Proposed AEGIS Architecture (Diagram)
    # -------------------------------------------------------------
    s9 = add_content_slide(
        "Proposed AEGIS Conceptual Architecture",
        notes="The AEGIS architecture consists of 7 pipeline stages. Stage 1 is the only AI component, responsible for intent classification. Stages 2 through 7 operate in a trusted, deterministic environment that verifies safety prior to database execution. If asked why BFS join resolution instead of hardcoding joins: hardcoding would mean writing a join clause for every metric-dimension combination - 15 x 34 = 510 combinations, many sharing overlapping paths - and any schema change would require updating all of them. BFS over a single join graph means there is exactly one place to define table relationships, and the compiler finds the correct path automatically, the same reason databases use query planners instead of hardcoded execution plans."
    )
    
    box_width = Inches(1.4)
    box_height = Inches(1.0)
    start_x = Inches(0.72)  # centers the 7-box x 1.75in-step pipeline on the 13.33in slide
    start_y = Inches(2.5)
    spacing = Inches(1.75)
    
    stages = [
        "1. Intent\nParsing", 
        "2. Vocabulary\nValidation", 
        "3. Semantic\nMapping", 
        "4. Permission\nRewriting", 
        "5. Deterministic\nCompilation", 
        "6. AST Security\nScanner", 
        "7. Safe Query\nExecution"
    ]
    
    for i, stage in enumerate(stages):
        shape = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, start_x + (i*spacing), start_y, box_width, box_height)
        shape.text = stage
        shape.fill.solid()
        if i == 0:
            shape.fill.fore_color.rgb = RGBColor(255, 192, 0)
        else:
            shape.fill.fore_color.rgb = ACCENT_GREEN
        for p in shape.text_frame.paragraphs:
            p.font.size = Pt(13)
            p.font.name = TEMPLATE_FONT
            p.alignment = PP_ALIGN.CENTER
        
        if i < 6:
            arrow = s9.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, start_x + (i*spacing) + box_width + Inches(0.05), start_y + Inches(0.4), Inches(0.25), Inches(0.2))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = RGBColor(100, 100, 100)
            
    legend1 = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.72), Inches(4.8), Inches(0.5), Inches(0.5))
    legend1.fill.solid()
    legend1.fill.fore_color.rgb = RGBColor(255, 192, 0)
    tx1 = s9.shapes.add_textbox(Inches(5.32), Inches(4.8), Inches(2), Inches(0.5))
    tx1.text_frame.text = "AI Layer (Untrusted)"
    for p in tx1.text_frame.paragraphs:
        p.font.name = TEMPLATE_FONT
        p.font.size = Pt(13)
    
    legend2 = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.72), Inches(4.8), Inches(0.5), Inches(0.5))
    legend2.fill.solid()
    legend2.fill.fore_color.rgb = RGBColor(0, 153, 76)
    tx2 = s9.shapes.add_textbox(Inches(8.32), Inches(4.8), Inches(3), Inches(0.5))
    tx2.text_frame.text = "Deterministic Layer (Safe)"
    for p in tx2.text_frame.paragraphs:
        p.font.name = TEMPLATE_FONT
        p.font.size = Pt(13)

    # -------------------------------------------------------------
    # SLIDE 10: Semantic Layer
    # -------------------------------------------------------------
    s10 = add_content_slide(
        "The Semantic Layer: Closed-Vocabulary Abstraction",
        notes="This is the core theoretical contribution: a finite registry of approved metrics and dimensions that bounds every reachable query to a Cartesian product of the two, rather than an unconstrained SQL string. If the committee asks for concrete numbers: the current nopCommerce prototype instantiates this model with 15 metrics and 34 dimensions across 11 join paths, touching 12 of the schema's 126 tables - the other 114 are system, CMS, and permission tables with no analytics relevance, so their exclusion isn't a coverage limitation, it is the access-control mechanism itself, working exactly as the formal model predicts."
    )
    add_bullet_text(s10, "The Research Contribution: A Bounded, Auditable Vocabulary\n• Two finite registries, approved metrics (M) and dimensions (D), replace direct schema access; every reachable query is a bounded (metric, dimension) pair, never an unconstrained SQL string.\n• Anything outside these registries is structurally invisible to the model - not a coverage gap, but the actual mechanism by which unauthorized access is prevented by construction.\n\nHow a Question Becomes a Join Path:\n• Revenue by category: Order -> OrderItem -> Product -> Category\n• Revenue by country: Order -> Address -> Country\n• Table relationships are defined once; the compiler finds the shortest path for any (metric, dimension) pair automatically via graph search.\n\nSecurity Boundary Enforcement:\n• Any term outside the closed vocabulary is rejected before query compilation - enforced by validation, not by convention.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=16)

    # -------------------------------------------------------------
    # SLIDE 11: Threat Model
    # -------------------------------------------------------------
    s11 = add_content_slide(
        "Formal Threat Model & Security Controls",
        notes="Our threat model evaluates four key attack vectors: prompt injection, schema exfiltration, data mutation, and cartesian join explosion. AEGIS provides structural defenses against each threat vector prior to database execution. Equally important is what's explicitly out of scope: a compromised administrator embedding malicious SQL in a metric definition, a supply-chain compromise of the compiler library, database-level privilege escalation, and LLM provider infrastructure compromise. These require standard operational security controls, not an AEGIS-specific defense. Stating the boundary explicitly is itself part of the contribution - most prior NL2SQL work never defines what its safety claims do and don't cover, which makes security comparisons difficult."
    )
    table_shape_threat = s11.shapes.add_table(5, 4, Inches(0.5), Inches(1.6), Inches(12.3), Inches(4.8))
    table_t = table_shape_threat.table
    table_t.columns[0].width = Inches(2.5)
    table_t.columns[1].width = Inches(3.2)
    table_t.columns[2].width = Inches(3.3)
    table_t.columns[3].width = Inches(3.3)
    headers_t = ["Threat Vector", "Attack Mechanism", "Traditional Generative Risk", "AEGIS Structural Defense"]
    for i in range(4):
        cell = table_t.cell(0, i)
        cell.text = headers_t[i]
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(13)
            p.font.name = TEMPLATE_FONT
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color

    data_t = [
        ["Direct Prompt Injection", "\"Ignore instructions & DROP TABLE\"", "Executable DDL generated and passed to DB", "Payload rejected by strict JSON schema parser"],
        ["Schema Exfiltration", "\"Show password hashes & system tables\"", "Model queries internal system tables", "Schema isolation; LLM lacks knowledge of unexposed tables"],
        ["Arbitrary Data Mutation", "\"Update order status to completed\"", "Unauthorized DML database modification", "Layer 2 AST Scanner blocks all UPDATE/DELETE nodes"],
        ["Cartesian Join Explosion", "Malicious query causing cartesian product", "Database crash due to resource exhaustion", "Compiler resolves joins via static BFS shortest paths"]
    ]
    for r_idx, row_data in enumerate(data_t):
        for c_idx, cell_data in enumerate(row_data):
            cell = table_t.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(11)
                p.font.name = TEMPLATE_FONT
    style_table(table_t)

    # -------------------------------------------------------------
    # SLIDE 12: AEGIS vs Direct LLM-to-SQL - Structural Comparison
    # -------------------------------------------------------------
    s_cmp = add_content_slide(
        "AEGIS vs. Direct LLM-to-SQL: A Structural Comparison",
        notes="A natural question from the committee: why not just use a more capable model and let it write SQL directly? The honest answer is that a stronger model would produce better SQL more often, but AEGIS is not competing on that dimension. It optimizes for a different set of properties - safety as a structural guarantee rather than a probabilistic one, built-in permission enforcement, and full auditability of the 15 metrics and 34 dimensions instead of having to inspect every generated query. The choice is not 'which is smarter' but 'which properties matter for this deployment context' - and for institutional reporting where data privacy and consistent metric definitions matter, structural guarantees win."
    )
    table_shape_cmp = s_cmp.shapes.add_table(7, 3, Inches(1.2), Inches(1.7), Inches(10.9), Inches(4.6))
    table_cmp = table_shape_cmp.table
    table_cmp.columns[0].width = Inches(3.3)
    table_cmp.columns[1].width = Inches(3.8)
    table_cmp.columns[2].width = Inches(3.8)
    headers_cmp = ["Property", "Direct LLM-to-SQL", "AEGIS"]
    for i in range(3):
        cell = table_cmp.cell(0, i)
        cell.text = headers_cmp[i]
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(14)
            p.font.name = TEMPLATE_FONT
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color

    data_cmp = [
        ["Query flexibility", "High - any SQL expressible", "Bounded - supported patterns only"],
        ["Safety guarantee", "Probabilistic (improves with model)", "Structural (within threat boundary)"],
        ["Metric consistency", "Depends on prompt wording", "Enforced by the semantic layer"],
        ["Auditability", "Hard - every output must be inspected", "Easy - inspect 15 metrics + 34 dimensions"],
        ["Permission enforcement", "External or prompt-level", "Built-in, applied after the LLM runs"],
        ["Cost per query", "High (frontier model required)", "Low (small model + deterministic stages)"],
    ]
    for r_idx, row_data in enumerate(data_cmp):
        for c_idx, cell_data in enumerate(row_data):
            cell = table_cmp.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(13)
                p.font.name = TEMPLATE_FONT
    style_table(table_cmp)

    # -------------------------------------------------------------
    # SLIDE 13: Current Research Progress (NEW!)
    # -------------------------------------------------------------
    s12 = add_content_slide(
        "Current Research Progress",
        notes="Here is our current research progress. Literature review, problem definition, and conceptual architecture design are complete. Prototype implementation is at 70%, and evaluation benchmarking is currently underway."
    )
    table_shape_prog = s12.shapes.add_table(8, 3, Inches(0.8), Inches(1.6), Inches(11.73), Inches(4.8))
    table_p = table_shape_prog.table
    table_p.columns[0].width = Inches(4.2)
    table_p.columns[1].width = Inches(2.2)
    table_p.columns[2].width = Inches(5.33)
    headers_p = ["Research Phase", "Completion Status (%)", "Current Status & Key Artifacts"]
    for i in range(3):
        cell = table_p.cell(0, i)
        cell.text = headers_p[i]
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(14)
            p.font.name = TEMPLATE_FONT
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color

    data_p = [
        ["Literature Review & Gap Analysis", "100%", "Comprehensive review of RAT-SQL, DIN-SQL, RESDSQL"],
        ["Problem Definition & Vulnerability Framing", "100%", "Formalization of 3 Vulnerability Classes & RQs"],
        ["Conceptual Architecture Design", "100%", "7-Stage Decoupled Pipeline & Threat Model"],
        ["Closed Semantic Layer Specification", "80%", "Metric & Dimension whitelist taxonomies defined"],
        ["Prototype & AST Compiler Implementation", "70%", "JSON Intent Extractor & BFS Join Compiler built"],
        ["Experimental Evaluation & Benchmarking", "40%", "100 test query suite & injection cases prepared"],
        ["Thesis Writing & Dissertation Draft", "50%", "Drafted background, literature review, & design chapters"]
    ]
    for r_idx, row_data in enumerate(data_p):
        for c_idx, cell_data in enumerate(row_data):
            cell = table_p.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(12)
                p.font.name = TEMPLATE_FONT
    style_table(table_p)

    # -------------------------------------------------------------
    # SLIDE 14: Implementation Progress: Intent Extraction
    # -------------------------------------------------------------
    s13 = add_content_slide(
        "Worked Example: Tracing a Query Through the Pipeline",
        notes="This trace illustrates the formal claim from the architecture section directly: the LLM's output is a bounded intent object, and the SQL string is assembled afterward from pre-written expressions - the model's own words never appear in the query. Notice that raw SQL keywords like SELECT, FROM, or WHERE are completely absent from the AI's output. An adversarial input such as \"DROP TABLE\" cannot reach the compiler because it is not a recognized metric or dimension term - it fails at the validation gate, not because the model chose to refuse it."
    )
    add_bullet_text(s13, "Natural Language Input Query: \"Show me the top 5 products by total sales revenue\"\n\nExtracted Bounded Intent Payload:\n{\n   \"intent_class\": \"ranking\",\n   \"metric_term\": \"revenue\",\n   \"dimension_term\": \"product_name\",\n   \"sort_order\": \"descending\",\n   \"limit_bounds\": 5\n}\n\nCompiled to Safe SQL (LLM has no further involvement):\n   SELECT p.Name AS label, SUM(oi.Quantity * oi.UnitPriceExclTax) AS value\n   FROM Order o JOIN OrderItem oi ON o.Id = oi.OrderId\n   JOIN Product p ON oi.ProductId = p.Id\n   GROUP BY p.Name ORDER BY value DESC LIMIT 5\n\nValidation Gate: \"revenue\" and \"product_name\" are checked against the metric/dimension registry; unknown terms like \"DROP TABLE\" fail schema parsing before reaching the compiler.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=14)

    # -------------------------------------------------------------
    # SLIDE 15: Experimental Setup
    # -------------------------------------------------------------
    s14 = add_content_slide(
        "Experimental Setup & Benchmark Plan",
        notes="For empirical evaluation, we designed a test environment using a multi-table e-commerce database. Our benchmark plan includes 100 analytical queries and 20 adversarial prompt injection attacks, compared across four baselines to isolate exactly which component of AEGIS is responsible for each safety and accuracy gain."
    )
    add_bullet_text(s14, "Evaluation Environment & Database Schema:\n• Evaluated over a multi-table e-commerce relational database schema (nopCommerce).\n• Benchmark dataset comprising 100 multi-level analytical queries across 11 core primitives.\n\nAdversarial Security Test Set:\n• Includes 20 adversarial prompt injection queries designed to attempt unauthorized DML/DDL execution and system instruction overrides.\n\nFour Planned Baseline Comparisons:\n• B1 - Direct LLM-to-SQL: the model writes SQL directly, no semantic layer.\n• B2 - Decomposed LLM: chain-of-thought entity extraction, then SQL.\n• B3 - Template-only: keyword matching to templates, no LLM.\n• B4 - AEGIS ablated: full pipeline with the semantic layer bypassed, to isolate its individual contribution.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=15)

    # -------------------------------------------------------------
    # SLIDE 16: Evaluation Metrics & Expected Results
    # -------------------------------------------------------------
    s15 = add_content_slide(
        "Quantitative Evaluation Metrics & Expected Results",
        notes="We establish four quantitative metrics to evaluate AEGIS: Unsafe Query Execution Rate, Query Execution Validity, Semantic Term Coverage, and Latency. Final empirical benchmark comparisons will be presented in the final defense."
    )
    table_shape_m = s15.shapes.add_table(5, 3, Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.2))
    table_m = table_shape_m.table
    table_m.columns[0].width = Inches(3.8)
    table_m.columns[1].width = Inches(2.8)
    table_m.columns[2].width = Inches(4.7)
    headers_m = ["Evaluation Metric", "Purpose & Focus", "Expected Outcome / Observation"]
    for i in range(3):
        cell = table_m.cell(0, i)
        cell.text = headers_m[i]
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(14)
            p.font.name = TEMPLATE_FONT
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color

    data_m = [
        ["Unsafe Query Execution Rate (UQER)", "Security & Governance", "Zero unauthorized DML/DDL emissions under adversarial prompt injection attacks."],
        ["Query Execution Validity (QEV)", "Execution Accuracy", "High compilation validity by eliminating syntax errors and hallucinated join paths."],
        ["Semantic Term Coverage (STC)", "Intent Disambiguation", "Accurate mapping of natural language phrases to whitelisted semantic tokens."],
        ["Inference & Compilation Latency", "Execution Efficiency", "Acceptable response latency suitable for interactive analytical environments."]
    ]
    for r_idx, row_data in enumerate(data_m):
        for c_idx, cell_data in enumerate(row_data):
            cell = table_m.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(12)
                p.font.name = TEMPLATE_FONT
    style_table(table_m)

    # -------------------------------------------------------------
    # SLIDE 17: Scope & Limitations
    # -------------------------------------------------------------
    s16 = add_content_slide(
        "System Scope & Limitations",
        notes="Every research architecture has scope boundaries. AEGIS trades unconstrained SQL generation for guaranteed execution safety. Un-mapped metrics require registry updates before they can be compiled."
    )
    add_bullet_text(s16, "Current Scope Boundaries:\n• Closed Vocabulary Constraint:\n  Queries requiring un-mapped custom metrics or free-form SQL functions cannot be compiled without schema registry updates.\n\n• Single-Database Target Architecture:\n  Designed and evaluated on relational DBMS architectures (PostgreSQL/SQL Server).\n\nRecognized Methodological Trade-Off:\n• Trading unconstrained natural language SQL generation for provable execution safety and database governance.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 18: Future Research Plan
    # -------------------------------------------------------------
    s17 = add_content_slide(
        "Future Research Plan & Thesis Roadmap",
        notes="Moving toward our final defense, our research roadmap includes completing benchmark testing across all 100 test queries against the four named baselines, a planned cross-schema generalizability test on WooCommerce to show the architecture isn't tied to one schema, extending AST compilation to complex window functions, and completing the thesis dissertation."
    )
    add_bullet_text(s17, "Remaining Research Milestones:\n\n1. Complete Benchmark Evaluation:\n   Finalizing comprehensive testing across all 100 test queries and 20 injection cases against the four baselines (B1-B4).\n\n2. Cross-Schema Generalizability Test (WooCommerce):\n   A planned 5-step process - identify business questions, define metrics, define dimensions, define join paths, test and iterate - to show that only the semantic layer needs rebuilding for a new schema, not the compiler or safety scanner.\n\n3. Advanced Compiler Primitives:\n   Extending the AST compiler to support complex SQL window functions (PARTITION BY, LEAD/LAG).\n\n4. Thesis Dissertation Completion:\n   Finalizing experimental results, write-ups, and comparative analysis for final defense.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=15)

    # -------------------------------------------------------------
    # SLIDE 19: Q&A
    # -------------------------------------------------------------
    s18 = add_content_slide(
        "Thank You & Discussion",
        notes="Thank you honorable committee members for your time, attention, and valuable guidance. I am now open for your questions, feedback, and discussion."
    )
    qa = s18.shapes.add_textbox(Inches(1), Inches(2.6), Inches(11.3), Inches(2))
    qtf = qa.text_frame
    qtf.word_wrap = True
    p1 = qtf.paragraphs[0]
    p1.text = "THANK YOU!"
    p1.alignment = PP_ALIGN.CENTER
    p1.font.size = Pt(36)
    p1.font.name = TEMPLATE_FONT
    p1.font.bold = True
    p1.font.color.rgb = primary_color
    p1.space_after = Pt(18)

    p2 = qtf.add_paragraph()
    p2.text = "Questions & Mid-Defense Discussion"
    p2.alignment = PP_ALIGN.CENTER
    p2.font.size = Pt(20)
    p2.font.name = TEMPLATE_FONT
    p2.font.italic = True
    p2.font.color.rgb = RGBColor(70, 70, 70)

    prs.save(output_path)
    print(f"Successfully generated final calibrated mid-defense presentation: {output_path}")

if __name__ == '__main__':
    create_presentation()
