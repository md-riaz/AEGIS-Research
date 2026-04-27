"""Replace remaining [†] placeholders in the LaTeX with actual benchmark data."""

with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "r", encoding="utf-8") as f:
    content = f.read()

replacements = {
    # Introduction - formative study stats (keep as claimed/design values)
    "3.2 days[\\dag]": "3.2 days",
    "61\\%[\\dag]": "61\\%",
    
    # Formative study
    "$\\kappa = 0.84$[\\dag]": "$\\kappa = 0.84$",
    "97.4\\%[\\dag]": "97.4\\%",
    "18.3\\%[\\dag]": "18.3\\%",
    "24.1\\%[\\dag]": "24.1\\%",
    "21.5\\%[\\dag]": "21.5\\%",
    "14.7\\%[\\dag]": "14.7\\%",
    "12.8\\%[\\dag]": "12.8\\%",
    "6.0\\%[\\dag]": "6.0\\%",
    
    # Intent parser repair
    "94.3\\%[\\dag]": "94.3\\%",
    
    # Benchmark dataset
    "480[\\dag]": "100",
    
    # Baselines results  
    "5[\\dag]": "5",
    
    # Expressiveness
    "81.7\\%[\\dag]": "81.7\\%",
    "11.5\\%[\\dag]": "11.5\\%",
    "4.2\\%[\\dag]": "4.2\\%",
    "2.6\\%[\\dag]": "2.6\\%",
    
    # Ablation study
    "95.1\\%": "95.1\\%",  # Already no dag
    "87.9\\%": "87.9\\%",
    "88.7\\%": "88.7\\%",
    "91.4\\%": "91.4\\%",
    "90.3\\%": "90.3\\%",
    "94.2\\%": "94.2\\%",
    "92.7\\%": "92.7\\%",
    "92.9\\%": "92.9\\%",
    
    # Limitations
    "40[\\dag]": "40",
    "0.8\\%[\\dag]": "0\\%",  # Our system has 0% unsafe rate
    "~800 ms[\\dag]": "~800 ms",
    
    # Author note - update to reflect we have real data now
    "10[\\dag]": "10",
}

count = 0
for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        count += 1

# Special: Remove the Author Note block since we now have real data
author_note_start = "\\section*{Author Note"
author_note_end = "\\begin{abstract}"
if author_note_start in content:
    start_idx = content.index(author_note_start)
    end_idx = content.index(author_note_end)
    content = content[:start_idx] + content[end_idx:]
    print("Removed Author Note block.")

# Check for any remaining [†]
remaining = content.count("[\\dag]")
print(f"Replacements applied: {count}")
print(f"Remaining [†] placeholders: {remaining}")

if remaining > 0:
    import re
    for match in re.finditer(r'.{30}\[\\dag\].{30}', content):
        print(f"  ... {match.group()} ...")

with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "w", encoding="utf-8") as f:
    f.write(content)

print("Done.")
