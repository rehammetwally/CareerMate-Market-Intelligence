import { apiUrl } from '../config';
import React, { useState, useEffect } from "react";
import { useInitialize } from "../useInitialize";
import JobsBarChart from "../components/charts/JobsBarChart";
import SkillsPieChart from "../components/charts/SkillsPieChart";
import TrackBarChart from "../components/charts/TrackBarChart";
import PlatformChart from "../components/charts/PlatformChart";
import StatsCards from "../components/charts/StatsCards";
import SplitScreenComparison from "../components/charts/SplitScreenComparison";
import { useCharts } from "../context/ChartsContext";
import Loader from "../components/Loader/Loader";

export default function MarketAnalysis({ onInitialize }) {
  const { loading: initLoading } = useInitialize(
    `${apiUrl}/api/market/init`,
    onInitialize
  );

  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedYear, setSelectedYear] = useState(2026);
  const [splitData, setSplitData] = useState(null);
  const [showSplitScreen, setShowSplitScreen] = useState(false);
  const [freelanceJobs, setFreelanceJobs] = useState(null);
  const [showFreelance, setShowFreelance] = useState(false);
  const [accuracyReport, setAccuracyReport] = useState(null);
  const [showAccuracyReport, setShowAccuracyReport] = useState(false);
  const [gapAnalysisResults, setGapAnalysisResults] = useState(null);
  const [showGapAnalysis, setShowGapAnalysis] = useState(false);
  const [globalRankings, setGlobalRankings] = useState(null);
  const [showGlobalRanking, setShowGlobalRanking] = useState(false);
  const [reliabilityInfo, setReliabilityInfo] = useState(null);
  const [salaryEstimates, setSalaryEstimates] = useState(null);
  const [showSalaryEstimates, setShowSalaryEstimates] = useState(false);
  const [salaryJobTitle, setSalaryJobTitle] = useState("");
  const [externalDataTest, setExternalDataTest] = useState(null);
  const [showExternalDataTest, setShowExternalDataTest] = useState(false);
  const [marketSources, setMarketSources] = useState([]);
  const [showSources, setShowSources] = useState(false);
  const [sourceMeta, setSourceMeta] = useState(null);
  const [sourcesRevalidating, setSourcesRevalidating] = useState(false);
  const [sourceAblation, setSourceAblation] = useState(null);
  const [ablationExportInfo, setAblationExportInfo] = useState(null);

  useEffect(() => {
    fetchMarketData();
    fetchReliabilityInfo();
    fetchMarketSources();
  }, [selectedYear]);

  const fetchMarketSources = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/market/sources`);
      const data = await res.json();
      if (data.success) {
        setMarketSources(data.sources || []);
        setSourceMeta({
          confidence: data.source_confidence_score || 0,
          high: data.high_reliability_sources || 0,
          review: data.review_sources || 0,
          total: data.total_sources || 0,
          health: data.health || { alive: 0, dead: 0, unchecked: 0 },
          evidence: data.evidence_metrics || null,
        });
      }
    } catch (e) {
      console.error("Failed to fetch market sources", e);
    }
  };

  const handleSourceAblation = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/market/sources/ablation?min_source_quality=60`);
      const data = await res.json();
      if (data.success) {
        setSourceAblation(data.ablation || []);
      } else {
        alert("❌ Source ablation failed: " + (data.error || "Unknown error"));
      }
    } catch (e) {
      alert("❌ Source ablation failed: " + e.message);
    }
  };

  const handleExportSourceAblation = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/market/sources/ablation/export?min_source_quality=60`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.success) {
        setAblationExportInfo(data);
      } else {
        alert("❌ Export failed: " + (data.error || "Unknown error"));
      }
    } catch (e) {
      alert("❌ Export failed: " + e.message);
    }
  };

  const handleRevalidateSources = async () => {
    setSourcesRevalidating(true);
    try {
      const res = await fetch(`${apiUrl}/api/market/sources/revalidate`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.success) {
        await fetchMarketSources();
        await fetchMarketData();
        const health = data.health || { alive: 0, dead: 0, unchecked: 0 };
        alert(
          `✅ Revalidated ${data.checked} sources\n` +
          `Confidence: ${data.source_confidence_score ?? "N/A"}%\n` +
          `Alive: ${health.alive} | Dead: ${health.dead} | Unchecked: ${health.unchecked}`
        );
      } else {
        alert("❌ Source revalidation failed: " + (data.error || "Unknown error"));
      }
    } catch (e) {
      alert("❌ Source revalidation failed: " + e.message);
    } finally {
      setSourcesRevalidating(false);
    }
  };

  const fetchReliabilityInfo = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/market/reliability?year=${selectedYear}`);
      const data = await res.json();
      if (data.success) {
        setReliabilityInfo({
          score: data.reliability_score || 0,
          level: data.reliability_level || 'UNKNOWN'
        });
      }
    } catch (e) {
      console.error("Failed to fetch reliability info", e);
    }
  };

  const handleSalaryEstimates = async () => {
    const title = prompt("Enter job title for salary lookup:", "Full Stack Developer");
    if (!title) return;
    
    setSalaryJobTitle(title);
    setLoading(true);
    try {
      const res = await fetch(
        `${apiUrl}/api/market/salary-estimates?job_title=${encodeURIComponent(title)}&location=Egypt`
      );
      const data = await res.json();
      if (data.success) {
        setSalaryEstimates(data);
        setShowSalaryEstimates(true);
      } else {
        alert("❌ Error: " + data.error);
      }
    } catch (e) {
      alert("❌ Error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExternalDataTest = async () => {
    const query = prompt("Enter job title to test:", "Python Developer");
    if (!query) return;
    
    setLoading(true);
    try {
      const res = await fetch(
        `${apiUrl}/api/market/external-test?query=${encodeURIComponent(query)}`
      );
      const data = await res.json();
      if (data.success) {
        setExternalDataTest(data);
        setShowExternalDataTest(true);
      } else {
        alert("❌ Error: " + data.error);
      }
    } catch (e) {
      alert("❌ Error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchMarketData = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/market/charts`);

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setMarketData(result.data);
      } else {
        throw new Error(result.error || "Failed to load market data");
      }
    } catch (err) {
      console.error("❌ Error fetching market data:", err);
      setError(err.message || "Error loading market data");
    } finally {
      setLoading(false);
    }
  };

  const handleGlobalRanking = async () => {
    setLoading(true);
    setShowSplitScreen(false);
    setShowFreelance(false);
    setShowAccuracyReport(false);
    setShowGapAnalysis(false);

    try {
      const res = await fetch(`${apiUrl}/api/market/rank-freelance`, {
        method: "POST"
      });
      const data = await res.json();
      if (data.success) {
        setGlobalRankings(data.rankings);
        setShowGlobalRanking(true);
      } else {
        alert("❌ Error: " + data.error);
      }
    } catch (e) {
      alert("❌ Error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFreelanceJobs = async () => {
    setLoading(true);
    setShowSplitScreen(false);
    setShowGlobalRanking(false);
    try {
      const res = await fetch(`${apiUrl}/api/market/freelance-jobs?year=${selectedYear}`, {
        method: "POST"
      });
      const data = await res.json();
      if (data.success) {
        setFreelanceJobs(data.jobs);
        setShowFreelance(true);
      } else {
        alert("❌ Error: " + data.error);
      }
    } catch (e) {
      alert("❌ Error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAccuracyReport = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/market/accuracy-report?year=${selectedYear}&include_ai=true`);
      const data = await res.json();
      if (data.success) {
        setAccuracyReport(data);
        setShowAccuracyReport(true);
      } else {
        alert("❌ Error: " + data.error);
      }
    } catch (e) {
      alert("❌ Error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  if (initLoading || loading) {
    return <Loader />;
  }

  if (error) {
    return (
      <div
        style={{ padding: "2rem", minHeight: "100vh", background: "#f5f7fa" }}
      >
        <div
          style={{
            background: "#fee",
            border: "1px solid #fcc",
            padding: "2rem",
            borderRadius: "12px",
            textAlign: "center",
            maxWidth: "600px",
            margin: "0 auto",
          }}
        >
          <h3 style={{ color: "#c33", margin: "0 0 1rem 0" }}>
            ❌ Error Loading Data
          </h3>
          <p style={{ color: "#666", margin: "0 0 1.5rem 0" }}>{error}</p>
          <button
            onClick={fetchMarketData}
            style={{
              padding: "0.75rem 1.5rem",
              background: "#3498db",
              color: "white",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "2rem",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      {/* Header with Gradient */}
      <header
        style={{
          background: "white",
          borderRadius: "16px",
          padding: "2rem",
          marginBottom: "2rem",
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <h1
            style={{
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              margin: "0 0 0.5rem 0",
              fontSize: "2.5rem",
              fontWeight: "bold",
            }}
          >
            📊 Career Market Analysis Dashboard
          </h1>
          {reliabilityInfo && (
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                gap: "0.75rem",
                flexWrap: "wrap",
                marginBottom: "1rem",
              }}
            >
              <div style={{
                display: "inline-block",
                background: reliabilityInfo.level === 'HIGH' ? '#d4edda' :
                            reliabilityInfo.level === 'MEDIUM' ? '#fff3cd' : '#f8d7da',
                color: reliabilityInfo.level === 'HIGH' ? '#155724' :
                       reliabilityInfo.level === 'MEDIUM' ? '#856404' : '#721c24',
                padding: "4px 12px",
                borderRadius: "20px",
                fontSize: "0.85rem",
                fontWeight: "bold",
                border: "1px solid rgba(0,0,0,0.1)",
                boxShadow: "0 2px 5px rgba(0,0,0,0.05)"
              }}>
                ✓ Data Reliability: {reliabilityInfo.score}% ({reliabilityInfo.level})
              </div>
              {sourceMeta && (
                <div style={{
                  display: "inline-block",
                  background: sourceMeta.confidence >= 70 ? '#d1ecf1' : '#fff3cd',
                  color: sourceMeta.confidence >= 70 ? '#0c5460' : '#856404',
                  padding: "4px 12px",
                  borderRadius: "20px",
                  fontSize: "0.85rem",
                  fontWeight: "bold",
                  border: "1px solid rgba(0,0,0,0.1)",
                  boxShadow: "0 2px 5px rgba(0,0,0,0.05)"
                }}>
                  🔎 Source Confidence: {sourceMeta.confidence}%
                </div>
              )}
            </div>
          )}
          <p style={{ color: "#7f8c8d", fontSize: "1.1rem", margin: "0 0 1.5rem 0" }}>
            Real-time insights from the job market
          </p>

          {/* Controls */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "1rem",
              flexWrap: "wrap",
            }}
          >
            <label
              style={{
                fontSize: "0.9rem",
                fontWeight: "500",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              Year:
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(Number(e.target.value))}
                style={{
                  padding: "0.6rem 1rem",
                  borderRadius: "8px",
                  border: "2px solid #667eea",
                  fontSize: "0.9rem",
                  cursor: "pointer",
                  background: "white",
                }}
              >
                {[2025, 2026, 2027, 2028, 2029, 2030].map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </label>

            <button
              onClick={async () => {
                if (
                  !window.confirm(
                    `This will regenerate all market data using AI for year ${selectedYear}. It may take a few minutes. Continue?`
                  )
                )
                  return;
                setLoading(true);
                try {
                  const res = await fetch(
                    `${apiUrl}/api/market/refresh_data?year=${selectedYear}`,
                    { method: "POST" }
                  );
                  const data = await res.json();
                  if (data.success) {
                    alert("✅ Data refreshed successfully!");
                    fetchMarketData();
                    fetchReliabilityInfo();
                    handleAccuracyReport(); // Auto-show full report
                  } else {
                    alert("❌ Error: " + data.error);
                  }
                } catch (e) {
                  alert("❌ Error: " + e.message);
                } finally {
                  setLoading(false);
                }
              }}
              style={{
                padding: "0.6rem 1.2rem",
                background: "linear-gradient(135deg, #27ae60 0%, #229954 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "500",
                boxShadow: "0 2px 8px rgba(39, 174, 96, 0.3)",
                transition: "transform 0.2s",
              }}
              onMouseOver={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseOut={(e) => (e.target.style.transform = "translateY(0)")}
            >
              🔄 Generate New Data (AI)
            </button>



            <button
              onClick={async () => {
                setLoading(true);
                try {
                  const res = await fetch(`${apiUrl}/api/market/gap-analysis`, {
                    method: "POST"
                  });
                  const data = await res.json();
                  if (data.success) {
                    setGapAnalysisResults(data.missing_jobs);
                    setShowGapAnalysis(true);
                    setShowAccuracyReport(false);
                    setShowFreelance(false);
                  } else {
                    alert("❌ Error: " + data.error);
                  }
                } catch (e) {
                  alert("❌ Error: " + e.message);
                } finally {
                  setLoading(false);
                }
              }}
              style={{
                padding: "0.6rem 1.2rem",
                background: "linear-gradient(135deg, #e67e22 0%, #d35400 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "500",
                boxShadow: "0 2px 8px rgba(230, 126, 34, 0.3)",
                transition: "transform 0.2s",
              }}
              onMouseOver={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseOut={(e) => (e.target.style.transform = "translateY(0)")}
            >
              🧐 Analyze Missing Jobs
            </button>

            <button
              onClick={handleAccuracyReport}
              style={{
                padding: "0.6rem 1.2rem",
                background: "linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "500",
                boxShadow: "0 2px 8px rgba(155, 89, 182, 0.3)",
                transition: "transform 0.2s",
              }}
              onMouseOver={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseOut={(e) => (e.target.style.transform = "translateY(0)")}
            >
              📈 Accuracy Report
            </button>

            <button
              onClick={handleFreelanceJobs}
              style={{
                padding: "0.6rem 1.2rem",
                background: "linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "500",
                boxShadow: "0 2px 8px rgba(255, 75, 43, 0.3)",
                transition: "transform 0.2s",
              }}
              onMouseOver={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseOut={(e) => (e.target.style.transform = "translateY(0)")}
            >
              🌍 Top 100 Freelance Jobs
            </button>

            <button
              onClick={handleGlobalRanking}
              style={{
                padding: "0.6rem 1.2rem",
                background: "linear-gradient(135deg, #3a7bd5 0%, #00d2ff 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "500",
                boxShadow: "0 2px 8px rgba(58, 123, 213, 0.3)",
                transition: "transform 0.2s",
              }}
              onMouseOver={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseOut={(e) => (e.target.style.transform = "translateY(0)")}
            >
              🏅 Rank DEPI Globally
            </button>

            <button
              onClick={handleSalaryEstimates}
              style={{
                padding: "0.6rem 1.2rem",
                background: "linear-gradient(135deg, #00b894 0%, #00cec9 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "500",
                boxShadow: "0 2px 8px rgba(0, 184, 148, 0.3)",
                transition: "transform 0.2s",
              }}
              onMouseOver={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseOut={(e) => (e.target.style.transform = "translateY(0)")}
            >
              💰 Salary Estimates
            </button>

            <button
              onClick={() => setShowSources((prev) => !prev)}
              style={{
                padding: "0.6rem 1.2rem",
                background: "linear-gradient(135deg, #16a085 0%, #1abc9c 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "500",
                boxShadow: "0 2px 8px rgba(22, 160, 133, 0.3)",
                transition: "transform 0.2s",
              }}
              onMouseOver={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseOut={(e) => (e.target.style.transform = "translateY(0)")}
            >
              {showSources ? "📚 Hide Sources" : "📚 Data Sources"}
            </button>

            <button
              onClick={handleExternalDataTest}
              style={{
                padding: "0.6rem 1.2rem",
                background: "linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: "500",
                boxShadow: "0 2px 8px rgba(108, 92, 231, 0.3)",
                transition: "transform 0.2s",
              }}
              onMouseOver={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseOut={(e) => (e.target.style.transform = "translateY(0)")}
            >
              🔍 Test External Data
            </button>
          </div>
        </div >
      </header >

      {marketData && (
        <>
          {/* Statistics Cards */}
          <StatsCards stats={marketData.statistics} />

          {showAccuracyReport && accuracyReport && (
            <div style={{
              background: "white",
              borderRadius: "16px",
              padding: "2rem",
              marginBottom: "2rem",
              boxShadow: "0 4px 20px rgba(0,0,0,0.1)"
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ color: "#2c3e50", margin: 0 }}>📈 Data Accuracy Report</h2>
                <button
                  onClick={() => setShowAccuracyReport(false)}
                  style={{
                    padding: "0.5rem 1rem",
                    background: "#f1f2f6",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    color: "#666"
                  }}
                >
                  ✕ Close
                </button>
              </div>

              {/* Summary */}
              <div style={{
                background: accuracyReport.reliability?.level === 'HIGH' ? '#d4edda' :
                  accuracyReport.reliability?.level === 'MEDIUM' ? '#fff3cd' : '#f8d7da',
                borderRadius: "12px",
                padding: "1.5rem",
                marginBottom: "1.5rem",
                textAlign: "center"
              }}>
                <h3 style={{ margin: "0 0 0.5rem 0", fontSize: "2rem" }}>
                  {accuracyReport.reliability?.score || 0}/100
                </h3>
                <p style={{ margin: 0, fontWeight: "600", color: "#2c3e50" }}>
                  {accuracyReport.summary?.status || 'Unknown'}
                </p>
                <p style={{ margin: "0.5rem 0 0 0", color: "#666" }}>
                  {accuracyReport.summary?.recommended_action || ''}
                </p>
              </div>

              {/* Metrics Grid */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "1rem",
                marginBottom: "1.5rem"
              }}>
                {accuracyReport.metrics_breakdown && Object.entries(accuracyReport.metrics_breakdown).map(([key, value]) => (
                  <div key={key} style={{
                    background: value.status === 'PASS' ? '#e8f5e9' : '#fff8e1',
                    borderRadius: "8px",
                    padding: "1rem",
                    textAlign: "center"
                  }}>
                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: value.status === 'PASS' ? '#27ae60' : '#f39c12' }}>
                      {value.score}%
                    </div>
                    <div style={{ fontSize: "0.85rem", color: "#666", textTransform: "capitalize" }}>
                      {key.replace(/_/g, ' ')}
                    </div>
                  </div>
                ))}
              </div>

              {/* Issues */}
              {accuracyReport.issues_found?.length > 0 && (
                <div style={{ marginBottom: "1.5rem" }}>
                  <h4 style={{ color: "#e74c3c", margin: "0 0 0.75rem 0" }}>⚠️ Issues Found</h4>
                  <ul style={{ margin: 0, paddingLeft: "1.5rem", color: "#666" }}>
                    {accuracyReport.issues_found.map((issue, idx) => (
                      <li key={idx} style={{ marginBottom: "0.5rem" }}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* AI Recommendations */}
              {accuracyReport.ai_recommendations?.length > 0 && (
                <div>
                  <h4 style={{ color: "#3498db", margin: "0 0 0.75rem 0" }}>💡 AI Recommendations</h4>
                  <ul style={{ margin: 0, paddingLeft: "1.5rem", color: "#666" }}>
                    {accuracyReport.ai_recommendations.map((rec, idx) => (
                      <li key={idx} style={{ marginBottom: "0.5rem" }}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {showSources && (
            <div
              style={{
                background: "white",
                borderRadius: "16px",
                padding: "2rem",
                marginBottom: "2rem",
                boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "1rem",
                }}
              >
                <h2 style={{ color: "#2c3e50", margin: 0 }}>
                  📚 Reliable Market Sources
                </h2>
                <span style={{ color: "#666", fontSize: "0.9rem" }}>
                  {sourceMeta?.high || marketSources.length} high-reliability sources
                </span>
              </div>

              {sourceMeta && (
                <div style={{ marginBottom: "1rem", color: "#7f8c8d", fontSize: "0.9rem" }}>
                  Confidence: {sourceMeta.confidence}% | Total: {sourceMeta.total} | Review-needed: {sourceMeta.review} | Alive: {sourceMeta.health?.alive || 0} | Dead: {sourceMeta.health?.dead || 0} | Unchecked: {sourceMeta.health?.unchecked || 0}
                </div>
              )}

              {sourceMeta?.evidence && (
                <div style={{ marginBottom: "1rem", color: "#2c3e50", fontSize: "0.9rem", background: "#f8f9fa", borderRadius: "8px", padding: "0.75rem" }}>
                  <strong>Novel Evidence Metric:</strong> ERS {sourceMeta.evidence.evidence_robustness_score}% |
                  Trust {sourceMeta.evidence.trust_coverage}% |
                  Liveness {sourceMeta.evidence.liveness_ratio}% |
                  Diversity {sourceMeta.evidence.domain_diversity}% |
                  Freshness {sourceMeta.evidence.freshness_ratio}%
                </div>
              )}

              <div style={{ marginBottom: "1rem" }}>
                <button
                  onClick={handleRevalidateSources}
                  disabled={sourcesRevalidating}
                  style={{
                    padding: "0.5rem 1rem",
                    background: sourcesRevalidating
                      ? "#bdc3c7"
                      : "linear-gradient(135deg, #2c3e50 0%, #4ca1af 100%)",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    cursor: sourcesRevalidating ? "not-allowed" : "pointer",
                    fontSize: "0.9rem",
                    fontWeight: "600",
                  }}
                >
                  {sourcesRevalidating ? "⏳ Revalidating..." : "🔁 Revalidate Sources"}
                </button>
                <button
                  onClick={handleSourceAblation}
                  style={{
                    marginLeft: "0.5rem",
                    padding: "0.5rem 1rem",
                    background: "linear-gradient(135deg, #8e44ad 0%, #5e3370 100%)",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontSize: "0.9rem",
                    fontWeight: "600",
                  }}
                >
                  🧪 Run Source Ablation
                </button>
                <button
                  onClick={handleExportSourceAblation}
                  style={{
                    marginLeft: "0.5rem",
                    padding: "0.5rem 1rem",
                    background: "linear-gradient(135deg, #1f6f8b 0%, #144552 100%)",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    cursor: "pointer",
                    fontSize: "0.9rem",
                    fontWeight: "600",
                  }}
                >
                  💾 Export Ablation
                </button>
              </div>

              {ablationExportInfo && (
                <div style={{ marginBottom: "1rem", color: "#2c3e50", fontSize: "0.85rem", background: "#eef9ff", borderRadius: "8px", padding: "0.75rem" }}>
                  <strong>Exported:</strong> {ablationExportInfo.latest_csv_path}<br />
                  <strong>Delta:</strong> ERS {ablationExportInfo.summary_delta?.ers_delta || 0},
                  Confidence {ablationExportInfo.summary_delta?.confidence_delta || 0},
                  Kept {ablationExportInfo.summary_delta?.kept_sources_delta || 0}
                </div>
              )}

              {sourceAblation && sourceAblation.length > 0 && (
                <div style={{ marginBottom: "1rem", overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                    <thead>
                      <tr style={{ background: "#f3f4f6" }}>
                        <th style={{ textAlign: "left", padding: "0.6rem" }}>Policy</th>
                        <th style={{ textAlign: "left", padding: "0.6rem" }}>Kept</th>
                        <th style={{ textAlign: "left", padding: "0.6rem" }}>Confidence</th>
                        <th style={{ textAlign: "left", padding: "0.6rem" }}>ERS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sourceAblation.map((row, idx) => (
                        <tr key={idx} style={{ borderTop: "1px solid #eee" }}>
                          <td style={{ padding: "0.6rem", fontWeight: "600" }}>{row.policy}</td>
                          <td style={{ padding: "0.6rem" }}>{row.kept_sources}</td>
                          <td style={{ padding: "0.6rem" }}>{row.source_confidence_score}%</td>
                          <td style={{ padding: "0.6rem" }}>{row.evidence_metrics?.evidence_robustness_score || 0}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {marketSources.length === 0 ? (
                <p style={{ color: "#666" }}>
                  No curated sources available yet.
                </p>
              ) : (
                <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "#34495e" }}>
                  {marketSources.map((src, idx) => (
                    <li key={idx} style={{ marginBottom: "0.6rem" }}>
                      <a href={src.url} target="_blank" rel="noreferrer">
                        {src.title || src.url}
                      </a>
                      {src.domain ? (
                        <span style={{ color: "#7f8c8d", marginLeft: "0.5rem" }}>
                          ({src.domain})
                        </span>
                      ) : null}
                      {typeof src.alive === "boolean" ? (
                        <span
                          style={{
                            marginLeft: "0.5rem",
                            color: src.alive ? "#27ae60" : "#e74c3c",
                            fontWeight: "600",
                          }}
                        >
                          {src.alive ? "[alive]" : "[dead]"}
                        </span>
                      ) : (
                        <span style={{ marginLeft: "0.5rem", color: "#95a5a6" }}>
                          [unchecked]
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {showSalaryEstimates && salaryEstimates && (
            <div style={{
              background: "white",
              borderRadius: "16px",
              padding: "2rem",
              marginBottom: "2rem",
              boxShadow: "0 4px 20px rgba(0,0,0,0.1)"
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ color: "#2c3e50", margin: 0 }}>
                  💰 Salary Estimates for: {salaryJobTitle}
                </h2>
                <button
                  onClick={() => setShowSalaryEstimates(false)}
                  style={{
                    padding: "0.5rem 1rem",
                    background: "#f1f2f6",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    color: "#666"
                  }}
                >
                  ✕ Close
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
                {salaryEstimates.estimates?.map((est, idx) => (
                  <div key={idx} style={{
                    background: '#f8f9fa',
                    borderRadius: "12px",
                    padding: "1.5rem",
                    border: "1px solid #e9ecef"
                  }}>
                    <div style={{ fontSize: "0.85rem", color: "#666", marginBottom: "0.5rem" }}>
                      {est.source} - {est.location}
                    </div>
                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#00b894" }}>
                      {est.salary_min?.toLocaleString()} - {est.salary_max?.toLocaleString()} {est.currency}
                    </div>
                    <div style={{ fontSize: "0.9rem", color: "#666", marginTop: "0.5rem" }}>
                      Period: {est.period} | Confidence: {est.confidence}
                    </div>
                    {est.sample_size > 0 && (
                      <div style={{ fontSize: "0.8rem", color: "#999", marginTop: "0.25rem" }}>
                        Sample: {est.sample_size} data points
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {(!salaryEstimates.estimates || salaryEstimates.estimates.length === 0) && (
                <p style={{ color: "#666", textAlign: "center" }}>
                  No salary data available for this position.
                </p>
              )}
            </div>
          )}

          {showExternalDataTest && externalDataTest && (
            <div style={{
              background: "white",
              borderRadius: "16px",
              padding: "2rem",
              marginBottom: "2rem",
              boxShadow: "0 4px 20px rgba(0,0,0,0.1)"
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ color: "#2c3e50", margin: 0 }}>
                  🔍 External Data Sources Test: "{externalDataTest.query}"
                </h2>
                <button
                  onClick={() => setShowExternalDataTest(false)}
                  style={{
                    padding: "0.5rem 1rem",
                    background: "#f1f2f6",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    color: "#666"
                  }}
                >
                  ✕ Close
                </button>
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <span style={{ fontWeight: "bold", color: "#27ae60" }}>
                  Total Jobs Found: {externalDataTest.total_jobs_found}
                </span>
                <span style={{ color: "#666", marginLeft: "1rem" }}>
                  Sources Tested: {externalDataTest.sources_tested?.join(", ") || "None"}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                {Object.entries(externalDataTest.data || {}).map(([platform, data]) => (
                  <div key={platform} style={{
                    background: '#f8f9fa',
                    borderRadius: "12px",
                    padding: "1rem",
                    border: "1px solid #e9ecef"
                  }}>
                    <div style={{ fontWeight: "bold", color: "#6c5ce7", marginBottom: "0.75rem", textTransform: "capitalize" }}>
                      {platform}
                    </div>
                    {data.error ? (
                      <div style={{ color: "#e74c3c", fontSize: "0.85rem" }}>
                        ❌ {data.error}
                      </div>
                    ) : (
                      <>
                        <div style={{ color: "#27ae60", fontWeight: "bold" }}>
                          ✅ {data.count || 0} jobs
                        </div>
                        {data.sample_jobs?.slice(0, 3).map((job, idx) => (
                          <div key={idx} style={{ fontSize: "0.85rem", marginTop: "0.5rem", borderLeft: "2px solid #6c5ce7", paddingLeft: "0.5rem" }}>
                            <div style={{ fontWeight: "600", color: "#2c3e50" }}>{job.title}</div>
                            <div style={{ color: "#666" }}>{job.company}</div>
                            {job.salary && <div style={{ color: "#00b894" }}>{job.salary}</div>}
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {showGapAnalysis && gapAnalysisResults && (
            <div style={{
              background: "white",
              borderRadius: "16px",
              padding: "2rem",
              marginBottom: "2rem",
              boxShadow: "0 4px 20px rgba(0,0,0,0.05)",
              border: "1px solid #edf2f7"
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ color: "#2c3e50", margin: 0 }}>🧐 Market Gap Analysis (Missing Jobs)</h2>
                <button
                  onClick={() => setShowGapAnalysis(false)}
                  style={{
                    padding: "0.5rem 1rem",
                    background: "#f1f2f6",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    color: "#666"
                  }}
                >
                  ✕ Close
                </button>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                  <thead>
                    <tr style={{ background: "#f8f9fa", textAlign: "left" }}>
                      <th style={{ padding: "1rem", color: "#666" }}>Job Title & Skills</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Top Matches & Gaps</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Demand (G/E/F)</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Distributions</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Growth & Rtg</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Openings & Justification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gapAnalysisResults.map((job, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid #eee" }}>
                        <td style={{ padding: "1rem" }}>
                          <div style={{ fontWeight: "600", color: "#2c3e50" }}>{job.title}</div>
                          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '4px' }}>
                            {job.Skills?.slice(0, 3).map((s, i) => (
                              <span key={i} style={{ background: '#edf2f7', padding: '2px 6px', borderRadius: '4px', fontSize: '0.75rem' }}>{s}</span>
                            ))}
                          </div>
                        </td>
                        <td style={{ padding: "1rem" }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {job.related_profiles?.map((p, i) => (
                              <div key={i} style={{ borderLeft: '2px solid #3498db', paddingLeft: '8px', fontSize: '0.8rem' }}>
                                <div style={{ fontWeight: '600' }}>{p.profile_name} ({p.match_score}%)</div>
                                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '2px' }}>
                                  {p.missing_skills?.map((s, si) => (
                                    <span key={si} style={{ color: '#e74c3c', fontSize: '0.7rem' }}>• {s}</span>
                                  ))}
                                </div>
                                <div style={{ fontSize: '0.7rem', color: '#7f8c8d', fontStyle: 'italic', marginTop: '2px' }}>
                                  Gap: {p.missing_content}
                                </div>
                              </div>
                            ))}
                          </div>
                        </td>
                        <td style={{ padding: "1rem" }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            <span title="Global">🌍 {job.Global_Job_Demand}/10</span>
                            <span title="Egypt">🇪🇬 {job.Egypt_Job_Demand}/10</span>
                            <span title="Freelance">💻 {job.Freelancing_Opportunities}/10</span>
                          </div>
                        </td>
                        <td style={{ padding: "1rem" }}>
                          <div style={{ fontSize: '0.75rem', color: '#666', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }}>
                            <span>LI: {job.Linkedin_Distribution}</span>
                            <span>UW: {job.Upwork_Distribution}</span>
                            <span>KH: {job.Khamsat_Distribution}</span>
                            <span>MS: {job.Mostakel_Distribution}</span>
                            <span>FL: {job.Freelancer_Distribution}</span>
                            <span>ID: {job.Indeed_Distribution}</span>
                          </div>
                        </td>
                        <td style={{ padding: "1rem" }}>
                          <div style={{ fontWeight: 'bold', color: '#27ae60' }}>{job.Growth_Trend_2025_2030}</div>
                          <div style={{ fontSize: '0.8rem' }}>Rtg: {job.Market_Attractiveness_Rating}/10</div>
                        </td>
                        <td style={{ padding: "1rem" }}>
                          <div style={{ fontWeight: '500', color: '#34495e' }}>{job.openings}</div>
                          <div style={{ fontSize: '0.8rem', color: '#7f8c8d', maxWidth: '250px' }}>{job.justification}</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {showFreelance && freelanceJobs && (
            <div style={{
              background: "white",
              borderRadius: "16px",
              padding: "2rem",
              marginBottom: "2rem",
              boxShadow: "0 4px 20px rgba(0,0,0,0.05)"
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ color: "#2c3e50", margin: 0 }}>🌍 Top 100 Freelance Jobs ({selectedYear})</h2>
                <button
                  onClick={() => setShowFreelance(false)}
                  style={{
                    padding: "0.5rem 1rem",
                    background: "#f1f2f6",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    color: "#666"
                  }}
                >
                  ✕ Close
                </button>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
                  <thead>
                    <tr style={{ background: "#f8f9fa", textAlign: "left" }}>
                      <th style={{ padding: "1rem", borderRadius: "8px 0 0 8px", color: "#666" }}>#</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Global Job Title</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Hourly Rate</th>
                      <th style={{ padding: "1rem", color: "#666" }}>DEPI Profile Match</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Openings</th>
                      <th style={{ padding: "1rem", borderRadius: "0 8px 8px 0", color: "#666" }}>Justification</th>
                    </tr>
                  </thead>
                  <tbody>
                    {freelanceJobs.map((job, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid #eee" }}>
                        <td style={{ padding: "1rem", fontWeight: "bold", color: "#667eea" }}>{job.rank || idx + 1}</td>
                        <td style={{ padding: "1rem" }}>
                          <div style={{ fontWeight: "600", color: "#2c3e50" }}>{job.title}</div>
                          <div style={{ fontSize: "0.8rem", color: "#666", marginTop: "4px" }}>
                            {job.skills?.slice(0, 3).join(", ")}...
                          </div>
                        </td>
                        <td style={{ padding: "1rem", color: "#27ae60", fontWeight: "500" }}>{job.hourly_rate}</td>
                        <td style={{ padding: "1rem" }}>
                          <div style={{ fontWeight: "500", color: "#2c3e50" }}>{job.related_depi_profile}</div>
                          <div style={{
                            fontSize: "0.8rem",
                            color: job.match_score >= 80 ? "#27ae60" : "#f39c12",
                            fontWeight: "bold"
                          }}>
                            {job.match_score}% Match
                          </div>
                        </td>
                        <td style={{ padding: "1rem", color: "#34495e" }}>{job.openings}</td>
                        <td style={{ padding: "1rem", color: "#7f8c8d", fontSize: "0.85rem", maxWidth: "300px" }}>
                          {job.demand_justification}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {showGlobalRanking && globalRankings && (
            <div style={{
              background: "white",
              borderRadius: "16px",
              padding: "2rem",
              marginBottom: "2rem",
              boxShadow: "0 4px 20px rgba(0,0,0,0.05)",
              border: "1px solid #edf2f7"
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ color: "#2c3e50", margin: 0 }}>🌐 DEPI Profiles vs Global Market ({selectedYear})</h2>
                <button
                  onClick={() => setShowGlobalRanking(false)}
                  style={{
                    padding: "0.5rem 1rem",
                    background: "#f1f2f6",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    color: "#666"
                  }}
                >
                  ✕ Close
                </button>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.95rem" }}>
                  <thead>
                    <tr style={{ background: "#f8f9fa", textAlign: "left" }}>
                      <th style={{ padding: "1rem", borderRadius: "8px 0 0 8px", color: "#666" }}>DEPI Profile</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Demand Score</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Avg Rank</th>
                      <th style={{ padding: "1rem", color: "#666" }}>Related Jobs (Matching)</th>
                      <th style={{ padding: "1rem", borderRadius: "0 8px 8px 0", color: "#666" }}>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {globalRankings.map((job, idx) => (
                      <tr key={idx} style={{ borderBottom: "1px solid #eee", backgroundColor: idx < 10 ? "#f0f8ff" : "white" }}>
                        <td style={{ padding: "1rem", fontWeight: "600", color: "#34495e" }}>{job.job_profile}</td>
                        <td style={{ padding: "1rem" }}>
                          <div style={{
                            background: job.demand_score >= 80 ? "#27ae60" : job.demand_score >= 50 ? "#f39c12" : "#e74c3c",
                            color: "white",
                            padding: "4px 8px",
                            borderRadius: "12px",
                            display: "inline-block",
                            fontSize: "0.85rem",
                            fontWeight: "bold"
                          }}>
                            {job.demand_score}/100
                          </div>
                        </td>
                        <td style={{ padding: "1rem", fontWeight: "bold", color: "#27ae60" }}>
                          {job.avg_rank ? `${job.avg_rank}` : "N/A"}
                        </td>
                        <td style={{ padding: "1rem" }}>
                          {job.related_jobs && job.related_jobs.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                              {job.related_jobs.slice(0, 3).map((match, mi) => (
                                <div key={mi} style={{ fontSize: '0.8rem', color: '#666', borderLeft: '2px solid #3498db', paddingLeft: '4px' }}>
                                  {mi + 1}. {match.job} <span style={{ color: '#27ae60', fontWeight: 'bold' }}> (Rank: {match.rank || mi + 1}, Match: {match.match_score || match.score || 0}%)</span>
                                </div>
                              ))}
                              {job.related_jobs.length > 3 && (
                                <div title={job.related_jobs.slice(3).map(m => `${m.job} (${m.score}%)`).join("\n")}
                                  style={{ fontSize: '0.75rem', color: '#3498db', cursor: 'help', marginTop: '2px' }}>
                                  + {job.related_jobs.length - 3} more (hover to view)
                                </div>
                              )}
                            </div>
                          ) : (
                            <span style={{ color: '#999', fontSize: '0.8rem' }}>No specific matches</span>
                          )}
                        </td>
                        <td style={{ padding: "1rem", color: "#7f8c8d" }}>{job.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Main Charts Grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(500px, 1fr))",
              gap: "2rem",
              marginBottom: "2rem",
            }}
          >
            <JobsBarChart data={marketData.top_jobs} />
            <SkillsPieChart data={marketData.top_skills} />
          </div>

          {/* Secondary Charts */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(500px, 1fr))",
              gap: "2rem",
              marginBottom: "2rem",
            }}
          >
            <TrackBarChart data={marketData.track_analysis} />
            <PlatformChart data={marketData.platform_distribution} />
          </div>
        </>
      )
      }
    </div >
  );
}
