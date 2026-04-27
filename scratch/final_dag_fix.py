with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "r", encoding="utf-8") as f:
    content = f.read()

# Replace all remaining [\\dag] markers
old = "[\\dag]"
count = content.count(old)
content = content.replace(old, "")
print(f"Removed {count} [\\dag] markers")

# Also check for [$\\dag$] variant
old2 = "[$\\dag$]"
count2 = content.count(old2)
content = content.replace(old2, "")
print(f"Removed {count2} [$\\dag$] markers")

# Verify
remaining = content.count("dag")
print(f"Remaining 'dag' occurrences: {remaining}")

with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "w", encoding="utf-8") as f:
    f.write(content)

print("Done.")
