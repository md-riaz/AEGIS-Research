from __future__ import annotations

import re
import shutil
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_MD = ROOT / "docs" / "AEGIS_Manuscript.md"
OUT_DIR = ROOT / "paper" / "jiis_submission"
FIG_DIR = ROOT / "docs" / "scripts" / "thesis_book_generator" / "figures"


FIGURES = [
    ("fig1_architecture_pipeline.png", "mermaid-figure-03-architecture-pipeline.png"),
    ("fig2_semantic_layer.png", "mermaid-figure-04-semantic-layer-modularity.png"),
    ("fig3_sql_safety.png", "mermaid-figure-07-sql-safety-defense.png"),
    ("fig4_widget_lifecycle.png", "figure-08-widget-lifecycle.png"),
]

TABLE_CAPTIONS = [
    "Comparative positioning of AEGIS against related systems.",
    "Analytical task taxonomy used by the AEGIS compiler.",
    "Evaluation corpus components.",
    "500-question live natural-language benchmark results.",
    "Fidelity against nopCommerce's own report implementations.",
    "AEGIS and a direct LLM-to-SQL baseline on the same 500 questions.",
    "Per-stage latency over the supported questions of the live benchmark.",
    "Structural comparison between direct LLM-to-SQL and AEGIS.",
]


