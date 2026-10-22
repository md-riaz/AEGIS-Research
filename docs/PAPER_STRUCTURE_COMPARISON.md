# Paper structure comparison: AEGIS vs. reference papers

Purpose: show, with evidence from the papers in `references/`, that the AEGIS
manuscript (`docs/AEGIS_Manuscript.md`, compiled to `paper/jiis_submission/`)
follows the same section conventions as published work in the same field. This
is supporting material for the thesis defense — it answers "why is this section
here, and is this how other papers do it?"

Papers compared (all present in `references/`):

- **NaLIR** — Li, F. & Jagadish, H. V. (2014). *Constructing an interactive
  natural language interface for relational databases.* (NLIDB foundation.)
- **G-SQL** — Shalaan, H. S. et al. (2025). *A schema-aware and rule-guided
  approach for robust NL-to-SQL translation.* (Recent LLM text-to-SQL.)
- **TriSQL** — Su, X. et al. (2026). *A robust natural language text-to-SQL
  generation framework with dynamic strategies based on large language models.*
  (Recent LLM text-to-SQL, Scientific Reports.)

---

## 1. Related Work

| Aspect | NaLIR (2014) | G-SQL (2025) | TriSQL (2026) | AEGIS (this work) |
|---|---|---|---|---|
| Form | One "8. Related Work" section | Thematic subsections | Thematic subsections | Thematic subsections (Sec. 2.1–2.6) |
| Grouping basis | Chronology + method | Method family: `A. Rule-based`, `C. LLM-based` | Research line: *Context-aware…*, *Structure-aware…* | Research line: NLIDB, text-to-SQL, NL-viz, dashboards, semantic layers |
| Gap statement per group | Yes | Yes | Yes — e.g. "*Despite these advances, structure-aware methods still face important limitations…*" | Yes — each subsection ends "…but they do not address X, which AEGIS targets" |
| Comparison / positioning table | No | — | — | Yes (Table 1) |

**Reading.** AEGIS groups related work by research line and closes each
subsection with the gap it leaves, then positions itself in a capability table.
This is the same shape G-SQL and TriSQL use. TriSQL's "limitation sentence at
the end of each theme" and AEGIS's "gap sentence at the end of each subsection"
are directly parallel. The comparison table (Table 1) is an addition that makes
the positioning explicit; it is standard in survey and systems papers
(cf. Affolter et al., 2019).

Verbatim evidence from the extracted text of the reference PDFs:

- G-SQL, Section II (Related Work) subsection headings: `A. RULE-BASED
  APPROACH`, `C. LLM-BASED APPROACHES`.
- TriSQL, "Related work" subsection headings: *Context-aware Text2SQL
  generation methods*, *Structure-aware Text2SQL generation methods*; each
  ends with a limitation/gap statement before the next.
- NaLIR: a single "8. RELATED WORK" section.

---

## 2. Evaluation (structure)

| Aspect | G-SQL (2025) | TriSQL (2026) | AEGIS (this work) |
|---|---|---|---|
| Setup described | Yes | Yes (datasets, domain) | Yes (Sec. 6.1–6.2: scope, schema, seeded DB) |
| Metrics defined | Execution accuracy | **Formal definitions** of EM / EX (equations) | Defined in the Metrics paragraph of Sec. 6 (parser success, answer rate, execution validity, boundary rejection, result-set match) |
| Benchmarks | IMDB / Yelp / MAS | Spider + variants + custom PowerSQL | 500-question nopCommerce set + nopCommerce's own 20 admin reports |
| Baseline comparison | vs. prior systems | vs. T5-3B, RASAT+PICARD, … | vs. direct LLM-to-SQL (same model, no semantic layer) |
| Oracle for correctness | Reference SQL | Reference SQL / effect check | **nopCommerce's own report code** (differential oracle) |
| Error / limitation analysis | Yes | Yes (broader operations) | Yes (Sec. 6.8 interpretation, Sec. 8 limitations) |

**Reading.** AEGIS's evaluation is organized the same way as these papers
(setup → metrics → benchmark results → baseline → analysis). Two points of
difference are deliberate design, defended in the manuscript, not gaps:

- AEGIS does **not** use Spider/BIRD. It is not a cross-domain text-to-SQL
  engine; it answers questions declared in a semantic layer. Sections 3.2 and
  6.8 state why a cross-domain benchmark would measure a property AEGIS does
  not claim. (TriSQL makes the same move: it adds its own domain benchmark,
  PowerSQL, for its deployment scenario.)
- AEGIS evaluates on one schema (nopCommerce); this is stated as a limitation
  in Section 8.

Where AEGIS is **stronger** than the typical text-to-SQL evaluation: it checks
returned result sets against the platform's own shipped report code (a
differential oracle), not only whether SQL compiles or matches a reference
string; and it reports boundary-rejection behavior alongside the answer rate
that bounds it, rather than an unqualified accuracy headline.

---

_Generated as defense supporting material. Evidence taken from the PDFs in
`references/` via text extraction; section labels are quoted from those papers._
