"""
AEGIS Grounding Engine — evidence-based term resolution with alternatives.

Why this replaces the previous resolver
---------------------------------------
The original ``SemanticMapper._resolve_id`` walked four tiers and returned the
first hit::

    for obj in objects:
        if obj.id.lower() in term_clean or term_clean in obj.id.lower():
            return obj.id
    for obj in objects:
        if term_clean in obj.description.lower():
            return obj.id

Three properties made this unsafe as the core of a governed analytics system:

1. **Order dependence.**  The winner is whichever object happens to appear
   first in ``METRICS``/``DIMENSIONS``, not the best match.  Reordering the
   semantic layer silently changes query results.
2. **No notion of margin.**  A term matching two objects equally well is
   indistinguishable from a term matching one object perfectly.
3. **No provenance.**  Callers received a bare string, so nothing downstream
   could explain, audit, or question the binding.

This module produces a ranked candidate list with a score, a match kind, and a
human-readable evidence string for each candidate, then applies an explicit
acceptance rule (absolute floor *and* margin over the runner-up).  The result
is one of RESOLVED / AMBIGUOUS / UNSUPPORTED — never a silent substitution.

The design follows the schema-linking-as-a-separate-stage principle used by
RAT-SQL, G-SQL and TriSQL, and the ranked-alternatives model used by NaLIR's
interactive communicator and DataTone's ambiguity space.  The difference here
is that the candidate set is drawn from a curated business vocabulary rather
than raw schema columns, so the alternatives are meaningful to a business user.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Sequence

from .models import Binding, GroundingCandidate, MatchKind, Resolution
from .semantic_layer import DIMENSIONS, METRICS, SYNONYMS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Acceptance policy
# ---------------------------------------------------------------------------

#: A candidate must reach this score before it can be accepted at all.
ACCEPT_FLOOR = 0.62

#: The winner must beat the runner-up by this margin, otherwise the slot is
#: reported AMBIGUOUS and the user is asked which one they meant.
ACCEPT_MARGIN = 0.12

#: Candidates below this score are not worth showing as alternatives.
CANDIDATE_FLOOR = 0.34

#: How many alternatives to retain.  NaLIR surfaced its top 5 mappings and
#: found users could reliably pick the right one from that many.
MAX_CANDIDATES = 5

#: Tokens that carry no discriminating power inside a metric/dimension phrase.
_NOISE_TOKENS = {
    "the", "a", "an", "of", "for", "by", "in", "on", "at", "to", "and", "or",
    "total", "number", "count", "amount", "value", "sum", "all", "per",
    "each", "our", "my", "their", "its", "data", "report", "metric",
}


def _tokenise(text: str) -> List[str]:
    """Split into lower-case alphanumeric tokens, dropping noise words."""
    raw = re.split(r"[^a-z0-9]+", text.lower())
    return [t for t in raw if t and t not in _NOISE_TOKENS]


def _token_set(text: str) -> set:
    return set(_tokenise(text))


def _sequence_ratio(a: str, b: str) -> float:
    """Character-level similarity, used only to break near-ties."""
    return SequenceMatcher(None, a, b).ratio()


#: Recognises an explicit alias clause inside a semantic-layer description,
#: e.g. "Sum of order totals, also called sales or turnover".
_ALIAS_CLAUSE = re.compile(
    r"\b(?:also (?:called|known as)|a\.k\.a\.?|aka)\s+(?P<aliases>[^.;]+)",
    re.IGNORECASE,
)


def _declared_aliases(description: str) -> set:
    """Extract administrator-declared aliases from a description.

    A business vocabulary needs synonyms — users say "sales", the semantic
    layer defines "revenue" — but the thesis argues against a *separate*
    synonym dictionary, because a second registry is a second thing to keep in
    sync with the schema and a second place for an unreviewed term to appear.

    Declaring aliases inside the object's own description keeps them in one
    administrator-controlled artifact, inside the existing trust boundary, and
    visible to the prompt (the descriptions are already injected). The
    convention is a trailing "also called X, Y or Z" clause.

    This is deliberately distinct from incidental description word-overlap,
    which stays capped below the acceptance floor: an alias an administrator
    wrote on purpose is strong evidence, a word that merely appears in prose is
    not.

    Args:
        description: The semantic object's description text.

    Returns:
        The set of declared alias phrases, lower-cased.
    """
    match = _ALIAS_CLAUSE.search(description or "")
    if not match:
        return set()

    clause = match.group("aliases")
    aliases = set()
    for part in re.split(r",| or | and ", clause):
        phrase = part.strip().lower()
        if phrase:
            aliases.add(phrase)
    return aliases


class GroundingEngine:
    """Resolves natural-language terms to semantic-layer objects with evidence.

    The engine is deterministic and dependency-free: given the same semantic
    layer and the same term it always produces the same ranked list, which is
    what allows a compiled widget to be reproducible and auditable.
    """

    def __init__(
        self,
        metrics: Sequence = METRICS,
        dimensions: Sequence = DIMENSIONS,
        synonyms: Optional[Dict[str, str]] = None,
    ):
        self._objects = {"metric": list(metrics), "dimension": list(dimensions)}
        self._synonyms = dict(synonyms if synonyms is not None else SYNONYMS)

    # -- public API --------------------------------------------------------

    def ground(self, term: Optional[str], slot: str) -> Binding:
        """Ground one term against the vocabulary for ``slot``.

        Args:
            term: The natural-language or canonical term from the intent
                object.  ``None`` or empty means the slot was not requested.
            slot: Either ``"metric"`` or ``"dimension"``.

        Returns:
            A :class:`Binding` recording the outcome, the chosen id (if any),
            and the ranked alternatives that justify it.
        """
        if slot not in self._objects:
            raise ValueError(f"unknown slot '{slot}'")

        if term is None or not str(term).strip():
            return Binding(term=term, slot=slot, resolution=Resolution.ABSENT)

        candidates = self.candidates(term, slot)

        if not candidates:
            return Binding(
                term=term,
                slot=slot,
                resolution=Resolution.UNSUPPORTED,
                candidates=[],
                reason=(
                    f"no approved {slot} corresponds to '{term}'. "
                    f"This request cannot be expressed with the current "
                    f"semantic layer."
                ),
            )

        best = candidates[0]
        runner_up_score = candidates[1].score if len(candidates) > 1 else 0.0

        if best.score < ACCEPT_FLOOR:
            return Binding(
                term=term,
                slot=slot,
                resolution=Resolution.UNSUPPORTED,
                candidates=candidates,
                reason=(
                    f"'{term}' does not map confidently onto any approved "
                    f"{slot} (best match '{best.id}' scored "
                    f"{best.score:.2f}, below the {ACCEPT_FLOOR:.2f} threshold)."
                ),
            )

        if best.score - runner_up_score < ACCEPT_MARGIN:
            tied = [c for c in candidates if best.score - c.score < ACCEPT_MARGIN]
            return Binding(
                term=term,
                slot=slot,
                resolution=Resolution.AMBIGUOUS,
                candidates=tied,
                reason=(
                    f"'{term}' matches {len(tied)} approved {slot}s equally "
                    f"well: {', '.join(c.id for c in tied)}."
                ),
            )

        return Binding(
            term=term,
            slot=slot,
            resolution=Resolution.RESOLVED,
            chosen=best.id,
            candidates=candidates,
        )

    def candidates(self, term: str, slot: str) -> List[GroundingCandidate]:
        """Score every object in ``slot``'s vocabulary against ``term``."""
        term_clean = str(term).lower().strip().replace("_", " ")
        term_tokens = _token_set(term_clean)

        scored: List[GroundingCandidate] = []
        for obj in self._objects[slot]:
            candidate = self._score(obj, term_clean, term_tokens)
            if candidate and candidate.score >= CANDIDATE_FLOOR:
                scored.append(candidate)

        # Deterministic ordering: score first, then id, so ties never depend on
        # the declaration order of the semantic layer.
        scored.sort(key=lambda c: (-c.score, c.id))
        return scored[:MAX_CANDIDATES]

    # -- scoring -----------------------------------------------------------

    def _score(
        self, obj, term_clean: str, term_tokens: set
    ) -> Optional[GroundingCandidate]:
        """Score one semantic object, returning the strongest signal found."""
        obj_id = obj.id.lower()
        obj_id_spaced = obj_id.replace("_", " ")
        obj_label = obj.label.lower()

        # 1. Exact canonical id — the LLM is instructed to emit these, so this
        #    is the normal path and must dominate everything else.
        if term_clean in (obj_id, obj_id_spaced):
            return self._candidate(obj, 1.0, MatchKind.EXACT_ID,
                                   f"term equals canonical id '{obj.id}'")

        # 2. Exact human label.
        if term_clean == obj_label:
            return self._candidate(obj, 0.96, MatchKind.EXACT_LABEL,
                                   f"term equals label '{obj.label}'")

        # 3. Administrator-curated alias, from either the synonym map or an
        #    explicit alias clause in the object's own description.
        if self._synonyms.get(term_clean) == obj.id:
            return self._candidate(obj, 0.94, MatchKind.ALIAS,
                                   f"configured synonym for '{obj.id}'")

        if term_clean in _declared_aliases(obj.description):
            return self._candidate(
                obj, 0.94, MatchKind.ALIAS,
                f"'{obj.id}' is declared as also called '{term_clean}'",
            )

        # 4. Token overlap against id + label.  Symmetric (Jaccard-style) so
        #    that a short term does not automatically win against a long id.
        id_tokens = _token_set(obj_id_spaced) | _token_set(obj_label)
        if term_tokens and id_tokens:
            shared = term_tokens & id_tokens

            # 4a. Containment — every token of the term appears in the object's
            #     id or label ("country" → country_name, "quantity" →
            #     item_quantity).  A purely symmetric score penalises these for
            #     the object's extra qualifier token and pushes an obviously
            #     correct binding below the acceptance floor.  Scoring them high
            #     and letting the margin rule arbitrate is the right division of
            #     labour: "name" alone is genuinely ambiguous across the five
            #     *_name dimensions and will still be reported as such.
            if shared == term_tokens:
                specificity = len(shared) / len(id_tokens)
                score = round(0.80 + 0.13 * specificity, 4)
                return self._candidate(
                    obj, score, MatchKind.TOKEN_OVERLAP,
                    f"'{' '.join(sorted(term_tokens))}' is contained in "
                    f"'{obj.id}' / '{obj.label}'",
                )

            if shared:
                coverage = len(shared) / len(term_tokens)
                specificity = len(shared) / len(id_tokens)
                overlap = (2 * coverage * specificity) / (coverage + specificity)
                # Blend in character similarity to separate near-identical ids
                # such as `refund_count` vs `refund_amount`.
                score = 0.85 * overlap + 0.15 * _sequence_ratio(term_clean, obj_id_spaced)
                return self._candidate(
                    obj, round(min(score, 0.93), 4), MatchKind.TOKEN_OVERLAP,
                    f"shares {sorted(shared)} with '{obj.id}' / '{obj.label}'",
                )

        # 5. Description overlap — the weakest signal, and deliberately capped
        #    well below the acceptance floor.  In the previous implementation a
        #    description hit could win outright; here it can only ever surface
        #    an object as an *alternative* for the user to confirm.
        desc_tokens = _token_set(obj.description)
        if term_tokens and desc_tokens:
            shared = term_tokens & desc_tokens
            if shared:
                coverage = len(shared) / len(term_tokens)
                score = round(min(0.55, 0.30 + 0.25 * coverage), 4)
                if score >= CANDIDATE_FLOOR:
                    return self._candidate(
                        obj, score, MatchKind.DESCRIPTION_OVERLAP,
                        f"description of '{obj.id}' mentions {sorted(shared)}",
                    )

        return None

    @staticmethod
    def _candidate(obj, score: float, kind: MatchKind, evidence: str) -> GroundingCandidate:
        return GroundingCandidate(
            id=obj.id, label=obj.label, score=score,
            match_kind=kind, evidence=evidence,
        )

    # -- vocabulary introspection -----------------------------------------

    def vocabulary(self, slot: str) -> List[str]:
        """Return the approved ids for a slot, for clarification messages."""
        return sorted(obj.id for obj in self._objects[slot])

    def lexicon(self) -> set:
        """All tokens the semantic layer can account for.

        Used by the coverage analyser to decide which words in a request the
        vocabulary explains and which it does not.
        """
        tokens: set = set()
        for objects in self._objects.values():
            for obj in objects:
                tokens |= _token_set(obj.id.replace("_", " "))
                tokens |= _token_set(obj.label)
                tokens |= _token_set(obj.description)
        tokens |= {t for key in self._synonyms for t in _tokenise(key)}
        return tokens
