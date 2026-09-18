"""
Salary Crowdsource Agent
========================

Analyzes salary reports and crowdsourced data to provide:
- Salary bands by location and experience.
- Comparison against market benchmarks.
- Negotiation leverage points.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional

from .base import BaseAgent

logger = logging.getLogger(__name__)


class SalaryCrowdsourceAgent(BaseAgent):
    """Agent specialized in salary analysis"""

    def __init__(self, llm=None):
        super().__init__(llm, name="SalaryCrowdsourceAgent")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze salary data"""
        role = state.get("role", "")
        location = state.get("location", "Global")
        experience = state.get("experience", "3 years")
        
        self.log_info(f"Analyzing salary for {role} in {location}")

        prompt = f"""You are a Compensation & Benefits Specialist.
Analyze the market salary for:
**Role:** {role}
**Location:** {location}
**Experience:** {experience}

Provide a data-driven salary report.

Return ONLY valid JSON:
{{
  "salary_bands": {{
    "low_end": "$X,XXX",
    "median": "$Y,XXX",
    "high_end": "$Z,XXX"
  }},
  "market_sentiment": "High Demand / Stable / Declining",
  "top_paying_industries": ["Industry 1", "Industry 2"],
  "leverage_points": [
    "Specific skill that boosts pay by 20%",
    "Certification impact"
  ],
  "negotiation_advice": "A paragraph on how to negotiate this specific role/location."
}}"""

        try:
            response = await self.invoke_llm(
                prompt,
                system_message="You are a compensation expert. Return only valid JSON."
            )
            cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            result = json.loads(cleaned[start:end+1])

            return {
                "success": True,
                "salary_report": result
            }
        except Exception as e:
            self.log_error(f"Salary analysis failed: {e}")
            return {"success": False, "error": str(e)}


async def run_salary_crowdsource_agent(
    role: str,
    location: str = "Global",
    experience: str = "Junior",
    provider: str = "gemini"
) -> Dict[str, Any]:
    """Runner for SalaryCrowdsourceAgent"""
    try:
        from app import langchain_manager
        llm = langchain_manager.get_llm(provider)
        agent = SalaryCrowdsourceAgent(llm)
        return await agent.process({
            "role": role,
            "location": location,
            "experience": experience
        })
    except Exception as e:
        logger.error(f"Failed to run SalaryCrowdsourceAgent: {e}")
        return {"success": False, "error": str(e)}


__all__ = ["SalaryCrowdsourceAgent", "run_salary_crowdsource_agent"]
