"""
AEGIS Coverage Analyser — detecting requests the vocabulary cannot express.

The problem this solves
-----------------------
Dynamic vocabulary injection instructs the model to emit only approved metric
and dimension identifiers.  That is what makes the safety property hold: no
identifier outside the semantic layer can ever reach the compiler.  But it also
means the model is *structurally unable* to signal "this question is outside
the vocabulary" — asked for the average shipping distance, it must still return
some approved metric, and the downstream coverage check sees a perfectly valid
identifier and lets it through.

The consequence is a system that is safe and confidently wrong at the same
time.  Validating the model's *output* cannot detect this, because the output
is always in-vocabulary by construction.  The check has to run against the
model's *input*.

How it works
------------
``CoverageAnalyser`` compares the original request text against everything the
semantic layer can account for:

  * the tokens of every metric and dimension id, label, and description,
  * the temporal vocabulary recognised by :mod:`.time_grammar`,
  * analytic scaffolding (verbs, comparatives, question words) that carries no
    domain meaning,
  * literal values the intent bound into filters, which are data rather than
    vocabulary.

Whatever content words remain are **residual concepts** — domain nouns the
request depends on that the semantic layer has no binding for.  Their presence
is direct evidence that the model was forced to substitute, and the pipeline
declines rather than answering.

This is the inverse of schema linking.  Schema-linking work (RAT-SQL, G-SQL,
TriSQL) asks "which schema elements does this question refer to?".  Here the
vocabulary is closed and curated, so the answerable question is the complement:
"which parts of this question does the vocabulary fail to explain?".
"""

from __future__ import annotations

import logging
import re
from typing import Iterable, List, Optional, Sequence, Set

from .grounding import GroundingEngine
from .models import CoverageReport, IntentObject
from .semantic_layer import BUSINESS_LOGIC_MAPPINGS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Vocabulary that carries no domain meaning
# ---------------------------------------------------------------------------

#: Function words and pronouns.
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but",
    "by", "did", "do", "does", "for", "from", "had", "has", "have", "he",
    "her", "his", "i", "if", "in", "into", "is", "it", "its", "me", "my",
    "of", "on", "or", "our", "s", "she", "so", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "those", "to", "us",
    "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "whose", "why", "with", "you", "your", "am", "any", "each",
    "every", "not", "no", "only", "other", "out", "over", "same", "some",
    "such", "up", "via", "within", "across", "using", "used", "use", "also",
    "based", "given", "including", "regarding", "about", "after", "before",
    "during", "between", "against", "under", "above", "below", "per", "both",
}

#: Analytic scaffolding — the shape of the question, not its subject matter.
_ANALYTIC_VERBS = {
    "show", "list", "display", "give", "get", "find", "identify", "chart",
    "plot", "graph", "draw", "render", "visualise", "visualize", "report",
    "summarise", "summarize", "summary", "compare", "contrast", "rank",
    "order", "sort", "break", "breakdown", "group", "segment", "filter",
    "calculate", "compute", "measure", "track", "monitor", "analyse",
    "analyze", "analysis", "provide", "return", "tell", "want", "need",
    "please", "can", "could", "would", "should", "let", "make", "see",
    "view", "look", "check", "query", "ask", "pull", "fetch", "produce",
    "build", "create", "generate", "draw", "highlight", "surface",
    # Transactional verbs.  These describe how a fact came to exist, not what
    # is being measured: "orders *placed*", "revenue *generated*", "coupons
    # *redeemed*" all reduce to the same underlying binding.
    "place", "sell", "buy", "purchase", "spend", "pay", "process", "incur",
    "sign", "register", "redeem", "apply", "acquire", "convert", "complete",
    "cancel", "refund", "return", "ship", "deliver", "receive", "record",
    "occur", "happen", "exist", "remain", "include", "involve", "contribute",
    "drive", "reach", "achieve", "add", "remove", "take", "bring", "put",
    "come", "go", "get", "have", "do", "say", "call", "name", "know",
    "differ", "differs", "vary", "varies", "range", "span", "cover",
    # Irregular past/participle forms.  The suffix stemmer in `_stems` handles
    # regular "-ed"/"-ing" inflection, but "made", "sold" and "stuck" would
    # otherwise read as unknown domain concepts and abstain on answerable
    # requests.
    "made", "sold", "bought", "paid", "sent", "spent", "took", "taken",
    "got", "gotten", "came", "went", "gone", "saw", "seen", "did", "done",
    "had", "been", "was", "were", "gave", "given", "put", "brought",
    "found", "held", "kept", "left", "meant", "met", "ran", "run", "said",
    "told", "thought", "won", "wrote", "written", "stuck", "struck",
    "chose", "chosen", "began", "begun", "broke", "broken", "fell",
    "fallen", "grew", "grown", "knew", "known", "led", "lost", "shown",
}

