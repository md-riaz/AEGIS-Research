import re

with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "r", encoding="utf-8") as f:
    content = f.read()

# Replace the pattern template table (6 rows -> 10 rows)
old_table = r"""KPI & metric & time\_rule, filter & kpi\_card\\
Ranking & metric, dimension & time\_rule, filter, limit & bar\_chart\\
Trend & metric, time\_grain & time\_rule, filter & line\_chart\\
Comparison & metric, segment & time\_rule, filter & grouped\_bar\\
Exception & metric, threshold & dimension, time\_rule & table\\
Summary & metric[], dimension & time\_rule, filter & multi\_card\\
\bottomrule
\caption{Pattern template library}\label{tab:patterns}"""

new_table = r"""KPI (Aggregate) & metric & time\_rule, filter & kpi\_card\\
Ranking (Rank) & metric, dimension & time\_rule, filter, limit & bar\_chart\\
Trend & metric, time\_grain & time\_rule, filter & line\_chart\\
Comparison (Compare) & metric, segment & time\_rule, filter & grouped\_bar\\
Exception (Filter) & metric, threshold & dimension, time\_rule & table\\
Summary (Group) & metric[], dimension & time\_rule, filter & multi\_card\\
Segment & metric, dimension & time\_rule, filter & pie\_chart\\
Funnel & metric, stages & time\_rule, filter & funnel\_chart\\
Cohort & metric, group\_def & time\_rule, filter & grouped\_bar\\
Correlate & metric, attribute & time\_rule, filter & scatter\_plot\\
\bottomrule
\caption{Pattern template library --- ten reusable analytics primitives}\label{tab:patterns}"""

if old_table in content:
    content = content.replace(old_table, new_table)
    print("Replaced pattern table.")
else:
    print("ERROR: Could not find old pattern table.")

# Replace visualization selection rules table - add new rows
old_viz = r"""Exception & row\xe2\x80\x91level detail & Sortable table\\
Summary & 2\xe2\x80\x934 scalar measures & KPI card grid\\"""

# Let's do it by searching for the actual content
if "Summary" in content and "KPI card grid" in content:
    # Find and add new viz rows before \bottomrule in the viz table
    content = content.replace(
        "Summary & 2\u20134 scalar measures & KPI card grid\\\\\n\\bottomrule\n\\caption{Visualization selection rules}",
        "Summary & 2\u20134 scalar measures & KPI card grid\\\\\nSegment & 1 measure, categorical dimension & Pie chart\\\\\nFunnel & ordered conversion stages & Funnel chart\\\\\nCohort & 1 measure, 2+ groups & Grouped bar chart\\\\\nCorrelate & 2 measures, continuous & Scatter plot\\\\\n\\bottomrule\n\\caption{Visualization selection rules --- extended for ten primitives}"
    )
    print("Updated visualization rules table.")

# Replace intent_class enum in verbatim block  
old_intent = '"intent_class": "ranking | trend | kpi | comparison | exception | summary"'
new_intent = '"intent_class": "kpi | ranking | trend | comparison | exception | summary | segment | funnel | cohort | correlate"'
if old_intent in content:
    content = content.replace(old_intent, new_intent)
    print("Updated intent_class enum.")

# Replace "six intent classes" with "ten analytics primitives" where appropriate
content = content.replace("six reporting intent classes", "ten reusable analytics primitives")
content = content.replace("six intent classes", "ten analytics primitives")
content = content.replace("six primary intent classes", "ten primary analytics primitives")
content = content.replace("six classes cover", "ten primitives cover")
content = content.replace("(80[\\dag] per class)", "(10[\\dag] per class)")
print("Updated taxonomy references.")

with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "w", encoding="utf-8") as f:
    f.write(content)

print("LaTeX file updated successfully.")
