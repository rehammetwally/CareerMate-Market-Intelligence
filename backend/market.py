# market.py - النسخة المصححة
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
from pathlib import Path
import json
import ast
import re
import asyncio
import csv
import logging
from datetime import datetime, timezone

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

router = APIRouter()
logger = logging.getLogger(__name__)

CSV_FILE_PATH = Path("data/MarketplaceResearchAll82JobTitlePlusSkills.csv")
NEW_CSV_FILE_PATH = Path(
    "data/NewMarketplaceResearchAll82JobTitlePlusSkills.csv"
)  # Legacy default
MARKET_SOURCES_PATH = Path("data/market_sources.json")

TRUSTED_SOURCE_DOMAINS = {
    "weforum.org",
    "reports.weforum.org",
    "mckinsey.com",
    "linkedin.com",
    "news.linkedin.com",
    "oecd.org",
    "tuac.org",
}


def get_year_csv_path(year: int = 2026) -> Path:
    """Get CSV path for a specific year"""
    return Path(f"data/NewMarketplaceResearchAll82JobTitlePlusSkills_{year}.csv")


def clean_numeric_value(value):
    """تحويل القيمة لرقم مع معالجة الحالات الخاصة"""
    if pd.isna(value) or value == "" or value is None:
        return 0

    if isinstance(value, (int, float)):
        if np.isinf(value) or np.isnan(value):
            return 0
        return float(value)

    if isinstance(value, str):
        value = value.replace(",", "").replace(" ", "").strip()

        value_lower = value.lower()
        if value_lower in ["high", "very high", "excellent"]:
            return 8000
        elif value_lower in ["medium", "moderate", "good"]:
            return 5000
        elif value_lower in ["low", "poor"]:
            return 2000

        try:
            numeric_str = re.sub(r"[^\d.]", "", value)
            if numeric_str:
                return float(numeric_str)
        except:
            pass

    return 0


def convert_columns_to_numeric(df, columns):
    """تحويل أعمدة معينة لأرقام"""
    for col in columns:
        if col in df.columns:
            logger.info(f"Converting column '{col}' to numeric...")
            df[col] = df[col].apply(clean_numeric_value)
    return df


def extract_skills_list(skills_str, count):
    """استخراج المهارات من string"""
    if pd.isna(skills_str) or skills_str == 0 or not skills_str:
        return []

    try:
        if isinstance(skills_str, str):
            if skills_str.startswith("["):
                skills = ast.literal_eval(skills_str)
            else:
                skills = [s.strip() for s in skills_str.split(",")]
        else:
            skills = []

        return skills[: int(count)] if count > 0 else skills
    except:
        return []


def load_and_prepare_dataframe():
    """تحميل وتحضير الـ DataFrame"""
    # Prefer generated CSV if it exists
    path_to_use = NEW_CSV_FILE_PATH if NEW_CSV_FILE_PATH.exists() else CSV_FILE_PATH

    if not path_to_use.exists():
        raise FileNotFoundError(f"CSV file not found at {path_to_use}")

    logger.info(f"📂 Loading data from: {path_to_use}")
    df = pd.read_csv(path_to_use)
    logger.info(f"✅ CSV loaded: {len(df)} rows")

    numeric_columns = [
        "Global_Job_Demand",
        "Egypt_Job_Demand",
        "Freelancing_Opportunities",
        "Linkedin_Distribution",
        "Ziprecruiter_Distribution",
        "Upwork_Distribution",
        "Khamsat_Distribution",
        "Mostakel_Distribution",
        "Freelancer_Distribution",
        "Indeed_Distribution",
        "Market_Attractiveness_Rating",
        "AI_Skills_Count",
    ]

    # Ensure all expected columns exist with defaults
    expected_defaults = {
        "Global_Job_Demand": 1000,
        "Egypt_Job_Demand": 100,
        "Freelancing_Opportunities": 500,
        "Linkedin_Distribution": "30%",
        "Ziprecruiter_Distribution": "10%",
        "Upwork_Distribution": "25%",
        "Khamsat_Distribution": "5%",
        "Mostakel_Distribution": "5%",
        "Freelancer_Distribution": "10%",
        "Indeed_Distribution": "15%",
        "Market_Attractiveness_Rating": 4,
        "AI_Skills_Count": 5,
        "AI_Extracted_Skills": "[]",
        "Missing_Skills": "None",
        "Title": "Technology Specialist",
        "Track": "Software Engineering",
        "Courses": "General Technology Curriculum",
        "Description": "Technology professional",
        "Rank": 1,
        "Justify_Ranking": "Ranked based on global industry demand",
        "Growth_Trend_2025_2030": "High growth (+20%)",
    }
    for col, default_val in expected_defaults.items():
        if col not in df.columns:
            df[col] = default_val

    numeric_columns = [
        "Global_Job_Demand",
        "Egypt_Job_Demand",
        "Freelancing_Opportunities",
        "Linkedin_Distribution",
        "Ziprecruiter_Distribution",
        "Upwork_Distribution",
        "Khamsat_Distribution",
        "Mostakel_Distribution",
        "Freelancer_Distribution",
        "Indeed_Distribution",
        "Market_Attractiveness_Rating",
        "AI_Skills_Count",
    ]

    df = convert_columns_to_numeric(df, numeric_columns)
    df = df.fillna(0)
    df = df.replace([np.inf, -np.inf], 0)

    return df


