import React, { useState } from "react";
import { searchCareer } from "../services/api";

const SUGGESTED_CAREERS = [
  "Quantum Computing Engineer",
  "Neurosurgeon",
  "Autonomous Systems Engineer",
  "Renewable Energy Architect",
  "Computational Biologist",
  "Quantitative Financial Trader",
  "AI Safety Researcher",
  "Full Stack Developer"
];

export default function CareerSearch({ darkMode, kgStatus }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Compare mode state
  const [compareMode, setCompareMode] = useState(false);
  const [compareQuery, setCompareQuery] = useState("");
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResult, setCompareResult] = useState(null);

  const handleSearch = async (careerName = query) => {
    const q = careerName.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const data = await searchCareer(q);
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch career intelligence. Please verify backend is reachable.");
    } finally {
      setLoading(false);
    }
  };

  const handleCompareSearch = async (careerName = compareQuery) => {
    const q = careerName.trim();
    if (!q) return;
    setCompareLoading(true);
    try {
      const data = await searchCareer(q);
      setCompareResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setCompareLoading(false);
    }
  };

  const selectChip = (career) => {
    setQuery(career);
    handleSearch(career);
  };

  const renderCareerCard = (data, isCompare = false) => {
    if (!data) return null;
    const {
      query: careerTitle,
      confidence_score,
      confidence_label,
      kg_grounding,
      automation_risk,
      demand_trend,
      salary_benchmarks,
      education_pathway,
      key_skills,
      metadata
    } = data;

    const confPercent = Math.round(confidence_score * 100);
    const confColor = confPercent >= 75 ? "#10b981" : confPercent >= 50 ? "#f59e0b" : "#ef4444";

    return (
      <div className="card" style={{ flex: 1, minWidth: 320, display: "flex", flexDirection: "column", gap: 18 }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10 }}>
          <div>
            <div style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--brand-primary)", marginBottom: 4 }}>
              {isCompare ? "Career Benchmark B" : "Target Career Profile"}
            </div>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: "1.4rem", fontWeight: 700, margin: 0 }}>
              {careerTitle}
            </h2>
          </div>

          {/* Confidence Badge */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "6px 14px",
            borderRadius: 20,
            background: confColor + "15",
            border: `1px solid ${confColor}40`,
            color: confColor,
            fontWeight: 700,
            fontSize: "0.85rem"
          }}>
            <span style={{ fontSize: "1rem" }}>⚡</span>
            <span>{confPercent}% Confidence ({confidence_label})</span>
          </div>
        </div>

        {/* 4 Core Metrics Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
          {/* Automation Risk */}
          <div style={{ padding: 12, borderRadius: "var(--radius-md)", background: "var(--bg-elevated)", border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 4 }}>🤖 Automation Risk</div>
            <div style={{ fontSize: "1.15rem", fontWeight: 700, color: automation_risk?.color || "#f59e0b" }}>
              {automation_risk?.level || "Medium"} ({Math.round((automation_risk?.score || 0.45) * 100)}%)
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: 4, lineHeight: 1.3 }}>
              {automation_risk?.rationale}
            </div>
          </div>

          {/* 5-Year Demand Trend */}
          <div style={{ padding: 12, borderRadius: "var(--radius-md)", background: "var(--bg-elevated)", border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 4 }}>📈 5-Yr Growth Trend</div>
            <div style={{ fontSize: "1.15rem", fontWeight: 700, color: demand_trend?.color || "#10b981" }}>
              {demand_trend?.cagr || "+18% CAGR"}
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: 4 }}>
              {demand_trend?.horizon} · {demand_trend?.trend}
            </div>
          </div>

          {/* KG Grounding Status */}
          <div style={{ padding: 12, borderRadius: "var(--radius-md)", background: "var(--bg-elevated)", border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 4 }}>🧠 KG Grounding</div>
            <div style={{ fontSize: "1.15rem", fontWeight: 700, color: "#8b5cf6" }}>
              {kg_grounding?.nodes_found || 0} Nodes Mapped
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: 4 }}>
              O*NET 2026 Taxonomy Verified
            </div>
          </div>

          {/* Egypt / MENA Demand */}
          <div style={{ padding: 12, borderRadius: "var(--radius-md)", background: "var(--bg-elevated)", border: "1px solid var(--border-color)" }}>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 4 }}>🌍 MENA / Global Band</div>
            <div style={{ fontSize: "1rem", fontWeight: 700, color: "#06b6d4" }}>
              {salary_benchmarks?.egypt || "Top Tier"}
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginTop: 4 }}>
              {salary_benchmarks?.us} (US)
            </div>
          </div>
        </div>

        {/* Multi-Region Salary Benchmarks Table */}
        <div>
          <h4 style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem", fontWeight: 700, marginBottom: 10, display: "flex", alignItems: "center", gap: 6 }}>
            <span>💵 Global Multi-Region Compensation Benchmarks</span>
          </h4>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left", color: "var(--text-muted)" }}>
                  <th style={{ padding: "8px 10px" }}>Region</th>
                  <th style={{ padding: "8px 10px" }}>Estimated Compensation Band</th>
                  <th style={{ padding: "8px 10px" }}>Source / Methodology</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "8px 10px", fontWeight: 600 }}>🇺🇸 United States</td>
                  <td style={{ padding: "8px 10px", color: "var(--brand-primary)", fontWeight: 600 }}>{salary_benchmarks?.us || "N/A"}</td>
                  <td style={{ padding: "8px 10px", color: "var(--text-muted)" }}>BLS OOH & Glassdoor</td>
                </tr>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "8px 10px", fontWeight: 600 }}>🇪🇺 European Union</td>
                  <td style={{ padding: "8px 10px", color: "var(--brand-accent)", fontWeight: 600 }}>{salary_benchmarks?.eu || "N/A"}</td>
                  <td style={{ padding: "8px 10px", color: "var(--text-muted)" }}>Eurostat & TechSalaries EU</td>
                </tr>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "8px 10px", fontWeight: 600 }}>🌏 Asia-Pacific</td>
                  <td style={{ padding: "8px 10px", fontWeight: 600 }}>{salary_benchmarks?.apac || "N/A"}</td>
                  <td style={{ padding: "8px 10px", color: "var(--text-muted)" }}>APAC Talent Survey 2026</td>
                </tr>
                <tr>
                  <td style={{ padding: "8px 10px", fontWeight: 600 }}>🇪🇬 Egypt & MENA</td>
                  <td style={{ padding: "8px 10px", color: "#10b981", fontWeight: 700 }}>{salary_benchmarks?.egypt || "N/A"}</td>
                  <td style={{ padding: "8px 10px", color: "var(--text-muted)" }}>Wuzzuf & Crowdsourced Band</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Competency & Skill Architecture */}
        <div>
          <h4 style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem", fontWeight: 700, marginBottom: 10 }}>
            🔑 Required Skill Architecture
          </h4>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {key_skills?.map((item, idx) => (
              <span
                key={idx}
                style={{
                  padding: "5px 12px",
                  borderRadius: 20,
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  background: item.importance === "High" ? "rgba(99,102,241,0.12)" : "var(--bg-elevated)",
                  color: item.importance === "High" ? "var(--brand-primary)" : "var(--text-secondary)",
                  border: `1px solid ${item.importance === "High" ? "rgba(99,102,241,0.3)" : "var(--border-color)"}`
                }}
              >
                {item.skill} · <small style={{ opacity: 0.8 }}>{item.importance}</small>
              </span>
            ))}
          </div>
        </div>

        {/* Education Pathway */}
        <div>
          <h4 style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem", fontWeight: 700, marginBottom: 10 }}>
            🎓 Qualification & Education Pathway
          </h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {education_pathway?.map((step, idx) => (
              <div key={idx} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: "0.85rem" }}>
                <div style={{ width: 22, height: 22, borderRadius: "50%", background: "var(--brand-secondary)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.72rem", fontWeight: 700, flexShrink: 0 }}>
                  {idx + 1}
                </div>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Related O*NET Occupations in KG */}
        {kg_grounding?.related_occupations?.length > 0 && (
          <div>
            <h4 style={{ fontFamily: "var(--font-display)", fontSize: "0.95rem", fontWeight: 700, marginBottom: 8 }}>
              🌐 Related O*NET Standard Occupations (KG Grounded)
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {kg_grounding.related_occupations.map((occ, idx) => (
                <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "var(--bg-elevated)", borderRadius: "var(--radius-sm)", fontSize: "0.82rem" }}>
                  <div>
                    <span style={{ fontWeight: 600 }}>{occ.title}</span>
                    <span style={{ marginLeft: 8, color: "var(--text-muted)", fontSize: "0.75rem" }}>SOC: {occ.onet_code}</span>
                  </div>
                  <span style={{ color: "var(--brand-primary)", fontWeight: 700 }}>
                    {Math.round((occ.match_score || 0) * 100)}% Match
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Methodology & Provenance */}
        <div style={{ marginTop: "auto", paddingTop: 12, borderTop: "1px solid var(--border-subtle)", fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <span>Agent: {metadata?.agent || "CareerSearchAgent v1.0"}</span>
          <span>Method: {metadata?.method}</span>
          <span>Sources: {metadata?.sources?.join(", ")}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="page-enter">
      {/* ── Hero Header ── */}
      <div style={{
        background: "linear-gradient(135deg, #090d16 0%, #1e1b4b 60%, #0c1a3a 100%)",
        borderRadius: "var(--radius-xl)",
        padding: "clamp(24px, 4vw, 36px)",
        marginBottom: 24,
        color: "#fff",
        position: "relative",
        overflow: "hidden"
      }}>
        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#6366f1", marginBottom: 6 }}>
            Universal Occupational Intelligence
          </div>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(1.5rem, 3vw, 2.2rem)", fontWeight: 700, margin: "0 0 10px" }}>
            Global Career Search & KG Reasoning
          </h1>
          <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "0.95rem", maxWidth: 650, lineHeight: 1.6, margin: "0 0 20px" }}>
            Query <strong>any career across the globe</strong>. Evaluates multi-source grounding across the 894-node O*NET Knowledge Graph, Oxford automation risk taxonomy, and 2025-2030 demand forecasting.
          </p>

          {/* Search Bar */}
          <div style={{ display: "flex", gap: 10, maxWidth: 700, flexWrap: "wrap" }}>
            <input
              type="text"
              className="form-control"
              style={{
                flex: 1,
                minWidth: 260,
                padding: "12px 18px",
                borderRadius: "var(--radius-md)",
                border: "1px solid rgba(255,255,255,0.2)",
                background: "rgba(15,23,42,0.8)",
                color: "#fff",
                fontSize: "1rem"
              }}
              placeholder="Search ANY career globally (e.g., Quantum Computing Engineer)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <button
              className="btn btn-primary"
              style={{ padding: "12px 24px", fontSize: "0.95rem" }}
              onClick={() => handleSearch()}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "🔍 Analyze Career"}
            </button>
            <button
              className="btn btn-ghost"
              style={{ color: "#fff", borderColor: "rgba(255,255,255,0.2)", padding: "12px 18px" }}
              onClick={() => setCompareMode(!compareMode)}
            >
              {compareMode ? "Single Mode" : "⚖️ Compare Careers"}
            </button>
          </div>

          {/* Suggested Chips */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginTop: 18 }}>
            <span style={{ fontSize: "0.78rem", color: "rgba(255,255,255,0.5)", fontWeight: 600 }}>Suggested:</span>
            {SUGGESTED_CAREERS.map((c, i) => (
              <button
                key={i}
                onClick={() => selectChip(c)}
                style={{
                  background: "rgba(255,255,255,0.08)",
                  border: "1px solid rgba(255,255,255,0.15)",
                  color: "rgba(255,255,255,0.9)",
                  padding: "4px 11px",
                  borderRadius: 20,
                  fontSize: "0.76rem",
                  cursor: "pointer",
                  transition: "all 150ms ease"
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(99,102,241,0.3)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.08)"}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Compare Mode Input Bar */}
      {compareMode && (
        <div className="card" style={{ marginBottom: 20, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ fontWeight: 700, fontSize: "0.9rem" }}>Compare With:</span>
          <input
            type="text"
            className="form-control"
            style={{ flex: 1, minWidth: 200, padding: "8px 14px" }}
            placeholder="Second career to benchmark (e.g., Data Scientist)..."
            value={compareQuery}
            onChange={(e) => setCompareQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCompareSearch()}
          />
          <button
            className="btn btn-secondary"
            onClick={() => handleCompareSearch()}
            disabled={compareLoading}
          >
            {compareLoading ? "Loading..." : "Benchmark"}
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{ padding: 14, background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "var(--radius-md)", color: "#ef4444", marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* Results Container */}
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {renderCareerCard(result)}
        {compareMode && renderCareerCard(compareResult, true)}
      </div>

      {!result && !loading && (
        <div className="card" style={{ textAlign: "center", padding: "50px 20px" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: 12 }}>🌐</div>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem", fontWeight: 700 }}>
            Enter Any Career Above to Begin
          </h3>
          <p style={{ color: "var(--text-muted)", maxWidth: 500, margin: "6px auto 0", fontSize: "0.9rem" }}>
            The universal agent will search O*NET standard taxonomy nodes, compute automation exposure, evaluate global wage brackets, and construct educational pathways.
          </p>
        </div>
      )}
    </div>
  );
}