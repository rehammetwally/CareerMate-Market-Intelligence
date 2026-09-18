import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8001";

export const marketApi = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Intercept errors globally
marketApi.interceptors.response.use(
  r => r,
  err => {
    if (err.code === "ERR_NETWORK") {
      console.warn("[MarketAPI] Backend unreachable at", API_BASE_URL);
    }
    return Promise.reject(err);
  }
);

export const getMarketOverview = async (year = 2026) => {
  const response = await marketApi.get("/api/market/overview", { params: { year } });
  return response.data;
};

export const getMarketKgStatus = async () => {
  const response = await marketApi.get("/api/market/kg/status");
  return response.data;
};

export const getMarketVersions = async () => {
  const response = await marketApi.get("/api/market/versions");
  return response.data;
};

export const getHealthCheck = async () => {
  const response = await marketApi.get("/health");
  return response.data;
};

export const triggerEnhancedResearch = async (jobProfiles, year = 2026) => {
  const response = await marketApi.post("/api/market/research/enhanced", {
    job_profiles: jobProfiles,
    year,
  });
  return response.data;
};

export const getSalaryInsights = async (role, location = "Global", experience = "Junior") => {
  const response = await marketApi.post("/salary-crowdsource", { role, location, experience });
  return response.data;
};


export const searchCareer = async (query) => {
  const response = await marketApi.post("/api/career/search", { query });
  return response.data;
};

export const getKgAnalytics = async () => {
  const response = await marketApi.get("/api/kg/analytics");
  return response.data;
};

export const getBenchmarkEval = async () => {
  const response = await marketApi.get("/api/eval/benchmark");
  return response.data;
};

export const getEdgeTelemetry = async () => {
  const response = await marketApi.get("/api/edge/telemetry");
  return response.data;
};

export const auditHallucination = async (claim) => {
  const response = await marketApi.post("/api/hallucination/audit", { claim });
  return response.data;
};

export const getKgSubgraph = async (node = "15-1252.00", limit = 8) => {
  const response = await marketApi.get("/api/kg/subgraph", { params: { node, limit } });
  return response.data;
};

export const getThesisPaper = async () => {
  const response = await marketApi.get("/api/thesis/paper");
  return response.data;
};

export default marketApi;
