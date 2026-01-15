/**
 * 首页 - 简洁搜索页
 */

import { useState, FormEvent, useMemo, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Layout } from '../components';
import { useI18n } from '../lib/i18n';

// ============ Ticker Database ============
interface TickerInfo {
  symbol: string;
  name: string;
}

const TICKERS: TickerInfo[] = [
  { symbol: 'TSLA', name: 'Tesla Inc' },
  { symbol: 'AAPL', name: 'Apple Inc' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation' },
  { symbol: 'META', name: 'Meta Platforms' },
  { symbol: 'GOOGL', name: 'Alphabet Inc' },
  { symbol: 'AMZN', name: 'Amazon.com Inc' },
  { symbol: 'MSFT', name: 'Microsoft Corporation' },
  { symbol: 'AMD', name: 'Advanced Micro Devices' },
  { symbol: 'NFLX', name: 'Netflix Inc' },
  { symbol: 'JPM', name: 'JPMorgan Chase' },
  { symbol: 'V', name: 'Visa Inc' },
  { symbol: 'SPY', name: 'S&P 500 ETF' },
  { symbol: 'QQQ', name: 'Nasdaq 100 ETF' },
  { symbol: 'IWM', name: 'Russell 2000 ETF' },
  { symbol: 'GLD', name: 'Gold ETF' },
  { symbol: 'BTC/USD', name: 'Bitcoin' },
  { symbol: 'ETH/USD', name: 'Ethereum' },
  { symbol: 'SOL/USD', name: 'Solana' },
];

const MONO = '"SF Mono", "Fira Code", "Consolas", monospace';

// Recent history
const RECENT_KEY = 'klinelens:recent';
const MAX_RECENT = 6;

function getRecentTickers(): string[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(RECENT_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function addRecentTicker(symbol: string): void {
  if (typeof window === 'undefined') return;
  try {
    const recent = getRecentTickers().filter(s => s !== symbol);
    recent.unshift(symbol);
    localStorage.setItem(RECENT_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)));
  } catch {}
}

export default function Home() {
  const [ticker, setTicker] = useState('');
  const [error, setError] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [recentTickers, setRecentTickers] = useState<string[]>([]);
  const router = useRouter();
  const { t } = useI18n();

  // Load recent on mount
  useEffect(() => {
    setRecentTickers(getRecentTickers());
  }, []);

  const suggestions = useMemo(() => {
    if (!ticker.trim()) return [];
    const query = ticker.toLowerCase();
    return TICKERS
      .filter(t =>
        t.symbol.toLowerCase().includes(query) ||
        t.name.toLowerCase().includes(query)
      )
      .slice(0, 6);
  }, [ticker]);

  useEffect(() => {
    const handleClickOutside = () => setShowSuggestions(false);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError('');
    const sanitized = ticker.trim().toUpperCase();
    if (!sanitized) {
      setError(t('error_empty_ticker'));
      return;
    }
    if (!/^[A-Z0-9\-\.\/]+$/.test(sanitized)) {
      setError(t('error_invalid_ticker'));
      return;
    }
    addRecentTicker(sanitized);
    router.push(`/t/${encodeURIComponent(sanitized)}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      addRecentTicker(suggestions[selectedIndex].symbol);
      router.push(`/t/${encodeURIComponent(suggestions[selectedIndex].symbol)}`);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const handleSelectTicker = (symbol: string) => {
    addRecentTicker(symbol);
    router.push(`/t/${encodeURIComponent(symbol)}`);
  };

  return (
    <Layout>
      <div style={{
        minHeight: 'calc(100vh - 120px)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '2rem',
      }}>
        {/* Logo */}
        <h1 style={{
          fontSize: '3rem',
          fontWeight: 700,
          marginBottom: '0.5rem',
          color: '#000',
          letterSpacing: '-0.03em',
        }}>
          KLineLens
        </h1>

        {/* Subtitle */}
        <p style={{
          color: '#888',
          fontSize: '1rem',
          marginBottom: '2.5rem',
        }}>
          Market Structure Analysis
        </p>

        {/* Search */}
        <form onSubmit={handleSubmit} style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '1rem',
          width: '100%',
          maxWidth: '560px',
        }}>
          <div style={{ display: 'flex', gap: '0.75rem', width: '100%' }}>
            <div style={{ flex: 1, position: 'relative' }} onClick={e => e.stopPropagation()}>
              <input
                type="text"
                value={ticker}
                onChange={(e) => {
                  setTicker(e.target.value);
                  setShowSuggestions(true);
                  setSelectedIndex(-1);
                }}
                onFocus={() => setShowSuggestions(true)}
                onKeyDown={handleKeyDown}
                placeholder={t('search_placeholder')}
                style={{
                  width: '100%',
                  padding: '1rem 1.25rem',
                  fontSize: '1.125rem',
                  fontFamily: MONO,
                  border: '1px solid #ddd',
                  borderRadius: '12px',
                  outline: 'none',
                  backgroundColor: '#fff',
                }}
              />
              {showSuggestions && suggestions.length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  marginTop: '8px',
                  backgroundColor: '#fff',
                  border: '1px solid #ddd',
                  borderRadius: '12px',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                  zIndex: 100,
                  overflow: 'hidden',
                }}>
                  {suggestions.map((item, i) => (
                    <div
                      key={item.symbol}
                      onClick={() => handleSelectTicker(item.symbol)}
                      style={{
                        padding: '0.875rem 1.25rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1rem',
                        cursor: 'pointer',
                        backgroundColor: i === selectedIndex ? '#f5f5f5' : 'transparent',
                        borderBottom: i < suggestions.length - 1 ? '1px solid #eee' : 'none',
                      }}
                    >
                      <span style={{
                        fontFamily: MONO,
                        fontWeight: 600,
                        fontSize: '1rem',
                        color: '#000',
                      }}>
                        {item.symbol}
                      </span>
                      <span style={{ fontSize: '0.875rem', color: '#888' }}>
                        {item.name}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button
              type="submit"
              style={{
                padding: '1rem 2rem',
                fontSize: '1rem',
                fontWeight: 600,
                backgroundColor: '#000',
                color: '#fff',
                border: 'none',
                borderRadius: '12px',
                cursor: 'pointer',
              }}
            >
              {t('analyze')}
            </button>
          </div>
          {error && (
            <div style={{ color: '#e53935', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}
        </form>

        {/* Recent */}
        {recentTickers.length > 0 && (
          <div style={{
            display: 'flex',
            gap: '0.75rem',
            marginTop: '2rem',
            flexWrap: 'wrap',
            justifyContent: 'center',
            alignItems: 'center',
          }}>
            <span style={{ fontSize: '0.8125rem', color: '#aaa' }}>Recent:</span>
            {recentTickers.map(symbol => (
              <button
                key={symbol}
                onClick={() => handleSelectTicker(symbol)}
                style={{
                  padding: '0.625rem 1.25rem',
                  fontSize: '0.9375rem',
                  fontFamily: MONO,
                  fontWeight: 500,
                  color: '#333',
                  backgroundColor: '#fff',
                  border: '1px solid #ddd',
                  borderRadius: '999px',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f5f5f5';
                  e.currentTarget.style.borderColor = '#ccc';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#fff';
                  e.currentTarget.style.borderColor = '#ddd';
                }}
              >
                {symbol}
              </button>
            ))}
          </div>
        )}

        {/* Hint */}
        <p style={{
          marginTop: '3rem',
          color: '#aaa',
          fontSize: '0.8125rem',
        }}>
          {t('search_hint')}
        </p>
      </div>
    </Layout>
  );
}
