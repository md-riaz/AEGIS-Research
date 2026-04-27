with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "r", encoding="utf-8") as f:
    content = f.read()

# Find the bibliography section and replace with APA format
old_bib_start = r"\begin{thebibliography}{99}"
old_bib_end = r"\end{thebibliography}"

start_idx = content.index(old_bib_start)
end_idx = content.index(old_bib_end) + len(old_bib_end)

apa_bib = r"""\begin{thebibliography}{99}
\bibitem{affolter2019survey} Affolter, K., Stockinger, K., \& Bernstein, A. (2019). A comparative survey of recent natural language interfaces for databases. \emph{The VLDB Journal}, \emph{28}, 793--819. \url{https://doi.org/10.1007/s00778-019-00567-8}
\bibitem{deng2023dashbot} Deng, D., Wu, A., Qu, H., \& Wu, Y. (2023). DashBot: Insight-driven dashboard generation based on deep reinforcement learning. \emph{IEEE Transactions on Visualization and Computer Graphics}, \emph{29}(1), 690--700. \url{https://doi.org/10.1109/TVCG.2022.3209468}
\bibitem{gao2015datatone} Gao, T., Dontcheva, M., Adar, E., Liu, Z., \& Karahalios, K.~G. (2015). DataTone: Managing ambiguity in natural language interfaces for data visualization. \emph{Proceedings of the 28th Annual ACM Symposium on User Interface Software \& Technology (UIST)}, 489--500. \url{https://doi.org/10.1145/2807442.2807478}
\bibitem{lehmann2022building} Lehmann, C., Kehlbeck, R., Fekete, J.-D., \& Deussen, O. (2022). Building natural language interfaces for databases in practice. \emph{Proceedings of the 34th International Conference on Scientific and Statistical Database Management (SSDBM)}, Article~20. \url{https://doi.org/10.1145/3538712.3538744}
\bibitem{li2014nalir} Li, F., \& Jagadish, H.~V. (2014). Constructing an interactive natural language interface for relational databases. \emph{Proceedings of the VLDB Endowment}, \emph{8}(1), 73--84. \url{https://doi.org/10.14778/2735461.2735468}
\bibitem{li2023bigbench} Li, J., Hui, B., Qu, G., Yang, J., Li, B., Li, B., Wang, B., Qin, B., Geng, R., Huo, N., Zhou, X., Ma, C., Li, G., Chang, K.~C.-C., Qin, F., Cheng, R., \& Li, Y. (2023). Can large language models serve as a database interface? A big bench for large-scale database grounded text-to-SQLs. \emph{Advances in Neural Information Processing Systems (NeurIPS)}, \emph{36}.
\bibitem{liu2026systematic} Liu, M., Yang, H., Zhang, H., Zhang, Y., Wang, Y., \& Chen, Y. (2026). A systematic review of natural language interfaces for databases. \emph{Frontiers of Computer Science}, \emph{20}, 2011623. \url{https://doi.org/10.1007/s11704-025-50592-w}
\bibitem{luo2021nl2vis} Luo, Y., Tang, N., Li, G., Tang, J., Chai, C., \& Qin, X. (2021). Synthesizing natural language to visualization (NL2VIS) benchmarks from NL2SQL benchmarks. \emph{Proceedings of the 2021 International Conference on Management of Data (SIGMOD)}, 1235--1247. \url{https://doi.org/10.1145/3448016.3457259}
\bibitem{narechania2021nl4dv} Narechania, A., Srinivasan, A., \& Stasko, J. (2021). nl4dv: A toolkit for generating analytic specifications for data visualization from natural language queries. \emph{IEEE Transactions on Visualization and Computer Graphics}, \emph{27}(2), 369--379. \url{https://doi.org/10.1109/TVCG.2020.3030378}
\bibitem{openai2024structured} OpenAI. (2024). \emph{Introducing structured outputs in the API}. \url{https://openai.com/index/introducing-structured-outputs-in-the-api/}
\bibitem{postgresql} PostgreSQL Global Development Group. (2026). \emph{PostgreSQL documentation: CREATE POLICY}. \url{https://www.postgresql.org/docs/current/sql-createpolicy.html}
\bibitem{scholak2021picard} Scholak, T., Schucher, N., \& Bahdanau, D. (2021). PICARD: Parsing incrementally for constrained auto-regressive decoding from language models. \emph{Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing (EMNLP)}, 9895--9901. \url{https://doi.org/10.18653/v1/2021.emnlp-main.779}
\bibitem{setlur2016eviza} Setlur, V., Battersby, S.~E., Tory, M., Gossweiler, R., \& Chang, A.~X. (2016). Eviza: A natural language interface for visual analysis. \emph{Proceedings of the 29th Annual ACM Symposium on User Interface Software \& Technology (UIST)}, 365--377. \url{https://doi.org/10.1145/2984511.2984588}
\bibitem{shalaan2025gsql} Shalaan, H.~S., Soliman, T.~H.~A., \& AbdelAziz, A.~M. (2025). G-SQL: A schema-aware and rule-guided approach for robust natural language to SQL translation. \emph{IEEE Access}, \emph{13}, 158520--158534. \url{https://doi.org/10.1109/ACCESS.2025.3607879}
\bibitem{shailesh2025convbi} Shailesh, G.~N., Pavithran, M., Venkat, R.~H.~A., \& Kaliappan, P. (2025). Conversational BI: Natural language interface to business dashboards. \emph{International Journal of Engineering Research \& Technology}, \emph{14}(12). \url{https://doi.org/10.17577/IJERTV14IS120229}
\bibitem{su2026trisql} Su, X., Gu, Y., Wang, P., Gu, W., Qi, L., \& He, J. (2026). A robust natural language text-to-SQL generation framework with dynamic strategies based on large language models. \emph{Scientific Reports}, \emph{16}, Article~7892. \url{https://doi.org/10.1038/s41598-026-39128-9}
\bibitem{wang2020ratsql} Wang, B., Shin, R., Liu, X., Polozov, O., \& Richardson, M. (2020). RAT-SQL: Relation-aware schema encoding and linking for text-to-SQL parsers. \emph{Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics (ACL)}, 7567--7578. \url{https://doi.org/10.18653/v1/2020.acl-main.677}
\bibitem{yu2018spider} Yu, T., Zhang, R., Er, H.~Y., Li, S., Xue, E., Pang, B., \ldots\ Radev, D. (2018). Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL task. \emph{Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing (EMNLP)}, 3911--3921. \url{https://doi.org/10.18653/v1/D18-1425}
\bibitem{yu2019sparc} Yu, T., Zhang, R., Yasunaga, M., Tan, Y.~C., Lin, X.~V., Li, S., \ldots\ Xiong, C. (2019a). SParC: Cross-domain semantic parsing in context. \emph{Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics (ACL)}, 4511--4523. \url{https://doi.org/10.18653/v1/P19-1443}
\bibitem{yu2019cosql} Yu, T., Zhang, R., Er, H., Li, S., Xue, E., Pang, B., \ldots\ Radev, D. (2019b). CoSQL: A conversational text-to-SQL challenge towards cross-domain natural language interfaces to databases. \emph{Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP)}, 1962--1979. \url{https://doi.org/10.18653/v1/D19-1204}
\bibitem{zhong2018seq2sql} Zhong, V., Xiong, C., \& Socher, R. (2018). Seq2SQL: Generating structured queries from natural language using reinforcement learning. \emph{Proceedings of the International Conference on Learning Representations (ICLR)}.
\end{thebibliography}"""

content = content[:start_idx] + apa_bib + content[end_idx:]

with open(r"D:\Development\Personal\research\Full Verbatim LaTeX.tex", "w", encoding="utf-8") as f:
    f.write(content)

print("LaTeX bibliography converted to APA format successfully.")
print(f"Total references: {apa_bib.count('bibitem')}")
