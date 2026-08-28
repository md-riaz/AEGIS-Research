"""
Run from repo root:  python3 docs/scripts/generate_figures.py
Requires:  pip install matplotlib numpy
Outputs all figures to assets/images/
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'images')
os.makedirs(OUT, exist_ok=True)
DPI = 200


# ── helpers ─────────────────────────────────────────────────────────────────

def box(ax, x, y, w, h, label, color, fontsize=9, textcolor='white', style='round,pad=0.1'):
    p = FancyBboxPatch((x, y), w, h, boxstyle=style,
                        facecolor=color, edgecolor='white', linewidth=1.5, zorder=3)
    ax.add_patch(p)
    ax.text(x + w/2, y + h/2, label, ha='center', va='center',
            fontsize=fontsize, color=textcolor, fontweight='bold', zorder=4)

def arrow(ax, x0, y0, x1, y1, color='#555555'):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5))

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  saved {name}')


# ── Fig 1: Architecture ──────────────────────────────────────────────────────

def fig_architecture():
    fig, ax = plt.subplots(figsize=(16, 7))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117')
    ax.set_xlim(0, 16); ax.set_ylim(0, 7); ax.axis('off')
    ax.set_title('AEGIS: 11-Stage NL→Dashboard Pipeline', color='white',
                 fontsize=14, fontweight='bold', pad=12)

    stages = [
        ('1\nNL Input',       0.3, 4.0, '#1f6feb'),
        ('2\nIntent\nClassify', 2.0, 4.0, '#1f6feb'),
        ('3\nSemantic\nLookup', 3.7, 4.0, '#8957e5'),
        ('4\nVocab\nInjection', 5.4, 4.0, '#8957e5'),
        ('5\nLLM\nCall',       7.1, 4.0, '#1f6feb'),
        ('6\nJSON\nParse',     8.8, 4.0, '#1f6feb'),
        ('7\nTemplate\nSelect',10.5, 4.0, '#8957e5'),
        ('8\nSQL\nCompile',   12.2, 4.0, '#da3633'),
        ('9\nSafety\nScan',   12.2, 2.2, '#da3633'),
        ('10\nDB\nExecute',   13.9, 4.0, '#2ea043'),
        ('11\nDashboard\nRender',13.9, 2.2,'#2ea043'),
    ]
    for label, x, y, color in stages:
        box(ax, x, y, 1.5, 1.4, label, color, fontsize=8)

    # main flow arrows
    xs = [1.8, 3.5, 5.2, 6.9, 8.6, 10.3, 12.0, 13.7]
    ys = [4.7, 4.7, 4.7, 4.7, 4.7, 4.7,  4.7,  4.7]
    for i in range(len(xs)-1):
        arrow(ax, xs[i], ys[i], xs[i+1], ys[i+1])

    # safety scan branch
    arrow(ax, 12.95, 4.0, 12.95, 3.6)
    # rejection path
    ax.annotate('', xy=(11.2, 2.9), xytext=(12.2, 2.9),
                arrowprops=dict(arrowstyle='->', color='#f85149', lw=1.5))
    box(ax, 9.5, 2.4, 1.5, 1.0, 'REJECT\nSecurityError', '#f85149', fontsize=7)

    # execute → render
    arrow(ax, 15.4, 4.7, 15.4, 3.6)
    # arrow from 10→11
    arrow(ax, 14.65, 3.6, 14.65, 4.0)

    legend_items = [
        mpatches.Patch(color='#1f6feb', label='NL / AI stages'),
        mpatches.Patch(color='#8957e5', label='Semantic layer'),
        mpatches.Patch(color='#da3633', label='Safety stages'),
        mpatches.Patch(color='#2ea043', label='Execution / output'),
        mpatches.Patch(color='#f85149', label='Rejection path'),
    ]
    ax.legend(handles=legend_items, loc='lower left', framealpha=0.3,
              labelcolor='white', fontsize=8)
    save(fig, 'fig_architecture.png')


# ── Fig 2: LEGO Modularity ───────────────────────────────────────────────────

def fig_lego_modularity():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0d1117')
    fig.suptitle('Safety-by-Design: Modular (LEGO) vs Generative (Clay)',
                 color='white', fontsize=13, fontweight='bold')

    for ax in (ax1, ax2):
        ax.set_facecolor('#161b22'); ax.axis('off')

    # LEGO side
    ax1.set_title('AEGIS: Parameterized Templates', color='#2ea043', fontsize=11, pad=8)
    blocks = [
        ('Metrics (15)',      0.1, 0.72, '#1f6feb'),
        ('Dimensions (34)',   0.1, 0.55, '#8957e5'),
        ('Time Rules',        0.1, 0.38, '#e3b341'),
        ('Join Paths (11)',   0.55,0.72, '#2ea043'),
        ('Permissions',       0.55,0.55, '#da3633'),
        ('Patterns (11)',     0.55,0.38, '#f0883e'),
    ]
    for label, x, y, color in blocks:
        p = FancyBboxPatch((x, y), 0.38, 0.14, boxstyle='round,pad=0.02',
                            facecolor=color, edgecolor='white', lw=1.5,
                            transform=ax1.transAxes, zorder=3)
        ax1.add_patch(p)
        ax1.text(x+0.19, y+0.07, label, ha='center', va='center',
                 fontsize=9, color='white', fontweight='bold', transform=ax1.transAxes)
    ax1.text(0.5, 0.22, 'User text NEVER enters SQL\nInjection structurally impossible',
             ha='center', va='center', fontsize=10, color='#2ea043',
             fontweight='bold', transform=ax1.transAxes,
             bbox=dict(boxstyle='round', facecolor='#0d2311', edgecolor='#2ea043', lw=1.5))

    # Clay side
    ax2.set_title('Direct LLM: Free-form SQL Generation', color='#f85149', fontsize=11, pad=8)
    blob = mpatches.Polygon([[0.15,0.25],[0.35,0.65],[0.5,0.8],[0.65,0.65],
                         [0.85,0.55],[0.8,0.3],[0.6,0.15],[0.3,0.1]],
                        facecolor='#6e40c9', edgecolor='#8957e5', lw=2,
                        transform=ax2.transAxes, zorder=2)
    ax2.add_patch(blob)
    ax2.text(0.5, 0.5, 'LLM generates\narbitrary SQL', ha='center', va='center',
             fontsize=10, color='white', fontweight='bold', transform=ax2.transAxes)
    risks = [('SQL Injection', 0.12, 0.82), ('Data Exfiltration', 0.72, 0.78),
             ('Privilege Escalation', 0.08, 0.18), ('DROP TABLE', 0.7, 0.2)]
    for txt, x, y in risks:
        ax2.text(x, y, f'⚠ {txt}', ha='left', va='center', fontsize=8,
                 color='#f85149', fontweight='bold', transform=ax2.transAxes)
    ax2.text(0.5, 0.06, "e.g.  SELECT * FROM users; DROP TABLE orders;--",
             ha='center', va='center', fontsize=8, color='#ff7b72',
             fontfamily='monospace', transform=ax2.transAxes,
             bbox=dict(boxstyle='round', facecolor='#2d0f0f', edgecolor='#f85149', lw=1))
    save(fig, 'fig_lego_modularity.png')


# ── Fig 3: Vocab Injection ───────────────────────────────────────────────────

def fig_vocab_injection():
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117'); ax.axis('off')
    ax.set_title('Vocabulary Injection: Semantic Layer → LLM System Prompt',
                 color='white', fontsize=13, fontweight='bold', pad=10)

    components = [
        ('Semantic\nLayer\n\n15 metrics\n34 dims\n11 joins', 0.5, 2.5, 2.2, 2.8, '#8957e5'),
        ('Prompt\nBuilder',                                   3.5, 2.5, 2.0, 2.8, '#1f6feb'),
        ('LLM\n(Llama 3.1\n8B Instant)',                     8.5, 2.5, 2.2, 2.8, '#1f6feb'),
        ('Structured\nJSON\nOutput',                         11.5, 2.5, 2.0, 2.8, '#2ea043'),
    ]
    for label, x, y, w, h, color in components:
        box(ax, x, y, w, h, label, color, fontsize=9)
        ax.set_xlim(0, 14); ax.set_ylim(0, 6)

    # Prompt box
    prompt_text = ('SYSTEM PROMPT (~1,100 tokens)\n'
                   '─────────────────────────────\n'
                   'Available metrics: revenue, orders,\n'
                   '  avg_order_value, conversion_rate ...\n'
                   'Available dimensions: date, product,\n'
                   '  category, region, customer_type ...\n'
                   'Output: {"pattern":"ranking","metric":\n'
                   '  "revenue","dimension":"product",...}')
    ax.text(5.8, 3.9, prompt_text, fontsize=7.5, color='#e6edf3',
            fontfamily='monospace', va='top',
            bbox=dict(boxstyle='round', facecolor='#161b22',
                      edgecolor='#30363d', lw=1.5))

    for x0, x1 in [(2.7, 3.5), (5.5, 8.5), (10.7, 11.5)]:
        arrow(ax, x0, 3.9, x1, 3.9)

    badges = [
        ('Zero hallucinated\ncolumn names', 0.8, 0.7, '#2ea043'),
        ('Approx. 1,100\ntoken overhead', 4.8, 0.7, '#e3b341'),
        ('96.2% valid SQL\non first attempt', 8.8, 0.7, '#1f6feb'),
    ]
    for txt, x, y, color in badges:
        box(ax, x, y, 2.8, 1.1, txt, color, fontsize=8.5)
    save(fig, 'fig_vocab_injection.png')


# ── Fig 4: Patterns ──────────────────────────────────────────────────────────

def fig_patterns():
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117'); ax.axis('off')
    ax.set_title('AEGIS: 11 Analytics Primitives', color='white',
                 fontsize=14, fontweight='bold', pad=10)
    ax.set_xlim(0, 16); ax.set_ylim(0, 9)

    # root
    box(ax, 5.5, 7.8, 5.0, 0.9, 'AEGIS Analytics Engine', '#8957e5', fontsize=11)

    patterns = [
        ('KPI',         '#1f6feb', 'metric\n[filter]',          'Scorecard'),
        ('Ranking',     '#1f6feb', 'metric, dim\n[limit,dir]',  'Bar Chart'),
        ('Trend',       '#1f6feb', 'metric, time\n[granularity]','Line Chart'),
        ('Comparison',  '#8957e5', 'metric, dims\n[period]',    'Grouped Bar'),
        ('Exception',   '#da3633', 'metric\n[threshold,dir]',   'Alert Card'),
        ('Summary',     '#2ea043', 'metrics[]\n[dims[]]',       'Data Table'),
        ('Segment',     '#2ea043', 'dim\n[metric,limit]',       'Pie / Donut'),
        ('Funnel',      '#e3b341', 'steps[]\n[metric]',         'Funnel Chart'),
        ('Cohort',      '#e3b341', 'cohort_dim\n[metric,time]', 'Heatmap'),
        ('Correlate',   '#f0883e', 'metrics[]\n[dim]',          'Scatter Plot'),
        ('Tabular',     '#f0883e', 'dims[],metrics[]\n[filter[]','Raw Table'),
    ]

    cols = 4
    for i, (name, color, slots, viz) in enumerate(patterns):
        col = i % cols
        row = i // cols
        x = 0.3 + col * 3.9
        y = 5.8 - row * 2.4
        box(ax, x, y, 3.4, 1.0, name, color, fontsize=10)
        ax.text(x + 1.7, y - 0.35, slots, ha='center', va='top',
                fontsize=7.5, color='#8b949e', fontfamily='monospace')
        ax.text(x + 1.7, y - 0.95, f'→ {viz}', ha='center', va='top',
                fontsize=7.5, color='#58a6ff', style='italic')
        # arrow from root to box
        arrow(ax, 8.0, 7.8, x + 1.7, y + 1.0, color='#30363d')
    save(fig, 'fig_patterns.png')


# ── Fig 6: Safety Layers ─────────────────────────────────────────────────────

def fig_safety_layers():
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117'); ax.axis('off')
    ax.set_title('Two-Layer SQL Safety Defence', color='white',
                 fontsize=13, fontweight='bold', pad=10)
    ax.set_xlim(0, 14); ax.set_ylim(0, 6)

    box(ax, 0.3, 2.3, 2.4, 1.4, 'User\nInput', '#1f6feb', fontsize=10)
    box(ax, 3.5, 1.5, 3.5, 3.0, 'Layer 1\nParameterized\nSQL Templates\n\nUser text → %s\nbinding only', '#8957e5', fontsize=8)
    box(ax, 8.0, 1.5, 3.5, 3.0, 'Layer 2\nSafety Scanner\n\n16 forbidden\npatterns\n(regex)', '#da3633', fontsize=8)
    box(ax, 12.0, 2.3, 1.7, 1.4, 'Execute\nSQL', '#2ea043', fontsize=10)
    box(ax, 8.5, 0.1, 2.5, 0.9, 'SecurityError\nRaised', '#f85149', fontsize=9)

    arrow(ax, 2.7, 3.0, 3.5, 3.0)
    arrow(ax, 7.0, 3.0, 8.0, 3.0)
    arrow(ax, 11.5, 3.0, 12.0, 3.0)
    ax.annotate('', xy=(9.75, 1.0), xytext=(9.75, 1.5),
                arrowprops=dict(arrowstyle='->', color='#f85149', lw=2))

    patterns_text = 'DROP|DELETE|UPDATE|INSERT\nUNION|EXEC|xp_|INTO OUTFILE\nSCHEMA|GRANT|REVOKE|TRUNCATE ...'
    ax.text(8.25, 4.7, patterns_text, fontsize=7.5, color='#ff7b72',
            fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#2d0f0f', edgecolor='#da3633', lw=1))

    ax.text(3.75, 4.7, 'SELECT {metric}\nFROM {table}\nWHERE {dim} = %s\nLIMIT %s', fontsize=7.5,
            color='#cae8ff', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#0d1a2d', edgecolor='#8957e5', lw=1))

    ax.text(3.75, 1.2, 'Injection structurally\nimpossible at Layer 1',
            fontsize=8, color='#8957e5', ha='left', style='italic')
    ax.text(8.25, 1.2, 'Catches schema probing\n& malformed patterns',
            fontsize=8, color='#da3633', ha='left', style='italic')
    save(fig, 'fig_safety_layers.png')


# ── Fig 7: Widget Lifecycle ──────────────────────────────────────────────────

def fig_widget_lifecycle():
    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#0d1117'); ax.axis('off')
    ax.set_title('Widget Lifecycle: Creation → Storage → Reuse → Refresh',
                 color='white', fontsize=13, fontweight='bold', pad=10)
    ax.set_xlim(0, 14); ax.set_ylim(0, 5)

    stages = [
        ('User\nRequest',       0.5,  1.8, '#1f6feb'),
        ('Widget\nCreation',    3.0,  1.8, '#8957e5'),
        ('SHA-256\nDedup Check',5.5,  1.8, '#e3b341'),
        ('Widget\nStorage',     8.0,  1.8, '#2ea043'),
        ('Dashboard\nGrid',    10.5,  1.8, '#2ea043'),
    ]
    for label, x, y, color in stages:
        box(ax, x, y, 2.2, 1.4, label, color)
        ax.set_xlim(0, 14); ax.set_ylim(0, 5)

    # forward arrows
    for x0, x1 in [(2.7, 3.0), (5.2, 5.5), (7.7, 8.0), (10.2, 10.5)]:
        arrow(ax, x0, 2.5, x1, 2.5)

    # reuse path
    ax.annotate('', xy=(3.55, 1.8), xytext=(6.15, 1.8),
                arrowprops=dict(arrowstyle='->', color='#e3b341', lw=1.5,
                                connectionstyle='arc3,rad=-0.4'))
    ax.text(4.85, 0.9, '61% recurring\n(cache hit)', ha='center', fontsize=8,
            color='#e3b341', style='italic')

    # refresh arc
    ax.annotate('', xy=(9.0, 3.2), xytext=(11.6, 3.2),
                arrowprops=dict(arrowstyle='<-', color='#30363d', lw=1.5,
                                connectionstyle='arc3,rad=-0.5'))
    ax.text(10.3, 4.1, 'Scheduled\nRefresh', ha='center', fontsize=8,
            color='#8b949e', style='italic')
    save(fig, 'fig_widget_lifecycle.png')


# ── Fig 8: Evaluation ────────────────────────────────────────────────────────

def fig_evaluation():
    systems = ['B1: Direct LLM', 'B2: Chain-of-Thought', 'B3: Keyword Match',
               'AEGIS (ablated)', 'AEGIS (full)']
    # Values from manuscript 100-query benchmark (Section 6.4)
    # B1: 5.0% unsafe, 99% validity, 99% coverage (manuscript Table 2)
    # AEGIS full: 0% unsafe, 100% validity, 100% coverage (manuscript Table 2)
    # AEGIS ablated: -11.3pp validity, -9pp coverage vs full (Figure 8 caption)
    unsafe_sql   = [5.0,  3.0,  1.0,  0.0,  0.0]
    exec_validity= [99.0, 97.0, 66.0, 88.7, 100.0]
    coverage     = [99.0, 97.0, 55.0, 91.0, 100.0]

    x = np.arange(len(systems))
    w = 0.26
    colors = ['#f85149', '#2ea043', '#1f6feb']

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')
    ax.set_title('Evaluation Results: 5-System Comparison (n=100 queries)',
                 color='white', fontsize=12, fontweight='bold', pad=10)

    b1 = ax.bar(x - w, unsafe_sql,    w, label='Unsafe SQL Rate (%)',    color=colors[0], edgecolor='#0d1117')
    b2 = ax.bar(x,     exec_validity, w, label='Execution Validity (%)', color=colors[1], edgecolor='#0d1117')
    b3 = ax.bar(x + w, coverage,      w, label='Coverage (%)',           color=colors[2], edgecolor='#0d1117')

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 0.5,
                        f'{h:.1f}', ha='center', va='bottom', fontsize=7,
                        color='#e6edf3')

    ax.set_xticks(x); ax.set_xticklabels(systems, color='#8b949e', fontsize=9)
    ax.set_ylabel('Percentage (%)', color='#8b949e')
    ax.set_ylim(0, 110)
    ax.tick_params(colors='#8b949e'); ax.spines[:].set_color('#30363d')
    ax.legend(facecolor='#161b22', labelcolor='#e6edf3', fontsize=9,
              edgecolor='#30363d')
    ax.axvline(x=3.5, color='#30363d', linestyle='--', lw=1)
    ax.text(3.7, 105, 'AEGIS', color='#2ea043', fontsize=9, fontweight='bold')
    save(fig, 'fig_evaluation.png')


# ── Fig 9: Ablation ──────────────────────────────────────────────────────────

def fig_ablation():
    configs = ['Full AEGIS', '- Safety\nScanner', '- Vocab\nInjection',
               '- Semantic\nLayer', '- Pattern\nTemplates', '+ Direct SQL', '+ No LLM']
    # Values from manuscript ablation table (Section 6.6)
    # Full AEGIS: 100%/100%; -vocab injection: -35.3pp validity (Figure 9 caption)
    # -semantic layer: -11.3pp validity, -9pp coverage (Figure 8 caption)
    validity = [100.0, 100.0, 64.7, 88.7, 45.0, 99.0, 12.0]
    coverage  = [100.0, 100.0, 65.0, 91.0, 43.0, 99.0,  9.0]

    x = np.arange(len(configs))
    w = 0.35

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')
    ax.set_title('Ablation Study: Component Contributions (n=100 queries)',
                 color='white', fontsize=12, fontweight='bold', pad=10)

    b1 = ax.bar(x - w/2, validity, w, label='Execution Validity (%)', color='#2ea043', edgecolor='#0d1117')
    b2 = ax.bar(x + w/2, coverage, w, label='Coverage (%)',           color='#1f6feb', edgecolor='#0d1117')

    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.5,
                    f'{h:.1f}', ha='center', va='bottom', fontsize=7.5, color='#e6edf3')

    ax.set_xticks(x); ax.set_xticklabels(configs, color='#8b949e', fontsize=8.5)
    ax.set_ylabel('Percentage (%)', color='#8b949e')
    ax.set_ylim(0, 110)
    ax.tick_params(colors='#8b949e'); ax.spines[:].set_color('#30363d')
    ax.legend(facecolor='#161b22', labelcolor='#e6edf3', fontsize=9, edgecolor='#30363d')

    # annotate the vocab injection drop
    ax.annotate('−35.3% validity\nwithout vocab injection',
                xy=(2, 61.3), xytext=(3.5, 85),
                arrowprops=dict(arrowstyle='->', color='#f85149', lw=1.5),
                color='#f85149', fontsize=8.5, fontweight='bold')
    save(fig, 'fig_ablation.png')


# ── Fig 10: Latency ──────────────────────────────────────────────────────────

def fig_latency():
    stages = ['Semantic\nMapping', 'LLM\nAPI Call', 'SQL\nCompile',
              'Query\nExecute', 'Viz\nSelector', 'Widget\nPersist']
    # Median (ms) values from manuscript Table 3 (Section 6.8)
    medians = [12, 1850, 8, 45, 2, 5]
    colors  = ['#8957e5','#1f6feb','#8957e5','#2ea043','#1f6feb','#2ea043']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6),
                                    gridspec_kw={'width_ratios': [2, 1]})
    fig.patch.set_facecolor('#0d1117')
    fig.suptitle('Pipeline Latency Breakdown (median, ms)', color='white',
                 fontsize=13, fontweight='bold')

    ax1.set_facecolor('#161b22')
    bars = ax1.bar(stages, medians, color=colors, edgecolor='#0d1117')
    ax1.set_yscale('log')
    ax1.set_ylabel('Latency (ms, log scale)', color='#8b949e')
    ax1.tick_params(colors='#8b949e'); ax1.spines[:].set_color('#30363d')
    for bar, val in zip(bars, medians):
        ax1.text(bar.get_x() + bar.get_width()/2, val * 1.3,
                 f'{val}ms', ha='center', va='bottom', fontsize=8, color='#e6edf3')
    ax1.annotate('96% of total\nrequest time',
                 xy=(2, 1850), xytext=(3.5, 800),
                 arrowprops=dict(arrowstyle='->', color='#e3b341', lw=1.5),
                 color='#e3b341', fontsize=9, fontweight='bold')

    # pie chart of time breakdown
    ax2.set_facecolor('#161b22')
    pie_labels = ['LLM API Call', 'Query Execute', 'Semantic Map', 'Other']
    pie_vals   = [1850, 45, 12, 15]
    pie_colors = ['#1f6feb', '#2ea043', '#8957e5', '#8b949e']
    wedges, texts, autotexts = ax2.pie(
        pie_vals, labels=pie_labels, colors=pie_colors,
        autopct='%1.1f%%', startangle=90,
        textprops={'color': '#8b949e', 'fontsize': 8},
        wedgeprops={'edgecolor': '#0d1117', 'linewidth': 1.5}
    )
    for at in autotexts:
        at.set_color('white'); at.set_fontsize(8)
    ax2.set_title('Time Distribution', color='white', fontsize=11)
    save(fig, 'fig_latency.png')


# ── Fig 11: Failure Analysis ─────────────────────────────────────────────────

def fig_failure_analysis():
    # Categories observed during design-time review and benchmark construction (manuscript
    # Section 6.10). No frequency has been measured for these categories yet (see the Future
    # Work item on outcome/rejection instrumentation), so this figure lists categories only,
    # with no counts, percentages, or pie charts implying a measured breakdown.
    outcomes = ['Answered directly', 'Answered after\nclarification',
                'Answered after\nsemantic layer extension', 'Could not be answered']
    rejection_reasons = ['Metric not in\nsemantic layer', 'Unregistered\ndimension',
                          'Multi-metric\naggregation', 'Causal /\nexplanatory question',
                          'Missing join\npath']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.patch.set_facecolor('#0d1117')
    fig.suptitle('Illustrative Query Outcome and Rejection Categories',
                 color='white', fontsize=13, fontweight='bold')
    fig.text(0.5, 0.92, 'Categories observed during design-time review; frequencies not yet '
             'instrumented (Section 6.10 / Future Work)', ha='center', color='#8b949e',
             fontsize=8.5, style='italic')

    for ax, items, title in ((ax1, outcomes, 'Query Outcome Categories'),
                              (ax2, rejection_reasons, 'Coverage-Boundary Rejection Categories')):
        ax.set_facecolor('#161b22')
        ypos = range(len(items))
        ax.barh(list(ypos), [1] * len(items), color='#30363d', edgecolor='#484f58', height=0.6)
        for y, label in zip(ypos, items):
            ax.text(0.03, y, label.replace('\n', ' '), va='center', ha='left',
                    color='#e6edf3', fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        ax.invert_yaxis()
        ax.set_yticks([])
        ax.set_title(title, color='white', fontsize=11)
        ax.spines[:].set_color('#30363d')
    save(fig, 'fig_failure_analysis.png')


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print(f'Generating figures -> {os.path.abspath(OUT)}')
    fig_architecture()
    fig_lego_modularity()
    fig_vocab_injection()
    fig_patterns()
    fig_safety_layers()
    fig_widget_lifecycle()
    fig_evaluation()
    fig_ablation()
    fig_latency()
    fig_failure_analysis()
    print('Done — 11 figures generated.')
