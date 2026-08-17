"""Render thesis Mermaid figures to PNG.

The Mermaid ``*.mmd`` files in this folder are the figure source of truth. This
script renders them through Mermaid CLI, preferring pnpm and falling back to npm.
It prints actionable setup messages when neither runner is available or the
Mermaid CLI package cannot be executed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
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


def _render_with(runner_name: str, runner_cmd: list[str], source_dir: Path, figures_dir: Path, config: Path) -> bool:
    print(f"Trying Mermaid CLI through {runner_name}...")
    for input_name, output_name, width, height in ITEMS:
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


def main() -> int:
    source_dir = Path(__file__).resolve().parent
    figures_dir = source_dir.parent
    config = source_dir / "puppeteer-config.json"

    runners = _candidate_runners()
    if not runners:
        print(
            "No pnpm or npm executable was found. Install Node.js with npm, or install pnpm, "
            "then rerun this script.",
            file=sys.stderr,
        )
        return 1

    for name, cmd in runners:
        if _render_with(name, cmd, source_dir, figures_dir, config):
            print(f"Rendered Mermaid figures into {figures_dir}")
            return 0

    print(
        "Unable to run @mermaid-js/mermaid-cli with pnpm or npm. Check network/package access, "
        "or install it with: npm install -g @mermaid-js/mermaid-cli",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