BIB = r"""
@article{affolter2019survey,
  author = {Affolter, Katrin and Stockinger, Kurt and Bernstein, Abraham},
  title = {A comparative survey of recent natural language interfaces for databases},
  journal = {The VLDB Journal},
  year = {2019},
  volume = {28},
  pages = {793--819}
}

@article{deng2023dashbot,
  author = {Deng, Dazhen and Wu, Aoyu and Qu, Huamin and Wu, Yingcai},
  title = {DashBot: Insight-driven dashboard generation based on deep reinforcement learning},
  journal = {IEEE Transactions on Visualization and Computer Graphics},
  year = {2023},
  volume = {29},
  number = {1},
  pages = {690--700}
}

@inproceedings{gao2015datatone,
  author = {Gao, Tong and Dontcheva, Mira and Adar, Eytan and Liu, Zhicheng and Karahalios, Karrie G.},
  title = {DataTone: Managing ambiguity in natural language interfaces for data visualization},
  booktitle = {Proceedings of the 28th Annual ACM Symposium on User Interface Software and Technology},
  year = {2015},
  pages = {489--500}
}

@inproceedings{lehmann2022veezoo,
  author = {Lehmann, Claude and Gehrig, Dennis and Holdener, Stefan and Saladin, Carlo and Monteiro, Jo{\~a}o Pedro and Stockinger, Kurt},
  title = {Building natural language interfaces for databases in practice},
  booktitle = {Proceedings of the 34th International Conference on Scientific and Statistical Database Management},
  year = {2022},
  articleno = {20}
}

@article{li2014nalir,
  author = {Li, Fei and Jagadish, H. V.},
  title = {Constructing an interactive natural language interface for relational databases},
  journal = {Proceedings of the VLDB Endowment},
  year = {2014},
  volume = {8},
  number = {1},
  pages = {73--84}
}

@inproceedings{li2023bird,
  author = {Li, Jinyang and Hui, Binyuan and Qu, Ge and Yang, Jiaxi and Li, Binhua and Li, Bowen and Wang, Binyuan and Qin, Bowen and Geng, Ruiying and Huo, Nan and Zhou, Xuanhe and Ma, Chenhao and Li, Guoliang and Chang, Kevin C.-C. and Huang, Fei and Cheng, Reynold and Li, Yongbin},
  title = {Can large language models serve as a database interface? A big bench for large-scale database grounded text-to-SQLs},
  booktitle = {Advances in Neural Information Processing Systems},
  year = {2023},
  volume = {36}
}

@article{liu2026review,
  author = {Liu, Minghao and Li, Jia and Wang, Tao and Yang, Shuang and Liu, Xiaofeng},
  title = {A systematic review of natural language interfaces for databases},
  journal = {Frontiers of Computer Science},
  year = {2026},
  volume = {20},
  pages = {2011623}
}

@inproceedings{luo2021nl2vis,
  author = {Luo, Yuyu and Tang, Nan and Li, Guoliang and Tang, Jian and Chai, Chengliang and Qin, Xiaohua},
  title = {Synthesizing natural language to visualization benchmarks from NL2SQL benchmarks},
  booktitle = {Proceedings of the ACM SIGMOD International Conference on Management of Data},
  year = {2021},
  pages = {1235--1247}
}

@article{narechania2021nl4dv,
  author = {Narechania, Arpit and Srinivasan, Arjun and Stasko, John},
  title = {nl4dv: A toolkit for generating analytic specifications for data visualization from natural language queries},
  journal = {IEEE Transactions on Visualization and Computer Graphics},
  year = {2021},
  volume = {27},
  number = {2},
  pages = {369--379}
}

@misc{openai2024structured,
  author = {{OpenAI}},
  title = {Introducing structured outputs in the API},
  year = {2024}
}

@inproceedings{scholak2021picard,
  author = {Scholak, Torsten and Schucher, Nathan and Bahdanau, Dzmitry},
  title = {PICARD: Parsing incrementally for constrained auto-regressive decoding from language models},
  booktitle = {Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing},
  year = {2021},
  pages = {9895--9901}
}

@inproceedings{setlur2016eviza,
  author = {Setlur, Vidya and Battersby, Sarah E. and Tory, Melanie and Gossweiler, Rich and Chang, Angel X.},
  title = {Eviza: A natural language interface for visual analysis},
  booktitle = {Proceedings of the 29th Annual ACM Symposium on User Interface Software and Technology},
  year = {2016},
  pages = {365--377}
}

@article{shailesh2025conversational,
  author = {Shailesh, G. N. and Prateek, M. and Vishal, S. and Shivananda, P.},
  title = {Conversational BI: Natural language interface to business dashboards},
  journal = {International Journal of Engineering Research and Technology},
  year = {2025},
  volume = {14},
  number = {12}
}

@article{shalaan2025gsql,
  author = {Shalaan, H. S. and Hammad, M. and El-Attar, N. E. and Elgendy, N.},
  title = {G-SQL: A schema-aware and rule-guided approach for natural language to SQL},
  journal = {IEEE Access},
  year = {2025},
  volume = {13},
  pages = {158520--158534}
}

@article{shi2021calliope,
  author = {Shi, Danqing and Xu, Xiang and Sun, Fanjie and Shi, Yang and Cao, Nan},
  title = {Calliope: Automatic visual data story generation from a spreadsheet},
  journal = {IEEE Transactions on Visualization and Computer Graphics},
  year = {2021},
  volume = {27},
  number = {2},
  pages = {464--474}
}

@article{su2026robust,
  author = {Su, Xuan and Zhang, Yong and Wang, Xin and Li, Yu and Liu, Hui},
  title = {A robust natural language text-to-SQL generation framework},
  journal = {Scientific Reports},
  year = {2026},
  volume = {16},
  pages = {7892}
}

@inproceedings{wang2020ratsql,
  author = {Wang, Bailin and Shin, Richard and Liu, Xiaodong and Polozov, Oleksandr and Richardson, Matthew},
  title = {RAT-SQL: Relation-aware schema encoding and linking for text-to-SQL parsers},
  booktitle = {Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics},
  year = {2020},
  pages = {7567--7578}
}

@article{wang2020datashot,
  author = {Wang, Yun and Sun, Zhutian and Zhang, Haidong and Cui, Weiwei and Xu, Ke and Ma, Xiaojuan and Zhang, Dongmei},
  title = {DataShot: Automatic generation of fact sheets from tabular data},
  journal = {IEEE Transactions on Visualization and Computer Graphics},
  year = {2020},
  volume = {26},
  number = {1},
  pages = {895--905}
}

@article{wu2022multivision,
  author = {Wu, Aoyu and Wang, Yun and Zhou, Mengyu and He, Xinyi and Qu, Huamin},
  title = {MultiVision: Designing analytical dashboards with deep learning based recommendation},
  journal = {IEEE Transactions on Visualization and Computer Graphics},
  year = {2022},
  volume = {28},
  number = {1},
  pages = {162--172}
}

@inproceedings{yu2018spider,
  author = {Yu, Tao and Li, Zifan and Zhang, Zilin and Zhang, Rui and Radev, Dragomir},
  title = {Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL task},
  booktitle = {Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing},
  year = {2018},
  pages = {3911--3921}
}

@inproceedings{yu2019sparc,
  author = {Yu, Tao and Zhang, Rui and Yang, Kai and Yasunaga, Michihiro and Wang, Dongxu and Li, Zifan and Ma, James and Li, Irene and Yao, Qingning and Roman, Shanelle and Zhang, Zilin and Radev, Dragomir},
  title = {SParC: Cross-domain semantic parsing in context},
  booktitle = {Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics},
  year = {2019},
  pages = {4511--4523}
}

@inproceedings{yu2019cosql,
  author = {Yu, Tao and Zhang, Rui and Er, Heyang and Li, Suyi and Xue, Eric and Pang, Bo and Lin, Xi Victoria and Tan, Yi Chern and Shi, Tianze and Li, Zihan and Jiang, Youxuan and Yasunaga, Michihiro and Shim, Sungrok and Chen, Tao and Fabbri, Alexander R. and Li, Zifan and Chen, Luyao and Zhang, Yizhe and Dixit, Shreya and Radev, Dragomir},
  title = {CoSQL: A conversational text-to-SQL challenge towards cross-domain natural language interfaces to databases},
  booktitle = {Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing},
  year = {2019},
  pages = {1962--1979}
}

@inproceedings{zhong2018seq2sql,
  author = {Zhong, Victor and Xiong, Caiming and Socher, Richard},
  title = {Seq2SQL: Generating structured queries from natural language using reinforcement learning},
  booktitle = {Proceedings of the International Conference on Learning Representations},
  year = {2018}
}
""".strip()


