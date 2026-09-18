"""
Integration test for Enhanced Multi-Agent Market System with Hallucination Guardrails
Validates:
1. EnhancedMarketGraph initializes HallucinationDetector and O*NET KG
2. FusionAgent performs entity grounding and salary consistency checks
3. Multi-agent cross-validation outputs overall_hr and overall_ocs metrics
4. Master CSV and market_versions.json persistence
"""

import pytest
import asyncio
from pathlib import Path
import networkx as nx
import numpy as np

from backend.multi_agent_market import (
    EnhancedMarketGraph,
    FusionAgent,
    ValidationAgent,
    get_market_kg,
    save_market_data_to_csv,
)
from backend.hallucination.detector import HallucinationDetector


def test_get_market_kg_loads():
    """Verify that O*NET Knowledge Graph is loaded from disk"""
    kg = get_market_kg()
    assert kg is not None
    assert isinstance(kg, nx.DiGraph)
    assert len(kg.nodes) > 100


def test_fusion_agent_kg_grounding():
    """Verify that FusionAgent detects and bounds ungrounded estimates"""
    kg = get_market_kg()
    detector = HallucinationDetector(kg) if kg else None
    
    fusion = FusionAgent(llm=None, detector=detector, kg=kg)
    
    # Test record with realistic software developer profile
    profile = {
        "title": "Software Developers",
        "Track": "Software Development",
        "Courses": "Python, JavaScript, Data Structures, Algorithms",
    }
    
    external_data = {
        "job_title": "Software Developers",
        "api_data": {"total_jobs": 45000},
        "sources": ["external_api"]
    }
    
    # LLM proposed an exaggerated salary ($450,000)
    llm_data = {
        "title": "Software Developers",
        "global_job_demand": 50000,
        "salary": "400000 - 500000",
        "missing_skills": "Quantum Computing, Brain Computer Interface, Critical Thinking"
    }
    
    fused = asyncio.run(
        fusion._fuse_record("Software Developers", external_data, llm_data, profile)
    )
    
    assert fused is not None
    assert fused["title"] == "Software Developers"
    assert fused["reliability_score"] >= 0.6
    # Verify that salary was grounded against BLS median wage ($130k range)
    if detector and kg:
        assert fused["salary_max_usd"] < 250000  # bounded away from $500,000 hallucination
        assert "kg_bls_grounding" in fused["data_sources"] or fused["reliability_score"] > 0.5


def test_enhanced_market_graph_audit():
    """Verify EnhancedMarketGraph completes with hallucination audit telemetry"""
    kg = get_market_kg()
    detector = HallucinationDetector(kg) if kg else None
    
    graph = EnhancedMarketGraph(llm=None, detector=detector, kg=kg)
    
    test_profiles = [
        {
            "title": "Data Scientists",
            "Track": "AI & Data Science",
            "Courses": "Python, Machine Learning, SQL, Statistics",
        }
    ]
    
    result = asyncio.run(
        graph.run(test_profiles, year=2026, use_external_data=False, use_llm_generation=False)
    )
    
    assert result["success"] is True
    assert result["total_records"] == 1
    assert "hallucination_metrics" in result
    assert result["hallucination_metrics"]["overall_hr"] >= 0.0
    assert result["hallucination_metrics"]["overall_ocs"] <= 1.0


def test_market_versions_persistence(tmp_path):
    """Verify that save_market_data_to_csv saves files and updates version manifest"""
    test_data = [
        {
            "title": "Cloud Architect",
            "track": "Infrastructure",
            "global_job_demand": 12000,
            "egypt_job_demand": 800,
            "freelancing_opportunities": 1500,
            "salary_min_usd": 90000,
            "salary_max_usd": 150000,
            "reliability_score": 0.88,
            "skills": ["AWS", "Docker"],
            "ai_skills": "AWS, Docker",
            "ai_skills_count": 2,
            "missing_skills": "Kubernetes",
        }
    ]
    
    asyncio.run(save_market_data_to_csv(test_data, year=2026))
    
    manifest = Path("data/market_versions.json")
    assert manifest.exists()
    
    master_csv = Path("data/NewMarketplaceResearchAll82JobTitlePlusSkills.csv")
    assert master_csv.exists()
