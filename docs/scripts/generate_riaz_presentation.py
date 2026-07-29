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
        title_shape.text = "AEGIS: A Constraint-Based Framework for Safe\nNatural Language to Reporting Widgets"
        for p in title_shape.text_frame.paragraphs:
            p.font.color.rgb = primary_color
            p.font.bold = True
            p.font.size = Pt(28)
            p.alignment = PP_ALIGN.CENTER
            
        subtitle_shape = s.placeholders[1]
        subtitle_shape.text = "Mid-Defense Presentation\n\nPresenter: Md. Riaz\nProgram: B.Sc. in CSE | ID: 0322310105101024"
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
        notes="Honorable Chairman, respected committee members, and distinguished faculty. Welcome to my mid-defense presentation. Today, I present AEGIS—a novel, constraint-based framework engineered to address the fundamental security and determinism challenges in translating natural language queries into interactive reporting widgets."
    )

    # -------------------------------------------------------------
    # SLIDE 2: Outline
    # -------------------------------------------------------------
    s2 = add_content_slide(
        "Presentation Outline",
        notes="Today's defense will systematically cover our research motivation, the theoretical vulnerabilities of existing models, our proposed architecture, the closed-vocabulary semantic model, and empirical benchmark evaluation results."
    )
    add_bullet_text(s2, "1. Research Background & Security Paradox\n2. Vulnerability Classes & Problem Statement\n3. Research Objectives & Core Contributions\n4. Theoretical Scope & Methodological Feasibility\n5. Literature Review & Methodological Gaps\n6. Methodology: The AEGIS Paradigm Shift\n7. Proposed Framework Architecture & Closed Vocabulary\n8. Dual-Layer Safety Verification Engine\n9. Empirical Evaluation & Comparative Results", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 3: Motivation
    # -------------------------------------------------------------
    s3 = add_content_slide(
        "Research Background & Motivation",
        notes="While natural language analytics is highly desirable for decision-makers, allowing Large Language Models to generate free-form SQL creates an inherent security paradox. Entrusting a stochastic neural model with direct query generation compromises data security and system determinism."
    )
    add_bullet_text(s3, "The Natural Language Interface Imperative:\n• Translating natural language directly into analytical reporting widgets democratizes enterprise data accessibility.\n\nThe Direct NL2SQL Security Paradox:\n• Existing state-of-the-art techniques rely on Generative LLMs emitting executable SQL strings directly.\n• The Paradox: Granting an un-trusted AI model direct SQL generation capabilities violates the Principle of Least Privilege and introduces non-deterministic code execution into database engines.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 4: Problem Statement
    # -------------------------------------------------------------
    s4 = add_content_slide(
        "Problem Statement & Vulnerability Taxonomy",
        notes="We categorize current NL2SQL flaws into three formal vulnerability classes: Structural Injection, Schema Hallucination, and Access Control Bypass. Without mathematical constraints on the LLM's emission space, natural language database interfaces cannot be safely deployed in enterprise environments."
    )
    add_bullet_text(s4, "Current Generative NL2SQL techniques suffer from 3 formal structural vulnerability classes:\n\n1. Vulnerability Class I: Structural Injection Vulnerability (SIV)\n   Adversarial prompts override LLM system rules to force DML/DDL execution (DROP, UPDATE).\n2. Vulnerability Class II: Unbounded Schema Hallucination (USH)\n   Probabilistic models invent invalid joins, non-existent tables, and incorrect column attributes.\n3. Vulnerability Class III: Access Control & Context Bypass (ACB)\n   Direct query generation bypasses application-level tenant boundaries and permission scopes.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 5: Research Objectives
    # -------------------------------------------------------------
    s5 = add_content_slide(
        "Research Objectives & Contributions",
        notes="Our objective is not to build a simple software tool, but to establish a formal framework that proves natural language intent can be mapped to database queries deterministically without allowing the AI to write raw SQL strings."
    )
    add_bullet_text(s5, "Primary Research Objective:\n• To propose and evaluate AEGIS—a novel constraint-based framework that physically decouples natural language understanding from SQL generation while preserving semantic intent.\n\nKey Methodological Contributions:\n1. Closed-Vocabulary Abstraction Layer: A formal grammar masking database schemas.\n2. Deterministic AST Query Compiler: Graph-based BFS AST compilation replacing AI generation.\n3. Dual-Layer Formal Verification Engine: Enforcing a mathematically provable 0% injection rate.\n4. Empirical Evaluation Benchmark: Comparative analysis against baseline Generative models.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 6: Feasibility Study
    # -------------------------------------------------------------
    s6 = add_content_slide(
        "Theoretical Scope & Methodological Feasibility",
        notes="Methodologically, AEGIS shifts the problem from unconstrained code generation to bounded intent classification. This makes the architecture completely model-agnostic, operating securely across open-weights and proprietary models alike."
    )
    add_bullet_text(s6, "Grammatical Bounding Feasibility:\n• Constraining LLM outputs to a context-free JSON grammar restricts the model's state space from infinite string generation to bounded classification.\n\nModel-Agnostic Architecture:\n• Operates independently of model parameter scale—functioning effectively using open-weights models (e.g., Llama 3) via standard zero-shot intent extraction APIs.\n\nEmpirical Rigor & Scope:\n• Formally validated against 100 multi-level analytical queries across 11 core primitives.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=18)

    # -------------------------------------------------------------
    # SLIDE 7: Literature Review (Table)
    # -------------------------------------------------------------
    s7 = add_content_slide(
        "Literature Review & Research Gaps",
        notes="Existing literature focuses almost exclusively on semantic parsing accuracy while neglecting execution safety and schema isolation. AEGIS fills this gap by introducing a deterministic compilation layer and structural schema masking."
    )
    table_shape = s7.shapes.add_table(7, 4, Inches(0.5), Inches(1.6), Inches(12.3), Inches(4.8))
    table = table_shape.table
    table.columns[0].width = Inches(2.8)
    table.columns[1].width = Inches(3.0)
    table.columns[2].width = Inches(3.5)
    table.columns[3].width = Inches(3.0)
    headers = ["Author(s) [Year]", "Methodology", "Methodological Limitations", "AEGIS Solution"]
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
        ["Wang et al. (2020) [RAT-SQL]", "Relation-aware schema encoding transformer", "Emits raw SQL strings; vulnerable to prompt injection & hallucinations", "Replaces raw SQL emission with structured Intent JSON compiling to parameterized AST"],
        ["Li et al. (2023) [RESDSQL]", "Decoupled schema linking & SQL skeleton generation", "Requires specialized fine-tuning; no formal execution safety guarantees", "Zero-shot intent extraction + mathematically guaranteed 0% injection rate"],
        ["Pourreza et al. (2024) [DIN-SQL]", "Multi-step decomposed prompting with GPT-4", "High inference latency & cost; prompt injection can bypass prompt guardrails", "Decouples language processing from compilation; deterministic zero-trust engine"],
        ["Sun et al. (2023) [SQL-PaLM]", "LLM fine-tuning for direct NL2SQL translation", "Opaque execution; direct database execution risks DML/DDL mutation", "AST Security Scanner statically inspects and blocks non-SELECT AST nodes"],
        ["Guo et al. (2022) [Robust Parsing]", "Domain-shift robust semantic parsing", "Lacks access control; exposes full raw schema to the neural network", "Closed-Vocabulary Semantic Layer isolates raw database schema completely"],
        ["Zhong et al. (2020) [Seq2SQL]", "Deep reinforcement learning for SQL generation", "Fails on multi-table joins; hallucinations on table relations", "Breadth-First Search (BFS) graph compilation auto-resolves valid joins"]
    ]
    for r_idx, row_data in enumerate(data):
        for c_idx, cell_data in enumerate(row_data):
            cell = table.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(11)

    # -------------------------------------------------------------
    # SLIDE 8: Methodology
    # -------------------------------------------------------------
    s8 = add_content_slide(
        "Methodology: The AEGIS Paradigm Shift",
        notes="The fundamental contribution of AEGIS is decoupling natural language understanding from query execution. The LLM acts purely as an intent classifier. The actual SQL construction is executed by a deterministic compiler."
    )
    add_bullet_text(s8, "The Theoretical Shift: Decoupling Understanding from Compilation\n\n• Generative Paradigm: NL  -->  LLM (Untrusted String Generator)  -->  Raw SQL  -->  Database\n• AEGIS Compiler Paradigm: NL  -->  LLM (Bounded Intent Classifier)  -->  JSON  -->  Deterministic Compiler  -->  Safe SQL\n\n• Role of the LLM: Restricted solely to Intent Disambiguation (extracting metric/dimension tokens).\n• Role of the Compiler: Resolves relational join paths via Breadth-First Search (BFS) & parameterization.\n• Security Invariant: The neural model never generates, observes, or manipulates executable SQL.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 9: Architecture Diagram (Native PPTX)
    # -------------------------------------------------------------
    s9 = add_content_slide(
        "Proposed Framework Architecture",
        notes="Our pipeline consists of 7 modular stages. Stage 1 is the only untrusted component where the LLM parses user text. Stages 2 through 7 operate inside a deterministic, trusted environment that guarantees safety before any query touches the database."
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
        "7. Visual Widget\nSynthesis"
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
        notes="Instead of exposing raw database tables, AEGIS presents a Closed-Vocabulary Semantic Layer. The AI model only sees abstract, pre-approved metrics and dimensions. Internal tables and administrative data are structurally inaccessible."
    )
    add_bullet_text(s10, "Principle of Schema Isolation & Abstraction:\n• Raw database schemas, system tables, and administrative metadata are completely isolated.\n\nClosed Vocabulary Primitives:\n• Metric Registry (M): Pre-compiled, immutable aggregate SQL expressions (e.g., Revenue = SUM(Price * Qty)).\n• Dimension Taxonomy (D): Pre-approved grouping attributes (e.g., category_name, order_period).\n\nSecurity Boundary Guarantee:\n• Any term requested in a user prompt outside the closed vocabulary whitelist V = M U D is immediately rejected by the parser prior to query compilation.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 11: Technical Example
    # -------------------------------------------------------------
    s11 = add_content_slide(
        "Methodology in Action: Intent Extraction",
        notes="Here is a formal execution example. The LLM converts the query into a validated JSON structure. Notice that SQL keywords like SELECT, FROM, or WHERE are completely absent from the AI's output."
    )
    add_bullet_text(s11, "Input Query: \"Show me the top 5 products by total sales revenue\"\n\nExtracted Bounded Intent Payload:\n{\n   \"intent_class\": \"ranking\",\n   \"metric_term\": \"revenue\",\n   \"dimension_term\": \"product_name\",\n   \"sort_order\": \"descending\",\n   \"limit_bounds\": 5\n}\n\nValidation Gate: \"revenue\" is validated against Metric Registry M, and \"product_name\" against Dimension Taxonomy D. Adversarial payload keywords like \"DROP TABLE\" fail JSON grammar parsing.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 12: Safety Diagram (Native PPTX)
    # -------------------------------------------------------------
    s12 = add_content_slide(
        "Dual-Layer Safety Verification Engine",
        notes="Safety is enforced across two independent layers. Layer 1 validates the JSON structure against our closed vocabulary. Layer 2 uses an AST parser to inspect the compiled query tree, ensuring zero DML or DDL mutations can ever execute."
    )
    
    q_shape = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(2.5), Inches(2.5), Inches(1.2))
    q_shape.text = "Malicious Query\n(e.g., 'DROP TABLE')"
    q_shape.fill.solid()
    q_shape.fill.fore_color.rgb = RGBColor(200, 50, 50)
    for p in q_shape.text_frame.paragraphs:
        p.font.size = Pt(16)
        p.alignment = PP_ALIGN.CENTER
        
    arrow1 = s12.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(3.2), Inches(2.9), Inches(0.8), Inches(0.4))
    arrow1.fill.solid()
    arrow1.fill.fore_color.rgb = RGBColor(100, 100, 100)
    
    l1_shape = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.2), Inches(1.8), Inches(4.0), Inches(1.8))
    l1_shape.text = "Layer 1: Vocabulary Constraint\nPydantic & JSON-Schema strict validation enforcing closed vocabulary bounds."
    l1_shape.fill.solid()
    l1_shape.fill.fore_color.rgb = primary_color
    for p in l1_shape.text_frame.paragraphs:
        p.font.size = Pt(16)
        p.alignment = PP_ALIGN.CENTER
        
    arrow2 = s12.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(6.0), Inches(3.8), Inches(0.4), Inches(0.6))
    arrow2.rotation = 90
    arrow2.fill.solid()
    arrow2.fill.fore_color.rgb = RGBColor(100, 100, 100)
    
    l2_shape = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.2), Inches(4.6), Inches(4.0), Inches(1.8))
    l2_shape.text = "Layer 2: AST Inspection & Sanitization\nParameterized prepared statements + sqlparse AST inspection blocking non-SELECT nodes."
    l2_shape.fill.solid()
    l2_shape.fill.fore_color.rgb = primary_color
    for p in l2_shape.text_frame.paragraphs:
        p.font.size = Pt(16)
        p.alignment = PP_ALIGN.CENTER
        
    arrow3 = s12.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(8.4), Inches(5.3), Inches(0.8), Inches(0.4))
    arrow3.fill.solid()
    arrow3.fill.fore_color.rgb = RGBColor(100, 100, 100)
    
    safe_shape = s12.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9.4), Inches(5.0), Inches(2.5), Inches(1.2))
    safe_shape.text = "Safe Read-Only\nSQL AST Output"
    safe_shape.fill.solid()
    safe_shape.fill.fore_color.rgb = RGBColor(0, 153, 76)
    for p in safe_shape.text_frame.paragraphs:
        p.font.size = Pt(16)
        p.alignment = PP_ALIGN.CENTER

    # -------------------------------------------------------------
    # SLIDE 13: Threat Model
    # -------------------------------------------------------------
    s13 = add_content_slide(
        "Threat Model & Security Controls",
        notes="Our threat matrix evaluates four major attack vectors: prompt injection, schema exfiltration, data mutation, and cartesian join attacks. AEGIS structurally mitigates all four before query execution."
    )
    add_bullet_text(s13, "Formal Threat Matrix & Defenses:\n\n• Direct Prompt Injection: Attacker attempts instruction override (DROP TABLE). Stopped by Structural JSON Schema Enforcement.\n• Schema Exfiltration: Attacker queries internal password hashes. Blocked by Zero-Trust Schema Isolation.\n• Arbitrary DML Mutation: Attacker attempts UPDATE or DELETE. Blocked by Static AST Node Whitelisting (SELECT-only).\n• Cartesian Join Explosion: Attacker attempts unconstrained joins. Mitigated by BFS Pre-computed Shortest Paths.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 14: Taxonomy
    # -------------------------------------------------------------
    s14 = add_content_slide(
        "Taxonomy of 11 Analytical Primitives",
        notes="We categorized analytical reporting into 11 formal primitives. These primitives cover over 95% of standard enterprise reporting needs, allowing AEGIS to compile diverse visual widgets deterministically."
    )
    table_shape2 = s14.shapes.add_table(6, 2, Inches(1.5), Inches(1.8), Inches(10.3), Inches(4.0))
    table2 = table_shape2.table
    table2.columns[0].width = Inches(5.15)
    table2.columns[1].width = Inches(5.15)
    table2.cell(0, 0).text = "Aggregation Primitives"
    table2.cell(0, 1).text = "Comparison & Temporal Primitives"
    for i in range(2):
        cell = table2.cell(0, i)
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(16)
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color

    data2 = [
        ["1. Metric (Single Value Summary)", "6. Time Trend (Period)"],
        ["2. Single Dimension Grouping", "7. Historical Period Comparison"],
        ["3. Multi-Dimension Grouping", "8. Period-over-Period Growth"],
        ["4. Double Temporal Filtering", "9. Top-N / Bottom-N Ranking"],
        ["5. Multi-Dimension Filtering", "10. Distribution & Ratio"]
    ]
    for r_idx, row_data in enumerate(data2):
        for c_idx, cell_data in enumerate(row_data):
            cell = table2.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(16)

    # -------------------------------------------------------------
    # SLIDE 15: Evaluation Methodology
    # -------------------------------------------------------------
    s15 = add_content_slide(
        "Experimental Benchmark Methodology",
        notes="To evaluate AEGIS, we built a benchmark suite of 100 queries, including 20 adversarial injection attacks. We measured security, execution validity, and term coverage against direct LLM generation baselines."
    )
    add_bullet_text(s15, "Benchmark Dataset & Environment:\n• 100 multi-level analytical queries evaluated over a complex multi-table e-commerce relational schema.\n• Includes 20 adversarial prompt injection queries designed to attempt unauthorized DML/DDL execution.\n\nQuantitative Evaluation Metrics:\n1. Unsafe SQL Rate (Security): Percentage of queries emitting unauthorized/DML code (Target: 0%).\n2. Execution Validity Rate (Reliability): Percentage of queries executing cleanly without SQL syntax or join errors.\n3. Semantic Term Coverage: Accuracy of natural language intent extraction into semantic tokens.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 16: Evaluation (Table)
    # -------------------------------------------------------------
    s16 = add_content_slide(
        "Empirical Evaluation Results",
        notes="Empirical results demonstrate that AEGIS achieves a 0.0% Unsafe SQL Rate and 100% Execution Validity. Baseline generative models failed over 35% of the time due to syntax errors and hallucinated joins, and suffered a 5% vulnerability rate under injection attacks."
    )
    table_shape3 = s16.shapes.add_table(4, 3, Inches(2.15), Inches(2.0), Inches(9.0), Inches(3.0))
    table3 = table_shape3.table
    table3.columns[0].width = Inches(3.0)
    table3.columns[1].width = Inches(3.0)
    table3.columns[2].width = Inches(3.0)
    
    headers3 = ["Performance Metric", "AEGIS (Proposed)", "Direct LLM (Baseline)"]
    for i in range(3):
        cell = table3.cell(0, i)
        cell.text = headers3[i]
        for p in cell.text_frame.paragraphs:
            p.font.bold = True
            p.font.size = Pt(16)
            p.font.color.rgb = RGBColor(255, 255, 255)
        cell.fill.solid()
        cell.fill.fore_color.rgb = primary_color
        
    data3 = [
        ["Unsafe SQL Rate (Security)", "0.0% (Safe)", "5.0% (Vulnerable)"],
        ["Execution Validity (Accuracy)", "100.0%", "64.7%"],
        ["Term Coverage Accuracy", "100.0%", "85.0%"]
    ]
    for r_idx, row_data in enumerate(data3):
        for c_idx, cell_data in enumerate(row_data):
            cell = table3.cell(r_idx + 1, c_idx)
            cell.text = cell_data
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(16)

    # -------------------------------------------------------------
    # SLIDE 17: Conclusion
    # -------------------------------------------------------------
    s17 = add_content_slide(
        "Conclusion & Future Research Directions",
        notes="In conclusion, AEGIS proves that decoupling natural language processing from SQL compilation yields a provably secure, highly reliable framework. Future work will expand our AST compiler to support complex SQL window functions and large-scale distributed environments."
    )
    add_bullet_text(s17, "Key Methodological Conclusions:\n• Decoupling natural language intent extraction from SQL compilation effectively eliminates SQL injection risks.\n• The Closed-Vocabulary Semantic Layer guarantees total schema isolation while maintaining high analytical expressiveness.\n\nFuture Research Agenda:\n1. Scalability Verification: Benchmarking graph-based BFS compilation over large-scale datasets (10M+ rows).\n2. Window Function Primitives: Extending the AST compiler to support complex window functions (PARTITION BY, LEAD/LAG).\n3. Thesis Manuscript Completion: Finalizing experimental write-ups for thesis submission.", Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.5), font_size=17)

    # -------------------------------------------------------------
    # SLIDE 18: Q&A
    # -------------------------------------------------------------
    s18 = add_content_slide(
        "",
        notes="Thank you honorable committee members for your time and guidance. I am now ready for your questions, feedback, and discussion."
    )
    qa = add_bullet_text(s18, "THANK YOU!\n\nQuestions & Mid-Defense Discussion", Inches(1), Inches(2.2), Inches(11.3), Inches(2))
    for p in qa.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = primary_color

    prs.save(output_path)
    print(f"Successfully generated highly academic 18-slide presentation: {output_path}")

if __name__ == '__main__':
    create_presentation()
