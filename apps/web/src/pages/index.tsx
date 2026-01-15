/**
 * 首页 - 简洁搜索页 + 自选股
 */

import { useState, FormEvent, useMemo, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Layout } from '../components';
import { useI18n } from '../lib/i18n';
import { fetchWatchlist, WatchlistItem } from '../lib/api';

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

export default function Home() {
  const [ticker, setTicker] = useState('');
  const [error, setError] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [watchlistMax, setWatchlistMax] = useState(8);
  const [watchlistLoading, setWatchlistLoading] = useState(true);
  const router = useRouter();
  const { t, lang } = useI18n();

  // Load watchlist on mount
  useEffect(() => {
    loadWatchlist();
    // Refresh watchlist every 5 seconds for realtime prices
    const interval = setInterval(loadWatchlist, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadWatchlist = async () => {
    try {
      const data = await fetchWatchlist();
      setWatchlist(data.items);
      setWatchlistMax(data.max);
    } catch (err) {
      console.error('Failed to load watchlist:', err);
    } finally {
      setWatchlistLoading(false);
    }
  };

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
      router.push(`/t/${encodeURIComponent(suggestions[selectedIndex].symbol)}`);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const handleSelectTicker = (symbol: string) => {
    router.push(`/t/${encodeURIComponent(symbol)}`);
  };

  const formatPrice = (price?: number) => {
    if (!price) return '—';
    return price >= 1000 ? price.toFixed(0) : price.toFixed(2);
  };

  const formatChange = (pct?: number) => {
    if (pct === undefined || pct === null) return '';
    const sign = pct >= 0 ? '+' : '';
    return `${sign}${pct.toFixed(2)}%`;
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

        {/* Watchlist */}
        <div style={{
          marginTop: '2.5rem',
          width: '100%',
          maxWidth: '560px',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            marginBottom: '1rem',
          }}>
            <span style={{ fontSize: '0.8125rem', color: '#888' }}>
              {lang === 'zh' ? '自选股' : 'Watchlist'}
            </span>
            <span style={{
              fontSize: '0.75rem',
              color: '#aaa',
              backgroundColor: '#f5f5f5',
              padding: '0.125rem 0.5rem',
              borderRadius: '999px',
            }}>
              {watchlist.length}/{watchlistMax}
            </span>
          </div>

          {watchlistLoading ? (
            <div style={{ textAlign: 'center', color: '#aaa', fontSize: '0.875rem' }}>
              {lang === 'zh' ? '加载中...' : 'Loading...'}
            </div>
          ) : watchlist.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#aaa', fontSize: '0.875rem' }}>
              {lang === 'zh' ? '暂无自选股，在详情页点击 ☆ 添加' : 'No watchlist items. Click ☆ on detail page to add.'}
            </div>
          ) : (
            <div style={{
              display: 'flex',
              gap: '0.75rem',
              flexWrap: 'wrap',
              justifyContent: 'center',
            }}>
              {watchlist.map(item => {
                const hasRealtime = !!item.realtime;
                const change = item.realtime?.change_pct;
                const isUp = (change ?? 0) >= 0;

                return (
                  <button
                    key={item.ticker}
                    onClick={() => handleSelectTicker(item.ticker)}
                    style={{
                      padding: '0.75rem 1rem',
                      minWidth: '120px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.25rem',
                      backgroundColor: '#fff',
                      border: '1px solid #ddd',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.15s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#fafafa';
                      e.currentTarget.style.borderColor = '#ccc';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#fff';
                      e.currentTarget.style.borderColor = '#ddd';
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                    }}>
                      <span style={{
                        fontFamily: MONO,
                        fontWeight: 600,
                        fontSize: '0.9375rem',
                        color: '#000',
                      }}>
                        {item.ticker}
                      </span>
                      {hasRealtime && (
                        <span style={{
                          fontSize: '0.625rem',
                          color: '#16a34a',
                        }}>
                          ⚡
                        </span>
                      )}
                    </div>
                    {hasRealtime && (
                      <>
                        <span style={{
                          fontFamily: MONO,
                          fontSize: '0.875rem',
                          fontWeight: 500,
                          color: '#333',
                        }}>
                          ${formatPrice(item.realtime?.price)}
                        </span>
                        <span style={{
                          fontFamily: MONO,
                          fontSize: '0.75rem',
                          fontWeight: 500,
                          color: isUp ? '#16a34a' : '#dc2626',
                        }}>
                          {formatChange(change)}
                        </span>
                      </>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Hint */}
        <p style={{
          marginTop: '2.5rem',
          color: '#aaa',
          fontSize: '0.8125rem',
        }}>
          {t('search_hint')}
        </p>
      </div>
    </Layout>
  );
}
