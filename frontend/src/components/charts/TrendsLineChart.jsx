import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function TrendsLineChart({ data }) {
  if (!data || data.length === 0) {
    return <div style={{ padding: '2rem', color: '#999' }}>No trends data available</div>;
  }

  return (
    <div style={{ width: '100%', height: 400, padding: '1rem', background: 'white', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
      <h3 style={{ marginBottom: '1rem', color: '#333' }}>📈 Market Trends</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip />
          <Legend />
          <Line yAxisId="left" type="monotone" dataKey="demand" stroke="#8884d8" strokeWidth={2} name="Demand" />
          <Line yAxisId="right" type="monotone" dataKey="salary" stroke="#82ca9d" strokeWidth={2} name="Avg Salary" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}