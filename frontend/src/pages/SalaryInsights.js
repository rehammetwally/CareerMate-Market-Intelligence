import React, { useState } from "react";
import "./NewFeatures.css";
import { getSalaryInsights } from "../services/api";

const PRESET_ROLES = [
  "Machine Learning Engineer",
  "Data Scientist",
  "Cloud Solutions Architect",
  "DevOps Engineer",
  "Cybersecurity Analyst",
  "Full Stack Developer"
];

const GLOBAL_BENCHMARKS = [
  { role: "Machine Learning Engineer", us: "$145,000 - $210,000", eu: "€75,000 - €120,000", apac: "$45,000 - $85,000", eg: "90,000 - 180,000 EGP" },
  { role: "Cloud Solutions Architect", us: "$150,000 - $220,000", eu: "€80,000 - €130,000", apac: "$50,000 - $95,000", eg: "85,000 - 170,000 EGP" },
  { role: "Data Scientist", us: "$125,000 - $185,000", eu: "€65,000 - €105,000", apac: "$38,000 - $75,000", eg: "70,000 - 140,000 EGP" },
  { role: "DevOps / SRE Engineer", us: "$130,000 - $190,000", eu: "€70,000 - €115,000", apac: "$40,000 - $80,000", eg: "75,000 - 150,000 EGP" },
  { role: "Full Stack Engineer", us: "$115,000 - $170,000", eu: "€60,000 - €95,000", apac: "$32,000 - $65,000", eg: "60,000 - 120,000 EGP" },
  { role: "Cybersecurity Analyst", us: "$110,000 - $165,000", eu: "€58,000 - €92,000", apac: "$30,000 - $62,000", eg: "55,000 - 110,000 EGP" }
];

