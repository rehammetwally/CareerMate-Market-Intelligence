"""
HallucinationDetector — unified orchestrator for all four checks.

Spec 002, Phase 7, Task T019 — Wires entity grounding, transition
validity, statistical consistency, and multi-agent cross-validation into
a single detection pipeline.

Usage::

    detector = HallucinationDetector(kg)
    report = detector.detect(agent_output_text)
    # or for multi-agent:
    report = detector.detect_multi({"agent_a": text_a, "agent_b": text_b})

Performance target: <200 ms per single agent response (FR-007).
All detection is purely computational — zero LLM calls (FR-008).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx

from backend.hallucination.models import (
    CrossValidationResult,
    EntityVerdict,
    HallucinationReport,
    StatisticalVerdict,
    TransitionVerdict,
)
from backend.hallucination.entity_extractor import EntityExtractor
from backend.hallucination.entity_grounding import EntityGroundingChecker
from backend.hallucination.transition_validity import TransitionValidityChecker
from backend.hallucination.statistical_consistency import StatisticalConsistencyChecker
from backend.hallucination.cross_validation import MultiAgentCrossValidator


class HallucinationDetector:
    """Unified hallucination detection pipeline.

    Orchestrates four checks against the knowledge graph:
      1. Entity grounding — validate occupation/skill mentions
      2. Transition validity — validate career path recommendations
      3. Statistical consistency — validate salary/employment claims
      4. Multi-agent cross-validation — detect inter-agent contradictions

    Each check is independently toggleable via constructor flags (FR-010).

    Args:
        kg: NetworkX DiGraph with O*NET occupation nodes.
        enable_entity_grounding: Enable entity grounding check.
        enable_transition_validity: Enable transition validity check.
        enable_statistical_consistency: Enable statistical consistency check.
        enable_cross_validation: Enable multi-agent cross-validation.
        statistical_tolerance: Tolerance for statistical claims (default 15%).
    """

    def __init__(
        self,
        kg: nx.DiGraph,
        *,
        enable_entity_grounding: bool = True,
        enable_transition_validity: bool = True,
        enable_statistical_consistency: bool = True,
        enable_cross_validation: bool = True,
        statistical_tolerance: float = 0.15,
    ) -> None:
        self._kg = kg

        # Feature flags
        self._enable_entity_grounding = enable_entity_grounding
        self._enable_transition_validity = enable_transition_validity
        self._enable_statistical_consistency = enable_statistical_consistency
        self._enable_cross_validation = enable_cross_validation

        # Sub-components (lazy: only create if enabled)
        self._extractor = EntityExtractor(kg)

        self._grounding_checker: Optional[EntityGroundingChecker] = (
            EntityGroundingChecker(kg) if enable_entity_grounding else None
        )
        self._transition_checker: Optional[TransitionValidityChecker] = (
            TransitionValidityChecker(kg) if enable_transition_validity else None
        )
        self._statistical_checker: Optional[StatisticalConsistencyChecker] = (
            StatisticalConsistencyChecker(kg, tolerance=statistical_tolerance)
            if enable_statistical_consistency
            else None
        )
        self._cross_validator: Optional[MultiAgentCrossValidator] = (
            MultiAgentCrossValidator(kg) if enable_cross_validation else None
        )

    # ─── Public API ──────────────────────────────────────────────────────

    def detect(self, agent_output: str) -> HallucinationReport:
        """Run all enabled checks on a single agent response.

        Args:
            agent_output: Free-form text from one agent.

        Returns:
            :class:`HallucinationReport` with per-check verdicts and
            overall HR (Hallucination Rate).
        """
        # Step 1: Extract entities
        occupations = self._extractor.extract_occupations(agent_output)
        skills = self._extractor.extract_skills(agent_output)
        stat_claims = self._extractor.extract_statistical_claims(agent_output)

        # Step 2: Entity grounding
        entity_verdicts: List[EntityVerdict] = []
        if self._grounding_checker and self._enable_entity_grounding:
            entities_to_check: List[Tuple[str, str]] = []
            for entity_text, span, matched_soc, confidence in occupations:
                entities_to_check.append((entity_text, "occupation"))
            for entity_text, span, element_id, confidence in skills:
                entities_to_check.append((entity_text, "skill"))
            entity_verdicts = self._grounding_checker.check_all(entities_to_check)

        # Step 3: Transition validity
        transition_verdicts: List[TransitionVerdict] = []
        if self._transition_checker and self._enable_transition_validity:
            soc_codes = [soc for _, _, soc, _ in occupations]
            if len(soc_codes) >= 2:
                transition_verdicts = self._transition_checker.check_career_path(
                    soc_codes
                )

        # Step 4: Statistical consistency
        statistical_verdicts: List[StatisticalVerdict] = []
        if self._statistical_checker and self._enable_statistical_consistency:
            if stat_claims and occupations:
                # Associate each statistical claim with the most likely occupation
                # Simple heuristic: use the first occupation found
                primary_soc = occupations[0][2]  # matched_soc from first occupation

                claims_for_checker: List[Tuple[str, str, float, str]] = []
                for claim_text, claim_type, value, context in stat_claims:
                    # Try to match claim to a specific occupation from context
                    soc_for_claim = self._match_claim_to_occupation(
                        context, occupations, primary_soc
                    )
                    claims_for_checker.append(
                        (claim_text, claim_type, value, soc_for_claim)
                    )

                statistical_verdicts = self._statistical_checker.check_all_claims(
                    claims_for_checker
                )

        # Step 5: Compute HR
        overall_hr = self._compute_hr(
            entity_verdicts, transition_verdicts, statistical_verdicts
        )

        return HallucinationReport(
            entity_verdicts=entity_verdicts,
            transition_verdicts=transition_verdicts,
            statistical_verdicts=statistical_verdicts,
            cross_validation_results=[],
            overall_hr=overall_hr,
            overall_ocs=1.0,  # No cross-validation in single-agent mode
        )

    def detect_multi(self, outputs: Dict[str, str]) -> HallucinationReport:
        """Run all checks on multiple agent outputs with cross-validation.

        Args:
            outputs: Mapping of ``agent_name`` → ``agent_output_text``.

        Returns:
            :class:`HallucinationReport` with merged verdicts from all
            agents plus cross-validation results and OCS.
        """
        # Run detect() on each agent's output
        all_entity_verdicts: List[EntityVerdict] = []
        all_transition_verdicts: List[TransitionVerdict] = []
        all_statistical_verdicts: List[StatisticalVerdict] = []

        # Collect entity IDs per agent for cross-validation
        agent_entities: Dict[str, List[Tuple[str, str]]] = {}

        for agent_name, text in outputs.items():
            report = self.detect(text)
            all_entity_verdicts.extend(report.entity_verdicts)
            all_transition_verdicts.extend(report.transition_verdicts)
            all_statistical_verdicts.extend(report.statistical_verdicts)

            # Build entity ID list for cross-validation
            occupations = self._extractor.extract_occupations(text)
            skills = self._extractor.extract_skills(text)
            entity_ids: List[Tuple[str, str]] = []
            for _, _, matched_soc, _ in occupations:
                entity_ids.append((matched_soc, "occupation"))
            for _, _, element_id, _ in skills:
                entity_ids.append((element_id, "skill"))
            agent_entities[agent_name] = entity_ids

        # Step 6: Cross-validation
        cross_results: List[CrossValidationResult] = []
        overall_ocs = 1.0

        if (
            self._cross_validator
            and self._enable_cross_validation
            and len(agent_entities) >= 2
        ):
            cross_results = self._cross_validator.validate_batch(agent_entities)
            overall_ocs = self._cross_validator.compute_ocs(cross_results)

        # Compute merged HR
        overall_hr = self._compute_hr(
            all_entity_verdicts, all_transition_verdicts, all_statistical_verdicts
        )

        return HallucinationReport(
            entity_verdicts=all_entity_verdicts,
            transition_verdicts=all_transition_verdicts,
            statistical_verdicts=all_statistical_verdicts,
            cross_validation_results=cross_results,
            overall_hr=overall_hr,
            overall_ocs=overall_ocs,
        )

    # ─── Private Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _compute_hr(
        entity_verdicts: List[EntityVerdict],
        transition_verdicts: List[TransitionVerdict],
        statistical_verdicts: List[StatisticalVerdict],
    ) -> float:
        """Compute Hallucination Rate across all check types.

        HR = (flagged items) / (total items checked).
        Items:
          - Entity: is_valid == False
          - Transition: is_valid == False
          - Statistical: is_consistent == False (unverifiable excluded)

        Returns 0.0 if no items were checked.
        """
        total = 0
        flagged = 0

        for v in entity_verdicts:
            total += 1
            if not v.is_valid:
                flagged += 1

        for v in transition_verdicts:
            total += 1
            if not v.is_valid:
                flagged += 1

        for v in statistical_verdicts:
            if v.is_consistent is not None:  # skip unverifiable
                total += 1
                if not v.is_consistent:
                    flagged += 1

        if total == 0:
            return 0.0

        return flagged / total

    @staticmethod
    def _match_claim_to_occupation(
        context: str,
        occupations: List[Tuple[str, Tuple[int, int], str, float]],
        default_soc: str,
    ) -> str:
        """Try to match a statistical claim's context to a specific occupation.

        Simple heuristic: check if any extracted occupation title appears
        in the claim context.  Falls back to ``default_soc``.
        """
        context_lower = context.lower()
        for entity_text, _, matched_soc, _ in occupations:
            if entity_text.lower() in context_lower:
                return matched_soc
        return default_soc
