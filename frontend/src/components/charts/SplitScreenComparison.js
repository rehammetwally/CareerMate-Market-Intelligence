import React, { useState, useEffect } from "react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from "recharts";
import FullScreenMissingSkills from "./FullScreenMissingSkills";

const COLORS = ["#667eea", "#764ba2", "#f093fb", "#4facfe", "#43e97b", "#fa709a", "#fee140", "#30cfd0"];

export default function SplitScreenComparison({ comparisonData }) {
    if (!comparisonData || !comparisonData.old_data || !comparisonData.new_data) {
        return <div style={{ padding: "2rem", textAlign: "center" }}>No comparison data available</div>;
    }

    const { old_data, new_data } = comparisonData;

    const renderChartPanel = (data, title, bgGradient) => (
        <div style={{ flex: 1, padding: "1rem" }}>
            {/* Header */}
            <div
                style={{
                    background: bgGradient,
                    color: "white",
                    padding: "1.5rem",
                    borderRadius: "12px 12px 0 0",
                    textAlign: "center",
                }}
            >
                <h2 style={{ margin: 0, fontSize: "1.5rem" }}>{title}</h2>
                <p style={{ margin: "0.5rem 0 0 0", opacity: 0.9, fontSize: "0.9rem" }}>
                    {data.name}
                </p>
                <div
                    style={{
                        marginTop: "0.75rem",
                        fontSize: "1.1rem",
                        fontWeight: "bold",
                        background: "rgba(255,255,255,0.25)",
                        padding: "0.4rem 1rem",
                        borderRadius: "8px",
                        display: "inline-block",
                    }}
                >
                    📅 Year: {data.year || "N/A"}
                </div>
            </div>

            {/* Statistics Cards */}
            <div
                style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(2, 1fr)",
                    gap: "0.5rem",
                    padding: "1rem",
                    background: "#f8f9fa",
                }}
            >
                <div style={{ background: "white", padding: "1rem", borderRadius: "8px" }}>
                    <div style={{ fontSize: "0.75rem", color: "#7f8c8d" }}>Total Jobs</div>
                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#2c3e50" }}>
                        {data.statistics.total_jobs}
                    </div>
                </div>
                <div style={{ background: "white", padding: "1rem", borderRadius: "8px" }}>
                    <div style={{ fontSize: "0.75rem", color: "#7f8c8d" }}>Global Demand</div>
                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#2c3e50" }}>
                        {(data.statistics.total_global_demand / 1000).toFixed(0)}K
                    </div>
                </div>
                <div style={{ background: "white", padding: "1rem", borderRadius: "8px" }}>
                    <div style={{ fontSize: "0.75rem", color: "#7f8c8d" }}>Egypt Demand</div>
                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#2c3e50" }}>
                        {(data.statistics.total_egypt_demand / 1000).toFixed(1)}K
                    </div>
                </div>
                <div style={{ background: "white", padding: "1rem", borderRadius: "8px" }}>
                    <div style={{ fontSize: "0.75rem", color: "#7f8c8d" }}>Avg Rating</div>
                    <div style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#2c3e50" }}>
                        {data.statistics.avg_rating.toFixed(2)}
                    </div>
                </div>
            </div>

            {/* Top Jobs Chart */}
            <div style={{ background: "white", padding: "1rem", margin: "0.5rem 0" }}>
                <h3 style={{ margin: "0 0 1rem 0", fontSize: "1rem", color: "#2c3e50" }}>
                    📊 Top 10 Jobs by Demand
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={data.top_jobs.slice(0, 5)} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis dataKey="job_title" type="category" width={120} style={{ fontSize: "0.75rem" }} />
                        <Tooltip />
                        <Bar dataKey="global_demand" fill={bgGradient.split(",")[0].replace("linear-gradient(135deg, ", "")} radius={[0, 8, 8, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Track Analysis Chart */}
            <div style={{ background: "white", padding: "1rem", margin: "0.5rem 0" }}>
                <h3 style={{ margin: "0 0 1rem 0", fontSize: "1rem", color: "#2c3e50" }}>
                    🎯 Track Analysis
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={data.track_analysis}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="track" style={{ fontSize: "0.75rem" }} />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="global_demand" fill="#3498db" radius={[8, 8, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Top Skills Pie Chart */}
            <div style={{ background: "white", padding: "1rem", margin: "0.5rem 0" }}>
                <h3 style={{ margin: "0 0 1rem 0", fontSize: "1rem", color: "#2c3e50" }}>
                    💡 Top Skills Distribution
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                        <Pie
                            data={data.top_skills.slice(0, 6)}
                            dataKey="total_demand"
                            nameKey="skill_name"
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            label={(entry) => entry.skill_name}
                        >
                            {data.top_skills.slice(0, 6).map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );

    return (
        <div style={{ marginTop: "2rem" }}>
            <h2
                style={{
                    textAlign: "center",
                    color: "#2c3e50",
                    marginBottom: "1.5rem",
                    fontSize: "1.8rem",
                }}
            >
                📊 Split-Screen Comparison: Old vs New Data
            </h2>

            <div
                style={{
                    display: "flex",
                    gap: "1rem",
                    background: "white",
                    borderRadius: "12px",
                    boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                    overflow: "hidden",
                }}
            >
                {/* Left Panel - Old Data */}
                {renderChartPanel(
                    old_data,
                    "📋 Original Data",
                    "linear-gradient(135deg, #3498db 0%, #2980b9 100%)"
                )}

                {/* Divider */}
                <div style={{ width: "2px", background: "#ecf0f1" }} />

                {/* Right Panel - New Data */}
                {renderChartPanel(
                    new_data,
                    "✨ New Generated Data",
                    "linear-gradient(135deg, #27ae60 0%, #229954 100%)"
                )}
            </div>

            {/* Bottom Note */}
            <p
                style={{
                    textAlign: "center",
                    color: "#7f8c8d",
                    fontSize: "0.9rem",
                    marginTop: "1rem",
                }}
            >
                <strong>Tip:</strong> Scroll through both panels to compare charts side-by-side
            </p>

            {/* Full-Screen Missing Skills Section */}
            <FullScreenMissingSkills oldData={old_data} newData={new_data} />
        </div>
    );
}
