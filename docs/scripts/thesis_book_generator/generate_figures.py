# -*- coding: utf-8 -*-
"""Generate deterministic PNG figures for the AEGIS thesis.

The figures are intentionally simple and thesis-neutral: labeled boxes, arrows,
tables, and bar charts produced from fixed source values.
"""
from pathlib import Path
import math
import textwrap

from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(__file__).with_name("figures")
OUT_DIR.mkdir(exist_ok=True)

# Times New Roman where it exists, and Liberation Serif otherwise. The two are
# metrically compatible, so the same figure lays out identically either way.
# The pair is resolved at run time rather than hardcoded, because a figure
# source that only renders on the one machine with Windows fonts installed is
# not reproducible by anyone else.
FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\times.ttf", r"C:\Windows\Fonts\timesbd.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
    ("/Library/Fonts/Times New Roman.ttf", "/Library/Fonts/Times New Roman Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
]


def _resolve_fonts() -> tuple[str, str]:
    for regular, bold in FONT_CANDIDATES:
        if Path(regular).exists() and Path(bold).exists():
            return regular, bold
    raise SystemExit(
        "No serif font pair found. Install Liberation fonts (Debian/Ubuntu: "
        "apt-get install fonts-liberation) or add the path to FONT_CANDIDATES."
    )


FONT_REG, FONT_BOLD = _resolve_fonts()


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


W, H = 1800, 1050
BG = "white"
INK = "#1f2933"
MUTED = "#5b6770"
LINE = "#6b7280"
BLUE = "#dbeafe"
BLUE_D = "#2563eb"
GREEN = "#dcfce7"
GREEN_D = "#15803d"
RED = "#fee2e2"
RED_D = "#b91c1c"
AMBER = "#fef3c7"
AMBER_D = "#b45309"
PURPLE = "#ede9fe"
PURPLE_D = "#6d28d9"
GRAY = "#f3f4f6"


def canvas():
    return Image.new("RGB", (W, H), BG)


def save(img, name):
    img.save(OUT_DIR / name, "PNG", dpi=(300, 300))


def text_size(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(text, chars):
    return "\n".join(textwrap.wrap(text, width=chars, break_long_words=False))


def center_text(draw, xy, text, fnt, fill=INK, line_gap=8):
    x, y = xy
    lines = text.split("\n")
    heights = [text_size(draw, line, fnt)[1] for line in lines]
    total_h = sum(heights) + line_gap * (len(lines) - 1)
    cy = y - total_h / 2
    for line, h in zip(lines, heights):
        tw, _ = text_size(draw, line, fnt)
        draw.text((x - tw / 2, cy), line, font=fnt, fill=fill)
        cy += h + line_gap


def fit_label(draw, label, box_w, box_h, start_size=30, min_size=18, bold=False):
    for size in range(start_size, min_size - 1, -1):
        fnt = font(size, bold)
        chars = max(8, int(box_w / (size * 0.56)))
        wrapped = wrap_text(label, chars)
        lines = wrapped.split("\n")
        widths = [text_size(draw, line, fnt)[0] for line in lines]
        heights = [text_size(draw, line, fnt)[1] for line in lines]
        total_h = sum(heights) + 7 * (len(lines) - 1)
        if max(widths or [0]) <= box_w - 22 and total_h <= box_h - 18:
            return wrapped, fnt
    return wrap_text(label, max(8, int(box_w / (min_size * 0.56)))), font(min_size, bold)


def box(draw, x1, y1, x2, y2, label, fill=GRAY, outline=LINE, title=False, radius=16, width=3):
    draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=width)
    wrapped, fnt = fit_label(draw, label, x2 - x1, y2 - y1, start_size=32 if title else 28, bold=title)
    center_text(draw, ((x1 + x2) / 2, (y1 + y2) / 2), wrapped, fnt)


def arrow(draw, start, end, fill=LINE, width=5):
    x1, y1 = start
    x2, y2 = end
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 18
    line_end = (
        x2 - size * 0.72 * math.cos(ang),
        y2 - size * 0.72 * math.sin(ang),
    )
    draw.line((start, line_end), fill=fill, width=width)
    pts = [
        (x2, y2),
        (x2 - size * math.cos(ang - math.pi / 6), y2 - size * math.sin(ang - math.pi / 6)),
        (x2 - size * math.cos(ang + math.pi / 6), y2 - size * math.sin(ang + math.pi / 6)),
    ]
    draw.polygon(pts, fill=fill)


