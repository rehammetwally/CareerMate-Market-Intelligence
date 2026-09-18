"""
Data models for the hallucination detection pipeline.

Spec 002, Phase 1 — Frozen dataclasses representing verdicts and reports:

    EntityVerdict          — Verdict for a single entity grounding check.
    TransitionVerdict      — Verdict for a career transition validity check.
    StatisticalVerdict     — Verdict for a statistical claim consistency check.
    CrossValidationResult  — Result of pairwise multi-agent cross-validation.
    HallucinationReport    — Aggregated report from all four checks.

All dataclasses are frozen (immutable) for integrity and determinism.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ─── EntityVerdict ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EntityVerdict:
    """Verdict for a single entity grounding check against the KG.

    Attributes:
        entity_text:         The raw entity text as found in agent output.
        entity_type:         One of 'occupation', 'skill', 'knowledge', 'ability'.
        is_valid:            True if the entity is grounded in the KG.
        confidence:          Match confidence score in [0, 1].
        nearest_match_soc:   SOC code of the nearest KG match (if any).
        nearest_match_score: Similarity score of the nearest match.
    """

    entity_text: str
    entity_type: str
    is_valid: bool
    confidence: float
    nearest_match_soc: Optional[str] = None
    nearest_match_score: Optional[float] = None


# ─── TransitionVerdict ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class TransitionVerdict:
    """Verdict for a career transition validity check.

    Attributes:
        source_soc:    SOC code of the source occupation.
        target_soc:    SOC code of the target occupation.
        is_valid:      True if a valid path exists with sufficient skill overlap.
        skill_overlap: Cosine similarity between source and target feature vectors.
        path_length:   Number of hops in the shortest KG path (-1 if no path).
        path_hops:     List of SOC codes along the path (empty if no path).
    """

    source_soc: str
    target_soc: str
    is_valid: bool
    skill_overlap: float
    path_length: int
    path_hops: List[str]


# ─── StatisticalVerdict ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class StatisticalVerdict:
    """Verdict for a statistical claim consistency check against BLS data.

    When BLS data is unavailable, reference_value, deviation_pct, and
    is_consistent are all None (claim is 'unverifiable', not 'hallucinated').

    Attributes:
        claim_text:      The raw claim text from agent output.
        claim_type:      One of 'salary', 'employment', 'growth'.
        claim_value:     Numerical value extracted from the claim.
        reference_value: BLS reference value (None if unavailable).
        deviation_pct:   Percentage deviation from reference (None if unavailable).
        is_consistent:   True if within tolerance, None if unverifiable.
    """

    claim_text: str
    claim_type: str
    claim_value: float
    reference_value: Optional[float] = None
    deviation_pct: Optional[float] = None
    is_consistent: Optional[bool] = None


# ─── CrossValidationResult ───────────────────────────────────────────────────


@dataclass(frozen=True)
class CrossValidationResult:
    """Result of pairwise multi-agent cross-validation.

    Measures ontological consistency between two agents' outputs by comparing
    the KG regions they reference.

    Attributes:
        agent_a:              Identifier of the first agent.
        agent_b:              Identifier of the second agent.
        consistency_score:    Ontological consistency score in [0, 1].
        conflicting_entities: Entities where agents disagree.
        shared_entities:      Entities both agents reference consistently.
    """

    agent_a: str
    agent_b: str
    consistency_score: float
    conflicting_entities: List[str]
    shared_entities: List[str]


# ─── HallucinationReport ────────────────────────────────────────────────────


@dataclass(frozen=True)
class HallucinationReport:
    """Aggregated hallucination detection report from all four checks.

    Attributes:
        entity_verdicts:          List of per-entity grounding verdicts.
        transition_verdicts:      List of per-transition validity verdicts.
        statistical_verdicts:     List of per-claim statistical verdicts.
        cross_validation_results: List of pairwise cross-validation results.
        overall_hr:               Overall Hallucination Rate in [0, 1].
        overall_ocs:              Overall Ontological Consistency Score in [0, 1].
    """

    entity_verdicts: List[EntityVerdict]
    transition_verdicts: List[TransitionVerdict]
    statistical_verdicts: List[StatisticalVerdict]
    cross_validation_results: List[CrossValidationResult]
    overall_hr: float
    overall_ocs: float
