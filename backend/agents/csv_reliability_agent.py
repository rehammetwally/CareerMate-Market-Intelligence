"""
CSV Reliability Agent
=====================

Evaluates the quality and reliability of generated market data CSV.
- Data completeness checks
- Value range validation
- Consistency scoring
- Anomaly detection
- Overall reliability rating
"""

import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from .base import BaseAgent

logger = logging.getLogger(__name__)


class CSVReliabilityAgent(BaseAgent):
    """Agent specialized in evaluating CSV data reliability and accuracy"""
    
    def __init__(self, llm=None):
        super().__init__(llm, name="CSVReliabilityAgent")
        
        # Define expected columns and their validation rules
        self.required_columns = [
            "Title", "Track", "Global_Job_Demand", "Egypt_Job_Demand",
            "Freelancing_Opportunities", "Market_Attractiveness_Rating"
        ]
        
        self.numeric_columns = [
            "Global_Job_Demand", "Egypt_Job_Demand", "Freelancing_Opportunities",
            "Market_Attractiveness_Rating", "AI_Skills_Count"
        ]
        
        self.percentage_columns = [
            "Linkedin_Distribution", "Upwork_Distribution", "Indeed_Distribution",
            "Freelancer_Distribution", "Khamsat_Distribution", "Mostakel_Distribution"
        ]
        
        # Value range expectations
        self.ranges = {
            "Global_Job_Demand": (100, 500000),
            "Egypt_Job_Demand": (10, 50000),
            "Freelancing_Opportunities": (50, 100000),
            "Market_Attractiveness_Rating": (1, 5),
            "AI_Skills_Count": (0, 50)
        }

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate CSV reliability"""
        csv_path = state.get("csv_path", "data/NewMarketplaceResearchAll82JobTitlePlusSkills.csv")
        
        self.log_info(f"Evaluating CSV reliability: {csv_path}")
        
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load CSV: {e}",
                "reliability_score": 0
            }
        
        # Run all checks
        completeness = self._check_completeness(df)
        value_validity = self._check_value_validity(df)
        range_validity = self._check_range_validity(df)
        consistency = self._check_consistency(df)
        anomalies = self._detect_anomalies(df)
        
        # Calculate overall score
        scores = {
            "completeness": completeness["score"],
            "value_validity": value_validity["score"],
            "range_validity": range_validity["score"],
            "consistency": consistency["score"],
            "anomaly_score": 100 - anomalies["anomaly_percentage"]
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        # Determine reliability level
        if overall_score >= 90:
            reliability = "HIGH"
            recommendation = "Data is reliable for production use."
        elif overall_score >= 70:
            reliability = "MEDIUM"
            recommendation = "Data is usable but review flagged issues."
        elif overall_score >= 50:
            reliability = "LOW"
            recommendation = "Data needs significant review before use."
        else:
            reliability = "UNRELIABLE"
            recommendation = "Data regeneration recommended."
        
        return {
            "success": True,
            "csv_path": str(csv_path),
            "total_rows": len(df),
            "reliability_score": round(overall_score, 2),
            "reliability_level": reliability,
            "recommendation": recommendation,
            "metrics": {
                "completeness": completeness,
                "value_validity": value_validity,
                "range_validity": range_validity,
                "consistency": consistency,
                "anomalies": anomalies
            },
            "scores": scores,
            "issues": self._compile_issues(completeness, value_validity, range_validity, anomalies)
        }
    
    def _check_completeness(self, df) -> Dict[str, Any]:
        """Check for missing values and required columns"""
        import pandas as pd
        
        # Check required columns exist
        missing_cols = [c for c in self.required_columns if c not in df.columns]
        
        # Check for null/empty values
        null_counts = {}
        for col in df.columns:
            null_count = df[col].isna().sum() + (df[col] == "").sum() + (df[col] == 0).sum()
            if null_count > 0:
                null_counts[col] = int(null_count)
        
        # Calculate score
        total_cells = len(df) * len(self.required_columns)
        available_cols = [c for c in self.required_columns if c in df.columns]
        null_in_required = sum(
            df[c].isna().sum() + (df[c] == "").sum()
            for c in available_cols if c in df.columns
        )
        
        completeness_ratio = 1 - (null_in_required / total_cells) if total_cells > 0 else 0
        column_ratio = len(available_cols) / len(self.required_columns)
        
        score = (completeness_ratio * 0.7 + column_ratio * 0.3) * 100
        
        return {
            "score": round(score, 2),
            "missing_columns": missing_cols,
            "null_counts": null_counts,
            "total_rows": len(df)
        }
    
    def _check_value_validity(self, df) -> Dict[str, Any]:
        """Check if values are valid types"""
        import pandas as pd
        
        invalid_values = {}
        
        # Check numeric columns
        for col in self.numeric_columns:
            if col in df.columns:
                non_numeric = []
                for idx, val in df[col].items():
                    try:
                        if pd.notna(val) and val != "":
                            float(str(val).replace(",", "").replace("%", ""))
                    except:
                        non_numeric.append(idx)
                if non_numeric:
                    invalid_values[col] = {"count": len(non_numeric), "sample_indices": non_numeric[:5]}
        
        total_checked = len(df) * len([c for c in self.numeric_columns if c in df.columns])
        invalid_count = sum(v["count"] for v in invalid_values.values())
        
        score = (1 - invalid_count / total_checked) * 100 if total_checked > 0 else 100
        
        return {
            "score": round(score, 2),
            "invalid_values": invalid_values
        }
    
    def _check_range_validity(self, df) -> Dict[str, Any]:
        """Check if values are within expected ranges"""
        import pandas as pd
        
        out_of_range = {}
        
        for col, (min_val, max_val) in self.ranges.items():
            if col in df.columns:
                try:
                    values = pd.to_numeric(df[col], errors='coerce')
                    below = (values < min_val).sum()
                    above = (values > max_val).sum()
                    if below > 0 or above > 0:
                        out_of_range[col] = {
                            "below_min": int(below),
                            "above_max": int(above),
                            "expected_range": f"{min_val}-{max_val}"
                        }
                except:
                    pass
        
        total_checked = len(df) * len([c for c in self.ranges if c in df.columns])
        oor_count = sum(v["below_min"] + v["above_max"] for v in out_of_range.values())
        
        score = (1 - oor_count / total_checked) * 100 if total_checked > 0 else 100
        
        return {
            "score": round(score, 2),
            "out_of_range": out_of_range
        }
    
    def _check_consistency(self, df) -> Dict[str, Any]:
        """Check data consistency (e.g., Egypt demand <= Global demand)"""
        import pandas as pd
        
        inconsistencies = []
        
        # Check Egypt <= Global demand
        if "Egypt_Job_Demand" in df.columns and "Global_Job_Demand" in df.columns:
            try:
                egypt = pd.to_numeric(df["Egypt_Job_Demand"], errors='coerce')
                global_d = pd.to_numeric(df["Global_Job_Demand"], errors='coerce')
                violations = (egypt > global_d).sum()
                if violations > 0:
                    inconsistencies.append({
                        "rule": "Egypt_Job_Demand <= Global_Job_Demand",
                        "violations": int(violations)
                    })
            except:
                pass
        
        # Check rating is 1-5
        if "Market_Attractiveness_Rating" in df.columns:
            try:
                ratings = pd.to_numeric(df["Market_Attractiveness_Rating"], errors='coerce')
                invalid = ((ratings < 1) | (ratings > 5)).sum()
                if invalid > 0:
                    inconsistencies.append({
                        "rule": "Market_Attractiveness_Rating in [1,5]",
                        "violations": int(invalid)
                    })
            except:
                pass
        
        total_violations = sum(i["violations"] for i in inconsistencies)
        score = max(0, 100 - (total_violations / len(df) * 100)) if len(df) > 0 else 100
        
        return {
            "score": round(score, 2),
            "inconsistencies": inconsistencies
        }
    
    def _detect_anomalies(self, df) -> Dict[str, Any]:
        """Detect statistical anomalies"""
        import pandas as pd
        
        anomalies = []
        
        for col in self.numeric_columns:
            if col in df.columns:
                try:
                    values = pd.to_numeric(df[col], errors='coerce').dropna()
                    if len(values) > 3:
                        mean = values.mean()
                        std = values.std()
                        if std > 0:
                            # Find values > 3 std from mean
                            outliers = ((values - mean).abs() > 3 * std).sum()
                            if outliers > 0:
                                anomalies.append({
                                    "column": col,
                                    "outlier_count": int(outliers),
                                    "mean": round(mean, 2),
                                    "std": round(std, 2)
                                })
                except:
                    pass
        
        total_outliers = sum(a["outlier_count"] for a in anomalies)
        anomaly_pct = (total_outliers / len(df) * 100) if len(df) > 0 else 0
        
        return {
            "anomaly_percentage": round(anomaly_pct, 2),
            "anomalies": anomalies
        }
    
    def _compile_issues(self, completeness, validity, ranges, anomalies) -> List[str]:
        """Compile list of issues found"""
        issues = []
        
        if completeness["missing_columns"]:
            issues.append(f"Missing columns: {', '.join(completeness['missing_columns'])}")
        
        if completeness["null_counts"]:
            for col, count in list(completeness["null_counts"].items())[:3]:
                issues.append(f"{col}: {count} null/empty values")
        
        for col, info in ranges.get("out_of_range", {}).items():
            issues.append(f"{col}: {info['below_min'] + info['above_max']} values out of range")
        
        if anomalies["anomaly_percentage"] > 5:
            issues.append(f"High anomaly rate: {anomalies['anomaly_percentage']}%")
        
        return issues[:10]  # Limit to top 10


async def run_csv_reliability_agent(
    csv_path: str = "data/NewMarketplaceResearchAll82JobTitlePlusSkills.csv"
) -> Dict[str, Any]:
    """Main entry point for CSV reliability evaluation"""
    agent = CSVReliabilityAgent()
    return await agent.process({"csv_path": csv_path})


__all__ = ["CSVReliabilityAgent", "run_csv_reliability_agent"]
