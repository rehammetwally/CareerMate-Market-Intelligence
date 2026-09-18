"""
Multi-agent cross-validation for ontological consistency.

Spec 002, Phase 6, Task T017 — Detects inter-agent ontological
inconsistencies by comparing the KG regions referenced by different
agents' outputs.

**Methodology**: Given entity sets from two agents, consistency is
measured via Jaccard similarity of the grounded entity identifiers
(SOC codes for occupations, element IDs for skills). This captures
whether agents are "talking about the same part of the ontology".

For occupation entities, we additionally incorporate *neighbourhood
overlap*: even if two agents mention different occupations, they may
still be consistent if those occupations are KG-adjacent (high skill
overlap). This is captured via a weighted Jaccard that considers
1-hop neighbours.

**Performance target**: <5 ms per pair (set operations only).
"""

from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

import networkx as nx

from backend.hallucination.models import CrossValidationResult


class MultiAgentCrossValidator:
    """Validate ontological consistency between multiple agents' outputs.

    Compares entity sets from different agents using Jaccard similarity
    of KG-grounded identifiers, with optional neighbourhood expansion
    for occupations.

    Args:
        kg: NetworkX DiGraph with occupation nodes keyed by SOC code.
    """

    def __init__(self, kg: nx.DiGraph) -> None:
        self._kg = kg

    # ─── Public API ──────────────────────────────────────────────────────

    def validate_pair(
        self,
        entities_a: List[Tuple[str, str]],
        entities_b: List[Tuple[str, str]],
        agent_a: str = "agent_a",
        agent_b: str = "agent_b",
    ) -> CrossValidationResult:
        """Compute ontological consistency between two agents' entity sets.

        Args:
            entities_a: List of ``(entity_id, entity_type)`` tuples from
                agent A.  ``entity_id`` is a SOC code for occupations or
                an element ID for skills.  ``entity_type`` is
                ``"occupation"`` or ``"skill"``.
            entities_b: Same format, from agent B.
            agent_a: Identifier string for agent A.
            agent_b: Identifier string for agent B.

        Returns:
            :class:`CrossValidationResult` with consistency score,
            shared entities, and conflicting entities.
        """
        ids_a = {eid for eid, _ in entities_a}
        ids_b = {eid for eid, _ in entities_b}

        # Shared = intersection
        shared = ids_a & ids_b

        # Conflicting = symmetric difference (entities only one agent mentions)
        conflicting = ids_a ^ ids_b

        # --- Jaccard similarity as base consistency ---
        union = ids_a | ids_b
        if not union:
            # Both agents produced no entities — trivially consistent
            return CrossValidationResult(
                agent_a=agent_a,
                agent_b=agent_b,
                consistency_score=1.0,
                conflicting_entities=[],
                shared_entities=[],
            )

        jaccard = len(shared) / len(union)

        # --- Neighbourhood bonus for occupation entities ---
        # If agents mention different occupations that are KG-adjacent,
        # they're still partially consistent.
        occ_a = {eid for eid, etype in entities_a if etype == "occupation"}
        occ_b = {eid for eid, etype in entities_b if etype == "occupation"}

        neighbour_bonus = self._compute_neighbour_bonus(occ_a, occ_b)

        # Final consistency: weighted combination (Jaccard + neighbour bonus)
        # Clamp to [0, 1]
        consistency = min(1.0, jaccard + neighbour_bonus)

        return CrossValidationResult(
            agent_a=agent_a,
            agent_b=agent_b,
            consistency_score=round(consistency, 6),
            conflicting_entities=sorted(conflicting),
            shared_entities=sorted(shared),
        )

    def validate_batch(
        self,
        agent_entities: Dict[str, List[Tuple[str, str]]],
    ) -> List[CrossValidationResult]:
        """Compute pairwise consistency for all agent pairs.

        Args:
            agent_entities: Mapping of ``agent_name`` →
                ``List[(entity_id, entity_type)]``.

        Returns:
            List of :class:`CrossValidationResult`, one per unique pair
            (C(n,2) results for n agents).
        """
        results: List[CrossValidationResult] = []

        agent_names = sorted(agent_entities.keys())
        for name_a, name_b in combinations(agent_names, 2):
            result = self.validate_pair(
                entities_a=agent_entities[name_a],
                entities_b=agent_entities[name_b],
                agent_a=name_a,
                agent_b=name_b,
            )
            results.append(result)

        return results

    @staticmethod
    def compute_ocs(results: List[CrossValidationResult]) -> float:
        """Compute aggregate Ontological Consistency Score.

        OCS is the arithmetic mean of all pairwise consistency scores.

        Args:
            results: List of :class:`CrossValidationResult` from
                :meth:`validate_batch`.

        Returns:
            OCS in [0, 1].  Returns 1.0 if no results.
        """
        if not results:
            return 1.0
        return sum(r.consistency_score for r in results) / len(results)

    # ─── Private Helpers ─────────────────────────────────────────────────

    def _compute_neighbour_bonus(self, occ_a: set, occ_b: set) -> float:
        """Bonus for occupation sets that overlap in KG neighbourhood.

        For each occupation unique to one agent, check if it is a
        direct KG neighbour of any occupation in the other agent's set.
        The bonus is proportional to the fraction of "conflicting"
        occupations that are actually KG-adjacent.

        Returns a value in [0, 0.3] — capped to avoid overwhelming
        the Jaccard base score.
        """
        unique_a = occ_a - occ_b
        unique_b = occ_b - occ_a

        if not unique_a and not unique_b:
            return 0.0

        total_unique = len(unique_a) + len(unique_b)
        adjacent_count = 0

        for soc in unique_a:
            if soc in self._kg:
                neighbours = set(self._kg.successors(soc)) | set(
                    self._kg.predecessors(soc)
                )
                if neighbours & occ_b:
                    adjacent_count += 1

        for soc in unique_b:
            if soc in self._kg:
                neighbours = set(self._kg.successors(soc)) | set(
                    self._kg.predecessors(soc)
                )
                if neighbours & occ_a:
                    adjacent_count += 1

        if total_unique == 0:
            return 0.0

        # Bonus proportional to adjacency, capped at 0.3
        return min(0.3, 0.3 * (adjacent_count / total_unique))
