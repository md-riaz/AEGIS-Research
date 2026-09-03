# -*- coding: utf-8 -*-
"""Rewrite the page numbers in fm.py's TOC, List of Figures and List of Tables.

The three front-matter lists carry their page numbers as literal strings, so
every edit to a chapter silently invalidates them. They were last synchronised
against a 42-page layout; the book is longer now, which left every number in
all three lists wrong.

This script closes that loop: build the book, render it, read the printed page
number off the page each entry actually lands on, and write those numbers back
into fm.py. Because inserting or removing a list row can itself move a page,
it repeats until the numbers stop changing.

    python3 sync_front_matter.py

Requires LibreOffice for the DOCX to PDF render. The entry titles are left
alone -- this only ever rewrites the page column.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FM_PATH = HERE / "fm.py"
MAX_PASSES = 5

LIST_NAMES = ("TOC_ENTRIES", "LOF", "LOT")


def render_pdf(work: Path) -> Path:
    """Build the book and convert it to PDF, returning the PDF path."""
    docx = work / "book.docx"
    subprocess.run(
        [sys.executable, str(HERE / "main.py"), str(docx)],
        cwd=HERE, check=True, capture_output=True, text=True,
    )
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise SystemExit(
            "LibreOffice is required to measure page numbers. Install it "
            "(libreoffice-writer) or export the PDF from Word and pass it in."
        )
    subprocess.run(
        [soffice, f"-env:UserInstallation=file://{work / 'lo'}", "--headless",
         "--convert-to", "pdf", "--outdir", str(work), str(docx)],
        check=True, capture_output=True, text=True,
    )
    pdf = work / "book.pdf"
    if not pdf.exists():
        raise SystemExit("LibreOffice did not produce a PDF.")
    return pdf


def read_pages(pdf: Path) -> list[tuple[str, list[str]]]:
    """Return (printed page number, lines) for each physical page."""
    txt = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        check=True, capture_output=True, text=True,
    ).stdout
    pages = []
    for raw in txt.split("\f"):
        lines = [re.sub(r"\s+", " ", l).strip() for l in raw.splitlines()]
        lines = [l for l in lines if l]
        pages.append((lines[-1] if lines else "", lines))
    while pages and not pages[-1][1]:
        pages.pop()          # pdftotext leaves a trailing empty chunk
    return pages


def match_pattern(list_name: str, level: int, title: str) -> tuple[str, bool]:
    """Map an entry title to the line it should be found by.

    Returns (regex, expect_roman). Matching whole lines keeps a cross-reference
    in running prose ("as Chapter 5 shows") from being taken for the heading,
    and the roman flag keeps the front-matter lists from measuring themselves.
    """
    if list_name in ("LOF", "LOT"):
        # Anchor on this entry's own label ("Figure 2", "Table 5.4"); a pattern
        # matching any caption would report the first one for every row.
        return re.escape(title.split(":")[0]) + ":", False

    chapter = re.match(r"Chapter (\d+):", title)
    if chapter:
        return rf"CHAPTER {chapter.group(1)}\s*$", False
    if level == 0 and title == "References":
        return r"REFERENCES\s*$", False
    if level == 0:
        return re.escape(title.upper()) + r"\s*$", True
    return re.escape(re.sub(r"\s+", " ", title)), False


def locate(pages, pattern: str, roman: bool) -> str | None:
    rx = re.compile(pattern)
    for printed, lines in pages:
        if bool(re.fullmatch(r"[ivxlc]+", printed)) != roman:
            continue
        if any(rx.match(line) for line in lines):
            return printed
    return None


ENTRY_RX = re.compile(r'\((\d+),\s*"((?:[^"\\]|\\.)*)",\s*"([^"]*)"\)')
PAIR_RX = re.compile(r'\("((?:[^"\\]|\\.)*)",\s*"([^"]*)"\)')


def sync_once(source: str, pages) -> tuple[str, list[str]]:
    """Rewrite every page string in fm.py; report entries that went unfound."""
    missing: list[str] = []

    def rewrite(list_name: str, block: str) -> str:
        def fix_triple(m):
            level, title = int(m.group(1)), m.group(2)
            pat, roman = match_pattern(list_name, level, title)
            found = locate(pages, pat, roman)
            if found is None:
                missing.append(f"{list_name}: {title}")
                return m.group(0)
            return f'({level}, "{title}", "{found}")'

        def fix_pair(m):
            title = m.group(1)
            pat, roman = match_pattern(list_name, 0, title)
            found = locate(pages, pat, roman)
            if found is None:
                missing.append(f"{list_name}: {title}")
                return m.group(0)
            return f'("{title}", "{found}")'

        rx, fix = (ENTRY_RX, fix_triple) if list_name == "TOC_ENTRIES" else (PAIR_RX, fix_pair)
        rows = [l for l in block.splitlines() if l.strip().startswith("(")]
        if len(rx.findall(block)) != len(rows):
            # An entry the pattern does not match would be skipped in silence
            # and keep whatever stale number it had, so refuse instead.
            raise SystemExit(
                f"{list_name}: matched {len(rx.findall(block))} of {len(rows)} "
                "entries. Reformat them onto one line each, or update the regex."
            )
        return rx.sub(fix, block)

    out = source
    for name in LIST_NAMES:
        block_rx = re.compile(rf"({name}\s*=\s*\[)(.*?)(\n\])", re.S)
        match = block_rx.search(out)
        if not match:
            raise SystemExit(f"Could not find {name} in fm.py")
        head, body, tail = match.groups()
        out = out[: match.start()] + head + rewrite(name, body) + tail + out[match.end():]
    return out, missing


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for attempt in range(1, MAX_PASSES + 1):
            pages = read_pages(render_pdf(work))
            before = FM_PATH.read_text(encoding="utf-8")
            after, missing = sync_once(before, pages)
            for entry in missing:
                print(f"  not found, left as-is: {entry}", file=sys.stderr)
            if after == before:
                print(f"Front matter is in sync ({len(pages)} pages, pass {attempt}).")
                return 1 if missing else 0
            FM_PATH.write_text(after, encoding="utf-8")
            print(f"Pass {attempt}: page numbers updated, re-measuring.")
    print(f"Page numbers still moving after {MAX_PASSES} passes.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
