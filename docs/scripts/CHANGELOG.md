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
- Thesis title on first two cover pages must use curly quotation marks: `“...”`.
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

### Bullet Rendering Fix

- Word built-in `List Bullet` styles depend on Symbol/Wingdings bullet fonts.
- Because the thesis enforces `Times New Roman` across all DOCX font declarations, built-in bullet glyphs rendered as square boxes in the exported PDF.
- `build_thesis.add_bullet()` now creates a normal paragraph with an explicit Times New Roman bullet marker and hanging indent, instead of using Word's built-in bullet style.
- Future agents should avoid reintroducing Word built-in bullet/list styles unless they also preserve a compatible bullet font, which would conflict with the current Times New Roman-only rule.
