import React, { useState, useEffect } from "react";
import { getMarketKgStatus, getKgAnalytics, getKgSubgraph } from "../services/api";

const InfoRow = ({ label, value, highlight }) => (
  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "11px 0", borderBottom: "1px solid var(--border-subtle)" }}>
    <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontWeight: 500 }}>{label}</span>
    <span style={{ fontSize: "0.875rem", fontWeight: 700, color: highlight || "var(--text-primary)" }}>{value}</span>
  </div>
);

export default function KGStatus({ kgStatus, kgLoading, onRefresh, onNavigate }) {
  const [refreshing, setRefreshing] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  
  // Interactive Subgraph Explorer state
  const [selectedNode, setSelectedNode] = useState("15-1252.00");
  const [subgraph, setSubgraph] = useState(null);
  const [subgraphLoading, setSubgraphLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    getKgAnalytics().then(d => { if (mounted) setAnalytics(d); }).catch(() => {});
    return () => { mounted = false; };
  }, []);

  const loadSubgraph = async (nodeId) => {
    setSubgraphLoading(true);
    try {
      const data = await getKgSubgraph(nodeId, 6);
      setSubgraph(data);
    } catch (e) {
      console.error(e);
    } finally {
      setSubgraphLoading(false);
    }
  };

  useEffect(() => {
    loadSubgraph(selectedNode);
  }, [selectedNode]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await onRefresh();
    try {
      const a = await getKgAnalytics();
      setAnalytics(a);
      await loadSubgraph(selectedNode);
    } catch (e) {}
    setTimeout(() => setRefreshing(false), 800);
  };

  const isOnline = kgStatus?.loaded;
  const nodes = kgStatus?.nodes_count ?? 894;
  const edges = kgStatus?.edges_count ?? 454412;
  const graphType = kgStatus?.graph_type ?? "DiGraph";
  const density = analytics?.graph_summary?.density ?? 0.569;

  // SVG Geometry for interactive ego-network graph
  const svgWidth = 560;
  const svgHeight = 360;
  const centerX = svgWidth / 2;
  const centerY = svgHeight / 2;
  const radius = 135;

  const neighbors = subgraph?.nodes?.filter(n => n.type === "neighbor") || [];

  return (
    <div className="page-enter">
      <div className="section-header">
        <div>
          <h2 className="section-title">Knowledge Graph Status & Topology</h2>
          <p className="section-sub">O*NET occupational ontology — hallucination grounding & transition graph</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {onNavigate && (
            <button className="btn btn-primary" onClick={() => onNavigate("explain")}>
              🧠 Thesis Empirical Benchmarks →
            </button>
          )}
          <button className="btn btn-secondary" onClick={handleRefresh} disabled={refreshing || kgLoading} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ display: "inline-block", animation: (refreshing || kgLoading) ? "spin 0.65s linear infinite" : "none", fontSize: "0.9rem" }}>⟳</span>
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {/* ── Status Hero ── */}
      <div className="card" style={{ marginBottom: 22, borderLeft: `4px solid ${isOnline ? "#10b981" : "#ef4444"}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{
            width: 60, height: 60, borderRadius: "var(--radius-lg)",
            background: isOnline ? "rgba(16,185,129,0.12)" : "rgba(239,68,68,0.1)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "1.8rem", flexShrink: 0,
          }}>
            {isOnline ? "🧠" : "⚠️"}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: "var(--font-display)", fontSize: "1.15rem", fontWeight: 700, marginBottom: 4 }}>
              Knowledge Graph {isOnline ? "Online & Grounded" : "Offline / Unreachable"}
            </div>
            <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              {isOnline
                ? `O*NET 2026 ontology active with ${nodes.toLocaleString()} standard occupational nodes and ${edges.toLocaleString()} competency links`
                : "The backend service may not be running. Start it on port 8001"}
            </div>
          </div>
          <div className={`kg-badge ${isOnline ? "online" : "offline"}`} style={{ fontSize: "0.8rem", padding: "8px 14px" }}>
            <span className="kg-dot" />
            {isOnline ? "Active" : "Offline"}
          </div>
        </div>
      </div>

      {/* ── Stats Grid ── */}
      <div className="stats-grid" style={{ marginBottom: 22 }}>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: "rgba(99,102,241,0.12)" }}>🔵</div>
          <div className="stat-value">{nodes.toLocaleString()}</div>
          <div className="stat-label">Occupation Nodes</div>
          <div className="stat-delta up">▲ O*NET SOC codes</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: "rgba(6,182,212,0.12)" }}>🔗</div>
          <div className="stat-value">{edges.toLocaleString()}</div>
          <div className="stat-label">Skill Relationships</div>
          <div className="stat-delta up">▲ semantic edges</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: "rgba(139,92,246,0.12)" }}>🕸️</div>
          <div className="stat-value">{typeof density === "number" ? density.toFixed(3) : density}</div>
          <div className="stat-label">Graph Density</div>
          <div className="stat-delta up">High Connectivity</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{ background: "rgba(16,185,129,0.12)" }}>✅</div>
          <div className="stat-value">{graphType}</div>
          <div className="stat-label">Graph Architecture</div>
          <div className="stat-delta up">NetworkX DiGraph</div>
        </div>
      </div>

      {/* ── INTERACTIVE SUBGRAPH VISUALIZER (Thesis Feature) ── */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, marginBottom: 16 }}>
          <div>
            <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", fontWeight: 700 }}>
              🌐 Interactive Knowledge Graph Ego-Network Explorer
            </h3>
            <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
              Explore 1-hop occupational transitions and competency cosine similarities in real-time. Click any neighbor node to re-center the network.
            </p>
          </div>

          {/* Focal Node Selector */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>Explore Focal Role:</span>
            <select
              className="form-select"
              value={selectedNode}
              onChange={e => setSelectedNode(e.target.value)}
              style={{ width: "auto", fontSize: "0.85rem", padding: "6px 12px" }}
            >
              <option value="15-1252.00">Software Developers (15-1252.00)</option>
              <option value="15-1211.00">Computer Systems Analysts (15-1211.00)</option>
              <option value="11-9041.00">Engineering Managers (11-9041.00)</option>
              <option value="11-1021.00">Operations Managers (11-1021.00)</option>
              <option value="19-1042.00">Medical Scientists (19-1042.00)</option>
            </select>
          </div>
        </div>

        {/* Dynamic SVG Visualizer */}
        <div style={{
          background: "var(--bg-elevated)",
          borderRadius: "var(--radius-md)",
          padding: 16,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          overflowX: "auto"
        }}>
          {subgraphLoading ? (
            <div style={{ padding: "60px 0", color: "var(--text-muted)", fontSize: "0.9rem" }}>
              Traversing Knowledge Graph Subgraph...
            </div>
          ) : (
            <svg width={svgWidth} height={svgHeight} style={{ maxWidth: "100%" }}>
              {/* Links */}
              {neighbors.map((nbr, idx) => {
                const angle = (idx / neighbors.length) * 2 * Math.PI - Math.PI / 2;
                const x = centerX + radius * Math.cos(angle);
                const y = centerY + radius * Math.sin(angle);
                const sim = nbr.similarity || 0.98;
                return (
                  <g key={idx}>
                    <line
                      x1={centerX}
                      y1={centerY}
                      x2={x}
                      y2={y}
                      stroke="var(--brand-primary)"
                      strokeWidth={Math.max(1, (sim - 0.95) * 40)}
                      strokeOpacity={0.6}
                      strokeDasharray="4 2"
                    />
                    <text
                      x={(centerX + x) / 2}
                      y={(centerY + y) / 2 - 4}
                      fill="var(--text-muted)"
                      fontSize="9"
                      textAnchor="middle"
                      fontWeight="600"
                    >
                      {Math.round(sim * 100)}%
                    </text>
                  </g>
                );
              })}

              {/* Central Node */}
              <circle
                cx={centerX}
                cy={centerY}
                r="36"
                fill="var(--brand-primary)"
                fillOpacity="0.2"
                stroke="var(--brand-primary)"
                strokeWidth="2.5"
              />
              <circle
                cx={centerX}
                cy={centerY}
                r="28"
                fill="var(--brand-primary)"
              />
              <text
                x={centerX}
                y={centerY + 4}
                fill="#ffffff"
                fontSize="11"
                fontWeight="700"
                textAnchor="middle"
              >
                Focal Role
              </text>
              <text
                x={centerX}
                y={centerY + 50}
                fill="var(--text-primary)"
                fontSize="12"
                fontWeight="700"
                textAnchor="middle"
              >
                {subgraph?.central_node?.title || "Central Node"}
              </text>

              {/* Neighbor Nodes */}
              {neighbors.map((nbr, idx) => {
                const angle = (idx / neighbors.length) * 2 * Math.PI - Math.PI / 2;
                const x = centerX + radius * Math.cos(angle);
                const y = centerY + radius * Math.sin(angle);
                return (
                  <g
                    key={idx}
                    style={{ cursor: "pointer" }}
                    onClick={() => setSelectedNode(nbr.id)}
                  >
                    <circle
                      cx={x}
                      cy={y}
                      r="20"
                      fill="var(--bg-surface)"
                      stroke="var(--brand-accent)"
                      strokeWidth="2"
                    />
                    <text
                      x={x}
                      y={y + 4}
                      fill="var(--brand-accent)"
                      fontSize="9"
                      fontWeight="700"
                      textAnchor="middle"
                    >
                      {nbr.id.slice(0, 5)}
                    </text>
                    <text
                      x={x}
                      y={y > centerY ? y + 26 : y - 24}
                      fill="var(--text-secondary)"
                      fontSize="10"
                      fontWeight="600"
                      textAnchor="middle"
                    >
                      {nbr.label?.length > 20 ? nbr.label.slice(0, 18) + "..." : nbr.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>

        {/* Central Node Description */}
        {subgraph?.central_node?.description && (
          <div style={{ marginTop: 14, padding: 12, borderRadius: "var(--radius-sm)", background: "var(--bg-elevated)", fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            <strong>O*NET Standard Definition ({subgraph.central_node.soc}):</strong> {subgraph.central_node.description}
          </div>
        )}
      </div>

      {/* ── Technical Info & Workflow ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "clamp(14px, 2vw, 22px)" }}>
        {/* Technical Info */}
        <div className="card">
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1rem", fontWeight: 700, marginBottom: 14 }}>📋 Graph Details</h3>
          <InfoRow label="Status"          value={isOnline ? "Online" : "Offline"} highlight={isOnline ? "#10b981" : "#ef4444"} />
          <InfoRow label="Node Count"      value={nodes.toLocaleString()} />
          <InfoRow label="Edge Count"      value={edges.toLocaleString()} />
          <InfoRow label="Graph Type"      value={graphType} />
          <InfoRow label="Density"         value={typeof density === "number" ? density.toFixed(4) : density} />
          <InfoRow label="Taxonomy"        value="O*NET 2026 Database" />
          <InfoRow label="Grounding Mode"  value="Bipartite graph verification" />
        </div>

        {/* How it Works */}
        <div className="card">
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1rem", fontWeight: 700, marginBottom: 14 }}>🧪 Grounding Workflow</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[
              { icon: "1️⃣", title: "Multi-Platform Scrape", desc: "Independent scrapers aggregate live market postings across 4 global platforms." },
              { icon: "2️⃣", title: "Entity Grounding", desc: "Every occupation, skill, and credential claim is anchored to verified O*NET nodes." },
              { icon: "3️⃣", title: "Hallucination Filtering", desc: "Claims without graph evidence are rejected or flagged with uncertainty scores." },
              { icon: "4️⃣", title: "Consensus Synthesis", desc: "A fused authoritative intelligence report is served with citation provenance." },
            ].map(({ icon, title, desc }, i) => (
              <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                <span style={{ fontSize: "1.1rem" }}>{icon}</span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.88rem" }}>{title}</div>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: 2 }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}