"""
Statistical consistency checker for career agent claims.

Spec 002, Phase 5, Task T014 — Validates quantitative claims (salary,
employment) made by career advisory agents against BLS reference data
stored as node attributes in the O*NET knowledge graph.

Design decisions:
    - BLS data lives on KG nodes as ``bls_median_wage`` (float) and
      ``bls_employment`` (float) attributes.  If an attribute is absent,
      the claim is marked *unverifiable* (``is_consistent=None``), NOT
      hallucinated — missing data ≠ incorrect data.
    - Deviation is computed as *absolute* percentage:
      ``|claimed - reference| / reference * 100``.
    - Default tolerance is 15 % (configurable at init).

Performance target: <1 ms per claim (pure arithmetic, no graph traversal).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import networkx as nx

from backend.hallucination.models import StatisticalVerdict


class StatisticalConsistencyChecker:
    """Validate numerical claims against BLS data in the knowledge graph.

    Args:
        kg: NetworkX DiGraph with occupation nodes keyed by SOC code.
            Nodes may carry ``bls_median_wage`` and/or ``bls_employment``
            float attributes.
        tolerance: Maximum acceptable relative deviation (0-1).
            Default is 0.15 (15 %).
    """

    def __init__(self, kg: nx.DiGraph, *, tolerance: float = 0.15) -> None:
        self._kg = kg
        self._tolerance = tolerance

    # ─── Public API ──────────────────────────────────────────────────────

    def check_salary_claim(
        self, occupation_soc: str, claimed_value: float
    ) -> StatisticalVerdict:
        """Check a salary claim against BLS median wage.

        Args:
            occupation_soc: O*NET SOC code (e.g. ``"15-1252.00"``).
            claimed_value:  Dollar amount claimed by the agent.

        Returns:
            :class:`StatisticalVerdict` with consistency result.
        """
        return self._check_claim(
            occupation_soc=occupation_soc,
            claimed_value=claimed_value,
            claim_type="salary",
            bls_attr="bls_median_wage",
        )

    def check_employment_claim(
        self, occupation_soc: str, claimed_value: float
    ) -> StatisticalVerdict:
        """Check an employment claim against BLS employment count.

        Args:
            occupation_soc: O*NET SOC code.
            claimed_value:  Employment count claimed by the agent.

        Returns:
            :class:`StatisticalVerdict` with consistency result.
        """
        return self._check_claim(
            occupation_soc=occupation_soc,
            claimed_value=claimed_value,
            claim_type="employment",
            bls_attr="bls_employment",
        )

    def check_all_claims(
        self,
        claims: List[Tuple[str, str, float, str]],
    ) -> List[StatisticalVerdict]:
        """Batch-check multiple statistical claims.

        Args:
            claims: List of ``(claim_text, claim_type, value, occupation_soc)``
                tuples.  ``claim_type`` must be ``"salary"`` or
                ``"employment"``.

        Returns:
            List of :class:`StatisticalVerdict` in the same order as input.
        """
        verdicts: List[StatisticalVerdict] = []
        for claim_text, claim_type, value, occupation_soc in claims:
            if claim_type == "salary":
                v = self._check_claim(
                    occupation_soc=occupation_soc,
                    claimed_value=value,
                    claim_type="salary",
                    bls_attr="bls_median_wage",
                    claim_text_override=claim_text,
                )
            elif claim_type == "employment":
                v = self._check_claim(
                    occupation_soc=occupation_soc,
                    claimed_value=value,
                    claim_type="employment",
                    bls_attr="bls_employment",
                    claim_text_override=claim_text,
                )
            else:
                # Unknown claim type → unverifiable
                v = StatisticalVerdict(
                    claim_text=claim_text,
                    claim_type=claim_type,
                    claim_value=value,
                    reference_value=None,
                    deviation_pct=None,
                    is_consistent=None,
                )
            verdicts.append(v)
        return verdicts

    # ─── Private Helpers ─────────────────────────────────────────────────

    def _check_claim(
        self,
        occupation_soc: str,
        claimed_value: float,
        claim_type: str,
        bls_attr: str,
        claim_text_override: Optional[str] = None,
    ) -> StatisticalVerdict:
        """Core logic: compare claimed value against a BLS node attribute.

        If the occupation node is missing or lacks the BLS attribute,
        returns an *unverifiable* verdict (``is_consistent=None``).
        """
        claim_text = claim_text_override or f"{claim_type}:{claimed_value}"

        # Look up BLS reference value
        node_data = self._kg.nodes.get(occupation_soc)
        if node_data is None:
            return StatisticalVerdict(
                claim_text=claim_text,
                claim_type=claim_type,
                claim_value=claimed_value,
                reference_value=None,
                deviation_pct=None,
                is_consistent=None,
            )

        reference_value: Optional[float] = node_data.get(bls_attr)
        if reference_value is None:
            return StatisticalVerdict(
                claim_text=claim_text,
                claim_type=claim_type,
                claim_value=claimed_value,
                reference_value=None,
                deviation_pct=None,
                is_consistent=None,
            )

        # Compute deviation
        deviation_pct = abs(claimed_value - reference_value) / reference_value * 100.0
        is_consistent = deviation_pct <= (self._tolerance * 100.0)

        return StatisticalVerdict(
            claim_text=claim_text,
            claim_type=claim_type,
            claim_value=claimed_value,
            reference_value=reference_value,
            deviation_pct=deviation_pct,
            is_consistent=is_consistent,
        )
