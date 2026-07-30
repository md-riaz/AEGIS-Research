# -*- coding: utf-8 -*-
"""Reference list, restricted to the sources most closely related to AEGIS's technical
contribution (alphabetical, IEEE-numbered).

This list was deliberately narrowed from a broader 31-source draft review down to the
sources actually discussed in Chapter 2: systems and studies that are directly
comparable to AEGIS's architecture (NL-to-SQL, NL-to-visualization, dashboard
generation, applied conversational BI), rather than adjacent business-adoption,
governance, or evaluation-methodology literature. openai24 is cited in Chapter 3
(Methodology) rather than Chapter 2, as supporting evidence for a specific
implementation choice rather than as a comparable system.

Two entries were corrected against a filename/content mismatch found in
references/: the file named "Su, X. et al. (2026)..." and "Shailesh, G. N. et al.
(2025)..." are cited here under their genuine, verified titles/authors, confirmed
by downloading and reading the actual source PDFs.
"""

REFS = [
    ("affolter19", "K. Affolter, K. Stockinger, and A. Bernstein, \"A comparative survey of "
     "recent natural language interfaces for databases,\" The VLDB Journal, vol. 28, no. 5, "
     "pp. 793-819, 2019."),
    ("deng23", "D. Deng, A. Wu, H. Qu, and Y. Wu, \"DashBot: Insight-driven dashboard generation "
     "based on deep reinforcement learning,\" IEEE Transactions on Visualization and Computer "
     "Graphics, vol. 29, no. 1, pp. 690-700, 2023."),
    ("gao15", "T. Gao, M. Dontcheva, E. Adar, Z. Liu, and K. G. Karahalios, \"DataTone: Managing "
     "ambiguity in natural language interfaces for data visualization,\" in Proc. 28th Annual ACM "
     "Symposium on User Interface Software and Technology (UIST), 2015, pp. 489-500."),
    ("lehmann22", "C. Lehmann, D. Gehrig, S. Holdener, C. Saladin, J. P. Monteiro, and "
     "K. Stockinger, \"Building natural language interfaces for databases in practice,\" in Proc. "
     "34th Int. Conf. Scientific and Statistical Database Management (SSDBM), 2022, Art. no. 20."),
    ("li_jagadish14", "F. Li and H. V. Jagadish, \"Constructing an interactive natural language "
     "interface for relational databases,\" Proceedings of the VLDB Endowment, vol. 8, no. 1, "
     "pp. 73-84, 2014."),
    ("li_bird23", "J. Li et al., \"Can LLM already serve as a database interface? A big bench for "
     "large-scale database grounded text-to-SQLs,\" in Advances in Neural Information Processing "
     "Systems (NeurIPS), vol. 36, 2023."),
    ("liu_xu25", "M. Liu and J. Xu, \"NLI4DB: A systematic review of natural language interfaces "
     "for databases,\" arXiv:2503.02435, 2025."),
    ("narechania21", "A. Narechania, A. Srinivasan, and J. Stasko, \"nl4dv: A toolkit for "
     "generating analytic specifications for data visualization from natural language queries,\" "
     "IEEE Transactions on Visualization and Computer Graphics, vol. 27, no. 2, pp. 369-379, 2021."),
    ("openai24", "OpenAI, \"Introducing structured outputs in the API,\" OpenAI, 2024."),
    ("scholak21", "T. Scholak, N. Schucher, and D. Bahdanau, \"PICARD: Parsing incrementally for "
     "constrained auto-regressive decoding from language models,\" in Proc. 2021 Conf. Empirical "
     "Methods in Natural Language Processing (EMNLP), 2021, pp. 9895-9901."),
    ("shailesh25", "G. N. Shailesh, M. Pavithran, A. Rahul Hari Venkat, and P. Kaliappan, "
     "\"Conversational BI: Natural language interface to business dashboards,\" International "
     "Journal of Engineering Research & Technology, vol. 14, no. 12, 2025."),
    ("shalaan25", "H. S. Shalaan, T. H. A. Soliman, and A. M. Abdelaziz, \"G-SQL: A schema-aware "
     "and rule-guided approach for robust natural language to SQL translation,\" IEEE Access, "
     "vol. 13, pp. 158520-158534, 2025."),
    ("su_trisql26", "X. Su, Y. Gu, P. Wang, W. Gu, L. Qi, and J. He, \"A robust natural language "
     "text-to-SQL generation framework with dynamic strategies based on LLMs,\" Scientific "
     "Reports, vol. 16, Art. no. 7892, 2026."),
    ("valkenburgh24", "J. Valkenburgh, \"Enhancing business dashboards with explanatory analytics "
     "and AI: Exploring the use of AI and explanatory analytics to enhance business "
     "decision-making,\" M.S. thesis, Information Management, Turku School of Economics, "
     "University of Turku, Finland, 2024."),
    ("wang_rat20", "B. Wang, R. Shin, X. Liu, O. Polozov, and M. Richardson, \"RAT-SQL: "
     "Relation-aware schema encoding and linking for text-to-SQL parsers,\" in Proc. 58th Annual "
     "Meeting of the Association for Computational Linguistics (ACL), 2020, pp. 7567-7578."),
    ("yu_spider18", "T. Yu et al., \"Spider: A large-scale human-labeled dataset for complex and "
     "cross-domain semantic parsing and text-to-SQL task,\" in Proc. 2018 Conf. Empirical Methods "
     "in Natural Language Processing (EMNLP), 2018, pp. 3911-3921."),
]

_NUM = {key: i + 1 for i, (key, _) in enumerate(REFS)}


def cite(*keys):
    nums = sorted(_NUM[k] for k in keys)
    return "[" + ", ".join(str(n) for n in nums) + "]"
