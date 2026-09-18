import { apiUrl } from '../config';
import { createContext, useContext, useEffect, useState } from "react";

const ChartsContext = createContext();

export const ChartsProvider = ({ children }) => {
  const [chartsData, setChartsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchCharts = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/market/charts`);

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setChartsData(result.data);
      } else {
        throw new Error(result.error || "Failed to load market data");
      }
    } catch (err) {
      setError(err.message || "Error loading market data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharts();
  }, []);

  const value = {
    chartsData,
    loading,
    error,
    refetch: fetchCharts,
  };

  return (
    <ChartsContext.Provider value={value}>{children}</ChartsContext.Provider>
  );
};

export const useCharts = () => useContext(ChartsContext);