CITATION_KEYS = {
    "Affolter et al., 2019": r"\citep{affolter2019survey}",
    "Liu et al., 2026": r"\citep{liu2026review}",
    "Zhong et al., 2018": r"\citep{zhong2018seq2sql}",
    "Yu et al., 2018": r"\citep{yu2018spider}",
    "Yu et al., 2019": r"\citep{yu2019sparc,yu2019cosql}",
    "Li et al., 2023": r"\citep{li2023bird}",
    "Wang et al., 2020": r"\citep{wang2020ratsql}",
    "Scholak et al., 2021": r"\citep{scholak2021picard}",
    "Shalaan et al., 2025": r"\citep{shalaan2025gsql}",
    "Su et al., 2026": r"\citep{su2026robust}",
    "Narechania et al., 2021": r"\citep{narechania2021nl4dv}",
    "Luo et al., 2021": r"\citep{luo2021nl2vis}",
    "Setlur et al., 2016": r"\citep{setlur2016eviza}",
    "Gao et al., 2015": r"\citep{gao2015datatone}",
    "Deng et al., 2023": r"\citep{deng2023dashbot}",
    "Shi et al., 2021": r"\citep{shi2021calliope}",
    "Wu et al., 2022": r"\citep{wu2022multivision}",
    "Lehmann et al., 2022": r"\citep{lehmann2022veezoo}",
    "OpenAI, 2024": r"\citep{openai2024structured}",
    "Li & Jagadish, 2014": r"\citep{li2014nalir}",
}


def latex_escape(text: str) -> str:
    placeholders: dict[str, str] = {}

    def hold(value: str) -> str:
        key = f"@@HOLD{len(placeholders)}@@"
        placeholders[key] = value
        return key

    text = re.sub(r"`([^`]+)`", lambda m: hold(r"\texttt{" + m.group(1).replace("_", r"\_") + "}"), text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: hold(r"\textbf{" + m.group(1) + "}"), text)

    for plain, cite in sorted(CITATION_KEYS.items(), key=lambda item: -len(item[0])):
        text = text.replace(f"({plain})", hold(cite))
        text = text.replace(plain, hold(cite))

    text = text.replace("\\", r"\textbackslash{}")
    for old, new in [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]:
        text = text.replace(old, new)

    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text


def strip_references(md: str) -> str:
    idx = md.find("\n## References")
    return md[:idx].strip() if idx != -1 else md.strip()


