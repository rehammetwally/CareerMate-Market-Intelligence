"""
Entity grounding checker against the O*NET knowledge graph.

Spec 002, Phase 3, Task T008 — Validates extracted entities (occupations,
skills, knowledge areas, abilities) against the KG ground truth. Entities
not present in the KG are flagged as potential hallucinations.

Uses:
  - Exact title/name matching against KG node attributes.
  - ``rapidfuzz`` for fuzzy matching to find nearest KG entity for invalid ones.

Core Insight: Entity grounding is the most fundamental hallucination check.
If an agent mentions a non-existent occupation or skill, every downstream
claim built on it is invalid.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx
from rapidfuzz import fuzz, process as rfprocess

from backend.hallucination.models import EntityVerdict

# ─── Constants ───────────────────────────────────────────────────────────────

_FUZZY_VALID_THRESHOLD = 90
"""Minimum rapidfuzz score (0-100) to consider a fuzzy match as 'valid'."""


class EntityGroundingChecker:
    """Validate extracted entities against the O*NET knowledge graph.

    Initialised with a KG (NetworkX DiGraph) produced by ``ONetKGBuilder``.
    Builds internal lookup tables from node attributes for fast validation.

    Args:
        kg: NetworkX DiGraph with occupation nodes (keyed by SOC code)
            having ``title`` attributes, and optionally a graph-level
            ``element_names`` dict mapping element IDs to names.
    """

    def __init__(self, kg: nx.DiGraph) -> None:
        self._kg = kg

        # ── Occupation lookup tables ──────────────────────────────────────
        # title_lower → soc_code
        self._title_to_soc: Dict[str, str] = {}
        # soc_code → title
        self._soc_to_title: Dict[str, str] = {}
        # Ordered lists for rapidfuzz bulk extraction
        self._title_choices: List[str] = []
        self._title_choice_socs: List[str] = []

        for node, data in kg.nodes(data=True):
            title = data.get("title", "")
            self._soc_to_title[node] = title
            self._title_to_soc[title.lower()] = node
            self._title_choices.append(title)
            self._title_choice_socs.append(node)

        # ── Element (skill/knowledge/ability) lookup tables ───────────────
        self._element_names: Dict[str, str] = kg.graph.get("element_names", {})
        # name_lower → element_id
        self._element_name_to_id: Dict[str, str] = {
            name.lower(): eid for eid, name in self._element_names.items()
        }
        # Ordered lists for rapidfuzz
        self._element_choices: List[str] = list(self._element_names.values())
        self._element_choice_ids: List[str] = list(self._element_names.keys())

    # ─── Public API ──────────────────────────────────────────────────────

    def check_occupation(self, entity_text: str) -> EntityVerdict:
        """Validate an occupation entity against the KG.

        Checks for exact title match first, then falls back to fuzzy matching.

        Args:
            entity_text: The occupation name or title to validate.

        Returns:
            EntityVerdict with is_valid=True if the occupation exists in the KG,
            or is_valid=False with nearest_match_soc and nearest_match_score
            for the closest KG occupation.
        """
        text_lower = entity_text.lower()

        # Strategy 1: exact match by title
        if text_lower in self._title_to_soc:
            soc = self._title_to_soc[text_lower]
            return EntityVerdict(
                entity_text=entity_text,
                entity_type="occupation",
                is_valid=True,
                confidence=1.0,
                nearest_match_soc=soc,
                nearest_match_score=1.0,
            )

        # Strategy 2: fuzzy match
        best = rfprocess.extractOne(
            entity_text,
            self._title_choices,
            scorer=fuzz.ratio,
        )

        if best is not None:
            matched_title, score, idx = best
            soc = self._title_choice_socs[idx]
            confidence = score / 100.0
            is_valid = score >= _FUZZY_VALID_THRESHOLD

            return EntityVerdict(
                entity_text=entity_text,
                entity_type="occupation",
                is_valid=is_valid,
                confidence=confidence,
                nearest_match_soc=soc,
                nearest_match_score=confidence,
            )

        # No match at all (should only happen with empty KG)
        return EntityVerdict(
            entity_text=entity_text,
            entity_type="occupation",
            is_valid=False,
            confidence=0.0,
            nearest_match_soc=None,
            nearest_match_score=None,
        )

    def check_skill(self, entity_text: str) -> EntityVerdict:
        """Validate a skill/knowledge/ability entity against the KG elements.

        Checks for exact element name match first, then fuzzy matching.

        Args:
            entity_text: The skill, knowledge area, or ability name to validate.

        Returns:
            EntityVerdict with is_valid=True if the element exists in the KG,
            or is_valid=False with nearest match information.
        """
        text_lower = entity_text.lower()

        # Strategy 1: exact match by element name
        if text_lower in self._element_name_to_id:
            element_id = self._element_name_to_id[text_lower]
            return EntityVerdict(
                entity_text=entity_text,
                entity_type="skill",
                is_valid=True,
                confidence=1.0,
                nearest_match_soc=None,
                nearest_match_score=1.0,
            )

        # Strategy 2: fuzzy match against element names
        if self._element_choices:
            best = rfprocess.extractOne(
                entity_text,
                self._element_choices,
                scorer=fuzz.ratio,
            )

            if best is not None:
                matched_name, score, idx = best
                confidence = score / 100.0
                is_valid = score >= _FUZZY_VALID_THRESHOLD

                return EntityVerdict(
                    entity_text=entity_text,
                    entity_type="skill",
                    is_valid=is_valid,
                    confidence=confidence,
                    nearest_match_soc=None,
                    nearest_match_score=confidence,
                )

        # No match at all
        return EntityVerdict(
            entity_text=entity_text,
            entity_type="skill",
            is_valid=False,
            confidence=0.0,
            nearest_match_soc=None,
            nearest_match_score=None,
        )

    def check_all(self, entities: List[Tuple[str, str]]) -> List[EntityVerdict]:
        """Validate a batch of entities against the KG.

        Args:
            entities: List of ``(entity_text, entity_type)`` tuples where
                entity_type is one of ``'occupation'``, ``'skill'``,
                ``'knowledge'``, ``'ability'``.

        Returns:
            List of EntityVerdict in the same order as input.
        """
        verdicts: List[EntityVerdict] = []

        for entity_text, entity_type in entities:
            if entity_type == "occupation":
                verdicts.append(self.check_occupation(entity_text))
            else:
                # skill, knowledge, ability all use the element lookup
                verdict = self.check_skill(entity_text)
                # Override entity_type if it was knowledge or ability
                if entity_type != "skill":
                    verdict = EntityVerdict(
                        entity_text=verdict.entity_text,
                        entity_type=entity_type,
                        is_valid=verdict.is_valid,
                        confidence=verdict.confidence,
                        nearest_match_soc=verdict.nearest_match_soc,
                        nearest_match_score=verdict.nearest_match_score,
                    )
                verdicts.append(verdict)

        return verdicts

    @staticmethod
    def compute_grounding_rate(verdicts: List[EntityVerdict]) -> float:
        """Compute the grounding rate: proportion of valid entities.

        Args:
            verdicts: List of EntityVerdict objects.

        Returns:
            Float in [0, 1]. Returns 1.0 for empty list (no entities to
            validate = nothing wrong).
        """
        if not verdicts:
            return 1.0

        valid_count = sum(1 for v in verdicts if v.is_valid)
        return valid_count / len(verdicts)
