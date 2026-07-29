import os
import copy
import io
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def add_bullet_text(slide, text, left, top, width, height, font_size=18):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.text = text
    for p in tf.paragraphs:
        p.font.size = Pt(font_size)
        p.font.color.rgb = RGBColor(51, 51, 51)
    return txBox

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

    def apply_content_slide_branding(s):
        for sh in orig_s2.shapes:
            if sh.name in ['Rectangle 2', 'Rectangle 6', 'Rectangle 10']:
                s.shapes._spTree.insert(2, copy.deepcopy(sh._element))
        s.shapes.add_picture(io.BytesIO(logo_blob_s2), pic_s2.left, pic_s2.top, pic_s2.width, pic_s2.height)

    def add_title_slide(notes=""):
        s = prs.slides.add_slide(prs.slide_layouts[0])
        apply_title_slide_branding(s)
        
        title_shape = s.placeholders[0]
        title_shape.text = "AEGIS: A Constraint-Based Architecture for Safe\nLLM-Assisted Natural Language Analytics"
        for p in title_shape.text_frame.paragraphs:
            p.font.color.rgb = primary_color
            p.font.bold = True
            p.font.size = Pt(28)
            p.alignment = PP_ALIGN.CENTER
            
        subtitle_shape = s.placeholders[1]
        subtitle_shape.text = "Mid-Defense Research Presentation\n\nPresenter: Md. Riaz\nProgram: B.Sc. in CSE | ID: 0322310105101024"
        for p in subtitle_shape.text_frame.paragraphs:
            p.font.size = Pt(18)
            p.alignment = PP_ALIGN.CENTER
            
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    def add_content_slide(title_text, notes=""):
        s = prs.slides.add_slide(prs.slide_layouts[5])
        apply_content_slide_branding(s)
        
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
        notes="While natural language analytics is highly desirable for decision-makers, allowing Large Language Models to generate free-form SQL creates an inherent security paradox. Entrusting a stochastic neural model with direct query generation compromises database governance and execution safety."
    )
    add_bullet_text(s2, "The Natural Language Interface Imperative:\n• Translating natural language questions directly into analytical insights democratizes access to complex relational databases.\n\nThe Direct Execution Paradigm & Its Paradox:\n• Contemporary approaches rely on Generative LLMs emitting executable SQL statements directly.\n• The Research Paradox: Allowing a neural language model to directly write executable queries introduces non-deterministic execution risks and violates the Principle of Least Privilege in database security.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 3: Problem Statement
    # -------------------------------------------------------------
    s3 = add_content_slide(
        "Problem Statement & Vulnerability Taxonomy",
        notes="Our problem statement highlights three core vulnerability classes in current systems: Structural Injection, Schema Hallucination, and Access Control Bypass. We investigate how structural constraints can mitigate these risks without sacrificing natural language flexibility."
    )
    add_bullet_text(s3, "Current Generative NL2SQL approaches exhibit 3 structural vulnerability classes:\n\n1. Vulnerability Class I: Structural Injection Risk\n   Adversarial prompt manipulation can bypass model instructions, causing neural models to output data-modifying DML/DDL statements (DROP, DELETE, UPDATE).\n2. Vulnerability Class II: Unbounded Schema Hallucination\n   Probabilistic token generation leads to hallucinated table joins, non-existent entity relations, and invalid column attributes.\n3. Vulnerability Class III: Access Control & Context Bypass\n   Direct query generation bypasses application-level multi-tenant boundaries and row-level security scopes.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=16)

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
        notes="Our research is guided by three formal research questions: First, can we perform natural language analytics without LLM-generated SQL? Second, does deterministic compilation improve database security? And third, can semantic constraints maintain analytical utility while eliminating risks?"
    )
    add_bullet_text(s6, "This thesis investigates 3 primary research questions:\n\n• Research Question 1 (RQ1):\n  Can natural language analytics be performed without allowing Large Language Models to generate executable SQL code?\n\n• Research Question 2 (RQ2):\n  Can deterministic query compilation improve database security and execution governance compared to generative baselines?\n\n• Research Question 3 (RQ3):\n  Can closed-vocabulary semantic constraints preserve analytical expressiveness while eliminating execution risks?", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 7: Objectives & Contributions
    # -------------------------------------------------------------
    s7 = add_content_slide(
        "Research Objectives & Contributions",
        notes="Our objective is to investigate the separation of probabilistic language parsing from deterministic query compilation. We aim to contribute a closed-vocabulary abstraction layer, a deterministic AST compiler, a dual-layer verification engine, and empirical benchmark findings."
    )
    add_bullet_text(s7, "Primary Research Objective:\n• To propose, formalize, and evaluate AEGIS—a constraint-based architecture that investigates whether separating language understanding from database execution improves safety and governance in natural language analytics.\n\nExpected Research Contributions:\n1. Closed-Vocabulary Semantic Abstraction: A formal mapping restricting LLM emission space.\n2. Decoupled AST Query Compilation Engine: Graph-based BFS AST compilation replacing AI generation.\n3. Dual-Layer Verification Architecture: Structural prevention of SQL injection via static AST scanning.\n4. Comparative Empirical Evaluation: Benchmark evaluation against baseline Generative models.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 8: Research Methodology Paradigm
    # -------------------------------------------------------------
    s8 = add_content_slide(
        "Research Methodology Paradigm",
        notes="The theoretical core of AEGIS is shifting from query generation to deterministic compilation. The LLM acts purely as an intent classifier emitting JSON. The actual SQL construction is handled by a deterministic compiler."
    )
    add_bullet_text(s8, "Paradigm Shift: From AI Query Generation to Deterministic Compilation\n\n• Generative Paradigm: NL  -->  LLM (Untrusted String Generator)  -->  Raw SQL  -->  Database Execution\n• AEGIS Architecture: NL  -->  LLM (Bounded Intent Classifier)  -->  JSON  -->  Deterministic Compiler  -->  Safe SQL\n\n• LLM Function: Restricted strictly to Intent Classification (extracting metric/dimension tokens).\n• Compiler Function: Resolves relational join paths via Breadth-First Search (BFS) graph traversal.\n• Architectural Invariant: The neural model never generates, observes, or manipulates raw executable SQL.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 9: Proposed AEGIS Architecture (Diagram)
    # -------------------------------------------------------------
    s9 = add_content_slide(
        "Proposed AEGIS Conceptual Architecture",
        notes="The AEGIS architecture consists of 7 pipeline stages. Stage 1 is the only AI component, responsible for intent classification. Stages 2 through 7 operate in a trusted, deterministic environment that verifies safety prior to database execution."
    )
    
    box_width = Inches(1.4)
    box_height = Inches(1.0)
    start_x = Inches(0.5)
    start_y = Inches(2.5)
    spacing = Inches(1.75)
    
    stages = [
        "1. LLM Intent\nDisambiguation", 
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
            shape.fill.fore_color.rgb = RGBColor(0, 153, 76)
        for p in shape.text_frame.paragraphs:
            p.font.size = Pt(13)
            p.alignment = PP_ALIGN.CENTER
        
        if i < 6:
            arrow = s9.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, start_x + (i*spacing) + box_width + Inches(0.05), start_y + Inches(0.4), Inches(0.25), Inches(0.2))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = RGBColor(100, 100, 100)
            
    legend1 = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.5), Inches(4.8), Inches(0.5), Inches(0.5))
    legend1.fill.solid()
    legend1.fill.fore_color.rgb = RGBColor(255, 192, 0)
    tx1 = s9.shapes.add_textbox(Inches(5.1), Inches(4.8), Inches(2), Inches(0.5))
    tx1.text_frame.text = "AI Layer (Untrusted)"
    
    legend2 = s9.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.5), Inches(4.8), Inches(0.5), Inches(0.5))
    legend2.fill.solid()
    legend2.fill.fore_color.rgb = RGBColor(0, 153, 76)
    tx2 = s9.shapes.add_textbox(Inches(8.1), Inches(4.8), Inches(3), Inches(0.5))
    tx2.text_frame.text = "Deterministic Layer (Safe)"

    # -------------------------------------------------------------
    # SLIDE 10: Semantic Layer
    # -------------------------------------------------------------
    s10 = add_content_slide(
        "The Semantic Layer: Closed-Vocabulary Abstraction",
        notes="AEGIS introduces a Closed-Vocabulary Semantic Layer. Instead of exposing raw database schemas, the model interacts only with pre-approved metrics and dimensions. Unexposed tables and system metadata remain completely isolated."
    )
    add_bullet_text(s10, "Principle of Schema Isolation & Abstraction:\n• Internal database tables, system schemas, and administrative metadata are completely isolated from the AI model's context window.\n\nClosed-Vocabulary Primitives:\n• Metric Registry (M): Pre-compiled, immutable aggregate SQL expressions (e.g., Revenue = SUM(Price * Qty)).\n• Dimension Taxonomy (D): Pre-approved grouping attributes (e.g., category_name, order_period).\n\nSecurity Boundary Enforcement:\n• Any term requested in a user prompt outside the closed vocabulary whitelist V = M U D is immediately rejected by the validation parser before query compilation.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 11: Threat Model
    # -------------------------------------------------------------
    s11 = add_content_slide(
        "Formal Threat Model & Security Controls",
        notes="Our threat model evaluates four key attack vectors: prompt injection, schema exfiltration, data mutation, and cartesian join explosion. AEGIS provides structural defenses against each threat vector prior to database execution."
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

    # -------------------------------------------------------------
    # SLIDE 12: Implementation Progress
    # -------------------------------------------------------------
    s12 = add_content_slide(
        "Implementation Progress: Intent Extraction",
        notes="In our current prototype progress, intent extraction successfully maps user queries into bounded JSON structures. Notice that raw SQL keywords like SELECT, FROM, or WHERE are completely absent from the AI's output."
    )
    add_bullet_text(s12, "Natural Language Input Query: \"Show me the top 5 products by total sales revenue\"\n\nExtracted Bounded Intent Payload:\n{\n   \"intent_class\": \"ranking\",\n   \"metric_term\": \"revenue\",\n   \"dimension_term\": \"product_name\",\n   \"sort_order\": \"descending\",\n   \"limit_bounds\": 5\n}\n\nValidation Gate: \"revenue\" is validated against Metric Registry M, and \"product_name\" against Dimension Taxonomy D. Malicious keywords like \"DROP TABLE\" fail JSON schema parsing.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 13: Experimental Setup
    # -------------------------------------------------------------
    s13 = add_content_slide(
        "Experimental Setup & Evaluation Plan",
        notes="For empirical evaluation, we designed a test environment using a multi-table e-commerce database. Our benchmark plan includes 100 analytical queries and 20 adversarial prompt injection attacks to rigorously evaluate security and correctness."
    )
    add_bullet_text(s13, "Evaluation Environment & Database Schema:\n• Evaluated over a multi-table e-commerce relational database schema (nopCommerce).\n• Benchmark dataset comprising 100 multi-level analytical queries across 11 core primitives.\n\nAdversarial Security Test Set:\n• Includes 20 adversarial prompt injection queries designed to attempt unauthorized DML/DDL execution and system instruction overrides.\n\nBaseline Benchmark Model:\n• Direct zero-shot LLM SQL generation (Direct Generative Baseline).", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 14: Evaluation Metrics
    # -------------------------------------------------------------
    s14 = add_content_slide(
        "Quantitative Evaluation Metrics",
        notes="We establish three quantitative metrics to evaluate AEGIS: Unsafe Query Execution Rate for security, Query Execution Validity for compilation accuracy, and Semantic Term Coverage for intent disambiguation performance."
    )
    table_shape_m = s14.shapes.add_table(4, 3, Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.0))
    table_m = table_shape_m.table
    table_m.columns[0].width = Inches(3.8)
    table_m.columns[1].width = Inches(2.8)
    table_m.columns[2].width = Inches(4.7)
    headers_m = ["Evaluation Metric", "Scientific Focus", "Evaluation Methodology"]
    for i in range(3):
        cell = table_m.cell(0, i)
        cell.text = headers_m[i]
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color

    data_m = [
        ["Unsafe Query Execution Rate (UQER)", "Security & Governance", "Percentage of compiled queries emitting unauthorized DML/DDL code under adversarial attacks."],
        ["Query Execution Validity (QEV)", "Execution Accuracy", "Ratio of compiled SQL queries executing successfully without syntax errors or invalid join paths."],
        ["Semantic Term Coverage (STC)", "Intent Disambiguation", "Accuracy of the LLM in mapping natural language phrases to valid closed-vocabulary terms."]
    ]
    for r_idx, row_data in enumerate(data_m):
        for c_idx, cell_data in enumerate(row_data):
            cell = table_m.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(13)

    # -------------------------------------------------------------
    # SLIDE 15: Preliminary Results
    # -------------------------------------------------------------
    s15 = add_content_slide(
        "Preliminary Evaluation Results",
        notes="In our preliminary testing, AEGIS achieved a 0.0% Unsafe Query Rate and 100% Execution Validity. In comparison, direct generative baselines suffered from syntax errors, invalid joins, and vulnerable query generation under injection attacks."
    )
    table_shape3 = s15.shapes.add_table(4, 3, Inches(2.15), Inches(2.0), Inches(9.0), Inches(2.8))
    table3 = table_shape3.table
    table3.columns[0].width = Inches(3.0)
    table3.columns[1].width = Inches(3.0)
    table3.columns[2].width = Inches(3.0)
    
    headers3 = ["Performance Metric", "AEGIS Architecture (Proposed)", "Direct Generative LLM (Baseline)"]
    for i in range(3):
        cell = table3.cell(0, i)
        cell.text = headers3[i]
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(15)
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color
        
    data3 = [
        ["Unsafe Query Rate (Security)", "0.0% (Safe)", "5.0% (Vulnerable)"],
        ["Execution Validity (Accuracy)", "100.0%", "64.7%"],
        ["Term Coverage Accuracy", "100.0%", "85.0%"]
    ]
    for r_idx, row_data in enumerate(data3):
        for c_idx, cell_data in enumerate(row_data):
            cell = table3.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(15)

    note_box = add_bullet_text(s15, "*Note: Preliminary evaluation observations based on initial benchmark runs over 100 test queries.", Inches(1.5), Inches(5.0), Inches(10.3), Inches(0.5), font_size=13)
    for p in note_box.text_frame.paragraphs:
        p.font.italic = True
        p.font.color.rgb = RGBColor(100, 100, 100)

    # -------------------------------------------------------------
    # SLIDE 16: System Scope & Limitations
    # -------------------------------------------------------------
    s16 = add_content_slide(
        "System Scope & Limitations",
        notes="Every research architecture has scope boundaries. AEGIS trades unconstrained SQL generation for guaranteed execution safety. Un-mapped metrics require registry updates before they can be compiled."
    )
    add_bullet_text(s16, "Current Scope Boundaries:\n• Closed Vocabulary Constraint:\n  Queries requiring un-mapped custom metrics or free-form SQL functions cannot be compiled without schema registry updates.\n\n• Single-Database Target Architecture:\n  Designed and evaluated on relational DBMS architectures (PostgreSQL/SQL Server).\n\nRecognized Methodological Trade-Off:\n• Trading unconstrained natural language SQL generation for provable execution safety and database governance.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 17: Future Research Plan
    # -------------------------------------------------------------
    s17 = add_content_slide(
        "Future Research Plan & Thesis Roadmap",
        notes="Moving toward our final defense, our research roadmap includes expanding benchmark testing across additional schemas, extending AST compilation to complex window functions, and completing the thesis dissertation."
    )
    add_bullet_text(s17, "Remaining Research Milestones:\n\n1. Expanded Benchmark Evaluation:\n   Comprehensive testing across additional database schemas and edge-case query primitives.\n\n2. Advanced Compiler Primitives:\n   Extending the AST compiler to support complex SQL window functions (PARTITION BY, LEAD/LAG).\n\n3. Thesis Dissertation Completion:\n   Finalizing experimental write-ups and comparative empirical analysis for final defense.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 18: Q&A
    # -------------------------------------------------------------
    s18 = add_content_slide(
        "",
        notes="Thank you honorable committee members for your time, attention, and valuable guidance. I am now open for your questions, feedback, and discussion."
    )
    qa = add_bullet_text(s18, "THANK YOU!\n\nQuestions & Mid-Defense Discussion", Inches(1), Inches(2.2), Inches(11.3), Inches(2))
    for p in qa.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = primary_color

    prs.save(output_path)
    print(f"Successfully generated calibrated mid-defense presentation: {output_path}")

if __name__ == '__main__':
    create_presentation()
