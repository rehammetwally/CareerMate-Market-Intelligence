"""
Graph-Structural Hallucination Detection for Career Agents.

Spec 002: Real-time, zero-cost hallucination detection using the O*NET/ESCO
knowledge graph structure as ground truth. Four complementary checks:
  1. Entity grounding against O*NET occupations and elements
  2. Transition validity via skill-overlap edges
  3. Statistical consistency against BLS data
  4. Multi-agent cross-validation for ontological consistency

Core research insight: at the edge, where smaller models hallucinate more
frequently, the KG provides a free, always-available structural oracle.

Modules:
    models                  - Data classes for verdicts and reports
    entity_extractor        - Extract occupation/skill/statistical mentions
    entity_grounding        - Validate entities against KG ground truth
    transition_validity     - Validate career transitions via KG paths
    statistical_consistency - Validate quantitative claims against BLS data
    cross_validation        - Inter-agent ontological consistency
    detector                - Orchestrates all 4 checks
"""

from backend.hallucination.models import (
    EntityVerdict,
    TransitionVerdict,
    StatisticalVerdict,
    CrossValidationResult,
    HallucinationReport,
)
from backend.hallucination.entity_extractor import EntityExtractor
from backend.hallucination.entity_grounding import EntityGroundingChecker
from backend.hallucination.transition_validity import TransitionValidityChecker
from backend.hallucination.statistical_consistency import StatisticalConsistencyChecker
from backend.hallucination.cross_validation import MultiAgentCrossValidator
from backend.hallucination.detector import HallucinationDetector

__all__ = [
    "EntityVerdict",
    "TransitionVerdict",
    "StatisticalVerdict",
    "CrossValidationResult",
    "HallucinationReport",
    "EntityExtractor",
    "EntityGroundingChecker",
    "TransitionValidityChecker",
    "StatisticalConsistencyChecker",
    "MultiAgentCrossValidator",
    "HallucinationDetector",
]
