# AEGIS JIIS Submission Package

Target journal: Journal of Intelligent Information Systems (Springer).

The journal's official submission guidance states a 25-page limit including references, tables, and figures; LaTeX is the only acceptable manuscript format; and the upload should include source files, style files, figures, bibliography files, and a compiled PDF. This folder keeps the paper-submission track independent from the Pundra University thesis-book DOCX/PDF.

Official guidance checked: https://link.springer.com/journal/10844/submission-guidelines

## Files

- `main.tex` - Springer Nature LaTeX manuscript source.
- `references.bib` - BibTeX references for the manuscript.
- `fig*.png` - figure assets placed beside `main.tex` for submission-system compatibility.
- `sn-jnl.cls`, `sn-basic.bst`, `sn-apacite.bst`, `sn-mathphys-num.bst` - Springer Nature template/style files.
- `AEGIS_JIIS_Manuscript.md` - Markdown source snapshot used to generate the LaTeX package.

## Build

Use a Springer-compatible LaTeX environment, then run:

```powershell
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

If using Overleaf, upload all files in this folder and compile `main.tex`.
