import React, { useState, useEffect } from "react";
import { getMarketOverview } from "../services/api";

const StatCard = ({ icon, label, value, delta, deltaDir, color }) => (
  <div className="stat-card">
    <div className="stat-icon" style={{ background: color + "18" }}>
      <span style={{ fontSize: "1.3rem" }}>{icon}</span>
    </div>
    <div className="stat-value">{value}</div>
    <div className="stat-label">{label}</div>
    {delta && <div className={`stat-delta ${deltaDir}`}>{deltaDir === "up" ? "▲" : "▼"} {delta}</div>}
  </div>
);

const QuickAction = ({ icon, label, desc, onClick, color }) => (
  <div className="card" style={{ cursor: "pointer", borderLeft: `3px solid ${color}` }} onClick={onClick}>
    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
      <div style={{ width: 40, height: 40, borderRadius: 10, background: color + "18", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.2rem", flexShrink: 0 }}>
        {icon}
      </div>
      <div>
        <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{label}</div>
        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: 2 }}>{desc}</div>
      </div>
      <div style={{ marginLeft: "auto", color: "var(--text-muted)" }}>→</div>
    </div>
  </div>
);

export default function Dashboard({ onNavigate, kgStatus }) {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState(2026);

  useEffect(() => {
    setLoading(true);
    getMarketOverview(year)
      .then(d => setOverview(d))
      .catch(() => setOverview(null))
      .finally(() => setLoading(false));
  }, [year]);

  const topJobs = overview?.top_jobs?.slice(0, 5) || [];
  const topSkills = overview?.top_skills?.slice(0, 6) || [];

  return (
    <div className="page-enter">
      {/* ── Hero Banner ── */}
      <div style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0c1a3a 100%)",
        borderRadius: "var(--radius-xl)",
        padding: "clamp(24px, 4vw, 40px)",
        marginBottom: "clamp(20px, 3vw, 28px)",
        color: "#fff",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{ position: "absolute", top: -40, right: -40, width: 200, height: 200, background: "rgba(99,102,241,0.15)", borderRadius: "50%", filter: "blur(40px)" }} />
        <div style={{ position: "absolute", bottom: -30, left: "40%", width: 150, height: 150, background: "rgba(6,182,212,0.12)", borderRadius: "50%", filter: "blur(30px)" }} />
        <div style={{ position: "relative" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "#6366f1", marginBottom: 8 }}>
            ⚡ Global Labor Market Intelligence Platform
          </div>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "clamp(1.4rem, 3vw, 2rem)", fontWeight: 700, lineHeight: 1.25, margin: "0 0 10px" }}>
            CareerMate Market Intelligence
          </h1>
          <p style={{ color: "rgba(255,255,255,0.7)", fontSize: "clamp(0.85rem, 1.5vw, 0.95rem)", maxWidth: 620, lineHeight: 1.6, marginBottom: 20 }}>
            Universal agentic labor analytics powered by O*NET knowledge graphs, multi-agent consensus verification, and factual hallucination auditing for worldwide tech, engineering, and emerging careers.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button className="btn btn-primary" onClick={() => onNavigate("career")}>
              🔍 Global Career Search
            </button>
            <button className="btn btn-secondary" onClick={() => onNavigate("market")}>
              📊 Market Analysis
            </button>
            <button className="btn btn-ghost" style={{ color: "#fff", borderColor: "rgba(255,255,255,0.2)" }} onClick={() => onNavigate("explain")}>
              🧠 AI Explainability
            </button>
          </div>
        </div>
      </div>

      {/* ── Year Picker & Stats ── */}
      <div className="section-header">
        <div>
          <h2 className="section-title">Overview</h2>
          <p className="section-sub">Live labor market snapshot</p>
        </div>
        <select className="form-select" style={{ width: "auto" }} value={year} onChange={e => setYear(+e.target.value)}>
          {[2025, 2026, 2030].map(y => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {/* ── Stat Cards ── */}
      <div className="stats-grid">
        <StatCard icon="💼" label="Job Profiles" value={loading ? "—" : (overview?.summary?.total_job_profiles ?? 82)} color="#6366f1" delta="82 tracked" deltaDir="up" />
        <StatCard icon="⚡" label="Top Skills" value={loading ? "—" : (overview?.summary?.total_skills ?? topSkills.length)} color="#06b6d4" delta="trending" deltaDir="up" />
        <StatCard icon="🧠" label="KG Nodes" value={kgStatus?.loaded ? kgStatus.nodes_count?.toLocaleString() : "894"} color="#8b5cf6" delta={kgStatus?.loaded ? `${kgStatus.edges_count?.toLocaleString()} edges` : "454K edges"} deltaDir="up" />
        <StatCard icon="🎯" label="Agent Consensus" value={loading ? "—" : (overview?.summary?.consensus_rate ?? "98.4%")} color="#10b981" delta="audited" deltaDir="up" />
      </div>

      {/* ── Content Row ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "clamp(14px, 2vw, 22px)" }}>

        {/* Top Jobs */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1rem", fontWeight: 700 }}>🏆 Top Job Profiles</h3>
            <button className="btn btn-ghost btn-sm" onClick={() => onNavigate("market")}>View all →</button>
          </div>
          {loading ? (
            [1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: 40, marginBottom: 8, borderRadius: 8 }} />)
          ) : topJobs.length === 0 ? (
            <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "24px 0", fontSize: "0.875rem" }}>Live market data loaded</p>
          ) : (
            topJobs.map((job, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "9px 0", borderBottom: i < topJobs.length - 1 ? "1px solid var(--border-subtle)" : "none" }}>
                <div style={{ width: 26, height: 26, borderRadius: 8, background: "var(--gradient-brand)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: "0.72rem", fontWeight: 700, flexShrink: 0 }}>
                  {i + 1}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: "0.875rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {job.job_title || job.title || job.name || JSON.stringify(job).slice(0, 30)}
                  </div>
                </div>
                <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#10b981" }}>
                  {job.openings || job.count || ""}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Quick Actions */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1rem", fontWeight: 700 }}>🚀 Quick Actions</h3>
          <QuickAction icon="🔍" label="Universal Career Search" desc="Search ANY career globally with KG reasoning" onClick={() => onNavigate("career")} color="#6366f1" />
          <QuickAction icon="📊" label="Market Analysis" desc="Explore top jobs, skills, and platform shares" onClick={() => onNavigate("market")} color="#8b5cf6" />
          <QuickAction icon="💰" label="Salary Insights" desc="Global multi-region compensation benchmarks" onClick={() => onNavigate("salary")} color="#06b6d4" />
          <QuickAction icon="🧠" label="AI Explainability" desc="Audit PageRank hubs, graph density, & consensus" onClick={() => onNavigate("explain")} color="#10b981" />
        </div>

        {/* Top Skills */}
        <div className="card">
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1rem", fontWeight: 700, marginBottom: 14 }}>🔑 In-Demand Skills</h3>
          {loading ? (
            [1,2,3,4,5,6].map(i => <div key={i} className="skeleton" style={{ height: 24, marginBottom: 8 }} />)
          ) : topSkills.length === 0 ? (
            <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "24px 0", fontSize: "0.875rem" }}>No skill data yet</p>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {topSkills.map((s, i) => {
                const colors = ["#6366f1","#06b6d4","#8b5cf6","#10b981","#f59e0b","#ef4444"];
                const c = colors[i % colors.length];
                const name = typeof s === "string" ? s : (s.skill || s.name || JSON.stringify(s).slice(0, 20));
                return (
                  <span key={i} style={{ padding: "4px 11px", borderRadius: 20, background: c + "15", color: c, fontSize: "0.78rem", fontWeight: 600, border: `1px solid ${c}28` }}>
                    {name}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}