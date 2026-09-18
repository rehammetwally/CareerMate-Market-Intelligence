"""
Market Research Agent
=====================

Specializes in analyzing job market data:
- Global and Egypt job demand estimation
- Platform distribution (LinkedIn, Upwork, etc.)
- Growth trend predictions
- Market attractiveness rating
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

from .base import BaseAgent

logger = logging.getLogger(__name__)


class MarketResearchAgent(BaseAgent):
    """Agent specialized in market research and job demand analysis"""
    
    def __init__(self, llm):
        super().__init__(llm, name="MarketResearchAgent")
        
        self.system_prompt = """You are an expert labor market analyst specializing in job demand research.
Your task is to analyze job profiles and provide accurate market data estimates.

Focus on:
1. Global job demand (worldwide positions available)
2. Egypt-specific job demand
3. Freelancing opportunities
4. Platform distribution percentages (LinkedIn, Upwork, Indeed, etc.)
5. Growth trends for 2025-2030
6. Market attractiveness rating (1-5 scale)

Use realistic estimates based on current market data. Never return 0 for active job roles."""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process job profiles and generate market data"""
        self.log_info("Starting market research analysis...")
        
        job_profiles = state.get("job_profiles", [])
        year = state.get("year", 2026)
        batch_size = state.get("batch_size", 5)
        
        if not job_profiles:
            self.log_error("No job profiles provided")
            state["errors"].append("MarketResearchAgent: No job profiles")
            return state
        
        market_data = []
        
        # Process in batches
        for i in range(0, len(job_profiles), batch_size):
            batch = job_profiles[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(job_profiles) + batch_size - 1) // batch_size
            
            self.log_info(f"Processing batch {batch_num}/{total_batches}")
            
            try:
                batch_result = await self._process_batch(batch, year)
                market_data.extend(batch_result)
            except Exception as e:
                self.log_error(f"Batch {batch_num} failed: {e}")
                state["errors"].append(f"MarketResearchAgent batch {batch_num}: {str(e)}")
        
        state["market_data"] = market_data
        self.log_info(f"Completed market research for {len(market_data)} jobs")
        
        return state
    
    async def _process_batch(self, batch: List[Dict], year: int) -> List[Dict]:
        """Process a batch of job profiles"""
        
        prompt = f"""Analyze these job profiles and provide market data for {year}.

Job Profiles:
{json.dumps(batch, indent=2, ensure_ascii=False)}

For EACH job, return a JSON object with these exact keys:
- title: exact job title from input
- global_job_demand: integer (worldwide positions, estimate if needed)
- egypt_job_demand: integer (Egypt positions)
- freelancing_opportunities: integer (freelance listings)
- linkedin_distribution: string percentage (e.g., "35%")
- ziprecruiter_distribution: string percentage
- upwork_distribution: string percentage
- khamsat_distribution: string percentage
- mostakel_distribution: string percentage
- freelancer_distribution: string percentage
- indeed_distribution: string percentage
- growth_trend_2025_2030: string (e.g., "High growth (+22%)")
- market_attractiveness_rating: integer 1-5

Return ONLY a valid JSON array. No markdown, no explanation."""

        response = await self.invoke_llm(prompt, self.system_prompt)
        
        # Parse JSON response
        return self._parse_response(response)
    
    def _parse_response(self, response: str) -> List[Dict]:
        """Parse LLM response to extract JSON data"""
        try:
            # Clean markdown if present
            cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()
            
            # Find JSON array
            start = cleaned.find('[')
            end = cleaned.rfind(']')
            
            if start != -1 and end != -1:
                json_str = cleaned[start:end + 1]
                return json.loads(json_str)
            
            # Try direct parse
            return json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            self.log_error(f"JSON parse error: {e}")
            # Attempt repair using json_repair if available
            try:
                from json_repair import repair_json
                repaired = repair_json(response, return_objects=True)
                if isinstance(repaired, list):
                    return repaired
            except ImportError:
                pass
            
            return []


async def create_market_agent(llm) -> MarketResearchAgent:
    """Factory function to create a MarketResearchAgent"""
    return MarketResearchAgent(llm)