def load_market_sources() -> list[dict]:
    """Load curated external market sources (optional)."""
    if not MARKET_SOURCES_PATH.exists():
        return []

    try:
        with open(MARKET_SOURCES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            normalized = []
            seen_urls = set()
            for item in data:
                if not isinstance(item, dict):
                    continue

                url = str(item.get("url", "")).strip()
                url = re.sub(r"\[[0-9]+\]", "", url)
                if not url.startswith("http"):
                    continue

                domain = str(item.get("domain", "")).strip().lower().replace("www.", "")
                if not domain:
                    try:
                        domain = url.split("/")[2].lower().replace("www.", "")
                    except Exception:
                        domain = ""

                is_trusted = domain in TRUSTED_SOURCE_DOMAINS or any(
                    domain.endswith(f".{d}") for d in TRUSTED_SOURCE_DOMAINS
                )
                reliability = "high" if is_trusted else "review"

                if url.lower() in seen_urls:
                    continue
                seen_urls.add(url.lower())

                normalized.append(
                    {
                        "title": str(item.get("title", url)).strip()[:180],
                        "url": url,
                        "domain": domain,
                        "reliability": reliability,
                        "alive": item.get("alive"),
                        "http_status": item.get("http_status"),
                        "last_checked": item.get("last_checked"),
                        "check_error": item.get("check_error"),
                        "note": str(
                            item.get(
                                "note",
                                "Imported from curated market sources",
                            )
                        ),
                    }
                )

            return normalized
    except Exception as e:
        logger.warning(f"Failed to load market sources file: {e}")
    return []


def split_sources_by_reliability(sources: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split sources into high-reliability and review-required buckets."""
    high = []
    review = []
    for item in sources:
        if not isinstance(item, dict):
            continue
        if str(item.get("reliability", "review")).lower() == "high":
            high.append(item)
        else:
            review.append(item)
    return high, review


def compute_source_confidence_score(sources: list[dict]) -> float:
    """Compute source confidence [0,100], excluding dead links from trusted count."""
    total_count = len(sources)
    if total_count <= 0:
        return 0.0

    trusted_effective = 0
    for s in sources:
        if not isinstance(s, dict):
            continue
        is_high = str(s.get("reliability", "review")).lower() == "high"
        is_dead = s.get("alive") is False
        if is_high and not is_dead:
            trusted_effective += 1

    return round((trusted_effective / total_count) * 100.0, 1)


def summarize_health(sources: list[dict]) -> dict:
    """Summarize alive/dead/unchecked source status."""
    alive = 0
    dead = 0
    unchecked = 0
    for s in sources:
        state = s.get("alive") if isinstance(s, dict) else None
        if state is True:
            alive += 1
        elif state is False:
            dead += 1
        else:
            unchecked += 1
    return {"alive": alive, "dead": dead, "unchecked": unchecked}


def _is_recent_iso_datetime(value: str, days_threshold: int = 30) -> bool:
    """Return True if ISO datetime is within threshold days."""
    if not value:
        return False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - dt).days
        return age_days <= days_threshold
    except Exception:
        return False


def compute_evidence_novelty_metrics(sources: list[dict]) -> dict:
    """Evidence-aware market reliability metrics (novel contribution)."""
    total = len(sources)
    if total == 0:
        return {
            "evidence_robustness_score": 0.0,
            "trust_coverage": 0.0,
            "liveness_ratio": 0.0,
            "domain_diversity": 0.0,
            "freshness_ratio": 0.0,
        }

    high_sources = [
        s
        for s in sources
        if isinstance(s, dict) and str(s.get("reliability", "review")).lower() == "high"
    ]
    alive_sources = [
        s for s in sources if isinstance(s, dict) and s.get("alive") is True
    ]
    unique_domains = {
        s.get("domain")
        for s in sources
        if isinstance(s, dict) and str(s.get("domain", "")).strip()
    }
    fresh_sources = [
        s
        for s in sources
        if isinstance(s, dict)
        and _is_recent_iso_datetime(str(s.get("last_checked") or ""), 30)
    ]

    trust_coverage = len(high_sources) / total
    liveness_ratio = len(alive_sources) / total
    domain_diversity = min(len(unique_domains) / 6.0, 1.0)
    freshness_ratio = len(fresh_sources) / total

    robustness = (
        0.4 * trust_coverage
        + 0.3 * liveness_ratio
        + 0.2 * domain_diversity
        + 0.1 * freshness_ratio
    )

    return {
        "evidence_robustness_score": round(robustness * 100.0, 1),
        "trust_coverage": round(trust_coverage * 100.0, 1),
        "liveness_ratio": round(liveness_ratio * 100.0, 1),
        "domain_diversity": round(domain_diversity * 100.0, 1),
        "freshness_ratio": round(freshness_ratio * 100.0, 1),
    }


def compute_source_quality_score(source: dict) -> float:
    """Per-source evidence score [0,100] for gating."""
    if not isinstance(source, dict):
        return 0.0

    reliability = (
        1.0 if str(source.get("reliability", "review")).lower() == "high" else 0.3
    )

    alive_state = source.get("alive")
    if alive_state is True:
        liveness = 1.0
    elif alive_state is False:
        liveness = 0.0
    else:
        liveness = 0.6

    freshness = (
        1.0
        if _is_recent_iso_datetime(str(source.get("last_checked") or ""), 30)
        else 0.4
    )

    score = 0.5 * reliability + 0.3 * liveness + 0.2 * freshness
    return round(score * 100.0, 1)


def apply_evidence_gating(
    sources: list[dict],
    min_source_quality: float = 60.0,
    include_review: bool = False,
) -> tuple[list[dict], list[dict]]:
    """Filter sources by quality score and optional reliability gate."""
    accepted = []
    rejected = []

    for s in sources:
        if not isinstance(s, dict):
            continue

        source = dict(s)
        source["source_quality_score"] = compute_source_quality_score(source)
        is_high = str(source.get("reliability", "review")).lower() == "high"

        pass_quality = source["source_quality_score"] >= float(min_source_quality)
        pass_reliability = include_review or is_high

        if pass_quality and pass_reliability:
            accepted.append(source)
        else:
            rejected.append(source)

    return accepted, rejected


async def check_source_health(url: str, timeout_s: float = 8.0) -> dict:
    """Check URL health using HEAD with GET fallback."""
    import httpx

    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout_s,
            headers={"User-Agent": "CareerMateSourceValidator/1.0"},
        ) as client:
            response = await client.head(url)
            if response.status_code in (405, 403):
                response = await client.get(url)

        alive = 200 <= response.status_code < 400
        return {
            "alive": alive,
            "http_status": int(response.status_code),
            "last_checked": checked_at,
            "check_error": None,
        }
    except Exception as e:
        return {
            "alive": False,
            "http_status": None,
            "last_checked": checked_at,
            "check_error": str(e),
        }


@router.get("/init")
async def market_init():
    """Initialize market page data"""
    try:
        df = load_and_prepare_dataframe()

        tracks = []
        if "Track" in df.columns:
            tracks = df["Track"].dropna().unique().tolist()

        return {
            "success": True,
            "total_jobs": len(df),
            "tracks": tracks,
            "market_available": True,
            "message": "Market data initialized successfully",
            "initialText": "Market Trends Analysis ready. Explore the latest career demands.",
        }
    except Exception as e:
        logger.error(f"Error in market init: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "total_jobs": 0,
                "tracks": [],
                "market_available": False,
            },
        )


_MARKET_CHARTS_CACHE = {
    "data": None,
    "cached_at": None,
    "ttl_seconds": 180,  # 3 minutes cache for fast edge queries
}


@router.get("/charts")
async def get_market_charts(force_refresh: bool = Query(False)):
    """قراءة بيانات السوق من CSV وإرجاع بيانات للـ Charts مع دعم الـ In-Memory Caching"""
    try:
        now = datetime.now()
        if not force_refresh and _MARKET_CHARTS_CACHE["data"] is not None and _MARKET_CHARTS_CACHE["cached_at"] is not None:
            age = (now - _MARKET_CHARTS_CACHE["cached_at"]).total_seconds()
            if age < _MARKET_CHARTS_CACHE["ttl_seconds"]:
                logger.info(f"⚡ Returning cached market charts ({age:.1f}s old)")
                return _MARKET_CHARTS_CACHE["data"]

        df = load_and_prepare_dataframe()

        # 1. Top Jobs by Global Demand
        logger.info("📊 Processing top jobs...")
        top_jobs_data = df.nlargest(10, "Global_Job_Demand")[
            [
                "Title",
                "Track",
                "Global_Job_Demand",
                "Egypt_Job_Demand",
                "Market_Attractiveness_Rating",
            ]
        ].copy()

        top_jobs = []
        for _, row in top_jobs_data.iterrows():
            top_jobs.append(
                {
                    "job_title": str(row["Title"]),
                    "track": str(row["Track"]),
                    "global_demand": int(row["Global_Job_Demand"]),
                    "egypt_demand": int(row["Egypt_Job_Demand"]),
                    "rating": float(row["Market_Attractiveness_Rating"]),
                }
            )

        # 2. Skills Distribution
        logger.info("📊 Processing skills...")
        all_skills = {}
        for _, row in df.iterrows():
            skills = extract_skills_list(
                row.get("AI_Extracted_Skills", ""), row.get("AI_Skills_Count", 0)
            )
            demand = row["Global_Job_Demand"]

            for skill in skills:
                if skill and skill.strip():
                    skill = skill.strip()
                    all_skills[skill] = all_skills.get(skill, 0) + demand

        top_skills = [
            {"skill_name": skill, "demand": int(demand)}
            for skill, demand in sorted(
                all_skills.items(), key=lambda x: x[1], reverse=True
            )[:8]
        ]

        # 3. Track Analysis
        logger.info("📊 Processing track analysis...")
        track_data = (
            df.groupby("Track")
            .agg(
                {
                    "Global_Job_Demand": "sum",
                    "Egypt_Job_Demand": "sum",
                    "Market_Attractiveness_Rating": "mean",
                    "Freelancing_Opportunities": "mean",
                }
            )
            .reset_index()
        )

        track_analysis = []
        for _, row in track_data.iterrows():
            track_analysis.append(
                {
                    "track": str(row["Track"]),
                    "global_demand": int(row["Global_Job_Demand"]),
                    "egypt_demand": int(row["Egypt_Job_Demand"]),
                    "avg_rating": float(row["Market_Attractiveness_Rating"]),
                    "freelancing_score": float(row["Freelancing_Opportunities"]),
                }
            )

        # 4. Platform Distribution
        logger.info("📊 Processing platform distribution...")
        platform_columns = [
            "Linkedin_Distribution",
            "Ziprecruiter_Distribution",
            "Upwork_Distribution",
            "Indeed_Distribution",
            "Khamsat_Distribution",
            "Mostakel_Distribution",
            "Freelancer_Distribution",
        ]

        platform_distribution = []
        for col in platform_columns:
            if col in df.columns:
                platform_name = col.replace("_Distribution", "")
                avg_value = float(df[col].mean())
                platform_distribution.append(
                    {"platform": platform_name, "value": avg_value}
                )

        # 5. Growth Trends
        logger.info("📊 Processing growth trends...")
        growth_categories = []
        if "Growth_Trend_2025_2030" in df.columns:
            growth_counts = df["Growth_Trend_2025_2030"].value_counts().to_dict()
            for trend, count in growth_counts.items():
                if (
                    trend
                    and str(trend).strip()
                    and str(trend).lower() not in ["0", "nan", "none"]
                ):
                    growth_categories.append({"trend": str(trend), "count": int(count)})

        # 6. Overall Statistics
        stats = {
            "total_jobs": int(len(df)),
            "total_global_demand": int(df["Global_Job_Demand"].sum()),
            "total_egypt_demand": int(df["Egypt_Job_Demand"].sum()),
            "avg_market_rating": float(df["Market_Attractiveness_Rating"].mean()),
            "avg_freelancing_score": float(df["Freelancing_Opportunities"].mean()),
            "total_tracks": int(df["Track"].nunique()),
            "total_skills": len(all_skills),
        }

        # 7. Top Jobs in Egypt
        logger.info("📊 Processing top Egypt jobs...")
        top_egypt_jobs = []
        egypt_top = df.nlargest(10, "Egypt_Job_Demand")[
            ["Title", "Egypt_Job_Demand", "Track"]
        ].copy()
        for _, row in egypt_top.iterrows():
            top_egypt_jobs.append(
                {
                    "job_title": str(row["Title"]),
                    "demand": int(row["Egypt_Job_Demand"]),
                    "track": str(row["Track"]),
                }
            )

        # 8. Curated source summary (optional)
        sources = load_market_sources()
        high_sources, review_sources = split_sources_by_reliability(sources)
        source_domains = sorted(
            {
                item.get("domain")
                for item in high_sources
                if isinstance(item, dict) and item.get("domain")
            }
        )

        source_confidence = compute_source_confidence_score(sources)
        health = summarize_health(high_sources)
        evidence_metrics = compute_evidence_novelty_metrics(sources)

        # Build response
        response = {
            "success": True,
            "data": {
                "statistics": stats,
                "top_jobs": top_jobs,
                "top_egypt_jobs": top_egypt_jobs,
                "top_skills": top_skills,
                "track_analysis": track_analysis,
                "platform_distribution": platform_distribution,
                "growth_trends": growth_categories,
                "sources_summary": {
                    "total_sources": len(sources),
                    "high_reliability_sources": len(high_sources),
                    "review_sources": len(review_sources),
                    "source_confidence_score": source_confidence,
                    "health": health,
                    "domains": source_domains,
                },
                "evidence_metrics": evidence_metrics,
            },
        }

        logger.info("✅ Response prepared successfully! Updating cache.")
        _MARKET_CHARTS_CACHE["data"] = response
        _MARKET_CHARTS_CACHE["cached_at"] = now
        return response

    except FileNotFoundError as e:
        logger.error(f"❌ File Error: {e}")
        return JSONResponse(
            status_code=404, content={"success": False, "error": str(e), "data": {}}
        )
    except Exception as e:
        import traceback

        logger.error(f"❌ Error: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e), "data": {}}
        )


@router.get("/sources")
async def get_market_sources(
    include_review: bool = Query(False),
    use_gating: bool = Query(True),
    min_source_quality: float = Query(60.0, ge=0.0, le=100.0),
):
    """Return curated reliable market-report sources used for analysis context."""
    try:
        sources = load_market_sources()
        high_sources, review_sources = split_sources_by_reliability(sources)
        base_sources = sources if include_review else high_sources
        if use_gating:
            effective_sources, rejected_sources = apply_evidence_gating(
                base_sources,
                min_source_quality=min_source_quality,
                include_review=include_review,
            )
        else:
            effective_sources, rejected_sources = base_sources, []
        health = summarize_health(effective_sources)

        return {
            "success": True,
            "total_sources": len(effective_sources),
            "rejected_sources": len(rejected_sources),
            "high_reliability_sources": len(high_sources),
            "review_sources": len(review_sources),
            "source_confidence_score": compute_source_confidence_score(sources),
            "health": health,
            "evidence_metrics": compute_evidence_novelty_metrics(sources),
            "include_review": include_review,
            "use_gating": use_gating,
            "min_source_quality": min_source_quality,
            "sources": effective_sources,
        }
    except Exception as e:
        logger.error(f"Error loading market sources: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "sources": []},
        )


@router.get("/sources/validate")
async def validate_market_sources():
    """Validate source set and report trusted vs review buckets."""
    try:
        sources = load_market_sources()
        high_sources, review_sources = split_sources_by_reliability(sources)
        health = summarize_health(sources)

        return {
            "success": True,
            "total_sources": len(sources),
            "high_reliability_sources": len(high_sources),
            "review_sources": len(review_sources),
            "source_confidence_score": compute_source_confidence_score(sources),
            "health": health,
            "evidence_metrics": compute_evidence_novelty_metrics(sources),
            "trusted_domains": sorted(TRUSTED_SOURCE_DOMAINS),
            "review_source_domains": sorted(
                {
                    s.get("domain")
                    for s in review_sources
                    if isinstance(s, dict) and s.get("domain")
                }
            ),
        }
    except Exception as e:
        logger.error(f"Error validating market sources: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@router.get("/sources/ablation")
async def source_ablation(min_source_quality: float = Query(60.0, ge=0.0, le=100.0)):
    """Ablation over source filtering policies for novelty reporting."""
    try:
        sources = load_market_sources()
        high_sources, _ = split_sources_by_reliability(sources)

        baseline_all = sources
        trust_only = high_sources
        trust_alive = [
            s
            for s in high_sources
            if isinstance(s, dict) and s.get("alive") is not False
        ]
        ers_gated, _ = apply_evidence_gating(
            high_sources,
            min_source_quality=min_source_quality,
            include_review=False,
        )

        def summarize_policy(name: str, policy_sources: list[dict]) -> dict:
            return {
                "policy": name,
                "kept_sources": len(policy_sources),
                "source_confidence_score": compute_source_confidence_score(
                    policy_sources
                ),
                "health": summarize_health(policy_sources),
                "evidence_metrics": compute_evidence_novelty_metrics(policy_sources),
            }

        return {
            "success": True,
            "min_source_quality": min_source_quality,
            "ablation": [
                summarize_policy("baseline_all", baseline_all),
                summarize_policy("trust_only", trust_only),
                summarize_policy("trust_alive", trust_alive),
                summarize_policy("ers_gated", ers_gated),
            ],
        }
    except Exception as e:
        logger.error(f"Error running source ablation: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.post("/sources/ablation/export")
async def export_source_ablation(
    min_source_quality: float = Query(60.0, ge=0.0, le=100.0),
):
    """Export ablation results to JSON and CSV for paper tables."""
    try:
        ablation_result = await source_ablation(min_source_quality=min_source_quality)
        if isinstance(ablation_result, JSONResponse):
            return ablation_result

        if not ablation_result.get("success"):
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Ablation generation failed"},
            )

        rows = ablation_result.get("ablation", [])
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        out_dir = Path("data/experiment_results")
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / f"source_ablation_{ts}.json"
        csv_path = out_dir / f"source_ablation_{ts}.csv"
        latest_json = out_dir / "source_ablation_latest.json"
        latest_csv = out_dir / "source_ablation_latest.csv"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ablation_result, f, indent=2, ensure_ascii=False)
        with open(latest_json, "w", encoding="utf-8") as f:
            json.dump(ablation_result, f, indent=2, ensure_ascii=False)

        csv_fields = [
            "policy",
            "kept_sources",
            "source_confidence_score",
            "health_alive",
            "health_dead",
            "health_unchecked",
            "ers",
            "trust_coverage",
            "liveness_ratio",
            "domain_diversity",
            "freshness_ratio",
        ]

        flat_rows = []
        for r in rows:
            em = r.get("evidence_metrics", {}) if isinstance(r, dict) else {}
            h = r.get("health", {}) if isinstance(r, dict) else {}
            flat_rows.append(
                {
                    "policy": r.get("policy"),
                    "kept_sources": r.get("kept_sources"),
                    "source_confidence_score": r.get("source_confidence_score"),
                    "health_alive": h.get("alive", 0),
                    "health_dead": h.get("dead", 0),
                    "health_unchecked": h.get("unchecked", 0),
                    "ers": em.get("evidence_robustness_score", 0),
                    "trust_coverage": em.get("trust_coverage", 0),
                    "liveness_ratio": em.get("liveness_ratio", 0),
                    "domain_diversity": em.get("domain_diversity", 0),
                    "freshness_ratio": em.get("freshness_ratio", 0),
                }
            )

        for path in [csv_path, latest_csv]:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=csv_fields)
                writer.writeheader()
                writer.writerows(flat_rows)

        baseline = next(
            (r for r in flat_rows if r.get("policy") == "baseline_all"), None
        )
        ers_gated = next((r for r in flat_rows if r.get("policy") == "ers_gated"), None)
        delta = {}
        if baseline and ers_gated:
            delta = {
                "ers_delta": round(float(ers_gated["ers"]) - float(baseline["ers"]), 2),
                "confidence_delta": round(
                    float(ers_gated["source_confidence_score"])
                    - float(baseline["source_confidence_score"]),
                    2,
                ),
                "kept_sources_delta": int(ers_gated["kept_sources"])
                - int(baseline["kept_sources"]),
            }

        return {
            "success": True,
            "message": "Source ablation exported successfully",
            "min_source_quality": min_source_quality,
            "json_path": str(json_path),
            "csv_path": str(csv_path),
            "latest_json_path": str(latest_json),
            "latest_csv_path": str(latest_csv),
            "summary_delta": delta,
        }
    except Exception as e:
        logger.error(f"Error exporting source ablation: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@router.post("/sources/revalidate")
async def revalidate_market_sources(
    include_review: bool = Query(False),
    timeout_s: float = Query(8.0, ge=2.0, le=30.0),
):
    """Re-check source URLs and persist health metadata."""
    try:
        sources = load_market_sources()
        high_sources, _ = split_sources_by_reliability(sources)
        targets = sources if include_review else high_sources

        if not targets:
            return {
                "success": True,
                "checked": 0,
                "message": "No sources to validate",
                "health": summarize_health([]),
            }

        semaphore = asyncio.Semaphore(5)

        async def _bounded_check(item: dict):
            async with semaphore:
                result = await check_source_health(item.get("url", ""), timeout_s)
                merged = {**item, **result}
                return merged

        checked_targets = await asyncio.gather(*[_bounded_check(s) for s in targets])
        checked_by_url = {s.get("url", ""): s for s in checked_targets}

        merged_all = []
        for s in sources:
            key = s.get("url", "") if isinstance(s, dict) else ""
            if key in checked_by_url:
                merged_all.append(checked_by_url[key])
            else:
                merged_all.append(s)

        with open(MARKET_SOURCES_PATH, "w", encoding="utf-8") as f:
            json.dump(merged_all, f, indent=2, ensure_ascii=False)

        health = summarize_health(checked_targets)

        return {
            "success": True,
            "checked": len(checked_targets),
            "include_review": include_review,
            "timeout_s": timeout_s,
            "health": health,
            "source_confidence_score": compute_source_confidence_score(merged_all),
            "evidence_metrics": compute_evidence_novelty_metrics(merged_all),
            "updated_file": str(MARKET_SOURCES_PATH),
        }
    except Exception as e:
        logger.error(f"Error revalidating market sources: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.get("/tracks")
async def get_all_tracks():
    """Get all available tracks"""
    try:
        df = load_and_prepare_dataframe()

        if "Track" in df.columns:
            tracks = df["Track"].dropna().unique().tolist()

            track_details = []
            for track in tracks:
                track_df = df[df["Track"] == track]
                track_details.append(
                    {
                        "name": track,
                        "job_count": len(track_df),
                        "avg_rating": float(
                            track_df["Market_Attractiveness_Rating"].mean()
                        ),
                        "total_demand": int(track_df["Global_Job_Demand"].sum()),
                    }
                )

            return {"success": True, "tracks": track_details, "total": len(tracks)}

        return {"success": False, "error": "Track column not found", "tracks": []}

    except Exception as e:
        logger.error(f"Error getting tracks: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e), "tracks": []}
        )


@router.get("/track/{track_name}")
async def get_track_details(track_name: str):
    """Get details for a specific track"""
    try:
        df = load_and_prepare_dataframe()
        track_df = df[df["Track"] == track_name]

        if len(track_df) == 0:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Track '{track_name}' not found"},
            )

        jobs = []
        for _, row in track_df.iterrows():
            jobs.append(
                {
                    "title": str(row["Title"]),
                    "description": str(row.get("Description", "")),
                    "global_demand": int(row["Global_Job_Demand"]),
                    "egypt_demand": int(row["Egypt_Job_Demand"]),
                    "rating": float(row["Market_Attractiveness_Rating"]),
                    "skills": extract_skills_list(
                        row.get("AI_Extracted_Skills", ""),
                        row.get("AI_Skills_Count", 0),
                    ),
                }
            )

        return {
            "success": True,
            "track": track_name,
            "job_count": len(jobs),
            "jobs": jobs,
            "statistics": {
                "total_global_demand": int(track_df["Global_Job_Demand"].sum()),
                "total_egypt_demand": int(track_df["Egypt_Job_Demand"].sum()),
                "avg_rating": float(track_df["Market_Attractiveness_Rating"].mean()),
            },
        }

    except Exception as e:
        logger.error(f"Error getting track details: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.get("/search")
async def search_jobs(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search for jobs in market data"""
    try:
        df = load_and_prepare_dataframe()
        query_lower = query.lower()

        mask = (
            df["Title"].str.lower().str.contains(query_lower, na=False)
            | df.get("Description", pd.Series(dtype=str))
            .str.lower()
            .str.contains(query_lower, na=False)
            | df.get("AI_Extracted_Skills", pd.Series(dtype=str))
            .str.lower()
            .str.contains(query_lower, na=False)
        )

        results_df = df[mask].head(limit)

        results = []
        for _, row in results_df.iterrows():
            results.append(
                {
                    "title": str(row["Title"]),
                    "track": str(row["Track"]),
                    "description": str(row.get("Description", "")),
                    "global_demand": int(row["Global_Job_Demand"]),
                    "egypt_demand": int(row["Egypt_Job_Demand"]),
                    "rating": float(row["Market_Attractiveness_Rating"]),
                    "skills": extract_skills_list(
                        row.get("AI_Extracted_Skills", ""),
                        row.get("AI_Skills_Count", 0),
                    ),
                }
            )

        return {
            "success": True,
            "query": query,
            "total_found": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e), "results": []}
        )