export default function SalaryCrowdsource() {
  const [form, setForm] = useState({
    role: "Machine Learning Engineer",
    location: "Global",
    experience: "Mid-Level"
  });
  const [result, setResult] = useState({
    role: "Machine Learning Engineer",
    location: "Global",
    experience: "Mid-Level",
    salary_bands: {
      low_end: "$85,000 / yr",
      median: "$120,000 / yr",
      high_end: "$165,000+ / yr"
    },
    market_sentiment: "High Demand (Top Tier Compensation Tier)",
    top_paying_industries: [
      "Fintech & Algorithmic Trading",
      "Cloud & Distributed Systems",
      "Applied Generative AI Systems"
    ],
    leverage_points: [
      "Demonstrated hands-on experience with production model deployment & reliability",
      "Cross-functional communication & architectural leadership",
      "Experience working with remote global engineering standards"
    ],
    negotiation_advice: "Anchor at the top quartile of the market range and negotiate performance-based equity accelerators or remote flexibility stipends."
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async (roleToUse = form.role) => {
    if (!roleToUse) {
      setError("Please provide a role.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getSalaryInsights(roleToUse, form.location, form.experience);
      if (data.success) {
        setResult(data.salary_report);
      } else {
        setError(data.error || "Failed to retrieve salary insights.");
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const selectPreset = (r) => {
    const updated = { ...form, role: r };
    setForm(updated);
    handleAnalyze(r);
  };

  return (
    <div className="nf-page page-enter">
      {/* ── Header ── */}
      <div className="nf-header">
        <div className="nf-header-icon">💰</div>
        <div>
          <h1 className="nf-title">Global Salary Intelligence & Negotiation</h1>
          <p className="nf-subtitle">Multi-region compensation benchmarks, crowdsourced distributions, and strategic leverage points</p>
        </div>
      </div>

      {/* ── Preset Chips ── */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", alignSelf: "center", fontWeight: 600 }}>Quick Benchmarks:</span>
        {PRESET_ROLES.map((r, i) => (
          <button
            key={i}
            onClick={() => selectPreset(r)}
            style={{
              padding: "5px 12px",
              borderRadius: 20,
              fontSize: "0.78rem",
              background: form.role === r ? "var(--brand-primary)" : "var(--bg-elevated)",
              color: form.role === r ? "#fff" : "var(--text-secondary)",
              border: `1px solid ${form.role === r ? "var(--brand-primary)" : "var(--border-color)"}`,
              cursor: "pointer",
              transition: "all 150ms ease"
            }}
          >
            {r}
          </button>
        ))}
      </div>

      {/* ── Input Card ── */}
      <div className="nf-card">
        <h2 className="nf-section-title">📊 Compensation Parameters</h2>
        <div className="nf-form-grid">
          <div className="nf-form-group">
            <label>Target Role / Profession</label>
            <input 
              className="nf-input" 
              placeholder="e.g. Data Scientist, Solutions Architect" 
              value={form.role}
              onChange={e => setForm({ ...form, role: e.target.value })} 
              onKeyDown={e => e.key === "Enter" && handleAnalyze()}
            />
          </div>
          <div className="nf-form-group">
            <label>Geographic Market</label>
            <input 
              className="nf-input" 
              placeholder="e.g. Global Remote, Egypt, US, EU" 
              value={form.location}
              onChange={e => setForm({ ...form, location: e.target.value })} 
              onKeyDown={e => e.key === "Enter" && handleAnalyze()}
            />
          </div>
          <div className="nf-form-group">
            <label>Seniority / Experience</label>
            <select 
              className="nf-input"
              value={form.experience}
              onChange={e => setForm({ ...form, experience: e.target.value })}
            >
              <option value="Entry-Level">Entry-Level (0-2 yrs)</option>
              <option value="Mid-Level">Mid-Level (2-5 yrs)</option>
              <option value="Senior">Senior (5-8 yrs)</option>
              <option value="Staff / Principal">Staff / Principal (8+ yrs)</option>
            </select>
          </div>
        </div>
        <button className="nf-btn-primary" onClick={() => handleAnalyze()} disabled={loading}>
          {loading ? <><span className="nf-spinner" /> Synthesizing Market Data...</> : "💰 Generate Salary Report"}
        </button>
        {error && <div className="nf-error">⚠️ {error}</div>}
      </div>

      {/* ── Results ── */}
      {result && (
        <>
          <div className="nf-card">
            <h3 className="nf-section-title">💵 Calibrated Salary Bands: {result.role} ({form.location})</h3>
            <div className="nf-stats-row">
              <div className="nf-stat-card">
                <small>Entry / 25th Percentile</small>
                <strong>{result.salary_bands.low_end}</strong>
              </div>
              <div className="nf-stat-card" style={{ background: "var(--gradient-brand)", color: "white" }}>
                <small style={{ color: "rgba(255,255,255,0.8)" }}>Market Median (50th)</small>
                <strong style={{ color: "#fff" }}>{result.salary_bands.median}</strong>
              </div>
              <div className="nf-stat-card">
                <small>Top Tier / 90th Percentile</small>
                <strong style={{ color: "#10b981" }}>{result.salary_bands.high_end}</strong>
              </div>
            </div>
            <div className="nf-stat-badge" style={{ marginTop: "18px", display: "inline-block" }}>
              Market Sentiment: {result.market_sentiment}
            </div>
          </div>

          <div className="nf-two-col">
            <div className="nf-card">
              <h3 className="nf-section-title">🏗️ Top Paying Verticals & Sectors</h3>
              <ul className="nf-opt-list">
                {result.top_paying_industries?.map((ind, i) => (
                  <li key={i} className="nf-opt-item">{ind}</li>
                ))}
              </ul>
              <h3 className="nf-section-title" style={{ marginTop: "20px" }}>🧠 Career Leverage Points</h3>
              <ul className="nf-opt-list">
                {result.leverage_points?.map((p, i) => (
                  <li key={i} className="nf-opt-item" style={{ borderLeftColor: "#f59e0b" }}>{p}</li>
                ))}
              </ul>
            </div>
            <div className="nf-card">
              <h3 className="nf-section-title">🗣️ Strategic Negotiation Guidance</h3>
              <div className="nf-pitch-box" style={{ marginBottom: 16 }}>
                {result.negotiation_advice}
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                💡 <strong>Methodology Note:</strong> Compensation bands combine crowdsourced reporting, Glassdoor/LinkedIn benchmarks, and cost-of-living purchasing parity adjustments.
              </div>
            </div>
          </div>
        </>
      )}

      {/* ── Global Multi-Region Reference Table ── */}
      <div className="nf-card" style={{ marginTop: 24 }}>
        <h3 className="nf-section-title">🌐 Global Multi-Regional Benchmark Reference (2026 Baseline)</h3>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left", color: "var(--text-muted)" }}>
                <th style={{ padding: "10px 12px" }}>Role</th>
                <th style={{ padding: "10px 12px" }}>🇺🇸 United States</th>
                <th style={{ padding: "10px 12px" }}>🇪🇺 Europe (EU)</th>
                <th style={{ padding: "10px 12px" }}>🌏 Asia-Pacific</th>
                <th style={{ padding: "10px 12px" }}>🇪🇬 Egypt / MENA (Monthly)</th>
              </tr>
            </thead>
            <tbody>
              {GLOBAL_BENCHMARKS.map((b, idx) => (
                <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "10px 12px", fontWeight: 600 }}>{b.role}</td>
                  <td style={{ padding: "10px 12px", color: "var(--brand-primary)", fontWeight: 600 }}>{b.us}</td>
                  <td style={{ padding: "10px 12px", color: "var(--brand-accent)", fontWeight: 600 }}>{b.eu}</td>
                  <td style={{ padding: "10px 12px" }}>{b.apac}</td>
                  <td style={{ padding: "10px 12px", color: "#10b981", fontWeight: 700 }}>{b.eg}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}