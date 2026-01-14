import { useState, FormEvent } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const [ticker, setTicker] = useState('');
  const router = useRouter();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const sanitized = ticker.trim().toUpperCase();
    if (sanitized) {
      router.push(`/t/${sanitized}`);
    }
  };

  return (
    <main style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      fontFamily: 'system-ui, sans-serif',
    }}>
      <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>KLineLens</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Market structure analysis terminal
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Enter ticker (e.g., TSLA)"
          style={{
            padding: '0.75rem 1rem',
            fontSize: '1rem',
            border: '1px solid #ccc',
            borderRadius: '4px',
            width: '250px',
          }}
        />
        <button
          type="submit"
          style={{
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            backgroundColor: '#000',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Analyze
        </button>
      </form>
    </main>
  );
}
