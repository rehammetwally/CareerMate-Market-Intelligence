// src/components/charts/SkillsPieChart.jsx
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = [
  '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
  '#9b59b6', '#1abc9c', '#e67e22', '#34495e'
];

export default function SkillsPieChart({ data }) {
  if (!data || data.length === 0) {
    return <div style={{ padding: '2rem', color: '#999', textAlign: 'center' }}>
      No skills data available
    </div>;
  }

  const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        style={{ fontSize: '12px', fontWeight: 'bold' }}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

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
        🎯 Top 8 In-Demand Skills
      </h3>
      <ResponsiveContainer width="100%" height="90%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={CustomLabel}
            outerRadius={130}
            fill="#8884d8"
            dataKey="demand"
            nameKey="skill_name"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            formatter={(value, name) => [`${value.toLocaleString()} jobs`, name]}
            contentStyle={{ 
              background: '#fff', 
              border: '1px solid #ddd', 
              borderRadius: '8px' 
            }}
          />
          <Legend 
            verticalAlign="bottom" 
            height={36}
            formatter={(value, entry) => `${value}`}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}