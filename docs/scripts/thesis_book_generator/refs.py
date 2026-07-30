# -*- coding: utf-8 -*-
"""Consolidated, corrected reference list (alphabetical, IEEE-numbered).

During preparation of this thesis, two PDF files in references/ were found to be
filed under the wrong name: the file named "Su, X. et al. (2026)..." actually
contained Pinna et al. (2025), and the file named "Shailesh, G. N. et al. (2025)..."
actually contained Valkenburgh (2024). Both misfiled papers were genuinely relevant
and are retained here under their correct, verified titles/authors/years (pinna25,
valkenburgh24). The two originally-intended papers were then located and confirmed
online, downloaded, and added under their correct filenames (su_trisql26,
shailesh25) -- so both the originally intended citations and the two papers that
had been sitting in the folder under the wrong names are represented below. Liu &
Xu is corrected from (2026) to (2025) to match the PDF's own revision date.
"""

REFS = [
    ("affolter19", "K. Affolter, K. Stockinger, and A. Bernstein, \"A comparative survey of "
     "recent natural language interfaces for databases,\" The VLDB Journal, vol. 28, no. 5, "
     "pp. 793-819, 2019."),
    ("chinnappaiyan25", "B. Chinnappaiyan, \"Conversational analytics in self-service data "
     "platforms: Democratizing enterprise data access through natural language interfaces,\" "
     "European Journal of Computer Science and Information Technology, vol. 13, no. 46, "
     "pp. 94-102, 2025."),
    ("deng23", "D. Deng, A. Wu, H. Qu, and Y. Wu, \"DashBot: Insight-driven dashboard generation "
     "based on deep reinforcement learning,\" IEEE Transactions on Visualization and Computer "
     "Graphics, vol. 29, no. 1, pp. 690-700, 2023."),
    ("gao15", "T. Gao, M. Dontcheva, E. Adar, Z. Liu, and K. G. Karahalios, \"DataTone: Managing "
     "ambiguity in natural language interfaces for data visualization,\" in Proc. 28th Annual ACM "
     "Symposium on User Interface Software and Technology (UIST), 2015, pp. 489-500."),
    ("haikio24", "E. Häikiö, \"Adoption and governance of AI-powered dashboards in "
     "executive-level decision-making,\" M.S. thesis, Information System Science, Turku School of "
     "Economics, University of Turku, Finland, 2024."),
    ("jha25", "A. Jha, N. Anand, and H. Karthikeyan, \"Conversion of natural language text to SQL "
     "queries using generative AI,\" in Hybrid and Advanced Technologies, S. P. J. Christydass, "
     "N. Nurhayati, and S. Kannadhasan, Eds. Boca Raton, FL: CRC Press, 2025, pp. 25-32."),
    ("kavaz23", "E. Kavaz, A. Puig, and I. Rodríguez, \"Chatbot-based natural language "
     "interfaces for data visualisation: A scoping review,\" Applied Sciences, vol. 13, no. 12, "
     "p. 7025, 2023."),
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
    ("luo21", "Y. Luo, N. Tang, G. Li, J. Tang, C. Chai, and X. Qin, \"Synthesizing natural "
     "language to visualization (NL2VIS) benchmarks from NL2SQL benchmarks,\" in Proc. 2021 ACM "
     "SIGMOD Int. Conf. Management of Data, 2021, pp. 1235-1247."),
    ("mujeeb25", "M. Mujeeb, L. K. Sagar, and S. Shrestha, \"AI-powered conversational business "
     "intelligence: A natural language interface for data-driven decision making,\" International "
     "Journal of Scientific Development and Research, vol. 10, no. 11, pp. b685-b689, 2025."),
    ("narechania21", "A. Narechania, A. Srinivasan, and J. Stasko, \"nl4dv: A toolkit for "
     "generating analytic specifications for data visualization from natural language queries,\" "
     "IEEE Transactions on Visualization and Computer Graphics, vol. 27, no. 2, pp. 369-379, 2021."),
    ("openai24", "OpenAI, \"Introducing structured outputs in the API,\" OpenAI, 2024."),
    ("pinna25", "G. Pinna, Y. Perezhohin, L. Manzoni, M. Castelli, and A. De Lorenzo, \"Redefining "
     "text-to-SQL metrics by incorporating semantic and structural similarity,\" Scientific "
     "Reports, vol. 15, Art. no. 22357, 2025."),
    ("saidur25", "M. J. I. Saidur, \"AI-enhanced business intelligence dashboards for predictive "
     "market strategy in U.S. enterprises,\" International Journal of Business and Economics "
     "Insights, vol. 5, no. 3, pp. 603-648, 2025."),
    ("scholak21", "T. Scholak, N. Schucher, and D. Bahdanau, \"PICARD: Parsing incrementally for "
     "constrained auto-regressive decoding from language models,\" in Proc. 2021 Conf. Empirical "
     "Methods in Natural Language Processing (EMNLP), 2021, pp. 9895-9901."),
    ("setlur16", "V. Setlur, S. E. Battersby, M. Tory, R. Gossweiler, and A. X. Chang, \"Eviza: A "
     "natural language interface for visual analysis,\" in Proc. 29th Annual ACM Symposium on User "
     "Interface Software and Technology (UIST), 2016, pp. 365-377."),
    ("shailesh25", "G. N. Shailesh, M. Pavithran, A. Rahul Hari Venkat, and P. Kaliappan, "
     "\"Conversational BI: Natural language interface to business dashboards,\" International "
     "Journal of Engineering Research & Technology, vol. 14, no. 12, 2025."),
    ("shalaan25", "H. S. Shalaan, T. H. A. Soliman, and A. M. Abdelaziz, \"G-SQL: A schema-aware "
     "and rule-guided approach for robust natural language to SQL translation,\" IEEE Access, "
     "vol. 13, pp. 158520-158534, 2025."),
    ("shi21", "D. Shi, X. Xu, F. Sun, Y. Shi, and N. Cao, \"Calliope: Automatic visual data stories "
     "with Monte Carlo tree search,\" IEEE Transactions on Visualization and Computer Graphics, "
     "vol. 27, no. 2, pp. 464-474, 2021."),
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
    ("wang_datashot20", "Y. Wang, Z. Sun, H. Zhang, W. Cui, K. Xu, X. Ma, and D. Zhang, "
     "\"DataShot: Automatic generation of fact sheets from tabular data,\" IEEE Transactions on "
     "Visualization and Computer Graphics, vol. 26, no. 1, pp. 895-905, 2020."),
    ("wu22", "A. Wu, W. Tong, T. Dwyer, B. Lee, P. Isenberg, and H. Qu, \"MultiVision: Designing "
     "analytical dashboards with deep learning based recommendation,\" IEEE Transactions on "
     "Visualization and Computer Graphics, vol. 28, no. 1, pp. 162-172, 2022."),
    ("yu_spider18", "T. Yu et al., \"Spider: A large-scale human-labeled dataset for complex and "
     "cross-domain semantic parsing and text-to-SQL task,\" in Proc. 2018 Conf. Empirical Methods "
     "in Natural Language Processing (EMNLP), 2018, pp. 3911-3921."),
    ("yu_sparc19", "T. Yu et al., \"SParC: Cross-domain semantic parsing in context,\" in Proc. "
     "57th Annual Meeting of the Association for Computational Linguistics (ACL), 2019, "
     "pp. 4511-4523."),
    ("yu_cosql19", "T. Yu et al., \"CoSQL: A conversational text-to-SQL challenge towards "
     "cross-domain natural language interfaces to databases,\" in Proc. 2019 Conf. Empirical "
     "Methods in Natural Language Processing (EMNLP), 2019, pp. 1962-1979."),
    ("zhong18", "V. Zhong, C. Xiong, and R. Socher, \"Seq2SQL: Generating structured queries from "
     "natural language using reinforcement learning,\" arXiv:1709.00103, 2018."),
]

_NUM = {key: i + 1 for i, (key, _) in enumerate(REFS)}


def cite(*keys):
    nums = sorted(_NUM[k] for k in keys)
    return "[" + ", ".join(str(n) for n in nums) + "]"
