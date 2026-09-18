// src/components/charts/JobsBarChart.jsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function JobsBarChart({ data }) {
  if (!data || data.length === 0) {
    return <div style={{ padding: '2rem', color: '#999', textAlign: 'center' }}>
      No job data available
    </div>;
  }

  return (
    <div style={{ 
      width: '100%', 
      height: 450, 
      padding: '1.5rem', 
      background: 'white', 
      borderRadius: '12px', 
      boxShadow: '0 2px 12px rgba(0,0,0,0.08)' 
    }}>
      <h3 style={{ marginBottom: '1rem', color: '#2c3e50', fontSize: '1.2rem' }}>
        🌍 Top 10 Jobs by Global Demand
      </h3>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart 
          data={data} 
          margin={{ top: 20, right: 30, left: 20, bottom: 100 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="job_title" 
            angle={-45} 
            textAnchor="end" 
            height={120}
            style={{ fontSize: '11px' }}
            interval={0}
          />
          <YAxis style={{ fontSize: '12px' }} />
          <Tooltip 
            contentStyle={{ 
              background: '#fff', 
              border: '1px solid #ddd', 
              borderRadius: '8px',
              padding: '10px'
            }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
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