#: Verbs that request a state change.  This system is read-only, so a request
#: to modify data is not a coverage gap — it is a category error, and it
#: deserves to be declined on those grounds rather than because some noun in
#: the sentence happened to be unrecognised.
# "refund", "return" and "reject" are deliberately absent: in a reporting
# context they are overwhelmingly nouns or statuses ("refund rate", "returned
# items", "rejected orders"), and treating them as write verbs declined
# ordinary questions as attempts to modify data.
_WRITE_VERBS = {
    "cancel", "delete", "remove", "drop", "update", "modify", "change",
    "edit", "insert", "add", "create", "set", "reset", "void",
    "approve", "archive", "restore", "merge", "assign", "send",
    "email", "notify", "export", "import", "upload", "sync", "schedule",
    "disable", "enable", "activate", "deactivate", "close", "reopen",
}

#: Analytic nouns that describe the *shape* of a measurement rather than a
#: distinct business concept.
_ANALYTIC_NOUNS = {
    "usage", "volume", "spending", "spend", "activity", "performance",
    "level", "levels", "size", "quantity", "portion", "part", "piece",
    "unit", "units", "sales", "sale", "purchase", "purchases", "transaction",
    "transactions", "measure", "measures", "measurement", "insight",
    "insights", "overview", "picture", "status", "state", "type", "types",
    "kind", "category", "categories", "group", "groups", "segment",
    "segments", "bucket", "buckets", "side",
}

#: Modifiers that qualify an otherwise-bindable concept.  These do not make a
#: request unanswerable; they make the *definition* the user assumed differ
#: from the definition the semantic layer owns.  The correct response is to
#: surface the governed definition and let the user confirm, not to refuse.
_QUALIFIERS = {
    "net", "gross", "new", "returning", "repeat", "existing", "unique",
    "distinct", "effective", "adjusted", "margin", "margins", "blended",
    "weighted", "normalised", "normalized", "valid", "invalid", "active",
    "inactive", "successful", "failed", "abandoned", "recovered",
    "outstanding", "pending", "open", "closed", "cancelled", "canceled",
}

_QUANTIFIERS = {
    "how", "many", "much", "number", "count", "total", "sum", "amount",
    "average", "avg", "mean", "median", "percent", "percentage", "rate",
    "ratio", "share", "proportion", "value", "values", "figure", "figures",
    "highest", "lowest", "top", "bottom", "best", "worst", "most", "least",
    "greater", "less", "more", "fewer", "maximum", "minimum", "max", "min",
    "above", "below", "than", "equal", "exceeding", "exceed", "at", "least",
    "first", "last", "next", "prior", "previous", "current", "overall",
    "each", "all", "every", "versus", "vs", "against", "difference",
    "differences", "trend", "trends", "growth", "change", "changes",
    "comparison", "distribution", "breakdown", "split", "by",
    # Number words and ordinals — quantity, never subject matter.
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "fifteen", "twenty", "hundred", "thousand",
    "once", "twice", "second", "third", "fourth", "fifth", "half", "quarter",
    # Degree and framing adjectives/adverbs.
    "frequently", "frequent", "commonly", "typically", "usually", "often",
    "rarely", "significantly", "slightly", "roughly", "approximately",
    "major", "minor", "key", "main", "primary", "core", "high", "low",
    "large", "small", "big", "little", "good", "bad", "poor", "strong",
    "weak", "better", "worse", "combined", "combining", "respective",
    "individual", "separate", "specific", "general", "detailed", "brief",
    "quick", "full", "complete", "partial", "side", "snapshot", "glance",
    "saw", "seen", "seeing", "rise", "rose", "fall", "fell", "decline",
    "declined", "increase", "increased", "decrease", "decreased", "drop",
    "dropped", "grew", "grown", "gain", "gained", "loss", "lost",
    # Negation and existence.  "products never sold" is perfectly answerable
    # (quantity = 0); treating "never" as an unknown domain concept would
    # reject a supported request.
    "never", "ever", "nothing", "none", "neither", "nor", "without",
    "missing", "lacking", "absent", "empty", "zero", "excluding", "except",
    "besides", "outside", "unless", "yet", "still",
    # Rank position.  A "bestseller" is not a distinct measure — it is the top
    # of an existing one, which the ranking pattern already expresses.
    "bestseller", "bestsellers", "best-selling", "bestselling", "seller",
    "sellers", "leader", "leaders", "winner", "winners", "performer",
    "performers", "laggard", "laggards", "outlier", "outliers",
}

