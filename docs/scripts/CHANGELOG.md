# AEGIS Thesis Book Change Log

This file records user-directed thesis-book and presentation changes so future AI agents can continue safely without undoing prior decisions. Treat this as project-local memory for `D:\Development\Personal\research\docs\scripts`.

## 2026-08-03

### Thesis Book Generator and Outputs

Files:
- `thesis_book_generator\main.py`
- `thesis_book_generator\build_thesis.py`
- `thesis_book_generator\fm.py`
- `thesis_book_generator\ch1.py`
- `thesis_book_generator\ch2.py`
- `thesis_book_generator\ch3.py`
- `thesis_book_generator\ch4.py`
- `thesis_book_generator\ch5.py`
- `thesis_book_generator\ch67.py`
- `thesis_book_generator\refs.py`
- `AEGIS Thesis Book Draft - A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics.docx`
- `AEGIS Thesis Book Draft - A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics.pdf`

Current build command:

```powershell
& 'C:\laragon\bin\python\python-3.10\python.exe' 'D:\Development\Personal\research\docs\scripts\thesis_book_generator\main.py' 'D:\Development\Personal\research\docs\scripts\AEGIS Thesis Book Draft - A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics.docx'
```

Current Word PDF export command:

```powershell
$docx='D:\Development\Personal\research\docs\scripts\AEGIS Thesis Book Draft - A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics.docx'
$pdf='D:\Development\Personal\research\docs\scripts\AEGIS Thesis Book Draft - A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics.pdf'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
  $doc = $word.Documents.Open($docx, $false, $false)
  $doc.Save()
  $doc.ExportAsFixedFormat($pdf, 17)
  $doc.Close($false)
} finally {
  $word.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
```

### Required Thesis Formatting Decisions

- Use `Times New Roman` only across the generated DOCX.
- Use A4 page size with 1 inch margins on all sides.
- Do not keep extra left margin for binding.
- First two pages are cover/title pages and must not show page numbers.
- Visible page numbering starts from physical page 3:
  - Certification of Originality = `i`
  - Certification of Approval = `ii`
  - Acknowledgement = `iii`
  - Abstract = `iv`
  - Table of Contents = `v`
  - List of Figures = `vii`
  - List of Tables = `viii`
  - Chapter 1 starts at decimal page `1`
- Abstract must come after Acknowledgement.
- Remove the Abstract `Index Terms` line.
- First two cover pages must use the university-logo title layout based on the reference screenshots and presentation data.
- Thesis title on first two cover pages must use curly quotation marks: `"..."`.
- First cover page needs generous vertical spacing around title/course/supervisor/student/university blocks.
- Second cover/signature title page date must be `Date of submission: ____________________`.
- First cover page semester must remain `4th Year - 7th Semester` because this thesis work belongs to the previous semester.

### Content and Wording Rules

- Do not mention `mid defense`, `defense`, or presentation-stage wording inside the thesis book.
- Do not write phrases like `The verified mid-defense evaluation in Chapter 5 shows`.
- Avoid formulas entirely.
- Remove internal chapter/section references from normal prose where possible; rewrite those sentences naturally instead of saying "as discussed in Chapter X".
- Keep `Cross-Schema Generalizability` as a thesis objective or future evaluation benchmark, not as a completed benchmark result.
- Keep `Intent Parsing Accuracy` as a valid metric/benchmark concept where appropriate.
- `B3` was questioned by the user as unclear in a thesis book; avoid unexplained benchmark shorthand. If used, define it plainly or rewrite as `template-only baseline`.
- Remove AI buzzwords such as `governance` from the thesis book. Current replacements:
  - `enterprise governance and security policies` -> `institutional access-control and security policies`
  - `dashboard-governance literature` -> `dashboard policy literature`
  - `governance, or evaluation-methodology literature` -> `policy, or evaluation-methodology literature`
