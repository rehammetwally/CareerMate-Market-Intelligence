// src/components/charts/PlatformChart.jsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const COLORS = ['#0077B5', '#FF6B6B', '#6FDA44', '#4A90E2', '#F5A623', '#50E3C2', '#4A4A4A'];

export default function PlatformChart({ data }) {
  if (!data || data.length === 0) {
    return <div style={{ padding: '2rem', color: '#999', textAlign: 'center' }}>
      No platform data available
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
        🌐 Job Distribution Across Platforms
      </h3>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart 
          data={data} 
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          layout="vertical"
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis type="number" style={{ fontSize: '12px' }} />
          <YAxis 
            dataKey="platform" 
            type="category" 
            width={120}
            style={{ fontSize: '11px' }}
          />
          <Tooltip 
            contentStyle={{ 
              background: '#fff', 
              border: '1px solid #ddd', 
              borderRadius: '8px' 
            }}
          />
          <Bar dataKey="value" radius={[0, 8, 8, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}