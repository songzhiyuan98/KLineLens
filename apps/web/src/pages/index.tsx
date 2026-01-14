/**
 * 首页 - 股票代码搜索页面
 *
 * KLineLens 的主入口页面。
 * 用户在此输入股票代码（如 TSLA, AAPL）开始分析。
 */

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/router';
import { Layout } from '../components';
import { useI18n } from '../lib/i18n';

export default function Home() {
  const [ticker, setTicker] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();
  const { t } = useI18n();

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError('');

    const sanitized = ticker.trim().toUpperCase();

    // 验证输入
    if (!sanitized) {
      setError(t('error_empty_ticker'));
      return;
    }

    if (!/^[A-Z0-9\-\.]+$/.test(sanitized)) {
      setError(t('error_invalid_ticker'));
      return;
    }

    router.push(`/t/${sanitized}`);
  };

  return (
    <Layout>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 'calc(100vh - 120px)',
        padding: '2rem',
      }}>
        {/* 标题 */}
        <h1 style={{
          fontSize: '3rem',
          fontWeight: 700,
          marginBottom: '0.5rem',
          background: 'linear-gradient(135deg, #26a69a, #2196f3)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          KLineLens
        </h1>

        {/* 副标题 */}
        <p style={{
          color: '#666',
          fontSize: '1.1rem',
          marginBottom: '2.5rem',
        }}>
          {t('subtitle')}
        </p>

        {/* 搜索表单 */}
        <form onSubmit={handleSubmit} style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '1rem',
          width: '100%',
          maxWidth: '400px',
        }}>
          <div style={{
            display: 'flex',
            gap: '0.5rem',
            width: '100%',
          }}>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder={t('search_placeholder')}
              style={{
                flex: 1,
                padding: '0.875rem 1rem',
                fontSize: '1rem',
                border: '2px solid #eaeaea',
                borderRadius: '8px',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => e.target.style.borderColor = '#26a69a'}
              onBlur={(e) => e.target.style.borderColor = '#eaeaea'}
            />
            <button
              type="submit"
              style={{
                padding: '0.875rem 1.5rem',
                fontSize: '1rem',
                fontWeight: 600,
                backgroundColor: '#26a69a',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2bbbad'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#26a69a'}
            >
              {t('analyze')}
            </button>
          </div>

          {/* 错误提示 */}
          {error && (
            <div style={{
              color: '#ef5350',
              fontSize: '0.875rem',
            }}>
              {error}
            </div>
          )}
        </form>

        {/* 快速访问 */}
        <div style={{
          marginTop: '3rem',
          textAlign: 'center',
        }}>
          <p style={{
            color: '#999',
            fontSize: '0.875rem',
            marginBottom: '0.75rem',
          }}>
            {t('quick_access')}
          </p>
          <div style={{
            display: 'flex',
            gap: '0.5rem',
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}>
            {['TSLA', 'AAPL', 'NVDA', 'SPY', 'QQQ'].map((tickerItem) => (
              <button
                key={tickerItem}
                onClick={() => router.push(`/t/${tickerItem}`)}
                style={{
                  padding: '0.5rem 1rem',
                  fontSize: '0.875rem',
                  backgroundColor: '#fff',
                  color: '#666',
                  border: '1px solid #eaeaea',
                  borderRadius: '20px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#f8f9fa';
                  e.currentTarget.style.borderColor = '#26a69a';
                  e.currentTarget.style.color = '#26a69a';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = '#fff';
                  e.currentTarget.style.borderColor = '#eaeaea';
                  e.currentTarget.style.color = '#666';
                }}
              >
                {tickerItem}
              </button>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