- Do not create a separate `out-of-scope probes` benchmark category. User clarified the benchmark is a mixed set of 107 questions treated together.
- Scope-detection failures can be discussed as part of semantic correctness/accuracy or error analysis, not as a separate out-of-scope probe benchmark.
- Correctness/accuracy is a separate benchmark area from SQL safety and execution validity.
- `True database execution validity` means generated SQL was actually executed against the real MySQL database/container and succeeded; it does not mean the answer was semantically correct.

### Reference Rules

- Arrange references by first appearance in the thesis.
- Use only one citation style.
- Remove duplicate citation styles.
- Current thesis uses IEEE-style bracket citations.

### Table of Contents Page Numbers

TOC entries were updated to match the visible page labels after the first two cover pages were excluded from numbering. Current verified top-level labels:

- Certification of Originality = `i`
- Certification of Approval = `ii`
- Acknowledgement = `iii`
- Abstract = `iv`
- Chapter 1: Introduction = `1`
- Chapter 2: Literature Review and Research Gap = `5`
- Chapter 3: Methodology = `10`
- Chapter 4: Experimental Work = `24`
- Chapter 5: Results and Discussion = `28`
- Chapter 6: Limitations and Future Work = `34`
- Chapter 7: Conclusion = `37`
- References = `39`

Do not list `List of Figures` or `List of Tables` inside the Table of Contents. Those pages still remain in the thesis front matter, but they are not TOC entries in the expected format.

`List of Figures` and `List of Tables` must include right-aligned page numbers with dot leaders on their own pages. If long figure/table titles crowd the row, shorten the list entry while keeping the caption meaningful.

Tables must not split across pages. If a table is close to the bottom of a page, add a page break before it and shorten/tighten headers or row labels so the full table fits on one page. Table 4 was moved to a fresh page and shortened for this reason.

Figure placeholders in the thesis should not show long design descriptions inside the box. Keep the placeholder area and caption only. Store replacement/design notes in `figure.md` so real images can be created later without cluttering the thesis pages.

Latest PDF verification after export:

- PDF page count: 50
- `governance` hits in DOCX: 0
- `governance` pages in PDF: none
- DOCX font declarations: `Times New Roman` only

### Mid-Defense Presentation Changes

Files:
- `generate_riaz_presentation.py`
- `Md_Riaz_Mid_Defense_Final_0322310105101024.pptx`
- `Md_Riaz_Mid_Defense_Final_0322310105101024.pdf`

Presentation decisions made earlier:

- Footer dates must be `Friday, August 07, 2026`.
- First slide semester text must be `Semester 7th`, because the mid-defense was part of the previous semester.
- Use host PowerPoint app for PDF export and verification when possible.
- Problem statement slide points 1, 2, and 3 should be full black text, not mixed black and blue.
- Literature review slide text should not touch slide corners; keep top/bottom breathing room and adjust line height/spacing.
- Slide 10, 18, and 19 table alignment was specifically checked/fixed against PDF output.

### Verification Expectations for Future Agents

- After changing thesis generator files, regenerate DOCX and export PDF through host Word COM.
- Do not claim PDF work landed unless the PDF was exported after the change.
- Use `pdfplumber`/text extraction for quick checks and render important pages to PNG for visual checks where layout matters.
- For cover pages, certification pages, TOC, tables, and slide exports, visually inspect the exported PDF, not only the source DOCX/PPTX.
- Preserve unrelated user edits; do not revert files unless explicitly asked.
- Remove mojibake characters wherever they appear. Use plain ASCII quotes and hyphens unless the user explicitly requires a special symbol.
- For sentence-style problem points, avoid bold labels followed by a dot. Use short bullet points with clear labels instead.
- Completely remove `Organization of the Thesis` from the thesis body and Table of Contents.
- Do not describe the thesis benchmark as `published benchmark questions`; use `custom 107-request benchmark` or `custom benchmark requests`.

### Bullet Rendering Fix