#: Temporal vocabulary — handled by :mod:`.time_grammar`, not by bindings.
_TEMPORAL = {
    "today", "yesterday", "tomorrow", "now", "morning", "afternoon",
    "evening", "night", "tonight", "day", "days", "daily", "week", "weeks",
    "weekly", "month", "months", "monthly", "quarter", "quarters",
    "quarterly", "year", "years", "yearly", "annual", "annually", "hour",
    "hours", "hourly", "minute", "minutes", "date", "dates", "time", "times",
    "period", "periods", "ago", "since", "until", "till", "recent",
    "recently", "past", "ytd", "mtd", "qtd", "wtd", "q1", "q2", "q3", "q4",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct",
    "nov", "dec", "weekday", "weekend", "fiscal", "calendar", "window",
    "range", "duration", "over",
}

#: Generic commercial nouns that the semantic layer models implicitly through
#: its bindings.  These are safe to treat as accounted for.
_DOMAIN_GENERIC = {
    "data", "database", "record", "records", "row", "rows", "entry",
    "entries", "item", "items", "line", "lines", "detail", "details",
    "information", "info", "result", "results", "list", "table", "chart",
    "dashboard", "widget", "metric", "metrics", "kpi", "kpis", "business",
    "company", "store", "shop", "site", "system", "platform", "account",
}


def _tokenise(text: str) -> List[str]:
    """Lower-case word tokens, normalising unicode hyphens and separators."""
    normalised = (
        str(text)
        .replace("‑", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("’", "'")
    )
    return [t for t in re.split(r"[^a-z0-9']+", normalised.lower()) if t]


def _singular(token: str) -> str:
    """Very small stemmer — enough to align 'orders' with 'order'."""
    for suffix, replacement in (("ies", "y"), ("ses", "s"), ("es", ""), ("s", "")):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)] + replacement
    return token


def _stems(token: str) -> Set[str]:
    """Candidate base forms of an inflected token.

    Without this, "generated", "processed", "redeemed" and "purchased" all read
    as unknown domain concepts and the system abstains on requests it can
    answer perfectly well.  A residual token counts as known if *any* of its
    plausible stems is known.
    """
    forms = {token, _singular(token)}
    if token.endswith("ing") and len(token) > 5:
        base = token[:-3]
        forms |= {base, base + "e", base[:-1] if len(base) > 3 else base}
    if token.endswith("ed") and len(token) > 4:
        base = token[:-2]
        forms |= {base, base + "e", base[:-1] if len(base) > 3 else base}
    if token.endswith("ied") and len(token) > 4:
        forms.add(token[:-3] + "y")
    return {f for f in forms if f}


