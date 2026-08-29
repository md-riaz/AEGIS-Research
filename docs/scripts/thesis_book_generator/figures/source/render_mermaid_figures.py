"""Render thesis Mermaid figures to PNG.

The Mermaid ``*.mmd`` files in this folder are the figure source of truth. This
script renders them through Mermaid CLI, preferring pnpm and falling back to npm.
It prints actionable setup messages when neither runner is available or the
Mermaid CLI package cannot be executed.

Pass one or more figure numbers to render a subset::

    python render_mermaid_figures.py 04 05

One layout rule holds across every figure here, and breaking it produces a
different picture rather than an error. Mermaid ignores a subgraph's
``direction`` as soon as a node inside that subgraph has an edge crossing the
subgraph boundary, and the intended rows then collapse into a single column or
a single long row. So an edge that enters or leaves a subgraph attaches to the
*subgraph id*, never to a node inside it. Figures 01 and 03 were once written
the other way; they rendered correctly under the Mermaid release used at the
time and silently reshaped under later ones.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ITEMS = [
    ("figure-01-dsr-workflow.mmd", "mermaid-figure-01-dsr-workflow.png", 1800, 900),
    ("figure-03-architecture-pipeline.mmd", "mermaid-figure-03-architecture-pipeline.png", 1800, 1250),
    ("figure-04-semantic-layer-modularity.mmd", "mermaid-figure-04-semantic-layer-modularity.png", 1500, 1250),
    ("figure-05-vocabulary-injection.mmd", "mermaid-figure-05-vocabulary-injection.png", 1400, 1200),
    ("figure-06-pattern-taxonomy.mmd", "mermaid-figure-06-pattern-taxonomy.png", 1800, 1000),
    ("figure-07-sql-safety-defense.mmd", "mermaid-figure-07-sql-safety-defense.png", 1800, 1200),
    ("figure-08-widget-lifecycle.mmd", "mermaid-figure-08-widget-lifecycle.png", 1900, 700),
]


BROWSER_CANDIDATES = [
    "/opt/pw-browsers/chromium",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]


def _find_browser() -> str | None:
    """Locate a Chrome/Chromium binary for Mermaid CLI's headless renderer.

    The path is resolved at render time rather than committed, because a figure
    source that only renders on the one machine that has Chrome installed at a
    hardcoded path is not reproducible by anyone else.
    """
    env = os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    if env and Path(env).exists():
        return env
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def _puppeteer_config(source_dir: Path) -> Path:
    """Write a puppeteer config pointing at whichever browser this host has.

    Falls back to the committed config only when no browser can be found, so
    that the failure message comes from Mermaid CLI rather than from a silently
    wrong executable path.
    """
    browser = _find_browser()
    committed = source_dir / "puppeteer-config.json"
    if not browser:
        print(
            "No Chrome or Chromium binary was found. Install one, or set "
            "PUPPETEER_EXECUTABLE_PATH to its location.",
            file=sys.stderr,
        )
        return committed
    print(f"Using browser: {browser}")
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle as fh:
        json.dump(
            {"executablePath": browser, "args": ["--no-sandbox", "--disable-setuid-sandbox"]},
            fh,
        )
    return Path(handle.name)


def _candidate_runners() -> list[tuple[str, list[str]]]:
    home = Path.home()
    bundled_pnpm = home / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "bin" / "fallback" / "pnpm.cmd"
    runners: list[tuple[str, list[str]]] = []
    if bundled_pnpm.exists():
        runners.append(("bundled pnpm", [str(bundled_pnpm), "dlx", "@mermaid-js/mermaid-cli"]))
    pnpm = shutil.which("pnpm")
    if pnpm:
        runners.append(("pnpm", [pnpm, "dlx", "@mermaid-js/mermaid-cli"]))
    npm = shutil.which("npm")
    if npm:
        runners.append(("npm", [npm, "exec", "--yes", "@mermaid-js/mermaid-cli", "--"]))
    return runners


def _selected_items(argv: list[str]) -> list[tuple[str, str, int, int]]:
    """Filter ITEMS by the figure numbers named on the command line."""
    if not argv:
        return ITEMS
    wanted = {a.lstrip("0") or "0" for a in argv}
    chosen = [it for it in ITEMS if it[0].split("-")[1].lstrip("0") in wanted]
    if not chosen:
        known = ", ".join(it[0].split("-")[1] for it in ITEMS)
        raise SystemExit(f"No figure matched {argv}. Known figures: {known}")
    return chosen


def _render_with(
    runner_name: str,
    runner_cmd: list[str],
    source_dir: Path,
    figures_dir: Path,
    config: Path,
    items: list[tuple[str, str, int, int]],
) -> bool:
    print(f"Trying Mermaid CLI through {runner_name}...")
    for input_name, output_name, width, height in items:
        input_path = source_dir / input_name
        output_path = figures_dir / output_name
        cmd = [
            *runner_cmd,
            "-p",
            str(config),
            "-i",
            str(input_path),
            "-o",
            str(output_path),
            "-b",
            "white",
            "-w",
            str(width),
            "-H",
            str(height),
        ]
        result = subprocess.run(cmd, cwd=source_dir, text=True, capture_output=True)
        if result.returncode != 0:
            print(f"Mermaid render failed with {runner_name} while rendering {input_name}.", file=sys.stderr)
            if result.stdout.strip():
                print(result.stdout.strip(), file=sys.stderr)
            if result.stderr.strip():
                print(result.stderr.strip(), file=sys.stderr)
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    source_dir = Path(__file__).resolve().parent
    figures_dir = source_dir.parent
    config = _puppeteer_config(source_dir)
    items = _selected_items(list(argv if argv is not None else sys.argv[1:]))

    runners = _candidate_runners()
    if not runners:
        print(
            "No pnpm or npm executable was found. Install Node.js with npm, or install pnpm, "
            "then rerun this script.",
            file=sys.stderr,
        )
        return 1

    for name, cmd in runners:
        if _render_with(name, cmd, source_dir, figures_dir, config, items):
            rendered = ", ".join(it[0] for it in items)
            print(f"Rendered into {figures_dir}: {rendered}")
            return 0

    print(
        "Unable to run @mermaid-js/mermaid-cli with pnpm or npm. Check network/package access, "
        "or install it with: npm install -g @mermaid-js/mermaid-cli",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