- Word built-in `List Bullet` styles depend on Symbol/Wingdings bullet fonts.
- Because the thesis enforces `Times New Roman` across all DOCX font declarations, built-in bullet glyphs rendered as square boxes in the exported PDF.
- `build_thesis.add_bullet()` now creates a normal paragraph with an explicit Times New Roman bullet marker and hanging indent, instead of using Word's built-in bullet style.
- Future agents should avoid reintroducing Word built-in bullet/list styles unless they also preserve a compatible bullet font, which would conflict with the current Times New Roman-only rule.

### Chapter 2 Literature Review Compaction

- Convert Chapter 2 literature review prose into presentation-style review blocks.
- Each reviewed source/group should use short bullets under `Contribution`, `Limitations`, and `Gap for AEGIS`.
- Keep the comparative table and research-gap section, but keep gap wording short and scannable.
- After this change, regenerate the DOCX, export PDF through Word COM, and update TOC/List of Figures/List of Tables page numbers from the exported PDF.

### Table Numbering and Single-Page Tables

- All visible tables must have a real table number in the caption; do not use `Table (formative study)`.
- Do not use generic captions such as `Table: Plain-language AEGIS formal model`; every table caption must include a number so it can match List of Tables.
- The formative-study benchmark classification table is `Table 3.1`.
- Do not put raw repository file paths such as `evaluation_dataset/questions.json` in thesis prose; refer to project repository artifacts or benchmark artifacts instead. Exact file names can stay in internal changelog/figure notes if needed for future agents.
- The benchmark is 107 mixed requests. If showing the old 100-pattern classification, either clearly explain the excluded 7 requests or, preferably, make the table denominator `107` and include an `Additional mixed requests` row.
- Long tables should be shortened/tightened so they fit on a single page; avoid allowing a table to split across pages.
- Captions are kept with the table using `keepNext`, and generated table rows are marked `cantSplit`.
- Chapter-specific numbering is acceptable for Chapter 3 and Chapter 5 tables because it avoids renumbering confusion after adding the previously unnumbered formative-study table.

### Figure Numbering

- Figures use continuous numbering across the thesis (`Figure 1`, `Figure 2`, etc.), not chapter-prefixed numbering.
- List of Figures entries must exactly match the visible figure captions in the PDF.

### 2026-08-04 09:10 - Chapter 5 peer-style results rewrite

- Rewrote Chapter 5 opening to present evaluation results in thesis style instead of saying results were verified from repository artifacts.
- Renamed section 5.1 Benchmark Run and Verified Metrics to 5.1 Evaluation Overview.
- Removed internal-draft wording from Chapter 5 and described the 107 requests as one mixed benchmark set.
- Replaced repository/command wording in Chapter 5 evidence basis with benchmark evidence, model outputs, baseline outputs, and true database execution results.
- Rewrote the Chapter 5 failure-analysis opening to frame failures as prototype implementation limitations, not safety violations.
- Rewrote semantic correctness wording to avoid overclaiming with prove; correctness remains separate and not numerically scored yet.
- Converted 5.6 inline dot-ending labels into real subsection headings: 5.6.1 AEGIS vs. Direct LLM-to-SQL, 5.6.2 Semantic Layer versus Retrieval-Augmented Generation, and 5.6.3 Scope Boundary.
- Updated Table of Contents entry for section 5.1.
- Also removed remaining thesis-body wording that said project repository artifacts / project repository in Chapters 3 and 4, replacing it with thesis-supporting evaluation materials.

### 2026-08-04 09:23 - Remove thesis-artifact wording and shorten conclusion

- Checked peer thesis PDFs for wording style around conclusion and source/material availability.
- Removed materials and measurement scripts are preserved with this thesis style wording from Chapter 4 because peer thesis books generally discuss dataset/method/evaluation directly rather than saying scripts are preserved with the thesis.
- Rewrote the Chapter 4 caveat to say results are prototype evaluation results produced within this research, not independently audited benchmark results.
- Shortened Chapter 7 conclusion from four long paragraphs to three compact paragraphs so it follows peer-paper style and should fit within one page.

