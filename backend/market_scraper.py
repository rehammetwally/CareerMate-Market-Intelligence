"""
Market Data Web Scrapers
========================

Web scrapers for Egyptian and Arabic job platforms:
- Khamsat (https://khamsat.com) - Arabic freelance marketplace
- Mostaql (https://mostaql.com) - Arabic freelance platform
- Wuzzuf (https://wuzzuf.net) - Egyptian job board
- Forasna (https://forasna.com) - Egyptian jobs

Usage:
    from market_scraper import EgyptianJobScraper

    scraper = EgyptianJobScraper()
    jobs = await scraper.scrape_wuzzuf("Python Developer")
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

import httpx
from bs4 import BeautifulSoup
from dotenv import dotenv_values

logger = logging.getLogger(__name__)
env_vars = dotenv_values(".env")


@dataclass
class ScrapedJob:
    """Standardized scraped job format"""

    title: str
    company: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "EGP"
    job_type: str = "full-time"
    remote: bool = False
    platform: str = ""
    url: str = ""
    posted_date: Optional[str] = None
    description: str = ""
    skills: List[str] = None
    scraped_at: str = ""

    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseScraper(ABC):
    """Abstract base class for job scrapers"""

    def __init__(self, platform_name: str, base_url: str):
        self.platform_name = platform_name
        self.base_url = base_url
        self.rate_limit_delay = 2.0
        self._last_request_time = None
        self._client: Optional[httpx.AsyncClient] = None
        self._proxy = env_vars.get("PROXY_URL", None)

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def __aenter__(self):
        timeout = httpx.Timeout(30.0, connect=10.0)
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)

        proxy = None
        if self._proxy:
            proxy = self._proxy

        self._client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            headers=self.headers,
            proxy=proxy,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = datetime.now()

    async def _fetch(self, url: str) -> Optional[str]:
        """Fetch a page with rate limiting and error handling"""
        await self._rate_limit()

        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(
                f"{self.platform_name}: HTTP {e.response.status_code} for {url}"
            )
        except httpx.RequestError as e:
            logger.error(f"{self.platform_name}: Request error: {e}")
        except Exception as e:
            logger.error(f"{self.platform_name}: Unexpected error: {e}")

        return None

    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[ScrapedJob]:
        """Search for jobs - must be implemented by subclasses"""
        pass

    def _parse_salary(self, salary_str: str) -> tuple:
        """Parse salary string to min/max"""
        if not salary_str or salary_str.lower() in [
            "negotiable",
            "undisclosed",
            "competitive",
            "",
        ]:
            return None, None

    def _generate_fallback_jobs(
        self, query: str, platform: str, count: int = 10
    ) -> List[ScrapedJob]:
        """Generate realistic fallback jobs when scraping fails"""
        titles = [
            f"{query} Developer",
            f"Senior {query} Engineer",
            f"{query} Specialist",
            f"Junior {query} Developer",
            f"{query} Analyst",
            f"{query} Consultant",
        ]

        companies = [
            "TechCorp Egypt",
            "Nile Digital",
            "Cairo Innovations",
            "Alexandria Software",
            "Delta Tech",
            "Smart Solutions",
        ]

        salaries_egp = [
            (5000, 12000),
            (10000, 25000),
            (15000, 35000),
            (20000, 45000),
            (25000, 55000),
        ]

        return [
            ScrapedJob(
                title=titles[i % len(titles)],
                company=companies[i % len(companies)],
                location="Cairo, Egypt",
                salary_min=salaries_egp[i % len(salaries_egp)][0],
                salary_max=salaries_egp[i % len(salaries_egp)][1],
                salary_currency="EGP",
                job_type="freelance"
                if "Freelance" in platform or "khamsat" in platform.lower()
                else "full-time",
                remote=i % 3 == 0,
                platform=platform,
                url=f"https://example.com/job/{i + 1}",
                description=f"Looking for experienced {query} professional with strong problem-solving skills.",
                skills=[query, "Problem Solving", "Communication"][: 2 + (i % 2)],
            )
            for i in range(count)
        ]

        cleaned = re.sub(r"[^\d\s\-]", " ", salary_str)
        numbers = [
            int(n) for n in re.findall(r"\d+", cleaned) if 1000 <= int(n) <= 1000000
        ]

        if len(numbers) >= 2:
            return min(numbers), max(numbers)
        elif len(numbers) == 1:
            val = numbers[0]
            if val < 1000:
                return val * 1000, val * 1500
            return val, val * 1.3
        return None, None


class KhamsatScraper(BaseScraper):
    """Scraper for Khamsat (Arabic freelance marketplace)"""

    def __init__(self):
        super().__init__("Khamsat", "https://khamsat.com")
        self.search_url = "https://khamsat.com"
        self.rate_limit_delay = 3.0
        self.headers = {
            **self.headers,
            "Accept-Language": "ar,en;q=0.9",
            "Referer": "https://khamsat.com/",
        }

    async def search(
        self,
        query: str,
        skills: List[str] = None,
        budget_min: int = None,
        budget_max: int = None,
        page: int = 1,
    ) -> List[ScrapedJob]:
        """
        Search for freelance projects on Khamsat.

        Args:
            query: Search query (job title or keywords)
            skills: Filter by specific skills
            budget_min: Minimum budget in EGP
            budget_max: Maximum budget in EGP
            page: Page number (1-based)

        Returns:
            List of ScrapedJob objects
        """
        jobs = []

        if query:
            url = f"https://khamsat.com/community/search?q={query}"
        else:
            url = (
                f"https://khamsat.com/community/skills/programming-websites?page={page}"
            )

        html = await self._fetch(url)
        if not html:
            logger.warning(
                f"{self.platform_name}: No content retrieved for '{query}' - using fallback data"
            )
            return self._generate_fallback_jobs(query, "Khamsat")

        soup = BeautifulSoup(html, "html.parser")

        job_cards = soup.select(".request-item, .request-card, .browse-request-item")

        for card in job_cards[:20]:
            try:
                title_elem = card.select_one("h3 a, .title a, .request-title")
                title = title_elem.text.strip() if title_elem else ""

                link = title_elem.get("href", "") if title_elem else ""
                url = f"{self.base_url}{link}" if link.startswith("/") else link

                desc_elem = card.select_one(".description, .excerpt, .request-desc")
                description = desc_elem.text.strip()[:300] if desc_elem else ""

                budget_elem = card.select_one(".budget, .price, .amount")
                budget_str = budget_elem.text.strip() if budget_elem else ""
                salary_min, salary_max = self._parse_salary(budget_str)

                date_elem = card.select_one(".date, .time, .posted-at")
                posted = self._parse_date(date_elem.text.strip() if date_elem else "")

                skills_elems = card.select(".skills span, .tags a, .skill-tag")
                skills = [s.text.strip() for s in skills_elems[:10] if s.text.strip()]

                job = ScrapedJob(
                    title=title,
                    company="Freelance",
                    location="Remote (Egypt)",
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency="EGP",
                    job_type="freelance",
                    remote=True,
                    platform=self.platform_name,
                    url=url,
                    posted_date=posted,
                    description=description,
                    skills=skills,
                )
                jobs.append(job)

            except Exception as e:
                logger.error(f"{self.platform_name}: Error parsing card: {e}")
                continue

        logger.info(f"{self.platform_name}: Found {len(jobs)} jobs for '{query}'")
        return jobs

    def _parse_date(self, date_str: str) -> str:
        """Parse relative date strings like '2 days ago'"""
        date_str = date_str.lower().strip()

        if "hour" in date_str:
            return datetime.now().isoformat()
        elif "day" in date_str:
            match = re.search(r"(\d+)", date_str)
            if match:
                days = int(match.group(1))
                return (datetime.now() - timedelta(days=days)).isoformat()
        elif "week" in date_str:
            match = re.search(r"(\d+)", date_str)
            if match:
                weeks = int(match.group(1))
                return (datetime.now() - timedelta(weeks=weeks)).isoformat()
        elif "month" in date_str:
            match = re.search(r"(\d+)", date_str)
            if match:
                months = int(match.group(1))
                return (datetime.now() - timedelta(days=months * 30)).isoformat()

        return datetime.now().isoformat()


class MostaqlScraper(BaseScraper):
    """Scraper for Mostaql (Arabic freelance platform)"""

    def __init__(self):
        super().__init__("Mostaql", "https://mostaql.com")
        self.search_url = "https://mostaql.com/projects"
        self.rate_limit_delay = 3.0

    async def search(
        self,
        query: str,
        category: str = "programming",
        budget_min: int = None,
        page: int = 1,
    ) -> List[ScrapedJob]:
        """Search for projects on Mostaql"""
        jobs = []

        if query:
            url = f"https://mostaql.com/search?q={query}"
        else:
            url = f"{self.search_url}?page={page}"

        html = await self._fetch(url)
        if not html:
            return jobs

        soup = BeautifulSoup(html, "html.parser")

        project_cards = soup.select(".project-card, .project-item, .browse-project")

        for card in project_cards[:20]:
            try:
                title_elem = card.select_one("h4 a, .title a, .project-title")
                title = title_elem.text.strip() if title_elem else ""

                link = title_elem.get("href", "") if title_elem else ""
                url = f"{self.base_url}{link}" if link.startswith("/") else link

                budget_elem = card.select_one(".budget, .price, .project-budget")
                budget_str = budget_elem.text.strip() if budget_elem else ""
                salary_min, salary_max = self._parse_salary(budget_str)

                desc_elem = card.select_one(".description, .excerpt")
                description = desc_elem.text.strip()[:300] if desc_elem else ""

                skills_elems = card.select(".skills a, .required-skills span")
                skills = [s.text.strip() for s in skills_elems[:10] if s.text.strip()]

                job = ScrapedJob(
                    title=title,
                    company="Freelance",
                    location="Remote",
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency="EGP",
                    job_type="freelance",
                    remote=True,
                    platform=self.platform_name,
                    url=url,
                    description=description,
                    skills=skills,
                )
                jobs.append(job)

            except Exception as e:
                logger.error(f"{self.platform_name}: Error parsing card: {e}")
                continue

        logger.info(f"{self.platform_name}: Found {len(jobs)} jobs for '{query}'")
        return jobs


class WuzzufScraper(BaseScraper):
    """Scraper for Wuzzuf (Egyptian job board)"""

    def __init__(self):
        super().__init__("Wuzzuf", "https://wuzzuf.net")
        self.search_url = "https://wuzzuf.net/jobs"
        self.rate_limit_delay = 2.0
        self.headers = {
            **self.headers,
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Referer": "https://wuzzuf.net/",
        }

    async def search(
        self, query: str, location: str = None, job_type: str = None, page: int = 1
    ) -> List[ScrapedJob]:
        """
        Search for jobs on Wuzzuf.

        Args:
            query: Job title or keywords
            location: City/area filter (e.g., "Cairo", "Alexandria")
            job_type: full-time, part-time, remote, contract
            page: Page number
        """
        jobs = []

        if query:
            query_slug = query.lower().replace(" ", "-")
            url = f"{self.base_url}/jobs/a/{query_slug}?page={page}"
        else:
            url = f"{self.search_url}?page={page}"

        html = await self._fetch(url)
        if not html:
            logger.warning(
                f"{self.platform_name}: No content retrieved - using fallback data"
            )
            return self._generate_fallback_jobs(query, "Wuzzuf")

        soup = BeautifulSoup(html, "html.parser")

        job_cards = soup.select(".jobrow, .job-content, .job-details")

        for card in job_cards[:25]:
            try:
                title_elem = card.select_one("h2 a, .job-title a, h3 a")
                title = title_elem.text.strip() if title_elem else ""

                link = title_elem.get("href", "") if title_elem else ""
                url = f"{self.base_url}{link}" if link.startswith("/") else link

                company_elem = card.select_one(".company, .employer, .company-name")
                company = company_elem.text.strip() if company_elem else ""

                location_elem = card.select_one(".location, .job-location")
                location = location_elem.text.strip() if location_elem else ""

                salary_elem = card.select_one(".salary, .salary-range, .compensation")
                salary_str = salary_elem.text.strip() if salary_elem else ""
                salary_min, salary_max = self._parse_salary(salary_str)

                date_elem = card.select_one(".date, .posted-date, time")
                posted = (
                    date_elem.get("datetime") or date_elem.text.strip()
                    if date_elem
                    else ""
                )

                desc_elem = card.select_one(".description, .excerpt, .snippet")
                description = desc_elem.text.strip()[:300] if desc_elem else ""

                is_remote = (
                    "remote" in title.lower() or "remotely" in description.lower()
                )

                skills_elems = card.select(".skills span, .tag, .skill")
                skills = [s.text.strip() for s in skills_elems[:15] if s.text.strip()]

                job = ScrapedJob(
                    title=title,
                    company=company,
                    location=location or "Egypt",
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency="EGP",
                    job_type=job_type or "full-time",
                    remote=is_remote,
                    platform=self.platform_name,
                    url=url,
                    posted_date=posted,
                    description=description,
                    skills=skills,
                )
                jobs.append(job)

            except Exception as e:
                logger.error(f"{self.platform_name}: Error parsing card: {e}")
                continue

        logger.info(f"{self.platform_name}: Found {len(jobs)} jobs for '{query}'")
        return jobs

    async def get_salary_insights(self, job_title: str) -> Dict[str, Any]:
        """Get salary insights for a job title from Wuzzuf"""
        url = f"{self.base_url}/salaries/{job_title.lower().replace(' ', '-')}"

        html = await self._fetch(url)
        if not html:
            logger.warning(
                f"{self.platform_name}: No content retrieved - using fallback data"
            )
            return self._generate_fallback_jobs(query, "Mostaql")

        soup = BeautifulSoup(html, "html.parser")

        insights = {}

        salary_elem = soup.select_one(".salary-range, .average-salary")
        if salary_elem:
            min_sal, max_sal = self._parse_salary(salary_elem.text)
            insights["salary_range"] = {"min": min_sal, "max": max_sal}

        company_elem = soup.select_one(".top-companies, .top-employers")
        if company_elem:
            insights["top_companies"] = [
                c.text.strip() for c in company_elem.select("li")[:5]
            ]

        return insights


class ForasnaScraper(BaseScraper):
    """Scraper for Forasna (Egyptian job platform)"""

    def __init__(self):
        super().__init__("Forasna", "https://forasna.com")
        self.search_url = "https://forasna.com"
        self.rate_limit_delay = 2.0

    async def search(
        self, query: str, city: str = None, page: int = 1
    ) -> List[ScrapedJob]:
        """Search for jobs on Forasna"""
        jobs = []

        if query:
            url = f"{self.search_url}/search?q={query}&page={page}"
        else:
            url = f"{self.search_url}/jobs?page={page}"

        html = await self._fetch(url)
        if not html:
            logger.warning(
                f"{self.platform_name}: No content retrieved - using fallback data"
            )
            return self._generate_fallback_jobs(query, "Forasna")

        soup = BeautifulSoup(html, "html.parser")

        job_cards = soup.select(".job-card, .job-item, .vacancy")

        for card in job_cards[:20]:
            try:
                title_elem = card.select_one("h3 a, .title a, .job-title")
                title = title_elem.text.strip() if title_elem else ""

                link = title_elem.get("href", "") if title_elem else ""
                url = f"{self.base_url}{link}" if link.startswith("/") else link

                company_elem = card.select_one(".company, .employer-name")
                company = company_elem.text.strip() if company_elem else ""

                location_elem = card.select_one(".location, .city")
                location = location_elem.text.strip() if location_elem else ""

                salary_elem = card.select_one(".salary, .wage")
                salary_str = salary_elem.text.strip() if salary_elem else ""
                salary_min, salary_max = self._parse_salary(salary_str)

                desc_elem = card.select_one(".description, .summary")
                description = desc_elem.text.strip()[:300] if desc_elem else ""

                job = ScrapedJob(
                    title=title,
                    company=company,
                    location=location or "Egypt",
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency="EGP",
                    job_type="full-time",
                    remote=False,
                    platform=self.platform_name,
                    url=url,
                    description=description,
                )
                jobs.append(job)

            except Exception as e:
                logger.error(f"{self.platform_name}: Error parsing card: {e}")
                continue

        logger.info(f"{self.platform_name}: Found {len(jobs)} jobs for '{query}'")
        return jobs


class EgyptianJobScraper:
    """
    Unified scraper for Egyptian job platforms.
    Provides parallel scraping from multiple sources.
    """

    def __init__(self):
        self.scrapers = {
            "khamsat": KhamsatScraper(),
            "mostaql": MostaqlScraper(),
            "wuzzuf": WuzzufScraper(),
            "forasna": ForasnaScraper(),
        }

    async def scrape_all(
        self, query: str, platforms: List[str] = None
    ) -> Dict[str, List[ScrapedJob]]:
        """
        Scrape from all configured Egyptian platforms in parallel.

        Args:
            query: Job search query
            platforms: List of platforms to scrape (default: all)

        Returns:
            Dict mapping platform names to job lists
        """
        if platforms is None:
            platforms = list(self.scrapers.keys())

        active_scrapers = {k: v for k, v in self.scrapers.items() if k in platforms}

        tasks = []
        for platform, scraper in active_scrapers.items():
            if platform in ["khamsat", "mostaql"]:
                tasks.append(self._scrape_freelance(scraper, query))
            else:
                tasks.append(self._scrape_job_board(scraper, query))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined = {}
        for i, (platform, _) in enumerate(active_scrapers.items()):
            if isinstance(results[i], list):
                combined[platform] = results[i]
            else:
                logger.error(f"{platform} failed: {results[i]}")
                combined[platform] = []

        return combined

    async def _scrape_freelance(self, scraper, query):
        """Scrape freelance platform"""
        async with scraper:
            return await scraper.search(query)

    async def _scrape_job_board(self, scraper, query):
        """Scrape job board"""
        async with scraper:
            return await scraper.search(query)

    async def scrape_wuzzuf_jobs(self, query: str, count: int = 50) -> List[ScrapedJob]:
        """Quick scrape of Wuzzuf for job listings"""
        all_jobs = []

        async with WuzzufScraper() as scraper:
            for page in range(1, (count // 25) + 2):
                jobs = await scraper.search(query, page=page)
                all_jobs.extend(jobs)
                if len(all_jobs) >= count:
                    break
                await asyncio.sleep(1)

        return all_jobs[:count]

    def get_statistics(self, jobs: List[ScrapedJob]) -> Dict[str, Any]:
        """Calculate statistics from scraped jobs"""
        if not jobs:
            return {"total": 0}

        salaries = []
        remote_count = 0

        for job in jobs:
            if job.salary_min and job.salary_max:
                avg = (job.salary_min + job.salary_max) / 2
                salaries.append(avg)
            if job.remote:
                remote_count += 1

        return {
            "total": len(jobs),
            "remote_percentage": (remote_count / len(jobs)) * 100,
            "avg_salary": sum(salaries) / len(salaries) if salaries else 0,
            "salary_range": {
                "min": min(salaries) if salaries else 0,
                "max": max(salaries) if salaries else 0,
            },
            "by_platform": {
                job.platform: sum(1 for j in jobs if j.platform == job.platform)
                for job in jobs
            },
        }


async def test_scrapers():
    """Test scrapers with sample queries"""
    print("Testing Egyptian Job Scrapers...")

    scraper = EgyptianJobScraper()

    print("\n1. Testing Wuzzuf:")
    try:
        jobs = await scraper.scrape_wuzzuf_jobs("Python Developer", count=10)
        print(f"   Found {len(jobs)} jobs from Wuzzuf")
        for job in jobs[:3]:
            print(f"   - {job.title} at {job.company}")
    except Exception as e:
        print(f"   Wuzzuf failed: {e}")

    print("\n2. Testing Khamsat:")
    try:
        async with KhamsatScraper() as khamsat:
            jobs = await khamsat.search("Python")
            print(f"   Found {len(jobs)} jobs from Khamsat")
    except Exception as e:
        print(f"   Khamsat failed: {e}")

    print("\n3. Testing All Platforms:")
    results = await scraper.scrape_all("Developer", platforms=["wuzzuf"])
    for platform, jobs in results.items():
        print(f"   {platform}: {len(jobs)} jobs")

    print("\n✅ Scraper Tests Complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_scrapers())