def parse_blocks(md: str) -> list[str]:
    md = strip_references(md)
    lines = md.splitlines()
    blocks: list[str] = []
    para: list[str] = []
    table: list[str] = []
    list_lines: list[str] = []
    list_kind: str | None = None

    def flush_para() -> None:
        nonlocal para
        if para:
            blocks.append(" ".join(line.strip() for line in para).strip())
            para = []

    def flush_table() -> None:
        nonlocal table
        if table:
            blocks.append("\n".join(table))
            table = []

    def flush_list() -> None:
        nonlocal list_lines, list_kind
        if list_lines:
            blocks.append("\n".join(list_lines))
            list_lines = []
            list_kind = None

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped == "---":
            flush_para()
            flush_table()
            flush_list()
            continue
        if stripped.startswith("|"):
            flush_para()
            flush_list()
            table.append(stripped)
            continue
        flush_table()
        current_list_kind = None
        if stripped.startswith("- "):
            current_list_kind = "itemize"
        elif re.match(r"\d+\.\s+", stripped):
            current_list_kind = "enumerate"
        if current_list_kind:
            flush_para()
            if list_kind and list_kind != current_list_kind:
                flush_list()
            list_kind = current_list_kind
            list_lines.append(stripped)
            continue
        flush_list()
        if stripped.startswith("#"):
            flush_para()
            blocks.append(stripped)
        elif stripped.startswith(">"):
            flush_para()
            blocks.append(stripped)
        else:
            para.append(stripped)

    flush_para()
    flush_table()
    flush_list()
    return blocks


