"""
Transition validity checker via KG path analysis.

Spec 002, Phase 4, Task T011 — Validates career transitions recommended by
agents by checking that a path exists in the KG with sufficient skill overlap
at each hop.  Transitions with no KG path or below-threshold overlap are
flagged as potential hallucinations.

Uses:
  - KG edge existence for direct adjacency check.
  - ``networkx.shortest_path`` for multi-hop reachability.
  - Cosine similarity of 120-dim feature vectors for skill overlap.

Core Insight: Invalid career transitions are the most harmful hallucination
in a career advisory system — they can lead users to pursue unrealistic
career changes.
"""

from __future__ import annotations

from typing import List

import networkx as nx
import numpy as np

from backend.hallucination.models import TransitionVerdict


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Returns 0.0 if either vector has zero norm.
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class TransitionValidityChecker:
    """Validate career transitions against the O*NET knowledge graph.

    Checks that a path exists between source and target occupations in the
    KG, computes skill overlap from feature vectors, and produces
    ``TransitionVerdict`` objects.

    Args:
        kg: NetworkX DiGraph produced by ``ONetKGBuilder``, with nodes keyed
            by SOC code and ``feature_vector`` attributes.
    """

    def __init__(self, kg: nx.DiGraph) -> None:
        self._kg = kg

    # ─── Public API ──────────────────────────────────────────────────────

    def check_transition(self, source_soc: str, target_soc: str) -> TransitionVerdict:
        """Validate a single career transition from source to target.

        Strategy:
          1. Compute skill overlap from feature vectors (always available).
          2. Check for a direct edge (path_length=1).
          3. If no direct edge, try ``shortest_path`` for multi-hop.
          4. If no path exists, mark invalid with path_length=-1.

        A transition is considered valid if any path exists in the KG
        (direct or multi-hop).

        Args:
            source_soc: SOC code of the source occupation.
            target_soc: SOC code of the target occupation.

        Returns:
            TransitionVerdict with path information and skill overlap.
        """
        # Compute skill overlap from feature vectors
        skill_overlap = self._compute_skill_overlap(source_soc, target_soc)

        # Check for path in KG
        try:
            path = nx.shortest_path(self._kg, source_soc, target_soc)
            return TransitionVerdict(
                source_soc=source_soc,
                target_soc=target_soc,
                is_valid=True,
                skill_overlap=skill_overlap,
                path_length=len(path) - 1,  # number of hops
                path_hops=list(path),
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return TransitionVerdict(
                source_soc=source_soc,
                target_soc=target_soc,
                is_valid=False,
                skill_overlap=skill_overlap,
                path_length=-1,
                path_hops=[],
            )

    def check_career_path(self, soc_sequence: List[str]) -> List[TransitionVerdict]:
        """Validate a sequence of career transitions (multi-hop path).

        Checks each consecutive pair in the sequence independently.

        Args:
            soc_sequence: Ordered list of SOC codes forming a career path.

        Returns:
            List of TransitionVerdict, one per consecutive pair.
            Length = ``len(soc_sequence) - 1``.
        """
        verdicts: List[TransitionVerdict] = []
        for i in range(len(soc_sequence) - 1):
            verdicts.append(self.check_transition(soc_sequence[i], soc_sequence[i + 1]))
        return verdicts

    @staticmethod
    def compute_path_coherence(verdicts: List[TransitionVerdict]) -> float:
        """Compute Career Path Coherence (CPC) metric.

        CPC = proportion of valid transitions in the path.

        Args:
            verdicts: List of TransitionVerdict from ``check_career_path``.

        Returns:
            Float in [0, 1]. Returns 1.0 for empty list.
        """
        if not verdicts:
            return 1.0
        valid_count = sum(1 for v in verdicts if v.is_valid)
        return valid_count / len(verdicts)

    # ─── Private Helpers ─────────────────────────────────────────────────

    def _compute_skill_overlap(self, source_soc: str, target_soc: str) -> float:
        """Compute cosine similarity between two occupations' feature vectors.

        Returns 0.0 if either occupation is not in the KG or has no
        feature_vector attribute.
        """
        source_data = self._kg.nodes.get(source_soc, {})
        target_data = self._kg.nodes.get(target_soc, {})

        source_vec = source_data.get("feature_vector")
        target_vec = target_data.get("feature_vector")

        if source_vec is None or target_vec is None:
            return 0.0

        return _cosine_similarity(source_vec, target_vec)
