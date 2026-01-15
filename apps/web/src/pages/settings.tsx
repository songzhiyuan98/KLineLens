/**
 * 设置页面 - 简洁现代风格
 */

import { useState, useEffect, useMemo } from 'react';
import { Layout } from '../components';
import { useI18n, Language } from '../lib/i18n';
import {
  fetchWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  WatchlistItem,
} from '../lib/api';

// Fluid typography
const F = {
  small: 'clamp(0.75rem, 0.65rem + 0.2vw, 0.875rem)',
  body: 'clamp(0.875rem, 0.75rem + 0.25vw, 1rem)',
  heading: 'clamp(1.25rem, 1rem + 0.5vw, 1.5rem)',
};

const MONO = '"SF Mono", "Roboto Mono", "Fira Code", Menlo, Monaco, monospace';

// Ticker database for autocomplete
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

export default function Settings() {
  const { lang, setLang, t } = useI18n();

  // Watchlist state
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [watchlistMax, setWatchlistMax] = useState(8);
  const [watchlistLoading, setWatchlistLoading] = useState(true);
  const [newTicker, setNewTicker] = useState('');
  const [addingTicker, setAddingTicker] = useState(false);
  const [removingTicker, setRemovingTicker] = useState<string | null>(null);
  const [error, setError] = useState('');

  // Autocomplete state
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  // Confirmation dialog state
  const [confirmDialog, setConfirmDialog] = useState<{
    type: 'add' | 'remove';
    ticker: string;
    name?: string;
  } | null>(null);

  // Filter suggestions based on input
  const suggestions = useMemo(() => {
    if (!newTicker.trim()) return [];
    const query = newTicker.toLowerCase();
    const existingTickers = watchlist.map(w => w.ticker);
    return TICKERS
      .filter(t =>
        (t.symbol.toLowerCase().includes(query) ||
         t.name.toLowerCase().includes(query)) &&
        !existingTickers.includes(t.symbol)
      )
      .slice(0, 6);
  }, [newTicker, watchlist]);

  // Load watchlist
  useEffect(() => {
    loadWatchlist();
  }, []);

  // Close suggestions on outside click
  useEffect(() => {
    const handleClickOutside = () => setShowSuggestions(false);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter' && newTicker.trim()) {
        e.preventDefault();
        openAddDialog(newTicker.trim().toUpperCase());
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0) {
        openAddDialog(suggestions[selectedIndex].symbol, suggestions[selectedIndex].name);
      } else if (newTicker.trim()) {
        openAddDialog(newTicker.trim().toUpperCase());
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const openAddDialog = (ticker: string, name?: string) => {
    if (watchlist.length >= watchlistMax) {
      setError(lang === 'zh' ? `已达到 ${watchlistMax} 个上限` : `Maximum ${watchlistMax} items reached`);
      return;
    }
    setShowSuggestions(false);
    setConfirmDialog({ type: 'add', ticker, name });
  };

  const openRemoveDialog = (ticker: string) => {
    setConfirmDialog({ type: 'remove', ticker });
  };

  const handleConfirm = async () => {
    if (!confirmDialog) return;

    if (confirmDialog.type === 'add') {
      setAddingTicker(true);
      setError('');
      try {
        await addToWatchlist(confirmDialog.ticker);
        setNewTicker('');
        await loadWatchlist();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to add');
      } finally {
        setAddingTicker(false);
      }
    } else {
      setRemovingTicker(confirmDialog.ticker);
      try {
        await removeFromWatchlist(confirmDialog.ticker);
        await loadWatchlist();
      } catch (err) {
        console.error('Failed to remove:', err);
      } finally {
        setRemovingTicker(null);
      }
    }
    setConfirmDialog(null);
  };

  return (
    <Layout>
      <div style={{
        maxWidth: '560px',
        margin: '0 auto',
        padding: 'clamp(1.5rem, 4vw, 3rem) clamp(1rem, 3vw, 2rem)',
      }}>
        {/* Header */}
        <h1 style={{
          fontSize: F.heading,
          fontWeight: 600,
          marginBottom: 'clamp(2rem, 4vw, 3rem)',
          color: '#000',
        }}>
          {t('settings')}
        </h1>

        {/* Watchlist Setting */}
        <section style={{ marginBottom: '2.5rem' }}>
          <div style={{
            fontSize: 'clamp(0.625rem, 0.5rem + 0.2vw, 0.75rem)',
            fontWeight: 500,
            color: '#999',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}>
            <span>{lang === 'zh' ? '自选股（实时数据）' : 'Watchlist (Realtime Data)'}</span>
            <span style={{ fontFamily: MONO }}>{watchlist.length}/{watchlistMax}</span>
          </div>

          {/* Add ticker input with autocomplete */}
          <div style={{ position: 'relative', marginBottom: '1rem' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                type="text"
                value={newTicker}
                onChange={(e) => {
                  setNewTicker(e.target.value.toUpperCase());
                  setShowSuggestions(true);
                  setSelectedIndex(-1);
                }}
                onFocus={() => setShowSuggestions(true)}
                onKeyDown={handleKeyDown}
                placeholder={lang === 'zh' ? '搜索股票代码或名称' : 'Search ticker or name'}
                disabled={addingTicker || watchlist.length >= watchlistMax}
                style={{
                  flex: 1,
                  padding: '0.625rem 1rem',
                  fontSize: F.small,
                  fontFamily: MONO,
                  border: '1px solid #e5e5e5',
                  borderRadius: '8px',
                  outline: 'none',
                  backgroundColor: watchlist.length >= watchlistMax ? '#f5f5f5' : '#fff',
                }}
              />
              <button
                onClick={() => newTicker.trim() && openAddDialog(newTicker.trim().toUpperCase())}
                disabled={addingTicker || !newTicker.trim() || watchlist.length >= watchlistMax}
                style={{
                  padding: '0.625rem 1.25rem',
                  fontSize: F.small,
                  fontWeight: 500,
                  backgroundColor: '#000',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: addingTicker || !newTicker.trim() || watchlist.length >= watchlistMax ? 'not-allowed' : 'pointer',
                  opacity: addingTicker || !newTicker.trim() || watchlist.length >= watchlistMax ? 0.5 : 1,
                }}
              >
                {addingTicker ? '...' : (lang === 'zh' ? '添加' : 'Add')}
              </button>
            </div>

            {/* Autocomplete dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                marginTop: '4px',
                backgroundColor: '#fff',
                border: '1px solid #e5e5e5',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                zIndex: 100,
                overflow: 'hidden',
              }}>
                {suggestions.map((item, i) => (
                  <div
                    key={item.symbol}
                    onClick={() => openAddDialog(item.symbol, item.name)}
                    style={{
                      padding: '0.625rem 1rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      cursor: 'pointer',
                      backgroundColor: i === selectedIndex ? '#f5f5f5' : 'transparent',
                      borderBottom: i < suggestions.length - 1 ? '1px solid #f0f0f0' : 'none',
                    }}
                  >
                    <span style={{
                      fontFamily: MONO,
                      fontWeight: 600,
                      fontSize: F.small,
                      color: '#000',
                    }}>
                      {item.symbol}
                    </span>
                    <span style={{ fontSize: F.small, color: '#666' }}>
                      {item.name}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {error && (
            <div style={{
              fontSize: F.small,
              color: '#dc2626',
              marginBottom: '1rem',
            }}>
              {error}
            </div>
          )}

          {/* Watchlist items */}
          <div style={{
            backgroundColor: '#fafafa',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
            overflow: 'hidden',
          }}>
            {watchlistLoading ? (
              <div style={{
                padding: '1.5rem',
                textAlign: 'center',
                color: '#999',
                fontSize: F.small,
              }}>
                {lang === 'zh' ? '加载中...' : 'Loading...'}
              </div>
            ) : watchlist.length === 0 ? (
              <div style={{
                padding: '1.5rem',
                textAlign: 'center',
                color: '#999',
                fontSize: F.small,
              }}>
                {lang === 'zh' ? '暂无自选股' : 'No watchlist items'}
              </div>
            ) : (
              watchlist.map((item, i) => (
                <div
                  key={item.ticker}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem 1rem',
                    borderBottom: i < watchlist.length - 1 ? '1px solid #f0f0f0' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{
                      fontFamily: MONO,
                      fontWeight: 600,
                      fontSize: F.body,
                      color: '#000',
                    }}>
                      {item.ticker}
                    </span>
                    {item.realtime && (
                      <span style={{
                        fontFamily: MONO,
                        fontSize: F.small,
                        color: '#666',
                      }}>
                        ${item.realtime.price.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => openRemoveDialog(item.ticker)}
                    disabled={removingTicker === item.ticker}
                    style={{
                      padding: '0.375rem 0.75rem',
                      fontSize: F.small,
                      color: '#dc2626',
                      backgroundColor: 'transparent',
                      border: '1px solid #fecaca',
                      borderRadius: '6px',
                      cursor: removingTicker === item.ticker ? 'not-allowed' : 'pointer',
                      opacity: removingTicker === item.ticker ? 0.5 : 1,
                    }}
                  >
                    {removingTicker === item.ticker ? '...' : (lang === 'zh' ? '移除' : 'Remove')}
                  </button>
                </div>
              ))
            )}
          </div>

          <div style={{
            fontSize: 'clamp(0.625rem, 0.5rem + 0.15vw, 0.6875rem)',
            color: '#999',
            marginTop: '0.75rem',
            lineHeight: 1.5,
          }}>
            {lang === 'zh'
              ? '自选股将获得实时 WebSocket 数据推送，最多支持 8 个。'
              : 'Watchlist items receive real-time WebSocket data. Maximum 8 items.'}
          </div>
        </section>

        {/* Language Setting */}
        <section style={{ marginBottom: '2.5rem' }}>
          <div style={{
            fontSize: 'clamp(0.625rem, 0.5rem + 0.2vw, 0.75rem)',
            fontWeight: 500,
            color: '#999',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.75rem',
          }}>
            {t('language')}
          </div>

          <div style={{
            display: 'flex',
            gap: '0.5rem',
          }}>
            {(['zh', 'en'] as Language[]).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                style={{
                  padding: '0.625rem 1.25rem',
                  fontSize: F.small,
                  fontWeight: 500,
                  border: '1px solid',
                  borderColor: lang === l ? '#000' : '#e5e5e5',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: lang === l ? '#000' : '#fff',
                  color: lang === l ? '#fff' : '#666',
                  transition: 'all 0.15s',
                }}
              >
                {l === 'zh' ? '中文' : 'English'}
              </button>
            ))}
          </div>
        </section>

        {/* About */}
        <section style={{ marginBottom: '2.5rem' }}>
          <div style={{
            fontSize: 'clamp(0.625rem, 0.5rem + 0.2vw, 0.75rem)',
            fontWeight: 500,
            color: '#999',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.75rem',
          }}>
            {t('about')}
          </div>

          <div style={{
            padding: '1rem 1.25rem',
            backgroundColor: '#fafafa',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
          }}>
            <div style={{
              fontSize: F.body,
              fontWeight: 600,
              color: '#000',
              marginBottom: '0.375rem',
            }}>
              KLineLens
            </div>
            <div style={{
              fontSize: F.small,
              color: '#666',
              marginBottom: '0.5rem',
            }}>
              {t('app_description')}
            </div>
            <div style={{
              fontSize: F.small,
              fontFamily: MONO,
              color: '#999',
            }}>
              v0.2.0
            </div>
          </div>
        </section>

        {/* Disclaimer */}
        <section>
          <div style={{
            fontSize: 'clamp(0.625rem, 0.5rem + 0.2vw, 0.75rem)',
            fontWeight: 500,
            color: '#999',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.75rem',
          }}>
            {t('disclaimer')}
          </div>

          <div style={{
            fontSize: F.small,
            lineHeight: 1.6,
            color: '#666',
            padding: '1rem 1.25rem',
            backgroundColor: '#fff',
            borderRadius: '8px',
            border: '1px solid #e5e5e5',
          }}>
            {t('disclaimer_text')}
          </div>
        </section>
      </div>

      {/* Confirmation Dialog */}
      {confirmDialog && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setConfirmDialog(null)}
        >
          <div
            style={{
              backgroundColor: '#fff',
              borderRadius: '12px',
              padding: '1.5rem',
              maxWidth: '400px',
              width: '90%',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{
              fontSize: '1.125rem',
              fontWeight: 600,
              marginBottom: '0.75rem',
              color: '#000',
            }}>
              {confirmDialog.type === 'add'
                ? (lang === 'zh' ? '添加自选股' : 'Add to Watchlist')
                : (lang === 'zh' ? '移除自选股' : 'Remove from Watchlist')
              }
            </div>
            <div style={{
              fontSize: '0.9375rem',
              color: '#666',
              marginBottom: '1.25rem',
              lineHeight: 1.5,
            }}>
              {confirmDialog.type === 'add'
                ? (lang === 'zh'
                    ? <>确定添加 <strong>{confirmDialog.ticker}</strong>{confirmDialog.name ? ` (${confirmDialog.name})` : ''} 到自选股？添加后将开启实时数据推送。</>
                    : <>Add <strong>{confirmDialog.ticker}</strong>{confirmDialog.name ? ` (${confirmDialog.name})` : ''} to watchlist? This will enable real-time data streaming.</>
                  )
                : (lang === 'zh'
                    ? <>确定将 <strong>{confirmDialog.ticker}</strong> 从自选股中移除？移除后将停止实时数据推送。</>
                    : <>Remove <strong>{confirmDialog.ticker}</strong> from watchlist? Real-time data streaming will stop.</>
                  )
              }
            </div>
            <div style={{
              display: 'flex',
              gap: '0.75rem',
              justifyContent: 'flex-end',
            }}>
              <button
                onClick={() => setConfirmDialog(null)}
                style={{
                  padding: '0.625rem 1.25rem',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  backgroundColor: '#f5f5f5',
                  color: '#666',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                }}
              >
                {lang === 'zh' ? '取消' : 'Cancel'}
              </button>
              <button
                onClick={handleConfirm}
                style={{
                  padding: '0.625rem 1.25rem',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  backgroundColor: confirmDialog.type === 'remove' ? '#dc2626' : '#000',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                }}
              >
                {confirmDialog.type === 'add'
                  ? (lang === 'zh' ? '确认添加' : 'Add')
                  : (lang === 'zh' ? '确认移除' : 'Remove')
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
}
