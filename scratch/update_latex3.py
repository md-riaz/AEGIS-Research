with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Conversational BI reference before \end{thebibliography}
conv_bi_ref = r"""\bibitem{shailesh2025convbi} Shailesh, G.~N., Pavithran, M., Venkat, R.~H.~A., \& Kaliappan, P. (2025). Conversational BI: Natural language interface to business dashboards. \emph{International Journal of Engineering Research \& Technology}, \emph{14}(12).\hfill\url{https://doi.org/10.17577/IJERTV14IS120229}
"""
old_end = r"\end{thebibliography}"
content = content.replace(old_end, conv_bi_ref + old_end)
print("Added Conversational BI reference.")

# 2. Add LEGO metaphor — find the semantic layer subsection
target = "It decouples business language from physical schema structure"
if target in content:
    insert_after = content.index(target)
    # Find the end of that sentence/paragraph  
    next_newline = content.index("\n", insert_after)
    # Find end of that paragraph (next empty line or next section)
    para_end = content.index("\n\n", next_newline)
    
    lego_para = "\n\nA useful analogy is to think in \\textbf{LEGO blocks, not free-form clay}. The semantic layer defines a finite set of composable building blocks~--- metrics (what you can measure), dimensions (how you can slice), time rules (when), join paths (relationships), and permissions (who can see what). User questions are limitless, but every answerable question is a combination of these blocks. The system does not allow unlimited raw SQL; it supports controlled combinations of trusted reporting patterns."
    
    content = content[:para_end] + lego_para + content[para_end:]
    print("Added LEGO metaphor.")
else:
    print("WARNING: Could not find semantic layer text.")

with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "w", encoding="utf-8") as f:
    f.write(content)

print("LaTeX updated successfully.")
