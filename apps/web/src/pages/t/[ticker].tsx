import { useRouter } from 'next/router';

export default function TickerDetail() {
  const router = useRouter();
  const { ticker } = router.query;

  return (
    <main style={{
      padding: '2rem',
      fontFamily: 'system-ui, sans-serif',
    }}>
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
      }}>
        <h1 style={{ fontSize: '1.5rem' }}>
          <a href="/" style={{ textDecoration: 'none', color: 'inherit' }}>KLineLens</a>
          {' / '}
          <span style={{ color: '#0070f3' }}>{ticker}</span>
        </h1>
      </header>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '2rem',
      }}>
        {/* Chart placeholder */}
        <div style={{
          backgroundColor: '#f5f5f5',
          borderRadius: '8px',
          padding: '2rem',
          minHeight: '400px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <p style={{ color: '#999' }}>Chart will be rendered here</p>
        </div>

        {/* Analysis panel placeholder */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Card title="Market State">Regime and confidence will appear here</Card>
          <Card title="Behavior">Probabilities will appear here</Card>
          <Card title="Evidence">Evidence items will appear here</Card>
          <Card title="Timeline">Recent events will appear here</Card>
          <Card title="Playbook">Plan A/B will appear here</Card>
        </div>
      </div>
    </main>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      backgroundColor: '#fff',
      border: '1px solid #eee',
      borderRadius: '8px',
      padding: '1rem',
    }}>
      <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.875rem', color: '#666' }}>
        {title}
      </h3>
      <div style={{ color: '#999', fontSize: '0.875rem' }}>{children}</div>
    </div>
  );
}