def title(draw, text):
    center_text(draw, (W / 2, 70), text, font(42, True))


def fig1():
    img = Image.new("RGB", (W, 900), BG)
    d = ImageDraw.Draw(img)

    card_top, card_bottom = 60, 835
    card_h = card_bottom - card_top
    gap = 55
    x = 65
    widths = [275, 275, 420, 255, 255]
    cards = []
    for w in widths:
        cards.append((x, card_top, x + w, card_bottom))
        x += w + gap

    card_specs = [
        ("1. Problem\nIdentification", BLUE_D, "#fbfdff"),
        ("2. Artifact\nDesign", "#0f3d1d", "#fcfffd"),
        ("3. Build and Evaluation\nCycles", AMBER_D, "#fffaf2"),
        ("4. Final\nEvaluation", "#3b168f", "#fdfcff"),
        ("5. Thesis\nContribution", "#0f2f9e", "#fbfdff"),
    ]
    for rect, (label, outline, fill) in zip(cards, card_specs):
        d.rounded_rectangle(rect, radius=14, fill=fill, outline=outline, width=4)
        center_text(d, ((rect[0] + rect[2]) / 2, rect[1] + 105), label, font(34, True), fill=outline, line_gap=12)

    for left, right in zip(cards[:-1], cards[1:]):
        y = (card_top + card_bottom) / 2
        arrow(d, (left[2] + 8, y), (right[0] - 1, y), fill="#404040", width=6)

    # Minimal line icons keep the figure visual without depending on external assets.
    p = cards[0]
    cx, cy = (p[0] + p[2]) / 2, 520
    d.ellipse((cx - 48, cy - 48, cx + 48, cy + 48), outline=BLUE_D, width=6)
    d.line((cx + 36, cy + 36, cx + 82, cy + 94), fill=BLUE_D, width=7)

    a = cards[1]
    cx, cy = (a[0] + a[2]) / 2, 520
    d.rounded_rectangle((cx - 58, cy - 78, cx + 58, cy + 78), radius=9, outline="#0f3d1d", width=6)
    d.line((cx + 28, cy - 78, cx + 58, cy - 48), fill="#0f3d1d", width=5)
    d.line((cx + 28, cy - 78, cx + 28, cy - 48), fill="#0f3d1d", width=5)
    d.line((cx + 28, cy - 48, cx + 58, cy - 48), fill="#0f3d1d", width=5)
    for yy in [cy - 34, cy + 2, cy + 38]:
        d.line((cx - 34, yy, cx + 24, yy), fill="#0f3d1d", width=5)

    c = cards[2]
    cycle_rects = [
        (c[0] + 58, 245, c[2] - 58, 365, "Cycle 1:\nSemantic Layer\nand Compiler"),
        (c[0] + 58, 445, c[2] - 58, 585, "Cycle 2:\nAnalytical Patterns\nand Vocabulary"),
        (c[0] + 58, 675, c[2] - 58, 795, "Cycle 3:\nWidget Persistence\nand Benchmark"),
    ]
    for rect in cycle_rects:
        box(d, rect[0], rect[1], rect[2], rect[3], rect[4], fill="white", outline=AMBER_D, radius=12, width=3)
    arrow(d, ((c[0] + c[2]) / 2, 365), ((c[0] + c[2]) / 2, 445), fill="#404040", width=5)
    arrow(d, ((c[0] + c[2]) / 2, 585), ((c[0] + c[2]) / 2, 675), fill="#404040", width=5)

    e = cards[3]
    cx, cy = (e[0] + e[2]) / 2, 520
    d.rounded_rectangle((cx - 46, cy - 64, cx + 46, cy + 78), radius=9, outline="#3b168f", width=5)
    d.rounded_rectangle((cx - 22, cy - 84, cx + 22, cy - 48), radius=8, outline="#3b168f", width=5)
    for yy in [cy - 25, cy + 15, cy + 55]:
        d.line((cx + 4, yy, cx + 36, yy), fill="#3b168f", width=5)
    for yy in [cy - 25, cy + 15, cy + 55]:
        d.line((cx - 34, yy, cx - 24, yy + 10), fill="#3b168f", width=5)
        d.line((cx - 24, yy + 10, cx - 10, yy - 10), fill="#3b168f", width=5)

    t = cards[4]
    cx, cy = (t[0] + t[2]) / 2, 525
    d.polygon([(cx - 65, cy - 22), (cx, cy - 65), (cx + 65, cy - 22), (cx, cy + 20)], outline="#0f2f9e", width=5)
    d.line((cx - 38, cy - 6, cx - 38, cy + 42, cx, cy + 72, cx + 38, cy + 42, cx + 38, cy - 6), fill="#0f2f9e", width=5)
    d.line((cx + 38, cy - 6, cx + 38, cy + 70), fill="#0f2f9e", width=5)
    d.ellipse((cx + 32, cy + 65, cx + 44, cy + 85), fill="#0f2f9e")

    save(img, "figure-01-dsr-workflow.png")


