import React, { useState, useEffect } from 'react';
import { useInitialize } from '../useInitialize';
import JobsBarChart from '../components/charts/JobsBarChart';
import SkillsPieChart from '../components/charts/SkillsPieChart';
import TrackBarChart from '../components/charts/TrackBarChart';
import PlatformChart from '../components/charts/PlatformChart';
import StatsCards from '../components/charts/StatsCards';

export default function MarketAnalysis({ onInitialize }) {
  const { loading: initLoading } = useInitialize('http://localhost:8000/api/market/init', onInitialize);

  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchMarketData();
  }, []);

  const fetchMarketData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8000/api/market/charts');

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        setMarketData(result.data);
        console.log('✅ Market data loaded:', result.data);
      } else {
        throw new Error(result.error || 'Failed to load market data');
      }
    } catch (err) {
      console.error('❌ Error fetching market data:', err);
      setError(err.message || 'Error loading market data');
    } finally {
      setLoading(false);
    }
  };

  if (initLoading || loading) {
    return (
      <div style={{ padding: '3rem', textAlign: 'center', minHeight: '100vh', background: '#f5f7fa' }}>
        <div className="spinner"></div>
        <p style={{ marginTop: '1rem', color: '#666' }}>Loading Market Analysis Dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', minHeight: '100vh', background: '#f5f7fa' }}>
        <div style={{
          background: '#fee',
          border: '1px solid #fcc',
          padding: '2rem',
          borderRadius: '12px',
          textAlign: 'center',
          maxWidth: '600px',
          margin: '0 auto'
        }}>
          <h3 style={{ color: '#c33', margin: '0 0 1rem 0' }}>❌ Error Loading Data</h3>
          <p style={{ color: '#666', margin: '0 0 1.5rem 0' }}>{error}</p>
          <button
            onClick={fetchMarketData}
            style={{
              padding: '0.75rem 1.5rem',
              background: '#3498db',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      padding: '2rem',
      backgroundColor: '#f5f7fa',
    }}>
      <header style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ color: '#2c3e50', margin: '0 0 0.5rem 0', fontSize: '2.5rem' }}>
          📊 Career Market Analysis Dashboard
        </h1>
        <p style={{ color: '#7f8c8d', fontSize: '1.1rem' }}>
          Real-time insights from the job market
        </p>
      </header>

      {marketData && (
        <>
          {/* Statistics Cards */}
          <StatsCards stats={marketData.statistics} />

          {/* Main Charts Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
            gap: '2rem',
            marginBottom: '2rem'
          }}>
            <JobsBarChart data={marketData.top_jobs} />
            <SkillsPieChart data={marketData.top_skills} />
          </div>

          {/* Secondary Charts */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
            gap: '2rem',
            marginBottom: '2rem'
          }}>
            <TrackBarChart data={marketData.track_analysis} />
            <PlatformChart data={marketData.platform_distribution} />
          </div>
        </>
      )}
    </div>
  );
}