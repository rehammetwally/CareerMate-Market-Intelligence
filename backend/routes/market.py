"""
Market analysis routes for DEPI Career Advisor API.
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/market", tags=["market"])


# ============= Models =============

class MarketTrend(BaseModel):
    skill: str
    demand_score: float
    trend: str  # "up", "down", "stable"
    avg_salary: int


class JobMatch(BaseModel):
    title: str
    company: str
    match_score: float
    required_skills: List[str]
    salary_range: Dict[str, int]


class FreelanceOpportunity(BaseModel):
    platform: str
    title: str
    budget: str
    skills_required: List[str]
    link: str


# ============= Static Data =============

MARKET_TRENDS = [
    {"skill": "React", "demand_score": 0.92, "trend": "up", "avg_salary": 25000},
    {"skill": "Python", "demand_score": 0.95, "trend": "up", "avg_salary": 30000},
    {"skill": "Machine Learning", "demand_score": 0.88, "trend": "up", "avg_salary": 35000},
    {"skill": "AWS", "demand_score": 0.85, "trend": "stable", "avg_salary": 28000},
    {"skill": "Docker", "demand_score": 0.78, "trend": "stable", "avg_salary": 22000},
    {"skill": "TypeScript", "demand_score": 0.90, "trend": "up", "avg_salary": 24000},
    {"skill": "Flutter", "demand_score": 0.75, "trend": "up", "avg_salary": 20000},
    {"skill": "Data Analysis", "demand_score": 0.82, "trend": "stable", "avg_salary": 18000},
]

FREELANCE_JOBS = [
    {
        "platform": "Upwork",
        "title": "Full Stack Developer Needed",
        "budget": "$50-100/hr",
        "skills_required": ["React", "Node.js", "MongoDB"],
        "link": "https://upwork.com",
    },
    {
        "platform": "Fiverr",
        "title": "Python Script Developer",
        "budget": "$30-75",
        "skills_required": ["Python", "Automation"],
        "link": "https://fiverr.com",
    },
    {
        "platform": "Freelancer",
        "title": "Mobile App Developer",
        "budget": "$500-2000",
        "skills_required": ["Flutter", "iOS", "Android"],
        "link": "https://freelancer.com",
    },
]


# ============= Routes =============

@router.get("/trends", response_model=List[MarketTrend])
async def get_market_trends(
    track: Optional[str] = Query(None, description="Filter by track"),
    limit: int = Query(10, ge=1, le=50),
):
    """Get current market trends for skills."""
    trends = MARKET_TRENDS

    if track:
        track_skills = {
            "Web Development": ["React", "Python", "TypeScript", "Node.js"],
            "Data Science": ["Python", "Machine Learning", "SQL", "Data Analysis"],
            "Mobile": ["Flutter", "React Native", "Swift", "Kotlin"],
        }
        relevant_skills = track_skills.get(track, [])
        trends = [t for t in trends if t["skill"] in relevant_skills]

    return trends[:limit]


@router.get("/jobs", response_model=List[JobMatch])
async def search_jobs(
    query: str = Query(..., description="Job search query"),
    location: Optional[str] = Query(None, description="Job location"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search for jobs matching criteria."""
    # In production, this would query ChromaDB or external APIs
    sample_jobs = [
        {
            "title": "Full Stack Developer",
            "company": "TechCorp Egypt",
            "match_score": 0.85,
            "required_skills": ["React", "Python", "SQL"],
            "salary_range": {"min": 15000, "max": 25000},
        },
        {
            "title": "Junior Python Developer",
            "company": "Startup Labs",
            "match_score": 0.78,
            "required_skills": ["Python", "Django", "PostgreSQL"],
            "salary_range": {"min": 10000, "max": 18000},
        },
        {
            "title": "React Developer",
            "company": "Digital Agency",
            "match_score": 0.72,
            "required_skills": ["React", "JavaScript", "CSS"],
            "salary_range": {"min": 12000, "max": 20000},
        },
    ]

    return sample_jobs[:limit]


@router.get("/freelance", response_model=List[FreelanceOpportunity])
async def get_freelance_opportunities(
    skill: Optional[str] = Query(None, description="Filter by skill"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
):
    """Get freelance opportunities."""
    opportunities = FREELANCE_JOBS

    if skill:
        opportunities = [
            j for j in opportunities
            if skill.lower() in " ".join(j["skills_required"]).lower()
        ]

    if platform:
        opportunities = [j for j in opportunities if j["platform"].lower() == platform.lower()]

    return opportunities


@router.get("/salary-insights")
async def get_salary_insights(
    role: str = Query(..., description="Job role"),
    track: Optional[str] = Query(None, description="Career track"),
):
    """Get salary insights for a role."""
    salary_data = {
        "Full Stack Developer": {
            "junior": {"min": 8000, "max": 15000, "currency": "EGP"},
            "mid": {"min": 15000, "max": 25000, "currency": "EGP"},
            "senior": {"min": 25000, "max": 45000, "currency": "EGP"},
        },
        "Data Scientist": {
            "junior": {"min": 10000, "max": 18000, "currency": "EGP"},
            "mid": {"min": 18000, "max": 30000, "currency": "EGP"},
            "senior": {"min": 30000, "max": 50000, "currency": "EGP"},
        },
    }

    return salary_data.get(role, {
        "junior": {"min": 8000, "max": 15000, "currency": "EGP"},
        "mid": {"min": 15000, "max": 25000, "currency": "EGP"},
        "senior": {"min": 25000, "max": 40000, "currency": "EGP"},
    })