def fig3():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "AEGIS Architecture Pipeline")
    # No box repeats "AI-assisted" or "Deterministic": the footnote states which
    # single stage uses the model and that the rest are deterministic, so saying
    # it on two of the eight boxes only invited the question of what the other
    # six are.
    stages = [
        ("User\nRequest", GRAY, LINE), ("LLM Intent\nParser", BLUE, BLUE_D),
        ("Structured\nIntent\nValidator", GREEN, GREEN_D), ("Semantic\nMapper", PURPLE, PURPLE_D),
        ("Permission\nRewriter", RED, RED_D), ("Safe Query\nCompiler", RED, RED_D),
        ("Query\nExecutor", GREEN, GREEN_D), ("Visualization\nSelector", GREEN, GREEN_D), ("Widget\nEngine", GREEN, GREEN_D),
        ("Dashboard\nWidget", GRAY, LINE),
    ]
    # The seven numbered stages of Section 3.6, mapped onto the boxes. The
    # compiler and the executor are both Stage 5: compilation and read-only
    # execution are one stage, drawn as two boxes because they are separate
    # modules. The request and the widget are the pipeline's input and output,
    # not stages, so they carry no number.
    stage_numbers = [None, 1, 2, 3, 4, 5, 5, 6, 7, None]
    x0, y0, bw, bh, gap = 50, 220, 155, 138, 17
    centers = []
    num_font = font(24, bold=True)
    for i, (lab, fi, out) in enumerate(stages):
        x = x0 + i * (bw + gap)
        box(d, x, y0, x + bw, y0 + bh, lab, fi, out)
        centers.append((x + bw / 2, y0 + bh / 2))
        if i:
            arrow(d, (x - gap + 3, y0 + bh / 2), (x - 3, y0 + bh / 2))

    # One caption per stage, centred over the box or boxes it covers, so that
    # Stage 5 reads as spanning the compiler and the executor rather than as the
    # same number printed twice by mistake.
    for number in sorted({n for n in stage_numbers if n is not None}):
        owned = [i for i, n in enumerate(stage_numbers) if n == number]
        left = x0 + owned[0] * (bw + gap)
        right = x0 + owned[-1] * (bw + gap) + bw
        center_text(d, ((left + right) / 2, y0 - 26), f"Stage {number}", num_font, fill=MUTED)
    rej_y = 590
    box(d, 600, rej_y, 1200, rej_y + 150, "Structured Clarification or Rejection Message", AMBER, AMBER_D, title=True)
    arrow(d, (centers[2][0], y0 + bh), (720, rej_y), fill=AMBER_D)
    arrow(d, (centers[5][0], y0 + bh), (1080, rej_y), fill=AMBER_D)
    d.text((70, 900), "Seven stages. Only Stage 1 uses an LLM; Stages 2-7 are deterministic code. Stage 5 covers both compilation and read-only execution.", font=font(27), fill=MUTED)
    save(img, "figure-03-architecture-pipeline.png")


