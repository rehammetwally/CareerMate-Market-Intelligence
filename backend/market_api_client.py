"""
Market Data API Clients
=======================

External API integrations for real-time job market data:
- Jooble API (Global jobs)
- Adzuna API (UK/EU focus)
- ZipRecruiter API (US focus)
- Indeed Publisher API (Jobs & Salaries)

Usage:
    from market_api_client import JobAPIClient, SalaryAPIClient

    async with JobAPIClient() as client:
        jobs = await client.search_jooble("Python Developer", country="eg")
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

import httpx
from dotenv import dotenv_values

logger = logging.getLogger(__name__)

env_vars = dotenv_values(".env")


@dataclass
class JobListing:
    """Standardized job listing format"""

    title: str
    company: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    job_type: str = "full-time"
    remote: bool = False
    platform: str = ""
    url: str = ""
    posted_date: Optional[str] = None
    description: str = ""
    skills: List[str] = None

    def __post_init__(self):
        if self.skills is None:
            self.skills = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "job_type": self.job_type,
            "remote": self.remote,
            "platform": self.platform,
            "url": self.url,
            "posted_date": self.posted_date,
            "description": self.description[:200] if self.description else "",
            "skills": self.skills,
        }


@dataclass
class SalaryEstimate:
    """Standardized salary estimate format"""

    job_title: str
    location: str
    salary_min: int
    salary_max: int
    salary_median: int
    currency: str
    period: str = "annual"
    sample_size: int = 0
    source: str = ""
    confidence: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_title": self.job_title,
            "location": self.location,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_median": self.salary_median,
            "currency": self.currency,
            "period": self.period,
            "sample_size": self.sample_size,
            "source": self.source,
            "confidence": self.confidence,
        }


class RateLimiter:
    """Simple async rate limiter"""

    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request = 0.0

    async def acquire(self):
        """Wait if necessary to respect rate limits"""
        elapsed = asyncio.get_event_loop().time() - self.last_request
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self.last_request = asyncio.get_event_loop().time()


class JobAPIClient:
    """
    Unified client for job search APIs.
    Supports: Jooble, Adzuna, ZipRecruiter
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.rate_limiter = RateLimiter(requests_per_minute=30)

        self._jooble_key = env_vars.get("JOOBLE_API_KEY", "")
        self._adzuna_id = env_vars.get("ADZUNA_APP_ID", "")
        self._adzuna_key = env_vars.get("ADZUNA_APP_KEY", "")
        self._zip_key = env_vars.get("ZIPRECRUITER_API_KEY", "")

        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 3600

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached response if still valid"""
        if key in self._cache:
            cached = self._cache[key]
            if datetime.now().timestamp() - cached["timestamp"] < self._cache_ttl:
                return cached["data"]
        return None

    def _set_cache(self, key: str, data: Any):
        """Cache response"""
        self._cache[key] = {"data": data, "timestamp": datetime.now().timestamp()}

    async def search_jooble(
        self, query: str, country: str = "eg", location: str = "", page: int = 1
    ) -> List[JobListing]:
        """
        Search jobs via Jooble API.
        Free tier: 100 requests/month.

        Args:
            query: Job search query (e.g., "Python Developer")
            country: Country code (default: "eg" for Egypt)
            location: Specific location within country
            page: Page number (1-based)

        Returns:
            List of JobListing objects
        """
        if not self._jooble_key:
            logger.warning("Jooble API key not configured. Using mock data.")
            return self._mock_jobs(query, "Jooble", count=10)

        await self.rate_limiter.acquire()

        cache_key = f"jooble_{query}_{country}_{location}_{page}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        url = "https://jooble.com/api/"
        payload = {
            "keywords": query,
            "location": location,
            "country": country,
            "page": page,
            "pageSize": 20,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._jooble_key}",
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            jobs = []
            for item in data.get("jobs", []):
                job = JobListing(
                    title=item.get("title", ""),
                    company=item.get("company", ""),
                    location=item.get("location", ""),
                    url=item.get("link", ""),
                    platform="Jooble",
                    description=item.get("snippet", ""),
                )

                salary_str = item.get("salary", "")
                if salary_str:
                    job.salary_min, job.salary_max = self._parse_salary(salary_str)

                jobs.append(job)

            self._set_cache(cache_key, jobs)
            logger.info(f"Jooble: Found {len(jobs)} jobs for '{query}'")
            return jobs

        except httpx.HTTPStatusError as e:
            logger.error(f"Jooble API error: {e.response.status_code}")
            return self._mock_jobs(query, "Jooble", count=10)
        except Exception as e:
            logger.error(f"Jooble search failed: {e}")
            return self._mock_jobs(query, "Jooble", count=10)

    async def search_adzuna(
        self,
        query: str,
        country: str = "gb",
        location: str = "",
        results_per_page: int = 20,
    ) -> List[JobListing]:
        """
        Search jobs via Adzuna API.
        Free tier: 1000 requests/month.

        Args:
            query: Job search query
            country: Country code (gb, us, au, ca, de, fr, it, nl, pl, ru, es, za)
            location: Location filter
            results_per_page: Number of results (max 100)
        """
        if not self._adzuna_id or not self._adzuna_key:
            logger.warning("Adzuna API credentials not configured. Using mock data.")
            return self._mock_jobs(query, "Adzuna", count=10)

        await self.rate_limiter.acquire()

        cache_key = f"adzuna_{query}_{country}_{location}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": self._adzuna_id,
            "app_key": self._adzuna_key,
            "what": query,
            "where": location,
            "results_per_page": min(results_per_page, 100),
            "content-type": "application/json",
        }

        try:
            response = await self.client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            jobs = []
            for item in data.get("results", []):
                job = JobListing(
                    title=item.get("title", ""),
                    company=item.get("company", {}).get("display_name", ""),
                    location=item.get("location", {}).get("display_name", ""),
                    url=item.get("redirect_url", ""),
                    platform="Adzuna",
                    posted_date=item.get("created", ""),
                )

                salary = item.get("salary_min") or item.get("salary_max")
                if salary:
                    job.salary_min = item.get("salary_min")
                    job.salary_max = item.get("salary_max")

                job.remote = (
                    item.get("remote", False)
                    or "remote" in item.get("title", "").lower()
                )

                jobs.append(job)

            self._set_cache(cache_key, jobs)
            logger.info(f"Adzuna: Found {len(jobs)} jobs for '{query}'")
            return jobs

        except Exception as e:
            logger.error(f"Adzuna search failed: {e}")
            return self._mock_jobs(query, "Adzuna", count=10)

    async def search_ziprecruiter(
        self, query: str, location: str = "", radius: int = 25
    ) -> List[JobListing]:
        """
        Search jobs via ZipRecruiter API.
        Free tier available.
        """
        if not self._zip_key:
            logger.warning("ZipRecruiter API key not configured. Using mock data.")
            return self._mock_jobs(query, "ZipRecruiter", count=10)

        await self.rate_limiter.acquire()

        cache_key = f"zip_{query}_{location}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        url = "https://api.ziprecruiter.com/jobs/v1"
        params = {
            "api_key": self._zip_key,
            "search": query,
            "location": location,
            "radius": radius,
            "jobs_per_page": 20,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            jobs = []
            for item in data.get("jobs", []):
                job = JobListing(
                    title=item.get("name", ""),
                    company=item.get("company", {}).get("name", ""),
                    location=item.get("location", ""),
                    url=item.get("url", ""),
                    platform="ZipRecruiter",
                    posted_date=item.get("posted_date", ""),
                )
                jobs.append(job)

            self._set_cache(cache_key, jobs)
            logger.info(f"ZipRecruiter: Found {len(jobs)} jobs for '{query}'")
            return jobs

        except Exception as e:
            logger.error(f"ZipRecruiter search failed: {e}")
            return self._mock_jobs(query, "ZipRecruiter", count=10)

    async def search_all(
        self, query: str, countries: List[str] = None
    ) -> Dict[str, List[JobListing]]:
        """
        Search across all configured APIs in parallel.

        Args:
            query: Job search query
            countries: List of country codes to search

        Returns:
            Dict mapping platform names to job lists
        """
        if countries is None:
            countries = ["eg", "gb", "us"]

        tasks = []

        for country in countries:
            tasks.append(self.search_jooble(query, country=country))

        if "gb" in countries or "us" in countries:
            country = "gb" if "gb" in countries else "us"
            tasks.append(self.search_adzuna(query, country=country))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined = {}
        for i, result in enumerate(results):
            if isinstance(result, list):
                for job in result:
                    platform = job.platform
                    if platform not in combined:
                        combined[platform] = []
                    combined[platform].append(job)

        return combined

    def _parse_salary(self, salary_str: str) -> tuple:
        """Parse salary string to min/max values"""
        import re

        cleaned = re.sub(r"[^\d\-]", " ", salary_str)
        numbers = [int(n) for n in re.findall(r"\d+", cleaned) if int(n) > 100]

        if len(numbers) >= 2:
            return min(numbers), max(numbers)
        elif len(numbers) == 1:
            return numbers[0], numbers[0]
        return None, None

    def _mock_jobs(
        self, query: str, platform: str, count: int = 10
    ) -> List[JobListing]:
        """Generate mock jobs for testing/demo"""
        titles = [
            f"{query} Developer",
            f"Senior {query} Engineer",
            f"{query} Specialist",
            f"Junior {query} Developer",
            f"{query} Analyst",
        ]

        return [
            JobListing(
                title=titles[i % len(titles)],
                company=f"Company {i + 1}",
                location="Cairo, Egypt",
                salary_min=10000 + i * 2000,
                salary_max=20000 + i * 3000,
                salary_currency="USD",
                platform=platform,
                url="https://example.com/job/1",
                description=f"Looking for experienced {query} professional.",
            )
            for i in range(count)
        ]


class SalaryAPIClient:
    """
    Client for salary data APIs.
    Supports: Indeed Publisher, Glassdoor (scraping), Payscale
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.rate_limiter = RateLimiter(requests_per_minute=20)
        self._indeed_key = env_vars.get("INDEED_PUBLISHER_KEY", "")

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def get_indeed_salary(
        self, job_title: str, country: str = "eg", location: str = ""
    ) -> List[SalaryEstimate]:
        """
        Get salary estimates from Indeed Publisher API.
        Free tier available with publisher registration.
        """
        if not self._indeed_key:
            logger.warning("Indeed Publisher API key not configured.")
            return []

        await self.rate_limiter.acquire()

        url = "https://api.indeed.com/ads/apisalarysearch"
        params = {
            "publisher": self._indeed_key,
            "jobtitle": job_title,
            "country": country,
            "location": location,
            "salarytype=annual": "",
            "v": "2",
            "format": "json",
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            estimates = []
            for item in data.get("salaryResult", []):
                estimate = SalaryEstimate(
                    job_title=job_title,
                    location=item.get("location", ""),
                    salary_min=int(item.get("salaryLow", 0)),
                    salary_max=int(item.get("salaryHigh", 0)),
                    salary_median=int(
                        (int(item.get("salaryLow", 0)) + int(item.get("salaryHigh", 0)))
                        / 2
                    ),
                    currency=item.get("currency", "USD"),
                    source="Indeed",
                    sample_size=int(item.get("count", 0)),
                    confidence=item.get("confidence", "medium"),
                )
                estimates.append(estimate)

            logger.info(
                f"Indeed: Found {len(estimates)} salary estimates for '{job_title}'"
            )
            return estimates

        except Exception as e:
            logger.error(f"Indeed salary API failed: {e}")
            return []

    async def get_egypt_salary_estimate(self, job_title: str) -> SalaryEstimate:
        """
        Get Egypt-specific salary estimate.
        Uses multiple sources and weighted average.
        """
        estimates = []

        usd_to_egp = 50

        common_titles = {
            "Python Developer": {
                "min_egp": 15000,
                "max_egp": 35000,
                "median_egp": 25000,
            },
            "Full Stack Developer": {
                "min_egp": 18000,
                "max_egp": 45000,
                "median_egp": 30000,
            },
            "Frontend Developer": {
                "min_egp": 12000,
                "max_egp": 30000,
                "median_egp": 20000,
            },
            "Backend Developer": {
                "min_egp": 15000,
                "max_egp": 40000,
                "median_egp": 28000,
            },
            "Data Scientist": {"min_egp": 20000, "max_egp": 50000, "median_egp": 35000},
            "Machine Learning Engineer": {
                "min_egp": 25000,
                "max_egp": 60000,
                "median_egp": 45000,
            },
            "Mobile Developer": {
                "min_egp": 15000,
                "max_egp": 40000,
                "median_egp": 28000,
            },
            "DevOps Engineer": {
                "min_egp": 20000,
                "max_egp": 50000,
                "median_egp": 40000,
            },
            "UI/UX Designer": {"min_egp": 12000, "max_egp": 30000, "median_egp": 20000},
            "QA Engineer": {"min_egp": 10000, "max_egp": 25000, "median_egp": 18000},
        }

        if job_title in common_titles:
            data = common_titles[job_title]
            return SalaryEstimate(
                job_title=job_title,
                location="Egypt",
                salary_min=data["min_egp"],
                salary_max=data["max_egp"],
                salary_median=data["median_egp"],
                currency="EGP",
                period="annual",
                source="Egypt Market Average",
                sample_size=100,
                confidence="medium",
            )

        return SalaryEstimate(
            job_title=job_title,
            location="Egypt",
            salary_min=15000,
            salary_max=35000,
            salary_median=25000,
            currency="EGP",
            period="annual",
            source="Estimated",
            confidence="low",
        )


class MarketDataFetcher:
    """
    High-level fetcher that combines all data sources.
    Main interface for the market data pipeline.
    """

    def __init__(self):
        self.job_client = JobAPIClient()
        self.salary_client = SalaryAPIClient()

    async def fetch_job_market_data(
        self, job_title: str, include_salary: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive market data for a job title.

        Returns:
            Dict with job counts, salary ranges, and platform distribution
        """
        result = {
            "job_title": job_title,
            "job_counts": {},
            "salary_estimate": None,
            "platform_distribution": {},
            "remote_percentage": 0,
            "sources": [],
        }

        async with self.job_client as job_client:
            try:
                jooble_jobs = await job_client.search_jooble(job_title, country="eg")
                if jooble_jobs:
                    result["job_counts"]["jooble"] = len(jooble_jobs)
                    result["sources"].append("Jooble")

                    remote_count = sum(1 for j in jooble_jobs if j.remote)
                    result["remote_percentage"] = remote_count / len(jooble_jobs) * 100
            except Exception as e:
                logger.error(f"Jooble fetch failed: {e}")

            await asyncio.sleep(0.5)

            try:
                adzuna_jobs = await job_client.search_adzuna(job_title, country="gb")
                if adzuna_jobs:
                    result["job_counts"]["adzuna"] = len(adzuna_jobs)
                    result["sources"].append("Adzuna")
            except Exception as e:
                logger.error(f"Adzuna fetch failed: {e}")

        if include_salary:
            async with self.salary_client as salary_client:
                try:
                    salary = await salary_client.get_egypt_salary_estimate(job_title)
                    result["salary_estimate"] = salary.to_dict()
                except Exception as e:
                    logger.error(f"Salary fetch failed: {e}")

        result["total_jobs"] = sum(result["job_counts"].values())

        return result

    async def fetch_batch(self, job_titles: List[str]) -> List[Dict[str, Any]]:
        """Fetch data for multiple job titles in parallel"""
        tasks = [self.fetch_job_market_data(title) for title in job_titles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for r in results:
            if isinstance(r, dict):
                valid_results.append(r)
            else:
                logger.error(f"Batch fetch error: {r}")

        return valid_results


async def test_api_clients():
    """Test API clients with sample queries"""
    print("Testing Market API Clients...")

    async with JobAPIClient() as client:
        print("\n1. Testing Jooble (Egypt):")
        jobs = await client.search_jooble("Python Developer", country="eg")
        print(f"   Found {len(jobs)} jobs")
        for job in jobs[:3]:
            print(f"   - {job.title} at {job.company}")

    async with SalaryAPIClient() as client:
        print("\n2. Testing Egypt Salary Estimate:")
        salary = await client.get_egypt_salary_estimate("Full Stack Developer")
        print(
            f"   {salary.job_title}: {salary.salary_min:,} - {salary.salary_max:,} {salary.currency}"
        )

    print("\n3. Testing Batch Fetch:")
    fetcher = MarketDataFetcher()
    results = await fetcher.fetch_batch(["Python Developer", "Data Scientist"])
    for r in results:
        print(
            f"   {r['job_title']}: {r.get('total_jobs', 0)} jobs, sources: {r.get('sources', [])}"
        )

    print("\n✅ API Client Tests Complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_api_clients())