### 2026-08-04 09:26 - Refresh TOC after shortened conclusion

- After shortening Chapter 7, PDF page count reduced to 46.
- Updated Table of Contents, List of Figures, and List of Tables page numbers based on the exported PDF text positions.
- Chapter 7 now starts on thesis page 34 and References starts on thesis page 35.

### 2026-08-04 09:46 - Remove run-in headings and add Chapter 5 summary table

- Removed run-in dot-heading style from Chapter 6 limitations and converted the content into bullet points with colon labels.
- Converted Chapter 4 implementation and baseline descriptions to bullet points with colon labels instead of label-plus-sentence wording.
- Converted Chapter 3 threat-model and architecture-stage helper output to bullet points with colon labels.
- Added Chapter 5 5.2 Main Result Summary with a compact result table matching common research-paper evaluation structure.
- Split Chapter 5 evaluation into clearer sections: SQL Safety, True Database Execution Validity, Execution Failure Analysis, Semantic Correctness Limitation, B3 Template-Only Baseline, and Comparative Discussion.
- Renumbered Chapter 5 tables from Table 5.1 through Table 5.8 and updated TOC/List entries accordingly.

### 2026-08-04 10:14 - Tighten citation discipline in Chapter 1

- Removed direct citations from the three Problem Statement bullets because those bullets state the thesis problem framing rather than a specific claim taken from one paper.
- Kept citations where the text names concrete benchmarks/systems, such as Spider and BIRD, or where Chapter 2 directly reviews a cited system/paper.
- Restored reference order so Shailesh/Valkenburgh appear where they are first discussed in Chapter 2, not in Chapter 1.
- Rebuilt DOCX and exported PDF after the citation cleanup.

### 2026-08-04 10:42 - Compact Research Paradigm section

- Rewrote Section 3.1 Research Paradigm from prose-heavy explanation into a short thesis paragraph plus bullet points with colon labels.
- Added a Design Science Research workflow figure placeholder as Figure 1 so the section can be supported by a final diagram.
- Renumbered later figure placeholders so thesis figures run continuously from Figure 1 through Figure 9.
- Updated List of Figures to match the visible figure captions and current exported PDF pages.

### 2026-08-04 11:03 - Convert experimental setup to table

- Replaced the prose-heavy Section 4.2 Experimental Environment description with a short lead sentence and Table 4.1 Experimental setup.
- Table 4.1 now summarizes database engine, Docker execution mode, schema, schema size, dataset scale, data period, and evaluation scope.
- Added Table 4.1 to the List of Tables so checklist item 23 can be treated as fully followed after export verification.

### 2026-08-04 11:16 - Compress limitations and future work

- Reduced Chapter 6 limitations from ten bullets to five compact bullets.
- Reduced Chapter 6 future-work items from ten bullets to five compact bullets.
- Merged repeated or low-level engineering items into broader thesis-style points so checklist item 28 follows the supervisor's max 4-5 points preference.

### 2026-08-04 11:27 - Remove remaining narrative internal references

- Audited thesis-body prose for narrative chapter-navigation phrases such as this chapter, described above, and limitations section.
- Rewrote remaining matches in Chapters 2, 3, 4, 5, and the acknowledgement into direct content statements.
- Kept structural references such as Table of Contents entries, chapter headings, table references, and figure references.

### 2026-08-04 11:42 - Remove blank Chapter 2 page and refresh front matter

- Removed the forced page break before Section 2.5 Comparative Summary so the previously blank thesis page 7 is no longer produced.
- Refreshed Table of Contents, List of Figures, and List of Tables page numbers after the page count changed from 45 to 44 PDF pages.
- Rebuilt DOCX and exported PDF after the page-number refresh.