def fig4():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "Semantic Layer Modularity")
    d.rounded_rectangle((70, 150, 860, 910), radius=18, outline=GREEN_D, width=4, fill="#f8fff9")
    d.rounded_rectangle((940, 150, 1730, 910), radius=18, outline=RED_D, width=4, fill="#fff8f8")
    center_text(d, (465, 205), "AEGIS: Bounded Semantic Composition", font(34, True))
    center_text(d, (1335, 205), "Direct LLM-to-SQL: Unconstrained Generation", font(34, True))
    items = ["Approved\nMetrics", "Approved\nDimensions", "Filters", "Join Paths", "Patterns"]
    for i, lab in enumerate(items):
        x = 115 + i * 145
        box(d, x, 330, x + 125, 440, lab, fill=GREEN, outline=GREEN_D)
        arrow(d, (x + 62, 440), (455, 555), fill=GREEN_D)
    box(d, 300, 555, 610, 675, "Validated\nIntent Object", fill=BLUE, outline=BLUE_D, title=True)
    arrow(d, (610, 615), (685, 615), fill=GREEN_D)
    box(d, 685, 555, 835, 675, "Parameterized\nSQL Template", fill=GRAY, outline=LINE)
    box(d, 1040, 350, 1280, 500, "Natural-Language\nRequest", fill=GRAY, outline=LINE, title=True)
    arrow(d, (1280, 425), (1390, 425), fill=RED_D)
    box(d, 1390, 350, 1640, 500, "Free-form\nSQL Generation", fill=RED, outline=RED_D, title=True)
    center_text(d, (465, 790), "Control boundary:\nonly approved semantic objects compile into SQL", font(26), fill=GREEN_D)
    center_text(d, (1335, 790), "Risk boundary:\nLLM-authored SQL text executes directly", font(26), fill=RED_D)
    save(img, "figure-04-semantic-layer-modularity.png")


def fig5():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "Vocabulary Injection and Intent Validation")
    lanes = [("Semantic Layer", 140, 430), ("Prompt Builder", 610, 900), ("LLM Intent Parser", 1080, 1590)]
    for name, x1, x2 in lanes:
        d.rounded_rectangle((x1, 160, x2, 880), radius=14, fill="#f9fafb", outline="#d1d5db", width=3)
        center_text(d, ((x1 + x2) / 2, 210), name, font(34, True))
    box(d, 185, 330, 385, 500, "Approved metric\nand dimension\nlabels", fill=GREEN, outline=GREEN_D)
    arrow(d, (385, 415), (610, 415), fill=GREEN_D)
    box(d, 650, 330, 860, 500, "Constrained\ninstruction\ncontext", fill=BLUE, outline=BLUE_D)
    arrow(d, (860, 415), (1080, 415), fill=BLUE_D)
    box(d, 1130, 310, 1530, 545, "Typed IntentObject\nmetric_term\ndimension_term\nfilters\ntime_range\nintent_type", fill=AMBER, outline=AMBER_D)
    arrow(d, (1080, 590), (860, 590), fill=AMBER_D)
    center_text(d, (970, 645), "returns typed object,\nnot SQL", font(28, True), fill=AMBER_D)
    box(d, 650, 650, 1000, 800, "Validate structured intent\nplus narrow raw-text\nsafety/scope cues", fill=GREEN, outline=GREEN_D)
    d.text((170, 885), "The LLM normalizes vague wording; deterministic stages validate approved structured intent before SQL compilation.", font=font(27), fill=MUTED)
    save(img, "figure-05-vocabulary-injection.png")


def fig6():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "Taxonomy of AEGIS Analytical Patterns")
    patterns = [
        ("KPI", "Card"), ("Ranking", "Bar chart"), ("Trend", "Line chart"), ("Comparison", "Grouped bar"),
        ("Exception", "Table"), ("Summary", "Card grid"), ("Segment", "Pie chart"), ("Funnel", "Funnel chart"),
        ("Cohort", "Grouped bar"), ("Correlate", "Scatter plot"), ("Tabular", "Table"),
    ]
    cols, rows = 4, 3
    x0, y0, cw, ch = 120, 180, 390, 225
    for i, (name, out) in enumerate(patterns):
        r, c = divmod(i, cols)
        x, y = x0 + c * cw, y0 + r * ch
        box(d, x, y, x + 310, y + 150, f"{name}\nDefault: {out}", fill=BLUE if i < 4 else GRAY, outline=BLUE_D if i < 4 else LINE, title=True)
    d.text((120, 925), "Each pattern defines required slots, optional slots, and a default visualization rule.", font=font(29), fill=MUTED)
    save(img, "figure-06-pattern-taxonomy.png")


