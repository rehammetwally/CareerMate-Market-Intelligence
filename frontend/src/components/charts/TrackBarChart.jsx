// src/components/charts/TrackBarChart.jsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function TrackBarChart({ data }) {
  if (!data || data.length === 0) {
    return <div style={{ padding: '2rem', color: '#999', textAlign: 'center' }}>
      No track data available
    </div>;
  }

  return (
    <div style={{ 
      width: '100%', 
      height: 400, 
      padding: '1.5rem', 
      background: 'white', 
      borderRadius: '12px', 
      boxShadow: '0 2px 12px rgba(0,0,0,0.08)' 
    }}>
      <h3 style={{ marginBottom: '1rem', color: '#2c3e50', fontSize: '1.2rem' }}>
        📚 Career Tracks Analysis
      </h3>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart 
          data={data} 
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="track" 
            angle={-30} 
            textAnchor="end" 
            height={80}
            style={{ fontSize: '11px' }}
          />
          <YAxis style={{ fontSize: '12px' }} />
          <Tooltip 
            contentStyle={{ 
              background: '#fff', 
              border: '1px solid #ddd', 
              borderRadius: '8px' 
            }}
          />
          <Legend />
          <Bar 
            dataKey="global_demand" 
            fill="#3498db" 
            name="Global Demand" 
            radius={[8, 8, 0, 0]}
          />
          <Bar 
            dataKey="egypt_demand" 
            fill="#e74c3c" 
            name="Egypt Demand" 
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}