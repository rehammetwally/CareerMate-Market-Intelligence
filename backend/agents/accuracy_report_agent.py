"""
Accuracy Report Agent
=====================

Generates detailed accuracy reports for market data.
- Summarizes reliability findings
- Provides detailed metrics breakdown
- Generates recommendations
- Creates visual-ready report data
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

from .base import BaseAgent
from .csv_reliability_agent import run_csv_reliability_agent

logger = logging.getLogger(__name__)


class AccuracyReportAgent(BaseAgent):
    """Agent that generates accuracy and reliability reports"""
    
    def __init__(self, llm=None):
        super().__init__(llm, name="AccuracyReportAgent")
        self.reports_history: List[Dict] = []

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate accuracy report"""
        csv_path = state.get("csv_path", "data/NewMarketplaceResearchAll82JobTitlePlusSkills.csv")
        include_recommendations = state.get("include_recommendations", True)
        year = state.get("year", 2026)
        
        self.log_info("Generating accuracy report...")
        
        # First, get reliability evaluation
        reliability = await run_csv_reliability_agent(csv_path)
        
        if not reliability.get("success"):
            return {
                "success": False,
                "error": reliability.get("error", "Reliability check failed")
            }
        
        # Generate report sections
        report = {
            "generated_at": datetime.now().isoformat(),
            "csv_file": str(csv_path),
            "summary": self._generate_summary(reliability),
            "reliability": {
                "score": reliability["reliability_score"],
                "level": reliability["reliability_level"],
                "recommendation": reliability["recommendation"]
            },
            "metrics_breakdown": self._generate_metrics_breakdown(reliability["metrics"]),
            "score_details": reliability["scores"],
            "issues_found": reliability["issues"],
            "data_profile": {
                "total_rows": reliability["total_rows"],
                "columns_checked": len(reliability["metrics"]["completeness"]["null_counts"])
            }
        }
        
        # Add AI recommendations if LLM available and requested
        if include_recommendations and self.llm:
            report["ai_recommendations"] = await self._generate_ai_recommendations(reliability)
        
        # Save report
        report_path = self._save_report(report, year=year)
        report["report_path"] = str(report_path)
        
        # Add to history
        self.reports_history.append({
            "timestamp": report["generated_at"],
            "score": reliability["reliability_score"],
            "level": reliability["reliability_level"]
        })
        
        return {
            "success": True,
            "report": report
        }
    
    def _generate_summary(self, reliability: Dict) -> Dict[str, Any]:
        """Generate executive summary"""
        score = reliability["reliability_score"]
        level = reliability["reliability_level"]
        issues = reliability["issues"]
        
        if level == "HIGH":
            status = "✅ Data quality is excellent"
            action = "Ready for production use"
        elif level == "MEDIUM":
            status = "⚠️ Data quality is acceptable"
            action = "Review flagged issues before use"
        elif level == "LOW":
            status = "⚠️ Data quality needs improvement"
            action = "Address major issues before use"
        else:
            status = "❌ Data quality is poor"
            action = "Regenerate data recommended"
        
        return {
            "status": status,
            "overall_score": score,
            "quality_level": level,
            "recommended_action": action,
            "issues_count": len(issues),
            "top_issue": issues[0] if issues else "No issues found"
        }
    
    def _generate_metrics_breakdown(self, metrics: Dict) -> Dict[str, Any]:
        """Generate detailed metrics breakdown"""
        breakdown = {}
        
        # Completeness
        comp = metrics.get("completeness", {})
        breakdown["completeness"] = {
            "score": comp.get("score", 0),
            "description": "Measures presence of required data",
            "details": {
                "missing_columns": comp.get("missing_columns", []),
                "columns_with_nulls": len(comp.get("null_counts", {}))
            },
            "status": "PASS" if comp.get("score", 0) >= 80 else "NEEDS_ATTENTION"
        }
        
        # Value Validity
        val = metrics.get("value_validity", {})
        breakdown["value_validity"] = {
            "score": val.get("score", 0),
            "description": "Checks if values are valid types",
            "details": {
                "columns_with_invalid": len(val.get("invalid_values", {}))
            },
            "status": "PASS" if val.get("score", 0) >= 90 else "NEEDS_ATTENTION"
        }
        
        # Range Validity
        rng = metrics.get("range_validity", {})
        breakdown["range_validity"] = {
            "score": rng.get("score", 0),
            "description": "Checks if values are within expected ranges",
            "details": {
                "columns_out_of_range": len(rng.get("out_of_range", {}))
            },
            "status": "PASS" if rng.get("score", 0) >= 90 else "NEEDS_ATTENTION"
        }
        
        # Consistency
        cons = metrics.get("consistency", {})
        breakdown["consistency"] = {
            "score": cons.get("score", 0),
            "description": "Checks logical relationships between fields",
            "details": {
                "inconsistencies_found": len(cons.get("inconsistencies", []))
            },
            "status": "PASS" if cons.get("score", 0) >= 95 else "NEEDS_ATTENTION"
        }
        
        # Anomalies
        anom = metrics.get("anomalies", {})
        breakdown["anomalies"] = {
            "score": 100 - anom.get("anomaly_percentage", 0),
            "description": "Detects statistical outliers",
            "details": {
                "anomaly_percentage": anom.get("anomaly_percentage", 0),
                "columns_with_anomalies": len(anom.get("anomalies", []))
            },
            "status": "PASS" if anom.get("anomaly_percentage", 0) < 5 else "NEEDS_ATTENTION"
        }
        
        return breakdown
    
    async def _generate_ai_recommendations(self, reliability: Dict) -> List[str]:
        """Generate AI-powered recommendations"""
        issues = reliability["issues"]
        metrics = reliability["metrics"]
        
        prompt = f"""Based on this CSV data quality report, provide 3-5 specific recommendations:

Reliability Score: {reliability['reliability_score']}/100
Level: {reliability['reliability_level']}

Issues Found:
{chr(10).join(f"- {i}" for i in issues[:5])}

Metrics:
- Completeness: {metrics['completeness']['score']}%
- Value Validity: {metrics['value_validity']['score']}%
- Range Validity: {metrics['range_validity']['score']}%
- Consistency: {metrics['consistency']['score']}%

Provide actionable recommendations to improve data quality. Keep each recommendation to one sentence."""

        try:
            response = await self.invoke_llm(
                prompt,
                "You are a data quality expert. Provide brief, actionable recommendations."
            )
            
            # Parse recommendations
            lines = response.strip().split("\n")
            recommendations = [
                line.strip().lstrip("0123456789.-) ")
                for line in lines
                if line.strip() and len(line.strip()) > 10
            ]
            return recommendations[:5]
            
        except Exception as e:
            self.log_error(f"AI recommendations failed: {e}")
            return ["Review and fix the issues listed above."]
    
    def _save_report(self, report: Dict, year: Optional[int] = None) -> Path:
        """Save report to file (both timestamped and latest for year)"""
        reports_dir = Path("data/accuracy_reports")
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"accuracy_report_{timestamp}.json"
        
        # Save timestamped report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Save as latest for year if provided
        if year:
            latest_path = reports_dir / f"market_report_{year}.json"
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.log_info(f"Latest report saved to {latest_path}")
            
        self.log_info(f"Historical report saved to {report_path}")
        return report_path
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get report history"""
        return self.reports_history[-limit:]


async def run_accuracy_report_agent(
    csv_path: str = "data/NewMarketplaceResearchAll82JobTitlePlusSkills.csv",
    include_recommendations: bool = True,
    provider: str = None
) -> Dict[str, Any]:
    """Main entry point for accuracy report generation"""
    # Get LLM if available
    llm = None
    if include_recommendations:
        try:
            from app import langchain_manager
            import config
            provider = provider or config.current_settings.get("ai_provider", "gemini")
            llm = langchain_manager.get_llm(provider)
        except:
            pass
    
    agent = AccuracyReportAgent(llm)
    result = await agent.process({
        "csv_path": csv_path,
        "include_recommendations": include_recommendations,
        "year": int(Path(csv_path).stem.split('_')[-1]) if '_' in Path(csv_path).stem and Path(csv_path).stem.split('_')[-1].isdigit() else 2026
    })
    
    return result


__all__ = ["AccuracyReportAgent", "run_accuracy_report_agent"]