def md_table_to_latex(block: str, table_no: int) -> str:
    rows = [line for line in block.splitlines() if line.strip().startswith("|")]
    parsed = [
        [cell.strip() for cell in row.strip().strip("|").split("|")]
        for row in rows
        if not re.match(r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", row)
    ]
    if not parsed:
        return ""
    header, data = parsed[0], parsed[1:]
    cols = len(header)
    if table_no == 1:
        return comparative_table_to_latex(header, data, table_no)
    align = "p{0.22\\textwidth}" + "".join(["p{0.12\\textwidth}" for _ in range(cols - 1)])
    if cols <= 4:
        align = "p{0.26\\textwidth}" + "".join(["p{0.20\\textwidth}" for _ in range(cols - 1)])
    caption = TABLE_CAPTIONS[table_no - 1] if table_no <= len(TABLE_CAPTIONS) else f"Table {table_no}"
    body = [
        r"\begin{table}[t]",
        r"\caption{" + caption + r"}",
        r"\label{tab:" + str(table_no) + r"}",
        r"\begin{tabular}{" + align + r"}",
        r"\toprule",
        " & ".join(latex_escape(cell) for cell in header) + r" \\",
        r"\midrule",
    ]
    for row in data:
        row = row + [""] * (cols - len(row))
        body.append(" & ".join(latex_escape(cell) for cell in row[:cols]) + r" \\")
    body.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(body)


def comparative_table_to_latex(header: list[str], data: list[list[str]], table_no: int) -> str:
    caption = TABLE_CAPTIONS[table_no - 1]

    def compact(value: str) -> str:
        replacements = {
            "NL Parsing": "NL",
            "Semantic Layer": "Sem.",
            "Safe SQL": "Safe SQL",
            "Visualization": "Viz.",
            "Widget Persistence": "Widget",
            "Structured Intent Validation": "Intent Validation",
            "Production Evaluation": "Evaluation",
            "Benchmark only": "Benchmark",
            "In-memory data": "In-memory",
            "Synthetic data": "Synthetic",
            "Position paper": "Position",
            "nopCommerce evaluation": "nopCommerce",
        }
        return replacements.get(value, value)

    body = [
        r"\begin{table}[t]",
        r"\caption{" + caption + r"}",
        r"\label{tab:" + str(table_no) + r"}",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{p{0.25\textwidth}ccccccp{0.16\textwidth}}",
        r"\toprule",
        " & ".join(latex_escape(compact(cell)) for cell in header) + r" \\",
        r"\midrule",
    ]
    for row in data:
        row = row + [""] * (len(header) - len(row))
        body.append(" & ".join(latex_escape(compact(cell)) for cell in row[: len(header)]) + r" \\")
    body.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(body)


def block_to_latex(block: str, state: dict[str, int]) -> str:
    if block.startswith("# "):
        return ""
    if block.startswith("## Abstract"):
        return ""
    if block.startswith("**Keywords:**"):
        return ""
    if block.startswith("## "):
        title = block[3:].strip()
        title = re.sub(r"^\d+\.\s*", "", title)
        return r"\section{" + latex_escape(title) + "}"
    if block.startswith("### "):
        title = block[4:].strip()
        title = re.sub(r"^\d+(\.\d+)*\s*", "", title)
        return r"\subsection{" + latex_escape(title) + "}"
    if block.startswith(">"):
        return r"\begin{quote}" + latex_escape(block[1:].strip()) + r"\end{quote}"
    if block.startswith("|"):
        state["table_no"] += 1
        return md_table_to_latex(block, state["table_no"])
    if block.startswith("- "):
        items = [line[2:].strip() for line in block.splitlines()]
        body = "\n".join(r"\item " + latex_escape(item) for item in items)
        return r"\begin{itemize}" + "\n" + body + "\n" + r"\end{itemize}"
    if re.match(r"\d+\.\s+", block):
        items = [re.sub(r"^\d+\.\s+", "", line).strip() for line in block.splitlines()]
        body = "\n".join(r"\item " + latex_escape(item) for item in items)
        return r"\begin{enumerate}" + "\n" + body + "\n" + r"\end{enumerate}"
    return latex_escape(block) + "\n"


def extract_abstract_and_keywords(md: str) -> tuple[str, str]:
    abstract_match = re.search(r"## Abstract\s+(.*?)\n\n\*\*Keywords:\*\*\s*(.*?)\n", md, re.S)
    if not abstract_match:
        raise ValueError("Could not find abstract and keywords")
    abstract = " ".join(abstract_match.group(1).split())
    keywords = abstract_match.group(2).strip()
    return abstract, keywords


def inject_figures(tex_body: str) -> str:
    architecture = r"""
\begin{figure}[!htbp]
\centering
\includegraphics[width=0.88\textwidth]{fig1_architecture_pipeline.png}
\caption{AEGIS architecture pipeline from natural-language request to reusable dashboard widget.}
\label{fig:architecture}
\end{figure}
"""
    semantic = r"""
\begin{figure}[!htbp]
\centering
\includegraphics[width=0.82\textwidth]{fig2_semantic_layer.png}
\caption{Semantic-layer modularity: Approved business concepts are composed before SQL is compiled.}
\label{fig:semantic}
\end{figure}
"""
    safety = r"""
\begin{figure}[!htbp]
\centering
\includegraphics[width=0.78\textwidth]{fig3_sql_safety.png}
\caption{Two-layer SQL safety model combining structural prevention with post-compilation validation.}
\label{fig:safety}
\end{figure}
"""
    widget = r"""
\begin{figure}[!htbp]
\centering
\includegraphics[width=0.78\textwidth]{fig4_widget_lifecycle.png}
\caption{Widget lifecycle for reusable natural-language analytics.}
\label{fig:widget}
\end{figure}
"""
    tex_body = tex_body.replace(r"\subsection{System Overview}", r"\subsection{System Overview}" + "\n" + architecture, 1)
    tex_body = tex_body.replace(r"\subsection{Semantic Layer}", semantic + "\n" + r"\subsection{Semantic Layer}", 1)
    tex_body = tex_body.replace(r"\subsection{Safe Query Compiler}", safety + "\n" + r"\subsection{Safe Query Compiler}", 1)
    tex_body = tex_body.replace(r"\subsection{Visualization and Widget Generation}", widget + "\n" + r"\subsection{Visualization and Widget Generation}", 1)
    tex_body = tex_body.replace(r"\section{Evaluation}", r"\FloatBarrier" + "\n" + r"\section{Evaluation}", 1)
    tex_body = tex_body.replace(r"\section{References}", r"\FloatBarrier" + "\n" + r"\section{References}", 1)
    return tex_body


def fix_known_citations(tex_body: str) -> str:
    return tex_body.replace(
        "DataShot \\citep{wang2020ratsql}",
        "DataShot \\citep{wang2020datashot}",
    )


def make_tex(md: str) -> str:
    abstract, keywords = extract_abstract_and_keywords(md)
    state = {"table_no": 0}
    body_parts = [block_to_latex(block, state) for block in parse_blocks(md)]
    body = "\n\n".join(part for part in body_parts if part.strip())
    body = inject_figures(body)
    body = fix_known_citations(body)
    keyword_cmds = " \\sep ".join(k.strip() for k in keywords.split(";"))
    return textwrap.dedent(
        rf"""
        \documentclass[pdflatex,sn-basic]{{sn-jnl}}

        \usepackage{{graphicx}}
        \usepackage{{booktabs}}
        \usepackage{{array}}
        \usepackage{{amsmath}}
        \usepackage{{url}}
        \usepackage{{hyperref}}
        \usepackage{{placeins}}

        \theoremstyle{{thmstyleone}}
        \newtheorem{{theorem}}{{Theorem}}

        \raggedbottom

        \begin{{document}}

        \title[AEGIS: Safe LLM-Assisted Natural-Language Analytics]{{AEGIS: A Constraint-Based Architecture for Safe LLM-Assisted Natural Language Analytics}}

        \author*[1]{{\fnm{{Md.}} \sur{{Riaz}} \href{{https://orcid.org/0009-0003-8850-4122}}{{(ORCID: 0009-0003-8850-4122)}}}}\email{{mdriaz.wd@gmail.com}}

        \affil*[1]{{\orgdiv{{Department of Computer Science and Engineering}}, \orgname{{Pundra University of Science and Technology}}, \orgaddress{{\city{{Bogura}}, \country{{Bangladesh}}}}}}

        \abstract{{{latex_escape(abstract)}}}

        \keywords{{{keyword_cmds}}}

        \maketitle

        {body}

        \bmhead{{Declarations}}

        \textbf{{Funding}} No funding was received for this work.

        \textbf{{Conflict of interest}} The author declares no conflict of interest.

        \textbf{{Data availability}} The evaluation datasets and result artifacts are included with the released research repository.

        \textbf{{Code availability}} The prototype implementation and manuscript artifacts are maintained in the accompanying repository.

        \textbf{{Author contribution}} Md. Riaz designed the architecture, implemented the prototype, constructed the evaluation datasets, ran the experiments, and wrote the manuscript.

        \bibliography{{references}}

        \end{{document}}
        """
    ).strip() + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = SOURCE_MD.read_text(encoding="utf-8")
    (OUT_DIR / "AEGIS_JIIS_Manuscript.md").write_text(md, encoding="utf-8", newline="\n")
    (OUT_DIR / "main.tex").write_text(make_tex(md), encoding="utf-8", newline="\n")
    (OUT_DIR / "references.bib").write_text(BIB + "\n", encoding="utf-8", newline="\n")

    for target, source in FIGURES:
        shutil.copyfile(FIG_DIR / source, OUT_DIR / target)

    (OUT_DIR / "README.md").write_text(
        textwrap.dedent(
            """
            # AEGIS JIIS Submission Package

            Target journal: Journal of Intelligent Information Systems (Springer).

            The journal's official submission guidance states a 25-page limit including references, tables, and figures; LaTeX is the only acceptable manuscript format; and the upload should include source files, style files, figures, bibliography files, and a compiled PDF. This folder keeps the paper-submission track independent from the Pundra University thesis-book DOCX/PDF.

            Official guidance checked: https://link.springer.com/journal/10844/submission-guidelines

            ## Files

            - `main.tex` - Springer Nature LaTeX manuscript source.
            - `references.bib` - BibTeX references for the manuscript.
            - `fig*.png` - figure assets placed beside `main.tex` for submission-system compatibility.
            - `sn-jnl.cls`, `sn-basic.bst`, `sn-apacite.bst`, `sn-mathphys-num.bst` - Springer Nature template/style files.
            - `AEGIS_JIIS_Manuscript.md` - Markdown source snapshot used to generate the LaTeX package.

            ## Build

            Use a Springer-compatible LaTeX environment, then run:

            ```powershell
            pdflatex main.tex
            bibtex main
            pdflatex main.tex
            pdflatex main.tex
            ```

            If using Overleaf, upload all files in this folder and compile `main.tex`.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    (OUT_DIR / "SUBMISSION_CHECKLIST.md").write_text(
        textwrap.dedent(
            """
            # JIIS Submission Checklist

            - Target: Journal of Intelligent Information Systems (Springer).
            - Article type: regular research article.
            - Publishing route: subscription/no-APC route, not open access.
            - Format: LaTeX source package plus compiled PDF.
            - Page limit: 25 pages including references, tables, and figures.
            - Use no subfolders in the LaTeX upload; figures and bibliography files are flat beside `main.tex`.
            - Figures are included as separate image files next to `main.tex`.
            - Springer Nature LaTeX style files are included beside the manuscript source.
            - Declarations section is included.
            - The Pundra University thesis-book files are not part of this package.

            Before submission:

            - Compile with Springer Nature LaTeX template files (`sn-jnl.cls` and the matching `.bst` files).
            - Check final compiled PDF page count.
            - Confirm author email/ORCID before uploading.
            - Confirm that all coauthor/supervisor acknowledgements required by the journal are correct.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"Built JIIS package at {OUT_DIR}")


if __name__ == "__main__":
    main()
