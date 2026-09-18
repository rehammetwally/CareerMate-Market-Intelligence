import asyncio
import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_reliability_integration():
    print("🚀 Testing Market Data Reliability Integration...")
    
    # 1. Test Accuracy Report Agent directly with a known file
    from agents.accuracy_report_agent import run_accuracy_report_agent
    
    test_csv = "data/MarketplaceResearchAll82JobTitlePlusSkills.csv"
    print(f"Checking accuracy report for {test_csv}...")
    
    result = await run_accuracy_report_agent(test_csv, include_recommendations=False)
    
    if result.get("success"):
        report = result.get("report", {})
        print(f"✅ Accuracy Report Generated Successfully")
        print(f"   Score: {report.get('reliability', {}).get('score')}/100")
        print(f"   Level: {report.get('reliability', {}).get('level')}")
        
        # Check if predictable path exists
        latest_path = Path("data/accuracy_reports/market_report_2026.json")
        if latest_path.exists():
            print(f"✅ Latest report file exists at {latest_path}")
        else:
            print(f"❌ Latest report file NOT found at {latest_path}")
    else:
        print(f"❌ Accuracy Report Generation Failed: {result.get('error')}")

    # 2. Test the Reliability Alias endpoint logic (internal call)
    from market import check_csv_accuracy
    print("\nTesting reliability endpoint logic...")
    rel_result = await check_csv_accuracy(year=2026)
    if rel_result.get("success"):
        print(f"✅ Reliability check successful: Score {rel_result.get('reliability_score')}")
    else:
        print(f"❌ Reliability check failed: {rel_result.get('error')}")

    print("\n✅ Reliability Integration Verification Complete")

if __name__ == "__main__":
    asyncio.run(test_reliability_integration())
