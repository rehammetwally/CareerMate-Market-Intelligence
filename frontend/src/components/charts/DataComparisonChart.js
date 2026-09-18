import React, { useState } from "react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Cell,
    PieChart,
    Pie
} from "recharts";

export default function DataComparisonChart({ comparisonData }) {
    const [activeTab, setActiveTab] = useState("overview");
    const [showAllJobs, setShowAllJobs] = useState(false);

    if (!comparisonData) return null;

    const { old, new: newData, diff, job_details, track_comparison, growth_trends } = comparisonData;

    // Prepare data for visualization
    const overviewData = [
        {
            category: "Total Jobs",
            old: old.total_jobs,
            new: newData.total_jobs,
            diff: diff.total_jobs
        },
        {
            category: "Global Demand (K)",
            old: Math.round(old.total_global_demand / 1000),
            new: Math.round(newData.total_global_demand / 1000),
            diff: Math.round(diff.total_global_demand / 1000)
        },
        {
            category: "Egypt Demand (100s)",
            old: Math.round(old.total_egypt_demand / 100),
            new: Math.round(newData.total_egypt_demand / 100),
            diff: Math.round(diff.total_egypt_demand / 100)
        },
        {
            category: "Avg Rating",
            old: parseFloat(old.avg_rating.toFixed(2)),
            new: parseFloat(newData.avg_rating.toFixed(2)),
            diff: parseFloat(diff.avg_rating.toFixed(2))
        }
    ];

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div
                    style={{
                        background: "white",
                        padding: "12px",
                        border: "1px solid #ddd",
                        borderRadius: "8px",
                        boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
                    }}
                >
                    <p style={{ fontWeight: "bold", marginBottom: "8px" }}>
                        {data.category}
                    </p>
                    <p style={{ color: "#3498db", margin: "4px 0" }}>
                        Old: {data.old.toLocaleString()}
                    </p>
                    <p style={{ color: "#27ae60", margin: "4px 0" }}>
                        New: {data.new.toLocaleString()}
                    </p>
                    <p
                        style={{
                            color: data.diff >= 0 ? "#27ae60" : "#e74c3c",
                            margin: "4px 0",
                            fontWeight: "bold"
                        }}
                    >
                        Diff: {data.diff >= 0 ? "+" : ""}
                        {data.diff.toLocaleString()}
                    </p>
                </div>
            );
        }
        return null;
    };

    const tabStyle = (isActive) => ({
        padding: "0.75rem 1.5rem",
        background: isActive ? "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" : "white",
        color: isActive ? "white" : "#666",
        border: "none",
        borderRadius: "8px 8px 0 0",
        cursor: "pointer",
        fontSize: "0.9rem",
        fontWeight: "500",
        transition: "all 0.3s",
    });

    const renderJobTable = (jobs, title, bgColor) => (
        <div style={{ marginBottom: "2rem" }}>
            <h3 style={{ color: "#2c3e50", marginBottom: "1rem", fontSize: "1.2rem" }}>
                {title}
            </h3>
            <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                        <tr style={{ background: bgColor }}>
                            <th style={{ padding: "0.75rem", textAlign: "left", color: "white" }}>Job Title</th>
                            <th style={{ padding: "0.75rem", textAlign: "right", color: "white" }}>Old Demand</th>
                            <th style={{ padding: "0.75rem", textAlign: "right", color: "white" }}>New Demand</th>
                            <th style={{ padding: "0.75rem", textAlign: "right", color: "white" }}>Change</th>
                            <th style={{ padding: "0.75rem", textAlign: "right", color: "white" }}>Change %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {jobs.map((job, idx) => (
                            <tr key={idx} style={{ borderBottom: "1px solid #ecf0f1" }}>
                                <td style={{ padding: "0.75rem" }}>{job.title}</td>
                                <td style={{ padding: "0.75rem", textAlign: "right" }}>
                                    {job.old_global_demand.toLocaleString()}
                                </td>
                                <td style={{ padding: "0.75rem", textAlign: "right" }}>
                                    {job.new_global_demand.toLocaleString()}
                                </td>
                                <td
                                    style={{
                                        padding: "0.75rem",
                                        textAlign: "right",
                                        color: job.demand_change >= 0 ? "#27ae60" : "#e74c3c",
                                        fontWeight: "bold"
                                    }}
                                >
                                    {job.demand_change >= 0 ? "+" : ""}
                                    {job.demand_change.toLocaleString()}
                                </td>
                                <td
                                    style={{
                                        padding: "0.75rem",
                                        textAlign: "right",
                                        color: job.demand_change_pct >= 0 ? "#27ae60" : "#e74c3c",
                                        fontWeight: "bold"
                                    }}
                                >
                                    {job.demand_change_pct >= 0 ? "+" : ""}
                                    {job.demand_change_pct}%
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );

    return (
        <div
            style={{
                background: "white",
                padding: "2rem",
                borderRadius: "12px",
                boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                marginTop: "2rem"
            }}
        >
            <h2
                style={{
                    color: "#2c3e50",
                    marginBottom: "1.5rem",
                    fontSize: "1.5rem",
                    textAlign: "center"
                }}
            >
                ⚖️ Detailed Data Comparison: Old vs New
            </h2>

            {/* Tabs */}
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem", borderBottom: "2px solid #ecf0f1", flexWrap: "wrap" }}>
                <button onClick={() => setActiveTab("overview")} style={tabStyle(activeTab === "overview")}>
                    📊 Overview
                </button>
                <button onClick={() => setActiveTab("gainers")} style={tabStyle(activeTab === "gainers")}>
                    📈 Top Gainers
                </button>
                <button onClick={() => setActiveTab("losers")} style={tabStyle(activeTab === "losers")}>
                    📉 Top Losers
                </button>
                <button onClick={() => setActiveTab("tracks")} style={tabStyle(activeTab === "tracks")}>
                    🎯 Tracks
                </button>
                <button onClick={() => setActiveTab("trends")} style={tabStyle(activeTab === "trends")}>
                    📈 Growth Trends
                </button>
                <button onClick={() => setActiveTab("all")} style={tabStyle(activeTab === "all")}>
                    📋 All Jobs
                </button>
            </div>

            {/* Overview Tab */}
            {activeTab === "overview" && (
                <>
                    {/* Statistics Cards */}
                    <div
                        style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                            gap: "1rem",
                            marginBottom: "2rem"
                        }}
                    >
                        {overviewData.map((item, idx) => (
                            <div
                                key={idx}
                                style={{
                                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                    padding: "1.5rem",
                                    borderRadius: "12px",
                                    color: "white",
                                    textAlign: "center"
                                }}
                            >
                                <div style={{ fontSize: "0.9rem", opacity: 0.9, marginBottom: "0.5rem" }}>
                                    {item.category}
                                </div>
                                <div style={{ fontSize: "1.8rem", fontWeight: "bold", marginBottom: "0.5rem" }}>
                                    {item.new.toLocaleString()}
                                </div>
                                <div
                                    style={{
                                        fontSize: "0.85rem",
                                        opacity: 0.95,
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        gap: "0.5rem"
                                    }}
                                >
                                    <span style={{ opacity: 0.7 }}>
                                        from {item.old.toLocaleString()}
                                    </span>
                                    <span
                                        style={{
                                            background: "rgba(255,255,255,0.2)",
                                            padding: "0.2rem 0.5rem",
                                            borderRadius: "6px",
                                            fontWeight: "bold"
                                        }}
                                    >
                                        {item.diff >= 0 ? "+" : ""}
                                        {item.diff}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Summary Stats */}
                    {job_details && (
                        <div style={{ background: "#f8f9fa", padding: "1.5rem", borderRadius: "12px", marginBottom: "2rem" }}>
                            <h3 style={{ marginBottom: "1rem", color: "#2c3e50" }}>📊 Summary</h3>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem" }}>
                                <div>
                                    <div style={{ fontSize: "0.9rem", color: "#7f8c8d" }}>Total Compared</div>
                                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#2c3e50" }}>
                                        {job_details.total_compared}
                                    </div>
                                </div>
                                <div>
                                    <div style={{ fontSize: "0.9rem", color: "#7f8c8d" }}>Updated Jobs</div>
                                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#3498db" }}>
                                        {job_details.updated_jobs}
                                    </div>
                                </div>
                                <div>
                                    <div style={{ fontSize: "0.9rem", color: "#7f8c8d" }}>New Jobs</div>
                                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#27ae60" }}>
                                        {job_details.new_jobs}
                                    </div>
                                </div>
                                <div>
                                    <div style={{ fontSize: "0.9rem", color: "#7f8c8d" }}>Removed Jobs</div>
                                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#e74c3c" }}>
                                        {job_details.removed_jobs}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Bar Chart */}
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={overviewData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ecf0f1" />
                            <XAxis dataKey="category" stroke="#7f8c8d" />
                            <YAxis stroke="#7f8c8d" />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend />
                            <Bar dataKey="old" fill="#3498db" name="Previous Data" radius={[8, 8, 0, 0]} />
                            <Bar dataKey="new" fill="#27ae60" name="New Data" radius={[8, 8, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </>
            )}

            {/* Top Gainers Tab */}
            {activeTab === "gainers" && job_details && job_details.top_gainers && (
                renderJobTable(job_details.top_gainers, "🚀 Top 10 Jobs with Biggest Demand Increase", "#27ae60")
            )}

            {/* Top Losers Tab */}
            {activeTab === "losers" && job_details && job_details.top_losers && (
                renderJobTable(job_details.top_losers, "📉 Top 10 Jobs with Biggest Demand Decrease", "#e74c3c")
            )}

            {/* Tracks Tab */}
            {activeTab === "tracks" && track_comparison && track_comparison.length > 0 && (
                <div>
                    <h3 style={{ color: "#2c3e50", marginBottom: "1.5rem" }}>🎯 Track-wise Comparison</h3>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={track_comparison} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="track" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="old_global_demand" fill="#3498db" name="Old Global Demand" />
                            <Bar dataKey="new_global_demand" fill="#27ae60" name="New Global Demand" />
                        </BarChart>
                    </ResponsiveContainer>

                    <div style={{ marginTop: "2rem" }}>
                        {track_comparison.map((track, idx) => (
                            <div key={idx} style={{ background: "#f8f9fa", padding: "1rem", marginBottom: "0.5rem", borderRadius: "8px" }}>
                                <strong>{track.track}</strong>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "0.5rem" }}>
                                    <div>
                                        <span style={{ color: "#7f8c8d" }}>Global: </span>
                                        <span style={{ fontWeight: "bold" }}>{track.new_global_demand.toLocaleString()}</span>
                                        <span style={{ color: track.global_change >= 0 ? "#27ae60" : "#e74c3c", marginLeft: "0.5rem" }}>
                                            ({track.global_change >= 0 ? "+" : ""}{track.global_change.toLocaleString()})
                                        </span>
                                    </div>
                                    <div>
                                        <span style={{ color: "#7f8c8d" }}>Egypt: </span>
                                        <span style={{ fontWeight: "bold" }}>{track.new_egypt_demand.toLocaleString()}</span>
                                        <span style={{ color: track.egypt_change >= 0 ? "#27ae60" : "#e74c3c", marginLeft: "0.5rem" }}>
                                            ({track.egypt_change >= 0 ? "+" : ""}{track.egypt_change.toLocaleString()})
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Growth Trends Tab */}
            {activeTab === "trends" && growth_trends && Object.keys(growth_trends).length > 0 && (
                <div>
                    <h3 style={{ color: "#2c3e50", marginBottom: "1.5rem" }}>📈 Growth Trends Comparison</h3>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }}>
                        {Object.entries(growth_trends).map(([trend, data], idx) => (
                            <div key={idx} style={{ background: "#f8f9fa", padding: "1.5rem", borderRadius: "12px" }}>
                                <div style={{ fontWeight: "bold", marginBottom: "1rem", color: "#2c3e50" }}>{trend}</div>
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                                    <span style={{ color: "#7f8c8d" }}>Old:</span>
                                    <span style={{ fontWeight: "bold" }}>{data.old_count}</span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                                    <span style={{ color: "#7f8c8d" }}>New:</span>
                                    <span style={{ fontWeight: "bold" }}>{data.new_count}</span>
                                </div>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                    <span style={{ color: "#7f8c8d" }}>Change:</span>
                                    <span style={{ fontWeight: "bold", color: data.change >= 0 ? "#27ae60" : "#e74c3c" }}>
                                        {data.change >= 0 ? "+" : ""}{data.change}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* All Jobs Tab */}
            {activeTab === "all" && job_details && job_details.all_jobs && (
                renderJobTable(job_details.all_jobs, "📋 All Jobs Comparison (Top 50 by Change)", "#667eea")
            )}

            <p
                style={{
                    textAlign: "center",
                    color: "#7f8c8d",
                    fontSize: "0.9rem",
                    marginTop: "2rem"
                }}
            >
                <strong>Note:</strong> Use the tabs above to explore different aspects of the comparison.
            </p>
        </div>
    );
}
