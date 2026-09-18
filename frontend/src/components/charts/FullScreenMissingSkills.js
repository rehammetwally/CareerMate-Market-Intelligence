import React from "react";

export default function FullScreenMissingSkills({ oldData, newData }) {
    if (!oldData?.missing_skills?.length && !newData?.missing_skills?.length) {
        return null;
    }

    const renderJobCard = (job, idx, bgColor, borderColor) => (
        <div
            key={idx}
            style={{
                background: idx % 2 === 0 ? "white" : bgColor,
                padding: "1.2rem",
                marginBottom: "1rem",
                borderRadius: "12px",
                border: `2px solid ${borderColor}`,
                boxShadow: `0 2px 6px ${borderColor}40`,
                transition: "all 0.3s",
                cursor: "pointer"
            }}
            onMouseOver={(e) => {
                e.currentTarget.style.boxShadow = `0 6px 16px ${borderColor}80`;
                e.currentTarget.style.transform = "translateY(-3px)";
            }}
            onMouseOut={(e) => {
                e.currentTarget.style.boxShadow = `0 2px 6px ${borderColor}40`;
                e.currentTarget.style.transform = "translateY(0)";
            }}
        >
            <div style={{ fontWeight: "bold", color: "#2c3e50", fontSize: "1.1rem", marginBottom: "0.5rem" }}>
                💼 {job.job_title}
            </div>
            <div style={{ display: "flex", gap: "0.75rem", marginBottom: "0.75rem", flexWrap: "wrap" }}>
                <span style={{
                    background: "#3498db",
                    color: "white",
                    padding: "0.3rem 0.8rem",
                    borderRadius: "15px",
                    fontSize: "0.75rem"
                }}>
                    🎯 {job.track}
                </span>
                <span style={{
                    background: "#27ae60",
                    color: "white",
                    padding: "0.3rem 0.8rem",
                    borderRadius: "15px",
                    fontSize: "0.75rem"
                }}>
                    ✅ {job.skills_count} Extracted
                </span>
            </div>
            
            {/* Extracted Skills */}
            {job.extracted_skills && job.extracted_skills !== 'nan' && job.extracted_skills !== '' && (
                <div style={{ marginBottom: "0.75rem" }}>
                    <div style={{
                        fontSize: "0.75rem",
                        color: "#27ae60",
                        fontWeight: "bold",
                        marginBottom: "0.4rem",
                        textTransform: "uppercase"
                    }}>
                        ✅ EXTRACTED SKILLS:
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                        {job.extracted_skills.split(',').map((skill, skillIdx) => (
                            <span key={skillIdx} style={{
                                background: "#d4edda",
                                color: "#155724",
                                padding: "0.3rem 0.7rem",
                                borderRadius: "6px",
                                fontSize: "0.75rem",
                                border: "1px solid #c3e6cb",
                                fontWeight: "500"
                            }}>
                                {skill.trim()}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Missing Skills */}
            <div style={{
                background: `${borderColor}15`,
                padding: "0.9rem",
                borderRadius: "10px",
                borderLeft: `4px solid ${borderColor}`
            }}>
                <div style={{
                    fontSize: "0.75rem",
                    color: "#e74c3c",
                    fontWeight: "bold",
                    marginBottom: "0.5rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.5px"
                }}>
                    ⚠️ MISSING SKILLS:
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                    {job.missing_skills.split(',').map((skill, skillIdx) => (
                        <span key={skillIdx} style={{
                            background: "white",
                            color: "#e74c3c",
                            padding: "0.3rem 0.7rem",
                            borderRadius: "6px",
                            fontSize: "0.75rem",
                            border: "1px solid #fcc",
                            fontWeight: "500"
                        }}>
                            {skill.trim()}
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );

    return (
        <div style={{ marginTop: "3rem" }}>
            <div
                style={{
                    background: "linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%)",
                    padding: "2rem",
                    borderRadius: "16px",
                    border: "2px solid #fee",
                    boxShadow: "0 4px 20px rgba(231, 76, 60, 0.15)"
                }}
            >
                {/* Header */}
                <div style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "2rem",
                    paddingBottom: "1.5rem",
                    borderBottom: "3px solid #e74c3c"
                }}>
                    <h2 style={{
                        margin: 0,
                        fontSize: "2rem",
                        color: "#c0392b",
                        fontWeight: "bold",
                        display: "flex",
                        alignItems: "center",
                        gap: "1rem"
                    }}>
                        🔍 Complete Skills Analysis - All Job Profiles
                    </h2>
                    <div style={{
                        display: "flex",
                        gap: "1rem"
                    }}>
                        {oldData?.missing_skills?.length > 0 && (
                            <div style={{
                                background: "#3498db",
                                color: "white",
                                padding: "0.6rem 1.2rem",
                                borderRadius: "25px",
                                fontSize: "0.9rem",
                                fontWeight: "bold"
                            }}>
                                📅 {oldData.year}: {oldData.missing_skills.length} Jobs
                            </div>
                        )}
                        {newData?.missing_skills?.length > 0 && (
                            <div style={{
                                background: "#27ae60",
                                color: "white",
                                padding: "0.6rem 1.2rem",
                                borderRadius: "25px",
                                fontSize: "0.9rem",
                                fontWeight: "bold"
                            }}>
                                📅 {newData.year}: {newData.missing_skills.length} Jobs
                            </div>
                        )}
                    </div>
                </div>

                {/* Two Column Layout */}
                <div style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "2rem"
                }}>
                    {/* Old Data */}
                    {oldData?.missing_skills?.length > 0 && (
                        <div>
                            <h3 style={{
                                color: "#3498db",
                                marginBottom: "1rem",
                                fontSize: "1.3rem",
                                display: "flex",
                                alignItems: "center",
                                gap: "0.5rem"
                            }}>
                                📋 Original Data ({oldData.year})
                            </h3>
                            <div style={{ maxHeight: "800px", overflowY: "auto", paddingRight: "0.5rem" }}>
                                {oldData.missing_skills.map((job, idx) => 
                                    renderJobCard(job, idx, "#f0f8ff", "#3498db")
                                )}
                            </div>
                        </div>
                    )}

                    {/* New Data */}
                    {newData?.missing_skills?.length > 0 && (
                        <div>
                            <h3 style={{
                                color: "#27ae60",
                                marginBottom: "1rem",
                                fontSize: "1.3rem",
                                display: "flex",
                                alignItems: "center",
                                gap: "0.5rem"
                            }}>
                                ✨ New Generated Data ({newData.year})
                            </h3>
                            <div style={{ maxHeight: "800px", overflowY: "auto", paddingRight: "0.5rem" }}>
                                {newData.missing_skills.map((job, idx) => 
                                    renderJobCard(job, idx, "#f0fff4", "#27ae60")
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div style={{
                    marginTop: "2rem",
                    padding: "1rem",
                    background: "rgba(231, 76, 60, 0.1)",
                    borderRadius: "12px",
                    fontSize: "0.9rem",
                    color: "#c0392b",
                    textAlign: "center"
                }}>
                    💡 <strong>Note:</strong> Green badges show AI-extracted skills. Red badges show missing skills required for the international job market.
                </div>
            </div>
        </div>
    );
}