### 2026-08-04 12:04 - Add versioned figure generation workflow

- Added deterministic Python/PIL figure generation under `thesis_book_generator/generate_figures.py`.
- Added Mermaid source files for the architecture pipeline and vocabulary-injection workflow under `figures/source/`.
- Tested Mermaid CLI rendering on the host by configuring Puppeteer to use installed Google Chrome through `figures/source/puppeteer-config.json`.
- Added `figures/source/render_mermaid_figures.ps1` and linked the new thesis generator README from the root README for future diagram iterations.

### 2026-08-04 16:35 - Insert generated thesis figures

- Replaced visible figure placeholders with generated PNG figures in the thesis DOCX.
- Used Python/PIL figures where precise layout or measured chart values matter: Figure 1, Figure 2, and Figure 9.
- Used Mermaid-rendered PNGs for structured process/architecture diagrams: Figures 3, 4, 5, 6, 7, and 8.
- Kept Mermaid sources under `thesis_book_generator/figures/source/` and regenerated them with the host Mermaid CLI before DOCX build.
- Added `build_thesis.add_figure_image()` so generated figures receive the same centered thesis caption format as placeholders.
- Rebuilt DOCX, exported PDF through Word COM, verified no visible `PLACEHOLDER` text remains, and refreshed TOC/List of Figures/List of Tables page numbers after figure insertion.

### 2026-08-04 17:05 - Tighten Chapter 2 page flow and Figure 1 spacing

- Removed the unnecessary forced page break after Chapter 2 Table 1 so Section 2.6 now starts on the same page when space is available.
- Regenerated Figure 1 without the internal image title, relying on the normal thesis caption below the image.
- Reduced excessive vertical space inside the third Figure 1 card after title removal.
- Rebuilt DOCX, exported PDF through Word COM, and refreshed TOC/List of Figures/List of Tables page numbers after the page count changed to 45.

### 2026-08-04 17:24 - Final PDF verification fixes

- Removed the blank page between Chapter 6 and Chapter 7 by deleting the forced page break after Chapter 6.
- Rewrote outdated `After placeholder substitution` wording now that generated figures are inserted.
- Replaced `defense-in-depth layer` with `additional safety layer` to avoid unwanted defense wording in the thesis body.
- Rebuilt DOCX, exported PDF through Word COM, and refreshed the Chapter 7 and References page numbers after the PDF page count changed to 44.

### 2026-08-04 18:07 - Refresh mid-defense presentation diagrams

- Replaced the Research Methodology slide's old text-and-shape workflow with the thesis Figure 1 design-science workflow image.
- Replaced the Evaluation Metrics & Results slide's table with the thesis Figure 9 benchmark chart.
- Added short slide notes below both inserted figures to preserve the current thesis wording on the design-science process and execution-validity meaning.
- Rebuilt the PPTX, exported the PDF through PowerPoint COM, rendered all 27 slides to PNG, and visually checked the updated methodology and benchmark slides.

### 2026-08-04 18:17 - Use thesis-book Figure 1 copy in presentation

- Extracted the exact Figure 1 PNG embedded in the thesis DOCX into `docs/scripts/presentation_assets/thesis-figure-01-dsr-workflow.png`.
- Updated the presentation generator so Slide 14 uses that thesis-book image copy rather than relying on a newly regenerated or differently scaled workflow image.
- Reduced the inserted Figure 1 size on Slide 14 so the arrowheads remain readable after PowerPoint/PDF scaling.

### 2026-08-04 18:24 - Restore methodology slide and add metrics table slide

- Restored Slide 14 Research Methodology to the earlier text-and-flow-box layout because it was more readable for presentation use.
- Kept the benchmark chart as the main Evaluation Metrics & Results slide.
- Added the previous evaluation metrics table as a new companion slide immediately after the benchmark chart slide.
- Rebuilt PPTX/PDF and rendered the updated slides for visual checking.
