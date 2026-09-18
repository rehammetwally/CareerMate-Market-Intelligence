"""
Entity extraction from agent text output.

Spec 002, Phase 2, Task T005 — Extracts occupation titles, SOC codes,
skill/knowledge/ability mentions, and statistical claims (salary, employment)
from free-form agent response text.

Uses:
  - Pre-built lookup tables from KG node attributes for exact matching.
  - ``rapidfuzz`` for fuzzy occupation-title matching.
  - Pre-compiled regex patterns for SOC codes and numerical claims.

Performance target: <50ms for a 2000-token text on the project hardware.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

import networkx as nx
from rapidfuzz import fuzz, process as rfprocess

# ─── Type Aliases ────────────────────────────────────────────────────────────

OccupationMatch = Tuple[str, Tuple[int, int], str, float]
"""(entity_text, (start, end), matched_soc, confidence)"""

SkillMatch = Tuple[str, Tuple[int, int], str, float]
"""(entity_text, (start, end), element_id, confidence)"""

StatisticalClaim = Tuple[str, str, float, str]
"""(claim_text, claim_type, value, context)"""

# ─── Pre-compiled Regex ──────────────────────────────────────────────────────

_SOC_PATTERN = re.compile(r"\b(\d{2}-\d{4}\.\d{2})\b")
"""Matches O*NET SOC codes like 15-1252.00."""

_SALARY_PATTERN = re.compile(
    r"\$\s?([\d,]+(?:\.\d+)?)\s*(?:k|K)?"
    r"(?:\s*(?:per\s+year|annually|/yr|a\s+year|per\s+annum|salary|median salary))?"
)
"""Matches dollar amounts like $130,000, $85k, $130,000 per year."""

_EMPLOYMENT_PATTERN = re.compile(
    r"([\d,.]+)\s*(million|thousand|billion)?\s*"
    r"(?:workers|employees|employed|jobs|positions|people\s+(?:work|employed))",
    re.IGNORECASE,
)
"""Matches employment counts like '1.8 million workers', '500,000 employees'."""

# Fuzzy matching thresholds
_FUZZY_THRESHOLD = 60  # minimum rapidfuzz score to consider a match
_FUZZY_HIGH_CONFIDENCE = 90  # above this → confidence near 1.0

# Context window (chars) around a statistical claim
_CONTEXT_WINDOW = 80


class EntityExtractor:
    """Extract career-domain entities from agent text output.

    Initialised with a KG (NetworkX DiGraph) produced by ``ONetKGBuilder``.
    Builds internal lookup tables from node attributes for fast matching.

    Args:
        kg: NetworkX DiGraph with occupation nodes (keyed by SOC code)
            having ``title`` attributes, and optionally a graph-level
            ``element_names`` dict mapping element IDs to names.
    """

    def __init__(self, kg: nx.DiGraph) -> None:
        self._kg = kg

        # ── Build occupation lookup tables ────────────────────────────────
        # soc_code → title (lowered for matching)
        self._soc_to_title: Dict[str, str] = {}
        # title_lower → soc_code
        self._title_to_soc: Dict[str, str] = {}
        # List of (title, soc_code) for rapidfuzz bulk extraction
        self._title_choices: List[str] = []
        self._title_choice_socs: List[str] = []

        for node, data in kg.nodes(data=True):
            title = data.get("title", "")
            self._soc_to_title[node] = title
            self._title_to_soc[title.lower()] = node
            self._title_choices.append(title)
            self._title_choice_socs.append(node)

        # ── Build element (skill/knowledge/ability) lookup tables ─────────
        # element_id → element_name
        self._element_names: Dict[str, str] = kg.graph.get("element_names", {})
        # element_name_lower → element_id
        self._element_name_to_id: Dict[str, str] = {
            name.lower(): eid for eid, name in self._element_names.items()
        }

        # Pre-compile regex for element names (longest first to avoid partial)
        if self._element_names:
            sorted_names = sorted(self._element_names.values(), key=len, reverse=True)
            escaped = [re.escape(n) for n in sorted_names]
            self._element_pattern: Optional[re.Pattern] = re.compile(
                r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE
            )
        else:
            self._element_pattern = None

        # Pre-compile regex for exact occupation titles (longest first)
        if self._title_choices:
            sorted_titles = sorted(self._title_choices, key=len, reverse=True)
            escaped_titles = [re.escape(t) for t in sorted_titles]
            self._title_pattern: Optional[re.Pattern] = re.compile(
                r"\b(" + "|".join(escaped_titles) + r")\b", re.IGNORECASE
            )
        else:
            self._title_pattern = None

    # ─── Public API ──────────────────────────────────────────────────────

    def extract_occupations(self, text: str) -> List[OccupationMatch]:
        """Extract occupation mentions from text.

        Strategies (in order):
          1. Exact title match via pre-compiled regex.
          2. SOC code match via regex ``\\d{2}-\\d{4}\\.\\d{2}``.
          3. Fuzzy n-gram matching for informal references (e.g. "software dev").

        Args:
            text: Free-form agent response text.

        Returns:
            List of ``(entity_text, (start, end), matched_soc, confidence)`` tuples,
            deduplicated by SOC code (first/best match wins).
        """
        if not text:
            return []

        results: List[OccupationMatch] = []
        seen_socs: set = set()

        # Strategy 1: exact title match
        if self._title_pattern:
            for match in self._title_pattern.finditer(text):
                matched_text = match.group(0)
                soc = self._title_to_soc.get(matched_text.lower())
                if soc and soc not in seen_socs:
                    results.append(
                        (matched_text, (match.start(), match.end()), soc, 1.0)
                    )
                    seen_socs.add(soc)

        # Strategy 2: SOC code match
        for match in _SOC_PATTERN.finditer(text):
            soc = match.group(1)
            if soc in self._soc_to_title and soc not in seen_socs:
                results.append((soc, (match.start(), match.end()), soc, 1.0))
                seen_socs.add(soc)

        # Strategy 3: fuzzy n-gram matching
        # Generate candidate n-grams (2-5 words) from text
        if self._title_choices:
            words = text.split()
            for n in range(2, min(6, len(words) + 1)):
                for i in range(len(words) - n + 1):
                    candidate = " ".join(words[i : i + n])
                    # Skip if too short or already contains an exact match
                    if len(candidate) < 5:
                        continue

                    best = rfprocess.extractOne(
                        candidate,
                        self._title_choices,
                        scorer=fuzz.ratio,
                        score_cutoff=_FUZZY_THRESHOLD,
                    )
                    if best is not None:
                        matched_title, score, idx = best
                        soc = self._title_choice_socs[idx]
                        if soc not in seen_socs and score < 100:
                            # Compute span from text
                            start = text.find(candidate)
                            if start >= 0:
                                confidence = score / 100.0
                                results.append(
                                    (
                                        candidate,
                                        (start, start + len(candidate)),
                                        soc,
                                        confidence,
                                    )
                                )
                                seen_socs.add(soc)

        return results

    def extract_skills(self, text: str) -> List[SkillMatch]:
        """Extract skill/knowledge/ability mentions from text.

        Matches against the 120 O*NET element names stored in the KG's
        ``element_names`` graph attribute.

        Args:
            text: Free-form agent response text.

        Returns:
            List of ``(entity_text, (start, end), element_id, confidence)`` tuples.
        """
        if not text or self._element_pattern is None:
            return []

        results: List[SkillMatch] = []
        seen_ids: set = set()

        for match in self._element_pattern.finditer(text):
            matched_text = match.group(0)
            element_id = self._element_name_to_id.get(matched_text.lower())
            if element_id and element_id not in seen_ids:
                results.append(
                    (matched_text, (match.start(), match.end()), element_id, 1.0)
                )
                seen_ids.add(element_id)

        return results

    def extract_statistical_claims(self, text: str) -> List[StatisticalClaim]:
        """Extract statistical claims (salary, employment) from text.

        Args:
            text: Free-form agent response text.

        Returns:
            List of ``(claim_text, claim_type, value, context)`` tuples.
        """
        if not text:
            return []

        results: List[StatisticalClaim] = []

        # Salary claims
        for match in _SALARY_PATTERN.finditer(text):
            raw_value = match.group(1).replace(",", "")
            try:
                value = float(raw_value)
            except ValueError:
                continue

            # Handle $85k notation
            full_match = match.group(0)
            if full_match.rstrip().lower().endswith("k"):
                value *= 1000

            claim_text = match.group(0)
            context = self._get_context(text, match.start(), match.end())
            results.append((claim_text, "salary", value, context))

        # Employment claims
        for match in _EMPLOYMENT_PATTERN.finditer(text):
            raw_number = match.group(1).replace(",", "")
            try:
                value = float(raw_number)
            except ValueError:
                continue

            multiplier_str = match.group(2)
            if multiplier_str:
                multiplier_str = multiplier_str.lower()
                if multiplier_str == "million":
                    value *= 1_000_000
                elif multiplier_str == "thousand":
                    value *= 1_000
                elif multiplier_str == "billion":
                    value *= 1_000_000_000

            claim_text = match.group(0)
            context = self._get_context(text, match.start(), match.end())
            results.append((claim_text, "employment", value, context))

        return results

    # ─── Private Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _get_context(text: str, start: int, end: int) -> str:
        """Extract a context window around a match span."""
        ctx_start = max(0, start - _CONTEXT_WINDOW)
        ctx_end = min(len(text), end + _CONTEXT_WINDOW)
        return text[ctx_start:ctx_end]
