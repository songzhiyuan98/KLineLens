/**
 * 股票详情分析页面
 *
 * 显示指定股票的完整市场分析结果。
 * 路由: /t/[ticker] (如 /t/TSLA)
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import dynamic from 'next/dynamic';
import {
  Layout,
  MarketStateCard,
  BehaviorCard,
  EvidenceCard,
  TimelineCard,
  PlaybookCard,
} from '../../components';
import { useAnalysis, useBars } from '../../lib/hooks';

// 动态导入图表组件（禁用 SSR，因为 lightweight-charts 需要 window）
const CandlestickChart = dynamic(
  () => import('../../components/CandlestickChart'),
  { ssr: false }
);

type Timeframe = '1m' | '5m' | '1d';

export default function TickerDetail() {
  const router = useRouter();
  const { ticker } = router.query;
  const [timeframe, setTimeframe] = useState<Timeframe>('1d');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // 获取 K 线数据
  const { bars, error: barsError, isLoading: barsLoading } = useBars(
    ticker as string,
    timeframe,
    { refreshInterval: 60000 }
  );

  // 获取分析数据
  const { analysis, error: analysisError, isLoading: analysisLoading, refresh } = useAnalysis(
    ticker as string,
    timeframe,
    { refreshInterval: 60000 }
  );

  const isLoading = barsLoading || analysisLoading;
  const error = barsError || analysisError;

  // 更新时间戳
  useEffect(() => {
    if (analysis) {
      setLastUpdated(new Date());
    }
  }, [analysis]);

  // 时间周期切换
  const handleTimeframeChange = (tf: Timeframe) => {
    setTimeframe(tf);
  };

  // 手动刷新
  const handleRefresh = () => {
    refresh();
  };

  return (
    <Layout>
      <div style={{ padding: '1.5rem' }}>
        {/* 页面头部 */}
        <header style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.5rem',
        }}>
          {/* 左侧: 股票代码和状态 */}
          <div>
            <h1 style={{
              fontSize: '1.75rem',
              fontWeight: 700,
              margin: 0,
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
            }}>
              {ticker}
              {analysis?.market_state && (
                <span style={{
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  padding: '0.25rem 0.75rem',
                  borderRadius: '20px',
                  backgroundColor: analysis.market_state.regime === 'uptrend'
                    ? '#e8f5e9'
                    : analysis.market_state.regime === 'downtrend'
                      ? '#ffebee'
                      : '#fff3e0',
                  color: analysis.market_state.regime === 'uptrend'
                    ? '#26a69a'
                    : analysis.market_state.regime === 'downtrend'
                      ? '#ef5350'
                      : '#ff9800',
                }}>
                  {analysis.market_state.regime}
                </span>
              )}
            </h1>
            {lastUpdated && (
              <p style={{
                fontSize: '0.75rem',
                color: '#999',
                marginTop: '0.25rem',
              }}>
                Last updated: {lastUpdated.toLocaleTimeString()}
              </p>
            )}
          </div>

          {/* 右侧: 控制按钮 */}
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {/* 时间周期选择 */}
            <div style={{
              display: 'flex',
              backgroundColor: '#f0f0f0',
              borderRadius: '6px',
              padding: '2px',
            }}>
              {(['1m', '5m', '1d'] as Timeframe[]).map((tf) => (
                <button
                  key={tf}
                  onClick={() => handleTimeframeChange(tf)}
                  style={{
                    padding: '0.5rem 1rem',
                    fontSize: '0.8rem',
                    fontWeight: timeframe === tf ? 600 : 400,
                    backgroundColor: timeframe === tf ? '#fff' : 'transparent',
                    color: timeframe === tf ? '#333' : '#666',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  {tf}
                </button>
              ))}
            </div>

            {/* 刷新按钮 */}
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              style={{
                padding: '0.5rem 1rem',
                fontSize: '0.8rem',
                backgroundColor: '#fff',
                color: '#666',
                border: '1px solid #eaeaea',
                borderRadius: '6px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.5 : 1,
              }}
            >
              {isLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </header>

        {/* 错误状态 */}
        {error && (
          <div style={{
            padding: '2rem',
            backgroundColor: '#ffebee',
            borderRadius: '8px',
            textAlign: 'center',
            marginBottom: '1.5rem',
          }}>
            <div style={{ fontSize: '1rem', color: '#ef5350', fontWeight: 500 }}>
              Failed to load data
            </div>
            <div style={{ fontSize: '0.875rem', color: '#999', marginTop: '0.5rem' }}>
              {error.message}
            </div>
            <button
              onClick={handleRefresh}
              style={{
                marginTop: '1rem',
                padding: '0.5rem 1rem',
                fontSize: '0.875rem',
                backgroundColor: '#ef5350',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              Try Again
            </button>
          </div>
        )}

        {/* 加载状态 */}
        {isLoading && !analysis && (
          <div style={{
            padding: '4rem',
            textAlign: 'center',
            color: '#999',
          }}>
            <div style={{ fontSize: '1rem' }}>Loading analysis...</div>
          </div>
        )}

        {/* 主要内容 */}
        {analysis && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '2fr 1fr',
            gap: '1.5rem',
          }}>
            {/* 左侧: 图表 */}
            <div>
              <CandlestickChart
                bars={bars || []}
                supportZones={analysis.zones.support}
                resistanceZones={analysis.zones.resistance}
                height={500}
              />

              {/* 数据提示 */}
              {analysis.data_gaps && (
                <div style={{
                  marginTop: '0.75rem',
                  padding: '0.5rem 0.75rem',
                  backgroundColor: '#fff3e0',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  color: '#ff9800',
                }}>
                  Warning: Data gaps detected in this timeframe
                </div>
              )}
            </div>

            {/* 右侧: 分析面板 */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              maxHeight: 'calc(100vh - 200px)',
              overflowY: 'auto',
            }}>
              <MarketStateCard marketState={analysis.market_state} />
              <BehaviorCard behavior={analysis.behavior} />
              <EvidenceCard evidence={analysis.behavior.evidence} />
              <TimelineCard events={analysis.timeline} />
              <PlaybookCard plans={analysis.playbook} />
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