class CoverageAnalyser:
    """Reports which parts of a request the semantic layer cannot express."""

    #: Residual tokens shorter than this are ignored as noise.
    MIN_CONCEPT_LENGTH = 3

    def __init__(self, engine: Optional[GroundingEngine] = None):
        self._engine = engine or GroundingEngine()
        self._known = self._build_known_lexicon()

    def _build_known_lexicon(self) -> Set[str]:
        """Everything the deployment can account for, as singularised tokens."""
        known: Set[str] = set()
        known |= self._engine.lexicon()
        known |= _STOPWORDS | _ANALYTIC_VERBS | _QUANTIFIERS | _TEMPORAL
        known |= _DOMAIN_GENERIC | _ANALYTIC_NOUNS
        for key, mapping in BUSINESS_LOGIC_MAPPINGS.items():
            known |= set(_tokenise(key))
            known |= set(_tokenise(str(mapping.get("field", ""))))
        return {_singular(t) for t in known}

    # -- public API --------------------------------------------------------

    def analyse(
        self,
        question: str,
        intent: Optional[IntentObject] = None,
        bindings: Optional[Sequence] = None,
    ) -> CoverageReport:
        """Identify residual concepts and ambiguous slots in a request.

        Args:
            question: The original natural-language request.  This — not the
                model's output — is the only place an out-of-vocabulary concept
                is still visible.
            intent: The extracted intent, used to treat literal filter values
                and the model's own ``unmapped_terms`` as evidence.
            bindings: Grounding results, used to record ambiguous slots.

        Returns:
            A :class:`CoverageReport`.  ``is_covered`` is true only when the
            vocabulary accounts for every domain concept in the request.
        """
        accounted = set(self._known)
        accounted |= self._value_tokens(intent)
        accounted |= self._literal_tokens(question)

        residual: List[str] = []
        qualifiers: List[str] = []
        for token in _tokenise(question):
            if token.isdigit() or len(token) < self.MIN_CONCEPT_LENGTH:
                continue
            if _stems(token) & accounted:
                continue
            if token in _QUALIFIERS or self._is_near_miss(token):
                if token not in qualifiers:
                    qualifiers.append(token)
                continue
            if token not in residual:
                residual.append(token)

        concepts = self._phrase(question, residual)

        # The model's own admission of unmapped terms is independent evidence
        # and is merged in even when our lexicon happened to cover the tokens.
        if intent is not None:
            for term in self._credible_unmapped(intent, accounted):
                if term.lower() not in {c.lower() for c in concepts}:
                    concepts.append(term)

        ambiguous = [
            b.slot for b in (bindings or [])
            if getattr(b, "resolution", None) == "ambiguous"
        ]

        warnings: List[str] = []
        if intent is not None and intent.confidence == "low":
            warnings.append("intent extraction reported low confidence")
        if intent is not None and intent.needs_clarification:
            warnings.append(
                intent.clarification_reason or "intent extraction requested clarification"
            )

        report = CoverageReport(
            unmapped_concepts=concepts,
            qualified_concepts=qualifiers,
            ambiguous_slots=ambiguous,
            warnings=warnings,
            compound_request=self._is_compound(question),
            write_request=self._is_write_request(question),
        )
        if concepts:
            logger.info("Coverage gap on %r: %s", question, concepts)
        return report

    # -- helpers -----------------------------------------------------------

    #: Coordinators that reliably introduce a *second* request rather than a
    #: second component of the same request.
    _COMPOUND_MARKERS = (
        "and also", "and then", "as well as", "along with", "plus also",
        "and additionally", "; also", ", and also",
    )

    def _is_compound(self, question: str) -> bool:
        """Whether the request asks for two distinct reports in one sentence.

        A widget has exactly one result shape. "Show the revenue trend by month
        and also rank the top 5 customers" is two widgets, and answering only
        the first half without saying so is a silent partial answer. Detecting
        it lets the pipeline offer to build both.

        The test is deliberately conservative — an explicit coordinator plus a
        second analytic verb — because ordinary requests coordinate *fields*
        ("revenue, profit, and order count") far more often than they
        coordinate *reports*.
        """
        text = " " + str(question).lower().strip() + " "
        if not any(marker in text for marker in self._COMPOUND_MARKERS):
            return False
        for marker in self._COMPOUND_MARKERS:
            index = text.find(marker)
            if index == -1:
                continue
            tail = text[index + len(marker):]
            if any(_singular(t) in _ANALYTIC_VERBS for t in _tokenise(tail)[:3]):
                return True
        return False

    def _credible_unmapped(
        self, intent: IntentObject, accounted: Set[str]
    ) -> List[str]:
        """Filter the model's self-reported unmapped terms through our lexicon.

        The model is asked to list words no approved binding accounts for, and
        it answers over-literally: "daily", "average", "past 60 days",
        "generated" are all reported, because none of them is a metric or a
        dimension. They are granularity, aggregation, a time expression and a
        verb — every one of which the pipeline handles elsewhere.

        Taking that list at face value was the single largest source of wrongly
        refused requests. It is also the original mistake in a new costume:
        treating one component's output as authoritative instead of checking it
        against what the system actually knows. The model's report is evidence,
        not a verdict, so it goes through the same test as the question's own
        tokens — a term survives only if every one of its words is unknown to
        the lexicon *and* grounds to nothing.

        Args:
            intent: The extracted intent carrying ``unmapped_terms``.
            accounted: Tokens already explained by vocabulary, values or
                literals.

        Returns:
            The subset of reported terms that represent genuine coverage gaps.
        """
        credible: List[str] = []
        for raw in intent.unmapped_terms:
            phrase = str(raw).strip()
            if not phrase:
                continue

            tokens = [t for t in _tokenise(phrase) if len(t) >= self.MIN_CONCEPT_LENGTH]
            if not tokens:
                continue

            # Any token the vocabulary, scaffolding or time grammar explains
            # makes the whole phrase explicable — "past 60 days" is temporal,
            # "average discount" is an aggregation over a bound metric.
            if any(_stems(t) & accounted for t in tokens):
                continue

            # A term that grounds to something, even imprecisely, is a
            # near-miss to clarify rather than an unknown concept to refuse.
            if any(self._is_near_miss(t) for t in tokens):
                continue

            credible.append(phrase)
        return credible

    def _is_write_request(self, question: str) -> bool:
        """Whether the request asks to change data rather than report on it.

        AEGIS cannot express a write at all — the intent schema has no field
        for one and the compiler emits only SELECT — so such a request is
        already safe.  What it is not is *explained*: without this check, a
        request like "cancel all orders stuck in pending" is declined only
        because some noun in it failed to bind, and the user is told the
        vocabulary is missing a concept rather than that the system is
        read-only.

        Detecting it explicitly turns an accidental refusal into a stated one,
        and lets the system offer the read-only report the user probably wants
        instead.

        The test requires the write verb to lead the request, so that "orders
        with a cancelled status" — a perfectly ordinary report — is not caught
        by the word "cancel".
        """
        tokens = _tokenise(question)
        if not tokens:
            return False
        # An imperative write request puts its verb first, optionally behind a
        # politeness marker.
        head = [t for t in tokens[:3] if t not in {"please", "can", "you", "could"}]
        return bool(head) and _singular(head[0]) in _WRITE_VERBS

    def _literal_tokens(self, question: str) -> Set[str]:
        """Tokens that look like data values rather than business concepts.

        "Compare sales between Electronics and Apparel" names two *category
        values*. They are capitalised mid-sentence, which is the strongest
        signal available without a named-entity model, and they belong in a
        WHERE clause rather than in the vocabulary. Treating them as unmapped
        concepts would reject a request the system can answer.
        """
        tokens: Set[str] = set()
        for sentence in re.split(r"[.!?]", str(question)):
            words = re.findall(r"[A-Za-z][\w'‑-]*", sentence)
            for position, word in enumerate(words):
                if position == 0:
                    continue  # sentence-initial capitalisation is not a signal
                if word[0].isupper():
                    tokens |= {_singular(t) for t in _tokenise(word)}
        return tokens

    def _is_near_miss(self, token: str) -> bool:
        """Whether a residual token has any plausible binding in the vocabulary.

        A token that scores against some approved object is not an *unknown*
        concept — it is an imprecise reference to a known one. Rejecting it
        outright would be wrong; the useful response is to offer the candidates
        and let the user pick. Only tokens with no candidate at all constitute
        a hard coverage gap.
        """
        for slot in ("metric", "dimension"):
            if self._engine.candidates(token, slot):
                return True
        return False

    def _value_tokens(self, intent: Optional[IntentObject]) -> Set[str]:
        """Tokens that appear as literal filter values are data, not vocabulary.

        "Compare sales between Electronics and Apparel" should not be rejected
        for the words *Electronics* and *Apparel*: they are category values the
        compiler binds as parameters, not concepts the semantic layer must
        define.
        """
        if intent is None:
            return set()
        tokens: Set[str] = set()
        for f in intent.filters:
            if f.value is not None:
                tokens |= {_singular(t) for t in _tokenise(str(f.value))}
            tokens |= {_singular(t) for t in _tokenise(str(f.field))}
        for term in (intent.metric_term, intent.dimension_term, intent.time_term):
            if term:
                tokens |= {_singular(t) for t in _tokenise(str(term))}
        return tokens

    def _phrase(self, question: str, residual: List[str]) -> List[str]:
        """Re-join adjacent residual tokens so multi-word concepts read well.

        "average page load time for the checkout page" yields the residual
        tokens ``page``, ``load``, ``checkout``; reporting "page load" and
        "checkout" is far more actionable for the user than three fragments.
        """
        if not residual:
            return []

        residual_set = set(residual)
        tokens = _tokenise(question)
        phrases: List[str] = []
        current: List[str] = []

        for token in tokens:
            if token in residual_set:
                current.append(token)
            elif current:
                phrases.append(" ".join(current))
                current = []
        if current:
            phrases.append(" ".join(current))

        seen: Set[str] = set()
        unique: List[str] = []
        for phrase in phrases:
            if phrase not in seen:
                seen.add(phrase)
                unique.append(phrase)
        return unique
