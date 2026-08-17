# AEGIS Thesis Book Generator

This folder contains the source scripts used to generate the thesis DOCX/PDF and supporting figure assets.

## Build Thesis DOCX

```powershell
& 'C:\laragon\bin\python\python-3.10\python.exe' `
  'D:\Development\Personal\research\docs\scripts\thesis_book_generator\main.py' `
  'D:\Development\Personal\research\docs\scripts\AEGIS Thesis Book Draft - A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics.docx'
```

Export the DOCX to PDF through Microsoft Word COM after rebuilding.

## Figure Workflow

Figure sources are kept under `figures/source/` so diagrams can be versioned and regenerated after thesis changes.

- Mermaid source files (`*.mmd`) are used for flowchart and sequence-style diagrams.
- Generated PNGs are written to `figures/`.

### Render Mermaid Figures Locally

The Mermaid CLI is run by `figures/source/render_mermaid_figures.py`. The script uses bundled/local `pnpm` first, falls back to `npm`, and prints a setup warning if neither runner or the Mermaid CLI package is available. It uses the installed host Chrome through `figures/source/puppeteer-config.json`.

```powershell
python 'D:\Development\Personal\research\docs\scripts\thesis_book_generator\figures\source\render_mermaid_figures.py'
```

If Mermaid CLI reports that `chrome-headless-shell` is missing, keep using the checked-in `puppeteer-config.json`; it points Puppeteer to the host Chrome install instead of requiring a separate browser download.

### Preview Mermaid Figures in Browser

Open:

```text
D:\Development\Personal\research\docs\scripts\thesis_book_generator\figures\source\preview_mermaid.html
```

This is for quick visual review only. The committed `*.mmd` files remain the source of truth.
