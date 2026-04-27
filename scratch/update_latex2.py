with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add LEGO metaphor to semantic layer section
old_sl = "The semantic layer is the most important non\\hyp{}model artifact in SafeDash."
new_sl = """The semantic layer is the most important non\\hyp{}model artifact in SafeDash.

A useful analogy is to think in \\textbf{LEGO blocks, not free\\hyp{}form clay}. The semantic layer defines a finite set of composable building blocks~--- metrics (what you can measure), dimensions (how you can slice), time rules (when), join paths (relationships), and permissions (who can see what). User questions are limitless, but every answerable question is a combination of these blocks. The system does not allow unlimited raw SQL; it supports controlled combinations of trusted reporting patterns."""

if old_sl in content:
    content = content.replace(old_sl, new_sl)
    print("Added LEGO metaphor to LaTeX.")
else:
    print("WARNING: Could not find semantic layer paragraph. Trying alternative...")
    # Try without \hyp{}
    alt = "The semantic layer is the most important non"
    if alt in content:
        idx = content.index(alt)
        line_end = content.index("\n", idx)
        print(f"Found at {idx}, line: {content[idx:line_end][:80]}...")

# 2. Add Conversational BI reference
old_ref = "\\bibitem{postgresql2026}"
new_ref = """\\bibitem{postgresql2026}
PostgreSQL Global Development Group, ``PostgreSQL Documentation: CREATE POLICY,'' 2026.

\\bibitem{shailesh2025}
G.~N. Shailesh, M.~Pavithran, R.~H.~A.~Venkat, and P.~Kaliappan, ``Conversational BI: Natural Language Interface to Business Dashboards,'' \\textit{International Journal of Engineering Research \\& Technology}, vol.~14, no.~12, 2025. \\doi{10.17577/IJERTV14IS120229}"""

if old_ref in content:
    content = content.replace(old_ref, new_ref)
    print("Added Conversational BI reference to LaTeX.")
else:
    # Just append before \end{thebibliography}
    if "\\end{thebibliography}" in content:
        content = content.replace(
            "\\end{thebibliography}",
            "\n\\bibitem{shailesh2025}\nG.~N. Shailesh, M.~Pavithran, R.~H.~A.~Venkat, and P.~Kaliappan, ``Conversational BI: Natural Language Interface to Business Dashboards,'' \\textit{International Journal of Engineering Research \\& Technology}, vol.~14, no.~12, 2025.\n\n\\end{thebibliography}"
        )
        print("Appended Conversational BI reference before \\end{thebibliography}.")
    else:
        print("WARNING: Could not find bibliography section.")

with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "w", encoding="utf-8") as f:
    f.write(content)

print("LaTeX updated.")
