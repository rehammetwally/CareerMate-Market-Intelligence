import React, { useState, useEffect, useCallback } from "react";
import { getMarketKgStatus } from "./services/api";
import MarketAnalysis from "./pages/MarketAnalysis";
import SalaryInsights from "./pages/SalaryInsights";
import KGStatus from "./pages/KGStatus";
import Dashboard from "./pages/Dashboard";
import CareerSearch from "./pages/CareerSearch";
import AIExplainability from "./pages/AIExplainability";

// ── Icons (inline SVG to avoid extra deps) ──────────────────
const Icon = ({ d, size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const Icons = {
  dashboard:   "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z M9 22V12h6v10",
  career:      "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  market:      "M18 20V10 M12 20V4 M6 20v-6",
  salary:      "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 14.93V18h-2v-1.07C9.39 16.57 8 15.38 8 14h2c0 .55.81 1 2 1s2-.45 2-1-.41-.88-2.04-1.37C10.56 12.01 8 11.26 8 9c0-1.38 1.39-2.57 3-2.93V5h2v1.07c1.61.36 3 1.55 3 2.93h-2c0-.55-.81-1-2-1s-2 .45-2 1 .41.88 2.04 1.37C13.44 11.99 16 12.74 16 15c0 1.38-1.39 2.57-3 2.93z",
  explain:     "M9.5 2A2.5 2.5 0 017 4.5v15a2.5 2.5 0 002.5 2.5h5A2.5 2.5 0 0017 19.5v-15A2.5 2.5 0 0014.5 2h-5z",
  kg:          "M12 2a3 3 0 013 3 3 3 0 01-3 3 3 3 0 01-3-3 3 3 0 013-3M3 18a3 3 0 013-3 3 3 0 013 3 3 3 0 01-3 3 3 3 0 01-3-3M18 18a3 3 0 013-3 3 3 0 013 3 3 3 0 01-3 3 3 3 0 01-3-3M12 8v3m-4.24 2.76-2.12 2.12M16.24 13.76l2.12 2.12",
  collapse:    "M11 19l-7-7 7-7 M18 19l-7-7 7-7",
  expand:      "M13 5l7 7-7 7 M6 5l7 7-7 7",
  menu:        "M3 12h18 M3 6h18 M3 18h18",
  close:       "M18 6L6 18 M6 6l12 12",
  sun:         "M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42M12 5a7 7 0 100 14A7 7 0 0012 5z",
  moon:        "M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z",
};

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard",         icon: Icons.dashboard, section: "Overview"     },
  { id: "career",    label: "Career Search",     icon: Icons.career,    section: "Intelligence" },
  { id: "market",    label: "Market Analysis",   icon: Icons.market,    section: "Analytics"    },
  { id: "salary",    label: "Salary Insights",   icon: Icons.salary,    section: "Analytics"    },
  { id: "explain",   label: "AI Explainability", icon: Icons.explain,   section: "Intelligence" },
  { id: "kg",        label: "Knowledge Graph",   icon: Icons.kg,        section: "System"       },
];

const PAGE_TITLES = {
  dashboard: "Dashboard",
  career:    "Global Career Search & Reasoning",
  market:    "Market Analysis",
  salary:    "Salary Insights & Benchmarks",
  explain:   "AI Explainability & Graph Analytics",
  kg:        "Knowledge Graph Status & Topology",
};

export default function App() {
  const [page,          setPage]          = useState("dashboard");
  const [collapsed,     setCollapsed]     = useState(false);
  const [mobileOpen,    setMobileOpen]    = useState(false);
  const [darkMode,      setDarkMode]      = useState(() => {
    return localStorage.getItem("theme") === "dark";
  });
  const [kgStatus,      setKgStatus]      = useState(null);
  const [kgLoading,     setKgLoading]     = useState(true);

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  // Fetch KG status
  const fetchKg = useCallback(() => {
    setKgLoading(true);
    getMarketKgStatus()
      .then(d => setKgStatus(d))
      .catch(() => setKgStatus(null))
      .finally(() => setKgLoading(false));
  }, []);

  useEffect(() => {
    fetchKg();
    const t = setInterval(fetchKg, 30000);
    return () => clearInterval(t);
  }, [fetchKg]);

  // Close mobile sidebar on resize
  useEffect(() => {
    const handler = () => { if (window.innerWidth > 768) setMobileOpen(false); };
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  const navigate = (id) => {
    setPage(id);
    setMobileOpen(false);
  };

  // Group nav items by section
  const sections = [...new Set(NAV_ITEMS.map(n => n.section))];

  const renderPage = () => {
    const props = { darkMode, kgStatus };
    switch (page) {
      case "dashboard": return <Dashboard {...props} onNavigate={navigate} />;
      case "career":    return <CareerSearch {...props} />;
      case "market":    return <MarketAnalysis {...props} />;
      case "salary":    return <SalaryInsights {...props} />;
      case "explain":   return <AIExplainability {...props} />;
      case "kg":        return <KGStatus {...props} onRefresh={fetchKg} kgLoading={kgLoading} onNavigate={navigate} />;
      default:          return <Dashboard {...props} onNavigate={navigate} />;
    }
  };

  return (
    <div className="app-shell">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="mobile-overlay visible" onClick={() => setMobileOpen(false)} />
      )}

      {/* ── Sidebar ── */}
      <aside className={`sidebar${collapsed ? " collapsed" : ""}${mobileOpen ? " mobile-open" : ""}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </div>
          <div className="sidebar-logo-text">
            <div className="sidebar-logo-title">Market Intel</div>
            <div className="sidebar-logo-sub">Global Career Intelligence</div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          {sections.map(section => (
            <div key={section}>
              <div className="sidebar-section">{section}</div>
              {NAV_ITEMS.filter(n => n.section === section).map(item => (
                <div
                  key={item.id}
                  className={`sidebar-link${page === item.id ? " active" : ""}`}
                  onClick={() => navigate(item.id)}
                  title={collapsed ? item.label : undefined}
                >
                  <div className="sidebar-link-icon">
                    <Icon d={item.icon} size={17} />
                  </div>
                  <span className="sidebar-link-label">{item.label}</span>
                </div>
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <button
            className="sidebar-collapse-btn"
            onClick={() => setCollapsed(c => !c)}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <Icon d={collapsed ? Icons.expand : Icons.collapse} size={15} />
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <div className={`main-content${collapsed ? " sidebar-collapsed" : ""}`}>
        {/* Header */}
        <header className="top-header">
          <div className="header-left">
            <button className="hamburger-btn" onClick={() => setMobileOpen(o => !o)}>
              <Icon d={mobileOpen ? Icons.close : Icons.menu} size={18} />
            </button>
            <span className="header-title">{PAGE_TITLES[page]}</span>
          </div>

          <div className="header-right">
            {/* KG Status Badge */}
            <div className={`kg-badge${kgStatus?.loaded ? " online" : " offline"}`}>
              <span className="kg-dot" />
              {kgStatus?.loaded
                ? `KG Active · ${kgStatus.nodes_count?.toLocaleString()} nodes`
                : kgLoading ? "Connecting..." : "KG Offline"}
            </div>

            {/* Dark Mode Toggle */}
            <button
              className="theme-toggle"
              onClick={() => setDarkMode(d => !d)}
              title={darkMode ? "Light mode" : "Dark mode"}
            >
              {darkMode ? "☀️" : "🌙"}
            </button>
          </div>
        </header>

        {/* Page */}
        <main className="page-content page-enter" key={page}>
          {renderPage()}
        </main>
      </div>
    </div>
  );
}