"""
Market Data System - Integration Test Script
============================================

Tests all new endpoints and features:
1. External data sources (APIs & Scrapers)
2. Salary estimation
3. Enhanced market refresh
4. Existing market charts

Usage:
    python test_market_integration.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_api_clients():
    """Test external API clients"""
    print("\n" + "=" * 60)
    print("TEST 1: External API Clients")
    print("=" * 60)

    from market_api_client import JobAPIClient, SalaryAPIClient

    # Test Adzuna
    print("\n1.1 Adzuna API (UK/EU Jobs):")
    async with JobAPIClient() as client:
        jobs = await client.search_adzuna("Full Stack Developer", country="gb")
        print(f"    ✅ Found {len(jobs)} jobs")
        if jobs:
            print(f"    Sample: {jobs[0].title} at {jobs[0].company}")
            print(
                f"    Salary: {jobs[0].salary_min}-{jobs[0].salary_max} {jobs[0].salary_currency}"
            )

    # Test Egypt Salary
    print("\n1.2 Egypt Salary Estimates:")
    async with SalaryAPIClient() as client:
        titles = [
            "Python Developer",
            "Full Stack Developer",
            "Data Scientist",
            "DevOps Engineer",
        ]
        for title in titles:
            salary = await client.get_egypt_salary_estimate(title)
            print(
                f"    ✅ {title}: {salary.salary_min:,}-{salary.salary_max:,} {salary.currency}/year"
            )

    return True


async def test_web_scrapers():
    """Test web scrapers with fallback"""
    print("\n" + "=" * 60)
    print("TEST 2: Web Scrapers")
    print("=" * 60)

    from market_scraper import EgyptianJobScraper

    print("\n2.1 Egyptian Job Scraper:")
    scraper = EgyptianJobScraper()

    platforms = ["wuzzuf", "khamsat"]
    results = await scraper.scrape_all("Python Developer", platforms=platforms)

    for platform, jobs in results.items():
        print(f"    ✅ {platform}: {len(jobs)} jobs")
        if jobs:
            job = jobs[0]
            print(f"       Sample: {job.title} at {job.company}")
            if job.salary_min:
                print(
                    f"       Salary: {job.salary_min}-{job.salary_max} {job.salary_currency}"
                )

    return True


async def test_multi_agent_pipeline():
    """Test the multi-agent pipeline"""
    print("\n" + "=" * 60)
    print("TEST 3: Multi-Agent Pipeline")
    print("=" * 60)

    from multi_agent_market import ExternalDataAgent, FusionAgent

    class MockLLM:
        async def ainvoke(self, prompt):
            class Resp:
                content = '{"title": "Test Job", "global_job_demand": 1000}'

            return Resp()

    print("\n3.1 ExternalDataAgent:")
    llm = MockLLM()
    agent = ExternalDataAgent(llm)

    test_state = {
        "job_profiles": [
            {
                "title": "Python Developer",
                "Track": "Web Development",
                "Courses": "Python, Django, Flask",
            },
            {
                "title": "Data Scientist",
                "Track": "Data Science",
                "Courses": "Python, ML, Statistics",
            },
        ],
        "year": 2026,
        "errors": [],
    }

    result = await agent.process(test_state)
    print(f"    ✅ Processed {len(result.get('external_data', []))} profiles")

    print("\n3.2 FusionAgent:")
    fusion_agent = FusionAgent(llm)
    result = await fusion_agent.process(result)
    print(f"    ✅ Fused {len(result.get('fused_data', []))} records")

    return True


def test_endpoints_structure():
    """Verify endpoint structure in market.py"""
    print("\n" + "=" * 60)
    print("TEST 4: Endpoint Structure")
    print("=" * 60)

    from market import router

    endpoints = [
        "/api/market/external-test",
        "/api/market/enhanced-refresh",
        "/api/market/salary-estimates",
        "/api/market/charts",
        "/api/market/gap-analysis",
        "/api/market/freelance-jobs",
        "/api/market/accuracy-report",
    ]

    print("\n4.1 Registered Endpoints:")
    for ep in endpoints:
        rel_ep = ep.replace("/api/market", "")
        found = any(r.path in (ep, rel_ep) for r in router.routes)
        status = "✅" if found else "❌"
        print(f"    {status} {ep}")
        assert found, f"Endpoint {ep} not found in router.routes"


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "#" * 60)
    print("# MARKET DATA SYSTEM - INTEGRATION TESTS")
    print("#" * 60)

    results = []

    try:
        results.append(("API Clients", await test_api_clients()))
    except Exception as e:
        print(f"\n    ❌ API Clients test failed: {e}")
        results.append(("API Clients", False))

    try:
        results.append(("Web Scrapers", await test_web_scrapers()))
    except Exception as e:
        print(f"\n    ❌ Web Scrapers test failed: {e}")
        results.append(("Web Scrapers", False))

    try:
        results.append(("Multi-Agent Pipeline", await test_multi_agent_pipeline()))
    except Exception as e:
        print(f"\n    ❌ Multi-Agent Pipeline test failed: {e}")
        results.append(("Multi-Agent Pipeline", False))

    try:
        results.append(("Endpoint Structure", test_endpoints_structure()))
    except Exception as e:
        print(f"\n    ❌ Endpoint Structure test failed: {e}")
        results.append(("Endpoint Structure", False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"    {status}: {name}")

    print(f"\n    Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n    🎉 ALL TESTS PASSED!")
    else:
        print(f"\n    ⚠️  {total - passed} tests failed")

    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