def fig7():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "Two-Layer SQL Safety Defense")
    box(d, 620, 160, 1180, 280, "Natural-Language Request\nand Typed Intent", fill=GRAY, outline=LINE, title=True)
    arrow(d, (900, 280), (900, 360), fill=LINE)
    box(d, 520, 360, 1280, 500, "Layer 1: Parameterized Query Compiler\nApproved semantic identifiers and bound values enter fixed templates", fill=BLUE, outline=BLUE_D, title=True)
    arrow(d, (900, 500), (900, 580), fill=LINE)
    box(d, 500, 570, 1300, 750, "Layer 2: Post-Compilation Safety Scanner\nRejects non-SELECT statements, forbidden operators,\nexecution commands, and system-table references", fill=AMBER, outline=AMBER_D, title=True)
    arrow(d, (800, 750), (610, 835), fill=GREEN_D)
    arrow(d, (1000, 750), (1190, 835), fill=RED_D)
    box(d, 300, 835, 760, 950, "Safe SELECT Query\nExecuted", fill=GREEN, outline=GREEN_D, title=True)
    box(d, 1040, 835, 1500, 950, "SecurityError Raised\nBefore Database Execution", fill=RED, outline=RED_D, title=True)
    save(img, "figure-07-sql-safety-defense.png")


def fig8():
    img = canvas()
    d = ImageDraw.Draw(img)
    title(d, "Widget Lifecycle and Refresh Model")
    box(d, 100, 210, 420, 340, "New Natural-Language\nQuestion", fill=GRAY, outline=LINE, title=True)
    box(d, 550, 210, 900, 340, "Full AEGIS\nPipeline Execution", fill=BLUE, outline=BLUE_D, title=True)
    box(d, 1030, 210, 1360, 340, "Analysis Plan\nHashing", fill=PURPLE, outline=PURPLE_D, title=True)
    box(d, 1010, 500, 1360, 650, "Existing Widget\nHash Found?", fill=AMBER, outline=AMBER_D, title=True)
    box(d, 350, 500, 710, 650, "Return Cached\nWidget", fill=GREEN, outline=GREEN_D, title=True)
    box(d, 760, 790, 1310, 940, "Save New Widget\nSQL, chart configuration,\naccess rule, refresh schedule", fill=GREEN, outline=GREEN_D, title=True)
    box(d, 1440, 500, 1690, 650, "Dashboard\nWidget", fill=GRAY, outline=LINE, title=True)
    arrow(d, (420, 275), (550, 275))
    arrow(d, (900, 275), (1030, 275))
    arrow(d, (1195, 340), (1195, 500))
    arrow(d, (1010, 575), (710, 575), fill=GREEN_D)
    d.text((835, 535), "Yes", font=font(28, True), fill=GREEN_D)
    arrow(d, (1195, 650), (1040, 790), fill=GREEN_D)
    d.text((1215, 695), "No", font=font(28, True), fill=GREEN_D)
    arrow(d, (1310, 865), (1515, 650), fill=GREEN_D)
    arrow(d, (1360, 575), (1440, 575), fill=LINE)
    d.arc((1450, 380, 1720, 755), start=300, end=65, fill=PURPLE_D, width=5)
    d.text((1390, 760), "Scheduled refresh:\nre-execute stored safe query\non fresh data", font=font(24), fill=PURPLE_D)
    save(img, "figure-08-widget-lifecycle.png")


def main():
    for fn in [fig1, fig3, fig4, fig5, fig6, fig7, fig8]:
        fn()
    print(f"Generated 7 figures in {OUT_DIR}")


if __name__ == "__main__":
    main()