@router.get("/top-skills")
async def get_top_skills(limit: int = Query(20, ge=1, le=100)):
    """Get top skills by demand"""
    try:
        df = load_and_prepare_dataframe()

        all_skills = {}
        for _, row in df.iterrows():
            skills = extract_skills_list(
                row.get("AI_Extracted_Skills", ""), row.get("AI_Skills_Count", 0)
            )
            demand = row["Global_Job_Demand"]

            for skill in skills:
                if skill and skill.strip():
                    skill = skill.strip()
                    all_skills[skill] = all_skills.get(skill, 0) + demand

        top_skills = [
            {
                "skill_name": skill,
                "total_demand": int(demand),
                "job_count": sum(
                    1
                    for _, row in df.iterrows()
                    if skill
                    in extract_skills_list(
                        row.get("AI_Extracted_Skills", ""),
                        row.get("AI_Skills_Count", 0),
                    )
                ),
            }
            for skill, demand in sorted(
                all_skills.items(), key=lambda x: x[1], reverse=True
            )[:limit]
        ]

        return {
            "success": True,
            "total_skills": len(all_skills),
            "top_skills": top_skills,
        }

    except Exception as e:
        logger.error(f"Error getting top skills: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "top_skills": []},
        )


@router.post("/refresh_data")
async def refresh_market_data(
    year: int = 2026, force_provider: str = None, use_agents: bool = True
):
    """Regenerate market data using multi-agent system or legacy single-LLM mode"""
    try:
        # Try multi-agent system first (if enabled)
        if use_agents:
            try:
                from agents.supervisor import run_market_research_agents

                logger.info("🤖 Starting Multi-Agent Market Research...")
                result = await run_market_research_agents(
                    year=year, force_provider=force_provider
                )
                if result.get("success"):
                    return result
                else:
                    logger.warning(
                        f"⚠️ Multi-agent failed: {result.get('error')}. Falling back to legacy mode."
                    )
            except ImportError as e:
                logger.warning(
                    f"⚠️ Multi-agent system not available: {e}. Using legacy mode."
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Multi-agent error: {e}. Falling back to legacy mode."
                )

        # Legacy single-LLM mode (fallback)
        from app import langchain_manager
        import io

        logger.info("🔄 Starting market data refresh (legacy mode)...")

        # 2. Determine provider
        import config

        preferred_provider = force_provider or config.current_settings.get(
            "ai_provider", "gemini"
        )

        provider = None
        use_batching = False

        # Try user's preferred provider first
        if preferred_provider == "gemini" and langchain_manager.gemini_llm:
            provider = "gemini"
            logger.info("📊 Using Gemini for market data generation")
        elif preferred_provider == "llama" and langchain_manager.llama_llm:
            provider = "llama"
            use_batching = True
            batch_size = 5  # Reduced to prevent truncation
            logger.info(
                f"⚙️  Using Llama for market data generation (batch mode: {batch_size} jobs at a time)"
            )
        elif preferred_provider == "groq" and langchain_manager.groq_llm:
            provider = "groq"
            logger.info("📊 Using Groq for market data generation")
        # Fallback logic
        elif langchain_manager.groq_llm:
            provider = "groq"
            logger.info("📊 Falling back to Groq")
        elif langchain_manager.gemini_llm:
            provider = "gemini"
            logger.info("📊 Falling back to Gemini")
        # 3. Load Profiles
        try:
            profiles = json.load(open("data/courses_content.json", encoding="utf-8"))
            logger.info(f"✅ Loaded {len(profiles)} profiles from JSON")
        except Exception as e:
            logger.error(f"Failed to load courses_content.json: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Source JSON not found"},
            )

        # 4. Process Data
        all_market_json_data = []

        # Determine batch size - smaller for local/llama, larger for cloud/gemini/groq
        # Safer batch size (10) to avoid TPM limits on free tier
        batch_size = 5 if provider == "llama" else 10

        logger.info(
            f"🔄 Processing {len(profiles)} profiles in batches of {batch_size}..."
        )

        for batch_idx in range(0, len(profiles), batch_size):
            batch_df = profiles[batch_idx : batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            total_batches = (len(profiles) + batch_size - 1) // batch_size

            logger.info(
                f"📦 Processing batch {batch_num}/{total_batches} ({len(batch_df)} jobs)..."
            )

            # Read prompt template from file
            try:
                with open("data/prompt.txt", "r", encoding="utf-8") as f:
                    prompt_content = f.read()
                    if '"""' in prompt_content:
                        parts = prompt_content.split('"""')
                        # Find the longest part which is likely the prompt
                        prompt_template = max(parts, key=len)
                    else:
                        prompt_template = prompt_content
            except Exception as e:
                logger.warning(f"Could not read prompt.txt, using fallback: {e}")
                prompt_template = """You are an expert market researcher..."""

            # Construct dynamic prompt
            batch_prompt = prompt_template.replace("{year}", str(year))
            batch_prompt = batch_prompt.replace(
                "@courses_content.json", json.dumps(batch_df)
            )

            # Dynamic count replacement
            count = len(batch_df)
            batch_prompt = batch_prompt.replace(
                f"{len(profiles)} roles", f"{count} roles"
            )
            batch_prompt = batch_prompt.replace(
                f"{len(profiles)} data rows", f"{count} data items"
            )

            # Fallback strategy
            providers_to_try = [provider]
            if provider == "groq" and langchain_manager.gemini_llm:
                providers_to_try.append("gemini")
            elif provider == "gemini" and langchain_manager.groq_llm:
                providers_to_try.append("groq")

            # Add llama as a last resort if available
            if langchain_manager.llama_llm and "llama" not in providers_to_try:
                providers_to_try.append("llama")

            result = None
            used_provider = provider
            for try_provider in providers_to_try:
                logger.info(
                    f"🤖 Batch {batch_num}: Querying {try_provider} (Attempt 1)..."
                )
                result = await langchain_manager.query(
                    prompt=batch_prompt,
                    provider=try_provider,
                )
                if result.get("success"):
                    used_provider = try_provider
                    break
                logger.warning(
                    f"⚠️ Batch {batch_num}: {try_provider} failed. Trying next provider in chain..."
                )

            if not result or not result.get("success"):
                logger.error(
                    f"❌ Batch {batch_num} failed all providers: {result.get('error') if result else 'Unknown error'}"
                )
                continue

            # Add a small delay between successful batches to avoid RPM hits
            if batch_idx + batch_size < len(profiles):
                logger.info("⏸️ Waiting 2s before next batch...")
                await asyncio.sleep(2)

            response_text = result.get("response", "").strip()

            # Extract JSON from response
            try:
                # Find JSON array brackets
                start_idx = response_text.find("[")
                end_idx = response_text.rfind("]")

                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx : end_idx + 1]
                    batch_data = json.loads(json_str)

                    if isinstance(batch_data, list):
                        all_market_json_data.extend(batch_data)
                        logger.info(
                            f"✅ Batch {batch_num}: Successfully parsed {len(batch_data)} items."
                        )
                    else:
                        logger.warning(
                            f"⚠️ Batch {batch_num}: Response was not a JSON array."
                        )
                else:
                    logger.warning(
                        f"⚠️ Batch {batch_num}: No JSON array structure found in response."
                    )
                    logger.debug(f"Response: {response_text[:200]}...")

            except json.JSONDecodeError as e:
                logger.warning(
                    f"⚠️ Batch {batch_num} JSON Decode Error: {e}. Attempting repair..."
                )

                if repair_json:
                    try:
                        # Attempt to use json_repair library
                        repaired_data = repair_json(json_str, return_objects=True)
                        if isinstance(repaired_data, list):
                            all_market_json_data.extend(repaired_data)
                            logger.info(
                                f"✅ Batch {batch_num}: Successfully repaired and parsed {len(repaired_data)} items."
                            )
                            continue
                        elif isinstance(repaired_data, dict):
                            # Sometimes it returns a single dict if the list brackets are missing
                            all_market_json_data.append(repaired_data)
                            logger.info(
                                f"✅ Batch {batch_num}: Successfully repaired single object."
                            )
                            continue
                    except Exception as repair_error:
                        logger.error(
                            f"❌ Batch {batch_num} Repair failed: {repair_error}"
                        )

                # Fallback to manual cleanup if repair failed or not installed
                try:
                    # Attempt 2: Escape unescaped control characters using regex
                    # This is aggressive but might save the batch
                    cleaned_json_str = re.sub(r"(?<!\\)\n", "\\n", json_str)
                    cleaned_json_str = re.sub(r"(?<!\\)\r", "", cleaned_json_str)
                    cleaned_json_str = re.sub(r"(?<!\\)\t", "\\t", cleaned_json_str)

                    batch_data = json.loads(cleaned_json_str, strict=False)
                    if isinstance(batch_data, list):
                        all_market_json_data.extend(batch_data)
                        logger.info(
                            f"✅ Batch {batch_num}: Successfully parsed {len(batch_data)} items (with regex cleanup)."
                        )
                    else:
                        logger.error(
                            f"❌ Batch {batch_num} failed: clean result is not a list"
                        )
                except Exception as e2:
                    logger.error(f"❌ Batch {batch_num} JSON Cleanup Failed: {e2}")
                    logger.debug(f"Failed JSON fragment: {json_str[:500]}...")

        # Post-processing: Clean data and fill empty values
        cleaned_data = []
        for item in all_market_json_data:
            if not isinstance(item, dict):
                continue

            # Normalize keys to lowercase to prevent duplicates (e.g., "Courses" vs "courses")
            item = {k.lower(): v for k, v in item.items()}

            # Fill empty strings with defaults
            if not item.get("ai_skills") or item.get("ai_skills") == "None":
                item["ai_skills"] = "General Skills"

            if not item.get("missing_skills") or item.get("missing_skills") == "None":
                item["missing_skills"] = "None"

            # Ensure numeric fields have values
            numeric_fields = [
                "global_job_demand",
                "egypt_job_demand",
                "freelancing_opportunities",
                "market_attractiveness_rating",
                "ai_skills_count",
            ]
            for field in numeric_fields:
                if field not in item or item[field] == "" or item[field] is None:
                    item[field] = 0

            cleaned_data.append(item)

        all_market_json_data = cleaned_data

        # 5. Save intermediate JSON
        json_output_path = "data/last_generated_market_data.json"
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(all_market_json_data, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved raw JSON data to {json_output_path}")

        # 6. Convert to CSV and Ensure Completeness
        logger.info("📊 Ensuring all profiles from source are in final CSV...")

        # Create DataFrames
        df_source = pd.DataFrame(profiles)

        # Normalize source for merging
        # Convert all column names to lower case to handle variations
        df_source.columns = [c.lower() for c in df_source.columns]

        # Map 'jobprofile' to 'title' if 'title' doesn't exist (since source uses JobProfile)
        if "jobprofile" in df_source.columns and "title" not in df_source.columns:
            df_source.rename(columns={"jobprofile": "title"}, inplace=True)

        if "title" in df_source.columns:
            df_source["merge_key"] = (
                df_source["title"].astype(str).str.strip().str.lower()
            )
        else:
            logger.error(
                f"❌ Source data missing 'title' or 'jobprofile'. Found: {df_source.columns.tolist()}"
            )
            raise KeyError("title")

        if all_market_json_data:
            df_llm = pd.DataFrame(all_market_json_data)
            df_llm["merge_key"] = df_llm["title"].str.strip().str.lower()

            # Remove any duplicate title entries from LLM (keep last)
            df_llm = df_llm.drop_duplicates(subset=["merge_key"], keep="last")

            # Dropping source columns from LLM before merge to avoid _x _y suffixes
            # but we want to keep Title/Track/etc from source as the "truth"
            cols_to_drop = [
                c for c in df_source.columns if c in df_llm.columns and c != "merge_key"
            ]
            df_llm_subset = df_llm.drop(columns=cols_to_drop)

            # Left merge: Keep ALL source profiles
            df_final = pd.merge(df_source, df_llm_subset, on="merge_key", how="left")
        else:
            logger.warning(
                "⚠️ No LLM data generated, using source with empty market data"
            )
            df_final = df_source.copy()

        # Fill NaNs for market columns
        market_cols = [
            "rank",
            "justify_ranking",
            "global_job_demand",
            "egypt_job_demand",
            "freelancing_opportunities",
            "linkedin_distribution",
            "ziprecruiter_distribution",
            "upwork_distribution",
            "khamsat_distribution",
            "mostakel_distribution",
            "freelancer_distribution",
            "indeed_distribution",
            "growth_trend_2025_2030",
            "market_attractiveness_rating",
            "ai_skills",
            "ai_skills_count",
            "missing_skills",
        ]

        for col in market_cols:
            if col not in df_final.columns:
                df_final[col] = (
                    0
                    if "demand" in col
                    or "opportunities" in col
                    or "count" in col
                    or "rating" in col
                    or "rank" in col
                    else "N/A"
                )
            else:
                if (
                    "demand" in col
                    or "opportunities" in col
                    or "count" in col
                    or "rating" in col
                    or "rank" in col
                ):
                    df_final[col] = df_final[col].fillna(0)
                else:
                    df_final[col] = df_final[col].fillna("N/A")

        # Define column mapping for final CSV
        column_mapping = {
            "rank": "Rank",
            "justify_ranking": "Justify_Ranking",
            "title": "Title",
            "track": "Track",
            "courses": "Courses",
            "description": "Description",
            "global_job_demand": "Global_Job_Demand",
            "egypt_job_demand": "Egypt_Job_Demand",
            "freelancing_opportunities": "Freelancing_Opportunities",
            "linkedin_distribution": "Linkedin_Distribution",
            "ziprecruiter_distribution": "Ziprecruiter_Distribution",
            "upwork_distribution": "Upwork_Distribution",
            "khamsat_distribution": "Khamsat_Distribution",
            "mostakel_distribution": "Mostakel_Distribution",
            "freelancer_distribution": "Freelancer_Distribution",
            "indeed_distribution": "Indeed_Distribution",
            "growth_trend_2025_2030": "Growth_Trend_2025_2030",
            "market_attractiveness_rating": "Market_Attractiveness_Rating",
            "ai_skills": "AI_Extracted_Skills",
            "ai_skills_count": "AI_Skills_Count",
            "missing_skills": "Missing_Skills",
        }

        # Rename and filter
        df_final.rename(columns=column_mapping, inplace=True)
        final_cols_to_keep = [
            v for k, v in column_mapping.items() if v in df_final.columns
        ]
        df_final = df_final[final_cols_to_keep]

        # Save to CSV with full quoting to handle newlines in descriptions correctly
        year_csv_path = get_year_csv_path(year)
        df_final.to_csv(
            year_csv_path, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL
        )
        logger.info(
            f"✅ Converted and merged data to CSV at {year_csv_path} ({len(df_final)} roles)"
        )

        # Also save to the default path for backwards compatibility
        df_final.to_csv(
            NEW_CSV_FILE_PATH, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL
        )

        # 7. Generate Accuracy Report automatically
        try:
            from agents.accuracy_report_agent import run_accuracy_report_agent

            logger.info(f"📊 Automatically generating accuracy report for {year}...")
            await run_accuracy_report_agent(
                str(year_csv_path), include_recommendations=True
            )
            logger.info("✅ Automatic accuracy report generated")
        except Exception as report_err:
            logger.error(
                f"⚠️ Failed to generate automatic accuracy report: {report_err}"
            )

        return {
            "success": True,
            "message": f"Market data refreshed successfully for {year} with 100% profile coverage",
            "total_items": len(df_final),
            "source_count": len(profiles),
            "generated_count": len(all_market_json_data),
            "csv_file": str(year_csv_path),
        }

    #             jobs_context = ""
    #             for idx, (_, row) in enumerate(df_original.iterrows(), 1):
    #                 title = str(row.get('Title', '')).strip()
    #                 desc = str(row.get('Description', '')).strip()
    #                 track = str(row.get('Track', '')).strip()
    #                 if title:
    #                     jobs_context += f"{idx}. Title: {title}\n   Track: {track}\n   Description: {desc}\n\n"

    #             prompt = f"""You are an expert market researcher and labor-market analyst.
    #                                 I will provide you with  job titles, track,courses and detailed descriptions ({len(profiles)} roles) in the array {profiles}.
    #                                 For each role produce a single CSV row with the exact columns and order listed below.
    #                                 Return only valid CSV content (first row must be the header exactly as specified, then one row per job).
    #                                 Do not include any additional commentary or JSON — only the CSV.

    #                                 CSV header (exact order, single line):

    # title,track,courses,description,global_job_demand,egypt_job_demand,freelancing_opportunities,linkedin_distribution,ziprecruiter_distribution,upwork_distribution,khamsat_distribution,mostakel_distribution,freelancer_distribution,indeed_distribution,growth_trend_2025_2030,market_attractiveness_rating,extracted_skills,missing_skills

    # Column content rules (required):

    # title — exact job title string (no extra punctuation).
    # track — exact job track string (no extra punctuation).
    # description — exact job description (no extra punctuation).
    # courses — exact job courses string (no extra punctuation).
    # global_job_demand — numeric estimate of currently available positions worldwide (integer, approximate). Use the closest whole number (e.g., 240000). If exact number is unavailable, give best estimate  (e.g., 240000).
    # egypt_job_demand — numeric estimate of currently available positions in Egypt (integer, approximate). Use 0 if negligible or none found; otherwise integer or  number.
    # freelancing_opportunities — numeric estimate of active freelance/remote listings worldwide for this role (integer, approximate).
    # Distribution columns (linkedin_distribution, ziprecruiter_distribution, upwork_distribution, khamsat_distribution, mostakel_distribution, freelancer_distribution, indeed_distribution) — percentage values as numbers with % sign, representing approximate share of open listings for that role on that platform (e.g., 45%). If a platform is not relevant or no data, use 0%. These are platform-specific posting-share estimates (they need not sum to exactly 100% because some postings appear on multiple platforms; but they should reflect relative presence).
    # khamsat_distribution and mostakel_distribution refer to Egyptian/local freelance marketplaces (Khamsat, Mostaql respectively).
    # growth_trend_2025_2030 — concise text: one of High growth (+X%), Moderate growth (+X%), Stable (≈0%), or Decline (-X%). Wherever possible give a projected % change range or point estimate (e.g., High growth (+22%)).
    # market_attractiveness_rating — integer 1–5 (1 = low potential, 5 = highest potential) reflecting combined global and Egypt opportunity, growth, and freelancing prospects.
    # extracted_skills —  comma-separated list of AI extracted skills from job description and courses
    # extracted_skills_count — AI skills count
    # extraction_success — if extraction was successful
    # missing_skills— comma-separated list of missing skills that not found in job description and not found in courses

    # Method & assumptions (do not print these in the CSV):
    # Use latest publicly available {year} job-market data (job boards, platform APIs, market reports).
    # Where exact numbers are not available, derive best estimates using reasonable assumptions from platform posting counts and trends.

    # If you use any source or make key assumptions that materially change an estimate, embed a short note in the cell (in parentheses) — but minimize length so CSV stays readable. Example: ≈3500 (est. from LinkedIn+Indeed).

    # Round numbers to whole integers. Percentages show two-digit precision only if necessary, otherwise whole percent (e.g., 45% or 45.5%).

    # If you cannot estimate a value, set it to N/A (but prefer 0 for counts when appropriate).

    # Formatting rules (must be followed):

    # Output must be valid CSV (escape fields containing commas with double quotes).

    # The CSV must contain exactly {len(profiles)} data rows (one per job you will provide).

    # Output only CSV content — no preface, explanation, or trailing text.

    # Example (single-row example — not part of your output header):

    # DevOps Engineer	Software Development	Prompt Engineering\nDevOps Essentials & Perquisites\nConfiguration Management using Ansible\nUsing Git for DevOps\nContainerization basics using Docker\nDocker Advanced\nContinuous Integration using Jenkins\nIntroduction to Kubernetes\nContinuous Monitoring using Prometheus\nCloud for DevOps\nTerraform\nApplication Deployment (Resource Dependencies,….)\nweb server configurations\nCapstone Project	A DevOps Engineer is responsible for smoothing the operation of a company's IT infrastructure. A DevOps Engineer's roles and responsibilities are a combination of technical and management roles. DevOps Engineers build and set up new development tools and infrastructure, implement integrations requested by customers, deploy updates and fixes, develop scripts to automate visualization, design procedures for system troubleshooting and maintenance, and optimize software development processes.	259634	1049	23566	44.00%	12.00%	6.00%	1.00%	4.00%	7.00%	29.00%	High growth (+22%)	5	R, DevOps	2	True  Agile, Scrum

    # Now produce the CSV with the header above and one row per job title/track/description/courses I provided.
    # Use up-to-date {year}-informed estimates and keep values concise and comparable across rows."""

    #             result = await langchain_manager.query(
    #                 prompt=prompt,
    #                 provider=provider,
    #                 temperature=0.1,
    #                 max_tokens=16000
    #             )

    #             if not result.get("success"):
    #                 error_msg = result.get('error', 'Unknown error')
    #                 # Check if it's a quota error
    #                 if '429' in str(error_msg) or 'quota' in str(error_msg).lower():
    #                     raise Exception(f"Gemini API quota exceeded. Please wait or try using Llama instead. Error: {error_msg}")
    #                 raise Exception(f"LLM query failed: {error_msg}")

    #             csv_content = result.get("response", "").strip()

    #             logger.info(f"Raw LLM response length: {len(csv_content)} chars")

    #             # Clean up code blocks if present
    #             if "```csv" in csv_content:
    #                 csv_content = csv_content.split("```csv")[1].split("```")[0].strip()
    #             elif "```" in csv_content:
    #                 csv_content = csv_content.split("```")[1].split("```")[0].strip()

    #             # Remove common conversational prefixes/suffixes - ENHANCED
    #             lines = csv_content.split('\n')
    #             cleaned_lines = []
    #             found_header = False

    #             # Expected market data columns
    #             expected_columns = [
    #                 'Global_Job_Demand', 'Egypt_Job_Demand', 'Freelancing_Opportunities',
    #                 'Linkedin_Distribution', 'Ziprecruiter_Distribution', 'Upwork_Distribution',
    #                 'Khamsat_Distribution', 'Mostakel_Distribution', 'Freelancer_Distribution',
    #                 'Indeed_Distribution', 'Growth_Trend_2025_2030', 'Market_Attractiveness_Rating',
    #                 'AI_Extracted_Skills', 'AI_Skills_Count', 'Extraction_Success', 'Missing_Skills'
    #             ]

    #             for line in lines:
    #                 line_stripped = line.strip()
    #                 line_lower = line_stripped.lower()

    #                 # Skip empty lines
    #                 if not line_stripped:
    #                     continue

    #                 # Skip conversational lines - EXPANDED LIST
    #                 conversational_patterns = [
    #                     'here is the csv', "here's the csv", 'below is the',
    #                     'let me know', 'need any further', 'assistance', 'hope this helps',
    #                     'critical:', 'output only', 'remember:', 'note:', 'important:',
    #                     'generate', 'csv file', 'market data', 'job titles', 'column details',
    #                     'please find', 'attached', 'following', 'example output'
    #                 ]

    #                 if any(phrase in line_lower for phrase in conversational_patterns):
    #                     # But don't skip if this looks like actual CSV data (has commas and markers)
    #                     if not (line_stripped.count(',') >= 10):
    #                         logger.info(f"Skipping conversational line: {line_stripped[:50]}...")
    #                         continue

    #                 # Look for the header - it should contain market data columns
    #                 if not found_header:
    #                     # Check if this line has most of our expected columns
    #                     matching_cols = sum(1 for col in expected_columns if col in line_stripped)

    #                     if matching_cols >= 10:  # At least 10 of 16 columns must match
    #                         found_header = True
    #                         cleaned_lines.append(line_stripped)
    #                         logger.info(f"Found market data header with {matching_cols} matching columns")
    #                         continue
    #                 else:
    #                     # Add data rows only if they look valid
    #                     # Relaxed check: just check for enough commas
    #                     if line_stripped.count(',') >= 10:
    #                         cleaned_lines.append(line_stripped)
    #                     else:
    #                         logger.info(f"Skipping invalid data row: {line_stripped[:50]}...")

    #             if not found_header:
    #                 raise Exception("Could not find valid market data CSV header in LLM response")

    #             market_csv = '\n'.join(cleaned_lines)
    #             logger.info(f"Cleaned market data CSV: {len(cleaned_lines)} lines (including header)")

    #             # Parse market data into DataFrame
    #             try:
    #                 df_market = pd.read_csv(io.StringIO(market_csv), on_bad_lines='skip')
    #                 logger.info(f"✅ Parsed {len(df_market)} market data rows, {len(df_market.columns)} columns")
    #             except Exception as e:
    #                 raise Exception(f"Failed to parse generated market data: {e}")

    #             # Validate column count
    #             if len(df_market.columns) < 15:
    #                 raise Exception(f"Market data has only {len(df_market.columns)} columns, expected 16. Columns: {list(df_market.columns)}")

    #             # Ensure row counts match
    #             if len(df_market) != len(preserved_columns):
    #                 logger.warning(f"Row count mismatch: {len(preserved_columns)} original vs {len(df_market)} generated")
    #                 # Trim to minimum length
    #                 min_len = min(len(preserved_columns), len(df_market))
    #                 preserved_columns = preserved_columns.iloc[:min_len]
    #                 df_market = df_market.iloc[:min_len]

    #             # Combine preserved columns with new market data
    #             df_combined = pd.concat([preserved_columns.reset_index(drop=True), df_market.reset_index(drop=True)], axis=1)

    #             # Convert to CSV
    #             csv_content = df_combined.to_csv(index=False)

    #         # Validate CSV (common for both modes)
    #         try:
    #             test_df = pd.read_csv(io.StringIO(csv_content), on_bad_lines='skip')
    #             logger.info(f"CSV validation: {len(test_df)} rows, {len(test_df.columns)} columns")
    #             logger.info(f"Columns: {list(test_df.columns)}")

    #             # Check if we have the minimum required columns (should be 19)
    #             if len(test_df.columns) < 18:
    #                 raise Exception(f"CSV has only {len(test_df.columns)} columns, expected 18-19. Columns found: {list(test_df.columns)}")

    #             # Check if we have data rows
    #             if len(test_df) < 5:
    #                 # FIX: Used df_original instead of df
    #                 raise Exception(f"CSV has only {len(test_df)} data rows, expected at least {len(df_original)//2}")

    #         except Exception as e:
    #             logger.error(f"Generated CSV is invalid: {e}")
    #             logger.error(f"Content preview (first 800 chars): {csv_content[:800]}")
    #             raise Exception(f"Generated CSV is invalid: {e}")

    #         # 4. Save to file
    #         with open(NEW_CSV_FILE_PATH, "w", encoding="utf-8") as f:
    #             f.write(csv_content)

    #         logger.info("✅ Market data refreshed successfully")

    #         return {
    #             "success": True,
    #             "message": f"Market data refreshed successfully using {provider.upper()}",
    #             "rows_generated": len(csv_content.splitlines()) - 1,
    #             "provider_used": provider,
    #             "batch_mode": use_batching
    #         }

    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.get("/compare_data")
async def compare_market_data():
    """Compare old vs new market data"""
    try:
        if not CSV_FILE_PATH.exists():
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Original data not found"},
            )

        if not NEW_CSV_FILE_PATH.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "New data not found. Please generate it first.",
                },
            )

        # Load DataFrames
        try:
            df_old = pd.read_csv(CSV_FILE_PATH)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Failed to read original data: {str(e)}",
                },
            )

        try:
            # Use robust reading options
            df_new = pd.read_csv(NEW_CSV_FILE_PATH, on_bad_lines="skip")

            # Normalize column names to title case for consistent comparison
            df_new.columns = (
                df_new.columns.str.strip()
                .str.replace("_", " ")
                .str.title()
                .str.replace(" ", "_")
            )
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"New data is invalid/corrupt: {str(e)}. Please regenerate.",
                },
            )

        # Check if new data has minimal required columns (try both formats)
        required_cols = ["Global_Job_Demand", "Egypt_Job_Demand"]
        missing_cols = [col for col in required_cols if col not in df_new.columns]

        if missing_cols:
            # Log available columns for debugging
            logger.warning(
                f"Missing columns: {missing_cols}. Available: {list(df_new.columns)}"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"New data is missing required columns: {', '.join(missing_cols)}. Please regenerate with the correct format.",
                },
            )

        # Helper to get stats
        def get_stats(df):
            # Ensure numeric
            cols = [
                "Global_Job_Demand",
                "Egypt_Job_Demand",
                "Market_Attractiveness_Rating",
            ]
            for col in cols:
                if col in df.columns:
                    df[col] = df[col].apply(clean_numeric_value)

            return {
                "total_jobs": len(df),
                "total_global_demand": int(df["Global_Job_Demand"].sum())
                if "Global_Job_Demand" in df.columns
                else 0,
                "total_egypt_demand": int(df["Egypt_Job_Demand"].sum())
                if "Egypt_Job_Demand" in df.columns
                else 0,
                "avg_rating": float(df["Market_Attractiveness_Rating"].mean())
                if "Market_Attractiveness_Rating" in df.columns
                else 0,
            }

        stats_old = get_stats(df_old.copy())
        stats_new = get_stats(df_new.copy())

        # Prepare detailed job-by-job comparison
        job_comparisons = []

        # Ensure both dataframes have Title column
        if "Title" in df_old.columns and "Title" in df_new.columns:
            # Convert numeric columns for comparison
            for df in [df_old, df_new]:
                df["Global_Job_Demand"] = df["Global_Job_Demand"].apply(
                    clean_numeric_value
                )
                df["Egypt_Job_Demand"] = df["Egypt_Job_Demand"].apply(
                    clean_numeric_value
                )
                df["Market_Attractiveness_Rating"] = df[
                    "Market_Attractiveness_Rating"
                ].apply(clean_numeric_value)

            # Merge old and new data on Title
            merged = df_old.merge(
                df_new, on="Title", how="outer", suffixes=("_old", "_new")
            )

            for _, row in merged.iterrows():
                title = row["Title"]
                # Handle NaN values before conversion
                old_demand = row.get("Global_Job_Demand_old", 0)
                old_demand = 0 if pd.isna(old_demand) else old_demand
                new_demand = row.get("Global_Job_Demand_new", 0)
                new_demand = 0 if pd.isna(new_demand) else new_demand
                old_egypt = row.get("Egypt_Job_Demand_old", 0)
                old_egypt = 0 if pd.isna(old_egypt) else old_egypt
                new_egypt = row.get("Egypt_Job_Demand_new", 0)
                new_egypt = 0 if pd.isna(new_egypt) else new_egypt
                old_rating = row.get("Market_Attractiveness_Rating_old", 0)
                old_rating = 0 if pd.isna(old_rating) else old_rating
                new_rating = row.get("Market_Attractiveness_Rating_new", 0)
                new_rating = 0 if pd.isna(new_rating) else new_rating

                # Calculate change
                demand_change = new_demand - old_demand
                egypt_change = new_egypt - old_egypt
                rating_change = new_rating - old_rating

                # Determine status
                if pd.isna(row.get("Global_Job_Demand_old")):
                    status = "new"
                elif pd.isna(row.get("Global_Job_Demand_new")):
                    status = "removed"
                else:
                    status = "updated"

                job_comparisons.append(
                    {
                        "title": str(title),
                        "status": status,
                        "old_global_demand": int(old_demand),
                        "new_global_demand": int(new_demand),
                        "demand_change": int(demand_change),
                        "demand_change_pct": round(
                            (demand_change / old_demand * 100) if old_demand > 0 else 0,
                            1,
                        ),
                        "old_egypt_demand": int(old_egypt),
                        "new_egypt_demand": int(new_egypt),
                        "egypt_change": int(egypt_change),
                        "old_rating": float(old_rating),
                        "new_rating": float(new_rating),
                        "rating_change": round(rating_change, 2),
                    }
                )

            # Sort by absolute demand change
            job_comparisons = sorted(
                job_comparisons, key=lambda x: abs(x["demand_change"]), reverse=True
            )

        # Top gainers and losers
        updated_jobs = [j for j in job_comparisons if j["status"] == "updated"]
        top_gainers = sorted(
            [j for j in updated_jobs if j["demand_change"] > 0],
            key=lambda x: x["demand_change"],
            reverse=True,
        )[:10]
        top_losers = sorted(
            [j for j in updated_jobs if j["demand_change"] < 0],
            key=lambda x: x["demand_change"],
        )[:10]

        # Track-wise comparison
        track_comparison = []
        if "Track" in df_old.columns and "Track" in df_new.columns:
            tracks_old = (
                df_old.groupby("Track")
                .agg({"Global_Job_Demand": "sum", "Egypt_Job_Demand": "sum"})
                .to_dict()
            )

            tracks_new = (
                df_new.groupby("Track")
                .agg({"Global_Job_Demand": "sum", "Egypt_Job_Demand": "sum"})
                .to_dict()
            )

            all_tracks = set(
                list(tracks_old.get("Global_Job_Demand", {}).keys())
                + list(tracks_new.get("Global_Job_Demand", {}).keys())
            )

            for track in all_tracks:
                old_global = tracks_old.get("Global_Job_Demand", {}).get(track, 0)
                new_global = tracks_new.get("Global_Job_Demand", {}).get(track, 0)
                old_egypt = tracks_old.get("Egypt_Job_Demand", {}).get(track, 0)
                new_egypt = tracks_new.get("Egypt_Job_Demand", {}).get(track, 0)

                track_comparison.append(
                    {
                        "track": track,
                        "old_global_demand": int(old_global),
                        "new_global_demand": int(new_global),
                        "global_change": int(new_global - old_global),
                        "old_egypt_demand": int(old_egypt),
                        "new_egypt_demand": int(new_egypt),
                        "egypt_change": int(new_egypt - old_egypt),
                    }
                )

        # Growth trends comparison
        growth_comparison = {}
        if (
            "Growth_Trend_2025_2030" in df_old.columns
            and "Growth_Trend_2025_2030" in df_new.columns
        ):
            old_trends = df_old["Growth_Trend_2025_2030"].value_counts().to_dict()
            new_trends = df_new["Growth_Trend_2025_2030"].value_counts().to_dict()

            all_trends = set(list(old_trends.keys()) + list(new_trends.keys()))
            growth_comparison = {
                str(trend): {
                    "old_count": old_trends.get(trend, 0),
                    "new_count": new_trends.get(trend, 0),
                    "change": new_trends.get(trend, 0) - old_trends.get(trend, 0),
                }
                for trend in all_trends
                if str(trend).lower() not in ["nan", "none", "0"]
            }

        comparison = {
            "old": stats_old,
            "new": stats_new,
            "diff": {
                "total_jobs": stats_new["total_jobs"] - stats_old["total_jobs"],
                "total_global_demand": stats_new["total_global_demand"]
                - stats_old["total_global_demand"],
                "total_egypt_demand": stats_new["total_egypt_demand"]
                - stats_old["total_egypt_demand"],
                "avg_rating": round(
                    stats_new["avg_rating"] - stats_old["avg_rating"], 2
                ),
            },
            "job_details": {
                "total_compared": len(job_comparisons),
                "new_jobs": len([j for j in job_comparisons if j["status"] == "new"]),
                "removed_jobs": len(
                    [j for j in job_comparisons if j["status"] == "removed"]
                ),
                "updated_jobs": len(
                    [j for j in job_comparisons if j["status"] == "updated"]
                ),
                "top_gainers": top_gainers,
                "top_losers": top_losers,
                "all_jobs": job_comparisons[:50],  # Limit to top 50 for performance
            },
            "track_comparison": track_comparison,
            "growth_trends": growth_comparison,
        }

        return {"success": True, "comparison": comparison}

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.get("/split_comparison")
async def get_split_comparison_data():
    """Get chart data for both old and new CSVs for split-screen comparison"""
    try:
        # Load old data
        if not CSV_FILE_PATH.exists():
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Original data not found"},
            )

        # Load new data
        if not NEW_CSV_FILE_PATH.exists():
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "New data not found. Please generate it first.",
                },
            )

        # Function to process dataframe into chart data
        def process_chart_data(df, df_name):
            # Ensure numeric columns
            cols_to_convert = [
                "Global_Job_Demand",
                "Egypt_Job_Demand",
                "Freelancing_Opportunities",
                "Linkedin_Distribution",
                "Ziprecruiter_Distribution",
                "Upwork_Distribution",
                "Khamsat_Distribution",
                "Mostakel_Distribution",
                "Freelancer_Distribution",
                "Indeed_Distribution",
                "Market_Attractiveness_Rating",
                "AI_Skills_Count",
            ]

            for col in cols_to_convert:
                if col in df.columns:
                    df[col] = df[col].apply(clean_numeric_value)

            # Top 10 Jobs
            top_jobs = []
            if len(df) > 0:
                top_jobs_df = df.nlargest(10, "Global_Job_Demand")[
                    [
                        "Title",
                        "Track",
                        "Global_Job_Demand",
                        "Egypt_Job_Demand",
                        "Market_Attractiveness_Rating",
                    ]
                ].copy()
                for _, row in top_jobs_df.iterrows():
                    top_jobs.append(
                        {
                            "job_title": str(row["Title"]),
                            "track": str(row["Track"]),
                            "global_demand": int(row["Global_Job_Demand"]),
                            "egypt_demand": int(row["Egypt_Job_Demand"]),
                            "rating": float(row["Market_Attractiveness_Rating"]),
                        }
                    )

            # Track Analysis
            track_analysis = []
            if "Track" in df.columns:
                tracks = (
                    df.groupby("Track")
                    .agg({"Global_Job_Demand": "sum", "Egypt_Job_Demand": "sum"})
                    .reset_index()
                )

                for _, row in tracks.iterrows():
                    track_analysis.append(
                        {
                            "track": str(row["Track"]),
                            "global_demand": int(row["Global_Job_Demand"]),
                            "egypt_demand": int(row["Egypt_Job_Demand"]),
                        }
                    )

            # Top Skills
            all_skills = {}
            for _, row in df.iterrows():
                # Handle both original and normalized column names
                skills_col = row.get("AI_Extracted_Skills", "") or row.get(
                    "Ai_Extracted_Skills", ""
                )
                count_col = row.get("AI_Skills_Count", 0) or row.get(
                    "Ai_Skills_Count", 0
                )
                skills = extract_skills_list(skills_col, count_col)
                demand = row["Global_Job_Demand"]
                for skill in skills:
                    if skill and skill.strip():
                        skill = skill.strip()
                        all_skills[skill] = all_skills.get(skill, 0) + demand

            top_skills = [
                {"skill_name": skill, "total_demand": int(demand)}
                for skill, demand in sorted(
                    all_skills.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            logger.info(
                f"📊 Extracted {len(all_skills)} unique skills, top 10: {[s['skill_name'] for s in top_skills]}"
            )

            # Missing Skills (from the Skills column)
            missing_skills_data = []
            for _, row in df.iterrows():
                # Handle both original and normalized column names for Skills column
                missing_skills = row.get("Skills", "") or row.get("Skills", "")
                if (
                    missing_skills
                    and str(missing_skills).strip()
                    and str(missing_skills).lower() not in ["nan", "none", ""]
                ):
                    missing_skills_data.append(
                        {
                            "job_title": str(row["Title"]),
                            "track": str(row.get("Track", "N/A")),
                            "missing_skills": str(missing_skills),
                            "extracted_skills": str(
                                row.get("AI_Extracted_Skills", "")
                                or row.get("Ai_Extracted_Skills", "")
                            ),
                            "skills_count": int(
                                row.get("AI_Skills_Count", 0)
                                or row.get("Ai_Skills_Count", 0)
                                or 0
                            ),
                        }
                    )

            logger.info(
                f"📋 Found {len(missing_skills_data)} jobs with missing skills data"
            )

            # Statistics
            statistics = {
                "total_jobs": len(df),
                "total_global_demand": int(df["Global_Job_Demand"].sum()),
                "total_egypt_demand": int(df["Egypt_Job_Demand"].sum()),
                "avg_rating": float(df["Market_Attractiveness_Rating"].mean()),
            }

            return {
                "name": df_name,
                "year": 2025 if df_name == "Original Data" else 2026,  # Default years
                "top_jobs": top_jobs,
                "track_analysis": track_analysis,
                "top_skills": top_skills,
                "missing_skills": missing_skills_data,  # Return all jobs
                "statistics": statistics,
            }

        # Load and process old data
        df_old = pd.read_csv(CSV_FILE_PATH)
        old_chart_data = process_chart_data(df_old.copy(), "Original Data")

        # Load and process new data
        df_new = pd.read_csv(NEW_CSV_FILE_PATH, on_bad_lines="skip")
        df_new.columns = (
            df_new.columns.str.strip()
            .str.replace("_", " ")
            .str.title()
            .str.replace(" ", "_")
        )
        new_chart_data = process_chart_data(df_new.copy(), "New Generated Data")

        return {"success": True, "old_data": old_chart_data, "new_data": new_chart_data}

    except Exception as e:
        logger.error(f"Split comparison failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.post("/gap-analysis")
async def identify_missing_jobs(use_agents: bool = True):
    """
    Identifies top in-demand jobs that are missing from the current courses content.
    Enriched with comprehensive market metrics using MissingJobsAgent.
    """
    try:
        from app import langchain_manager
        import config

        # Determine provider from current settings
        provider = config.current_settings.get("ai_provider", "gemini")

        if use_agents:
            from agents.missing_jobs_agent import run_missing_jobs_agent

            result = await run_missing_jobs_agent(provider=provider)

            if result.get("success"):
                missing_jobs = result.get("missing_jobs", [])

                # Save to CSV for the user
                try:
                    csv_path = Path("data/missing_jobs_analysis.csv")
                    df_missing = pd.DataFrame(missing_jobs)

                    # Ensure column order and existence
                    cols = [
                        "title",
                        "related_depi_matches_detailed",
                        "justification",
                        "openings",
                        "Global_Job_Demand",
                        "Egypt_Job_Demand",
                        "Freelancing_Opportunities",
                        "Linkedin_Distribution",
                        "Ziprecruiter_Distribution",
                        "Upwork_Distribution",
                        "Khamsat_Distribution",
                        "Mostakel_Distribution",
                        "Freelancer_Distribution",
                        "Indeed_Distribution",
                        "Growth_Trend_2025_2030",
                        "Market_Attractiveness_Rating",
                        "Skills",
                    ]

                    # Convert list fields to strings for CSV
                    if "Skills" in df_missing.columns:
                        df_missing["Skills"] = df_missing["Skills"].apply(
                            lambda x: ", ".join(x) if isinstance(x, list) else x
                        )

                    if "related_profiles" in df_missing.columns:

                        def format_matches(matches):
                            if not isinstance(matches, list):
                                return matches
                            lines = []
                            for p in matches:
                                name = p.get("profile_name", "N/A")
                                score = p.get("match_score", 0)
                                skills = ", ".join(p.get("missing_skills", []))
                                content = p.get("missing_content", "N/A")
                                lines.append(
                                    f"{name} ({score}%) [Missing Skills: {skills} | Roadmap: {content}]"
                                )
                            return " | ".join(lines)

                        df_missing["related_depi_matches_detailed"] = df_missing[
                            "related_profiles"
                        ].apply(format_matches)

                    # Ensure all columns exist
                    for c in cols:
                        if c not in df_missing.columns:
                            df_missing[c] = ""

                    # Save CSV
                    df_missing[cols].to_csv(csv_path, index=False, encoding="utf-8")
                    logger.info(f"💾 Saved enriched missing jobs to {csv_path}")
                except Exception as save_err:
                    logger.error(f"❌ Failed to save missing jobs CSV: {save_err}")

                return {
                    "success": True,
                    "missing_jobs": missing_jobs,
                    "count": result.get("count", 0),
                    "csv_saved": True,
                    "agent_used": "MissingJobsAgent",
                }

        # Legacy Fallback
        try:
            with open("data/courses_content.json", "r", encoding="utf-8") as f:
                profiles = json.load(f)
            existing_titles = [
                p.get("JobProfile", "") for p in profiles if p.get("JobProfile")
            ]
        except Exception as e:
            logger.error(f"Failed to load course profiles: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Failed to load current job profiles",
                },
            )

        llm = langchain_manager.get_llm(provider)
        prompt_text = f"I have these job profiles: {existing_titles}. Identify 5 missing top tech roles for 2026. Return ONLY a JSON list of strings."

        response = await llm.ainvoke(prompt_text)
        response_text = (
            response.content if hasattr(response, "content") else str(response)
        )
        cleaned_text = re.sub(r"```json\s*|\s*```", "", response_text).strip()
        missing_titles = json.loads(cleaned_text)

        missing_jobs = [
            {"title": t, "justification": "High demand role."} for t in missing_titles
        ]

        return {
            "success": True,
            "missing_jobs": missing_jobs,
            "count": len(missing_jobs),
            "agent_used": "Legacy-Fallback",
        }

    except Exception as e:
        logger.error(f"Gap analysis failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.post("/freelance-jobs")
async def generate_freelance_jobs(year: int = 2026, use_agents: bool = True):
    """
    Generates the top 100 freelance job profiles in the global market using AI.
    Enriched with DEPI matching and demand analytics.
    """
    try:
        from app import langchain_manager
        import config

        logger.info(f"🚀 Generating Enriched Top 100 Freelance Jobs for {year}...")

        # Determine provider
        provider = config.current_settings.get("ai_provider", "gemini")

        if use_agents:
            from agents.freelance_agent import run_freelance_agent

            result = await run_freelance_agent(year=year, provider=provider)

            if result.get("success"):
                freelance_jobs = result.get("jobs", [])

                # Save to files for persistence
                try:
                    json_path = Path("data/freelance_jobs.json")
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(freelance_jobs, f, indent=2, ensure_ascii=False)

                    csv_path = Path("data/freelance_jobs.csv")
                    df_freelance = pd.DataFrame(freelance_jobs)
                    cols = [
                        "rank",
                        "title",
                        "hourly_rate",
                        "skills",
                        "demand_score",
                        "platforms",
                        "related_depi_profile",
                        "match_score",
                        "openings",
                        "demand_justification",
                        "Global_Job_Demand",
                        "Egypt_Job_Demand",
                        "Freelancing_Opportunities",
                        "Linkedin_Distribution",
                        "Ziprecruiter_Distribution",
                        "Upwork_Distribution",
                        "Khamsat_Distribution",
                        "Mostakel_Distribution",
                        "Freelancer_Distribution",
                        "Indeed_Distribution",
                        "Growth_Trend_2025_2030",
                        "Market_Attractiveness_Rating",
                    ]

                    # Ensure all columns exist
                    for c in cols:
                        if c not in df_freelance.columns:
                            df_freelance[c] = ""

                    df_freelance[cols].to_csv(csv_path, index=False, encoding="utf-8")
                    logger.info(f"💾 Saved enriched freelance jobs to JSON and CSV")
                except Exception as save_err:
                    logger.error(f"❌ Failed to save freelance job files: {save_err}")

                return {
                    "success": True,
                    "year": year,
                    "count": len(freelance_jobs),
                    "jobs": freelance_jobs,
                    "agent_used": "FreelanceAgent",
                }

        # Legacy Fallback (simplified for brevity here, but same as before)
        # 1. Determine Provider
        provider = config.current_settings.get("ai_provider", "gemini")
        llm = langchain_manager.get_llm(provider)

        # Simplified batching for legacy fallback
        all_jobs = []
        prompt = f"List the top 10 freelance jobs for {year} in JSON format: [{{title, hourly_rate, skills, demand_score, platforms}}]"

        try:
            if hasattr(llm, "ainvoke"):
                response = await llm.ainvoke(prompt)
            else:
                response = await asyncio.to_thread(llm.invoke, prompt)

            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )
            cleaned_text = re.sub(r"```json\s*|\s*```", "", response_text).strip()
            all_jobs = json.loads(cleaned_text)
        except:
            all_jobs = []

        return {
            "success": True,
            "year": year,
            "count": len(all_jobs),
            "jobs": all_jobs,
            "agent_used": "Legacy-Fallback",
        }

    except Exception as e:
        logger.error(f"❌ Freelance generation failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


# ============= CSV Accuracy Endpoints =============


@router.get("/reliability")
async def get_reliability_alias(year: int = 2026):
    """
    🔍 Alias for accuracy-check for consistency with requirement
    """
    return await check_csv_accuracy(year)


@router.get("/accuracy-check")
async def check_csv_accuracy(year: int = 2026):
    """
    🔍 Check CSV data reliability and accuracy using CSVReliabilityAgent
    """
    try:
        from agents.csv_reliability_agent import run_csv_reliability_agent

        csv_path = get_year_csv_path(year)
        if not csv_path.exists():
            csv_path = NEW_CSV_FILE_PATH

        logger.info(f"🔍 Running accuracy check on {csv_path}")
        result = await run_csv_reliability_agent(str(csv_path))

        return {
            "success": result.get("success", False),
            "csv_path": str(csv_path),
            "reliability_score": result.get("reliability_score", 0),
            "reliability_level": result.get("reliability_level", "UNKNOWN"),
            "recommendation": result.get("recommendation", ""),
            "total_rows": result.get("total_rows", 0),
            "scores": result.get("scores", {}),
            "issues": result.get("issues", []),
            "agent_used": "CSVReliabilityAgent",
        }

    except Exception as e:
        logger.error(f"❌ Accuracy check failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.get("/accuracy-report")
async def generate_accuracy_report(year: int = 2026, include_ai: bool = True):
    """
    📊 Generate detailed accuracy report using AccuracyReportAgent
    """
    try:
        from agents.accuracy_report_agent import run_accuracy_report_agent

        csv_path = get_year_csv_path(year)
        if not csv_path.exists():
            csv_path = NEW_CSV_FILE_PATH

        logger.info(f"📊 Generating accuracy report for {csv_path}")
        result = await run_accuracy_report_agent(
            str(csv_path), include_recommendations=include_ai
        )

        if result.get("success"):
            report = result.get("report", {})
            return {
                "success": True,
                "summary": report.get("summary", {}),
                "reliability": report.get("reliability", {}),
                "metrics_breakdown": report.get("metrics_breakdown", {}),
                "issues_found": report.get("issues_found", []),
                "ai_recommendations": report.get("ai_recommendations", []),
                "report_path": report.get("report_path", ""),
                "agent_used": "AccuracyReportAgent",
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Report generation failed"),
            }

    except Exception as e:
        logger.error(f"❌ Accuracy report failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.get("/external-test")
async def test_external_data(
    query: str = Query("Python Developer", description="Job title to search"),
    platform: str = Query(
        "all", description="Platform: all, jooble, adzuna, wuzzuf, khamsat"
    ),
):
    """
    Test external data sources (APIs and scrapers)
    Returns sample data from configured sources
    """
    try:
        logger.info(f"🧪 Testing external data sources for: '{query}' on {platform}")

        results = {
            "query": query,
            "platform": platform,
            "sources_tested": [],
            "total_jobs_found": 0,
            "data": {},
        }

        if platform in ["all", "jooble"]:
            try:
                from market_api_client import JobAPIClient

                async with JobAPIClient() as client:
                    jooble_jobs = await client.search_jooble(query, country="eg")

                    if jooble_jobs:
                        results["sources_tested"].append("Jooble API")
                        results["data"]["jooble"] = {
                            "count": len(jooble_jobs),
                            "sample_jobs": [
                                {
                                    "title": j.title,
                                    "company": j.company,
                                    "location": j.location,
                                    "salary": f"{j.salary_min}-{j.salary_max} {j.salary_currency}"
                                    if j.salary_min
                                    else "Not specified",
                                    "url": j.url[:100] + "..."
                                    if len(j.url) > 100
                                    else j.url,
                                }
                                for j in jooble_jobs[:5]
                            ],
                        }
                        results["total_jobs_found"] += len(jooble_jobs)
                        logger.info(f"✅ Jooble: Found {len(jooble_jobs)} jobs")
                    else:
                        results["data"]["jooble"] = {
                            "error": "No jobs found or API not configured"
                        }
                        logger.warning("⚠️ Jooble: No jobs found")

            except Exception as e:
                results["data"]["jooble"] = {"error": str(e)}
                logger.error(f"❌ Jooble error: {e}")

        if platform in ["all", "adzuna"]:
            try:
                from market_api_client import JobAPIClient

                async with JobAPIClient() as client:
                    adzuna_jobs = await client.search_adzuna(query, country="gb")

                    if adzuna_jobs:
                        results["sources_tested"].append("Adzuna API")
                        results["data"]["adzuna"] = {
                            "count": len(adzuna_jobs),
                            "sample_jobs": [
                                {
                                    "title": j.title,
                                    "company": j.company,
                                    "location": j.location,
                                    "url": j.url[:100] + "..."
                                    if len(j.url) > 100
                                    else j.url,
                                }
                                for j in adzuna_jobs[:5]
                            ],
                        }
                        results["total_jobs_found"] += len(adzuna_jobs)
                        logger.info(f"✅ Adzuna: Found {len(adzuna_jobs)} jobs")
                    else:
                        results["data"]["adzuna"] = {
                            "error": "No jobs found or API not configured"
                        }

            except Exception as e:
                results["data"]["adzuna"] = {"error": str(e)}
                logger.error(f"❌ Adzuna error: {e}")

        if platform in ["all", "wuzzuf"]:
            try:
                from market_scraper import WuzzufScraper

                async with WuzzufScraper() as scraper:
                    wuzzuf_jobs = await scraper.search(query)

                    if wuzzuf_jobs:
                        results["sources_tested"].append("Wuzzuf Scraper")
                        results["data"]["wuzzuf"] = {
                            "count": len(wuzzuf_jobs),
                            "sample_jobs": [
                                {
                                    "title": j.title,
                                    "company": j.company,
                                    "location": j.location,
                                    "salary": f"{j.salary_min}-{j.salary_max} {j.salary_currency}"
                                    if j.salary_min
                                    else "Not specified",
                                }
                                for j in wuzzuf_jobs[:5]
                            ],
                        }
                        results["total_jobs_found"] += len(wuzzuf_jobs)
                        logger.info(f"✅ Wuzzuf: Found {len(wuzzuf_jobs)} jobs")
                    else:
                        results["data"]["wuzzuf"] = {
                            "error": "No jobs found or blocked"
                        }

            except Exception as e:
                results["data"]["wuzzuf"] = {"error": str(e)}
                logger.error(f"❌ Wuzzuf error: {e}")

        if platform in ["all", "khamsat"]:
            try:
                from market_scraper import KhamsatScraper

                async with KhamsatScraper() as scraper:
                    khamsat_jobs = await scraper.search(query)

                    if khamsat_jobs:
                        results["sources_tested"].append("Khamsat Scraper")
                        results["data"]["khamsat"] = {
                            "count": len(khamsat_jobs),
                            "sample_jobs": [
                                {
                                    "title": j.title,
                                    "budget": f"{j.salary_min}-{j.salary_max} EGP"
                                    if j.salary_min
                                    else "Negotiable",
                                    "skills": j.skills[:5] if j.skills else [],
                                }
                                for j in khamsat_jobs[:5]
                            ],
                        }
                        results["total_jobs_found"] += len(khamsat_jobs)
                        logger.info(f"✅ Khamsat: Found {len(khamsat_jobs)} jobs")
                    else:
                        results["data"]["khamsat"] = {
                            "error": "No jobs found or blocked"
                        }

            except Exception as e:
                results["data"]["khamsat"] = {"error": str(e)}
                logger.error(f"❌ Khamsat error: {e}")

        return {"success": True, **results}

    except Exception as e:
        logger.error(f"❌ External data test failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.post("/enhanced-refresh")
async def enhanced_refresh_market_data(
    year: int = 2026,
    use_external: bool = Query(True, description="Use external APIs and scrapers"),
    use_llm: bool = Query(True, description="Use LLM generation"),
):
    """
    Enhanced market data refresh with external data sources.
    Combines API data, web scraping, and LLM generation.
    """
    try:
        from app import langchain_manager
        import config

        logger.info(f"🚀 Starting ENHANCED market data refresh for {year}")
        logger.info(f"   External Data: {use_external}, LLM: {use_llm}")

        profiles_path = Path("data/generated_courses_Mar_17.json")
        if not profiles_path.exists():
            profiles_path = Path("data/courses_content.json")

        with open(profiles_path, encoding="utf-8") as f:
            profiles = json.load(f)

        logger.info(f"✅ Loaded {len(profiles)} job profiles")

        if use_external:
            try:
                from multi_agent_market import run_enhanced_market_research

                provider = config.current_settings.get("ai_provider", "gemini")

                result = await run_enhanced_market_research(
                    job_profiles=profiles, year=year, provider=provider
                )

                if result.get("success"):
                    return {
                        "success": True,
                        "message": "Enhanced market data refresh complete",
                        "total_records": result.get("total_records", 0),
                        "sources_used": result.get("sources_used", []),
                        "validation": result.get("validation", {}),
                        "mode": "enhanced_multi_agent",
                    }
                else:
                    logger.warning(
                        f"⚠️ Enhanced mode failed: {result.get('error')}. Falling back to standard mode."
                    )

            except ImportError as e:
                logger.warning(f"⚠️ Enhanced module not available: {e}")
            except Exception as e:
                logger.warning(f"⚠️ Enhanced refresh failed: {e}")

        return await refresh_market_data(year=year, use_agents=True)

    except Exception as e:
        logger.error(f"❌ Enhanced refresh failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.get("/salary-estimates")
async def get_salary_estimates(
    job_title: str = Query(..., description="Job title for salary lookup"),
    location: str = Query("Egypt", description="Location (Egypt, UK, US, etc.)"),
):
    """
    Get salary estimates from multiple sources for a job title.
    """
    try:
        from market_api_client import SalaryAPIClient

        async with SalaryAPIClient() as client:
            estimates = []

            if location.lower() == "egypt":
                salary = await client.get_egypt_salary_estimate(job_title)
                estimates.append(
                    {
                        "source": "Egypt Market Average",
                        "location": "Egypt",
                        "salary_min": salary.salary_min,
                        "salary_max": salary.salary_max,
                        "salary_median": salary.salary_median,
                        "currency": salary.currency,
                        "period": salary.period,
                        "confidence": salary.confidence,
                    }
                )

            indeed_salaries = await client.get_indeed_salary(
                job_title, country="eg" if location.lower() == "egypt" else "gb"
            )
            for sal in indeed_salaries:
                estimates.append(sal.to_dict())

            return {
                "success": True,
                "job_title": job_title,
                "location": location,
                "estimates": estimates,
                "sources_count": len(estimates),
            }

    except Exception as e:
        logger.error(f"❌ Salary lookup failed: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@router.post("/sync-vector-store")
async def sync_market_vector_store():
    """Index all market profiles into ChromaDB for offline edge vector search"""
    try:
        try:
            from chromadb_client import ChromaDBClient
        except ImportError:
            try:
                from .chromadb_client import ChromaDBClient
            except ImportError:
                ChromaDBClient = None

        if ChromaDBClient is None:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "ChromaDBClient not available on this edge device"},
            )

        df = load_and_prepare_dataframe()
        chroma_client = ChromaDBClient()
        collection_name = "market_job_profiles"

        try:
            collection = chroma_client.client.get_or_create_collection(
                name=collection_name,
                embedding_function=chroma_client.embedding_function,
            )
        except Exception as e:
            logger.warning(f"Error accessing Chroma collection: {e}")
            return JSONResponse(
                status_code=500, content={"success": False, "error": str(e)}
            )

        documents = []
        metadatas = []
        ids = []

        for idx, row in df.iterrows():
            title = str(row.get("Title", f"Job_{idx}"))
            track = str(row.get("Track", ""))
            skills = str(row.get("AI_Extracted_Skills", ""))
            courses = str(row.get("Courses", ""))
            desc = str(row.get("Description", ""))
            doc = f"Job Title: {title}. Track: {track}. Required Skills: {skills}. Courses: {courses}. Description: {desc}"

            meta = {
                "title": title,
                "track": track,
                "global_demand": int(row.get("Global_Job_Demand", 0)),
                "egypt_demand": int(row.get("Egypt_Job_Demand", 0)),
                "freelance_opportunities": int(row.get("Freelancing_Opportunities", 0)),
                "rating": float(row.get("Market_Attractiveness_Rating", 0)),
            }
            documents.append(doc)
            metadatas.append(meta)
            ids.append(f"market_profile_{idx}")

        if documents:
            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(
                f"✅ Indexed {len(documents)} market profiles into ChromaDB collection '{collection_name}'"
            )

        return {
            "success": True,
            "message": f"Successfully indexed {len(documents)} profiles into ChromaDB collection '{collection_name}'",
            "indexed_count": len(documents),
            "collection": collection_name,
        }
    except Exception as e:
        logger.error(f"Failed to sync vector store: {e}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )

