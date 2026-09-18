export default function StatsCards({ stats }) {
  if (!stats) {
    return null;
  }

  const cards = [
    {
      title: '💼 Total Jobs',
      value: stats.total_jobs?.toLocaleString() || '0',
      subtitle: 'Unique Positions',
      color: '#3498db'
    },
    {
      title: '🌍 Global Demand',
      value: stats.total_global_demand?.toLocaleString() || '0',
      subtitle: 'Job Openings',
      color: '#2ecc71'
    },
    {
      title: '🇪🇬 Egypt Demand',
      value: stats.total_egypt_demand?.toLocaleString() || '0',
      subtitle: 'Local Openings',
      color: '#e74c3c'
    },
    {
      title: '💻 Freelancing',
      value: stats.avg_freelancing_score?.toFixed(1) || '0',
      subtitle: 'Avg Score',
      color: '#9b59b6'
    },
    {
      title: '📚 Career Tracks',
      value: stats.total_tracks || '0',
      subtitle: 'Available Paths',
      color: '#1abc9c'
    }
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1.5rem',
      marginBottom: '2.5rem',
      width: '100%'
    }}>
      {cards.map((card, index) => (
        <div key={index} style={{
          background: 'white',
          padding: '1.5rem',
          borderRadius: '12px',
          boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
          borderLeft: `4px solid ${card.color}`,
          transition: 'transform 0.2s, box-shadow 0.2s',
          cursor: 'pointer'
        }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.12)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,0.08)';
          }}
        >
          <div style={{ fontSize: '0.85rem', color: '#7f8c8d', marginBottom: '0.5rem', fontWeight: '500' }}>
            {card.title}
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: card.color, marginBottom: '0.25rem' }}>
            {card.value}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#95a5a6' }}>
            {card.subtitle}
          </div>
        </div>
      ))}
    </div>
  );
}