/**
 * 数据获取 Hooks
 *
 * 使用 SWR 进行数据获取和缓存。
 */

import useSWR from 'swr';
import { fetchBars, fetchAnalysis, BarsResponse, AnalysisReport } from './api';

/** 刷新间隔 (60秒) */
const REFRESH_INTERVAL = 60 * 1000;

/**
 * 获取 K 线数据 Hook
 *
 * @param ticker - 股票代码
 * @param tf - 时间周期
 * @param options - SWR 选项
 */
export function useBars(
  ticker: string | undefined,
  tf: string = '1d',
  options: { refreshInterval?: number } = {}
) {
  const { data, error, isLoading, mutate } = useSWR<BarsResponse>(
    ticker ? `bars:${ticker}:${tf}` : null,
    () => fetchBars(ticker!, tf),
    {
      refreshInterval: options.refreshInterval ?? REFRESH_INTERVAL,
      revalidateOnFocus: false,
    }
  );

  return {
    bars: data?.bars,
    barCount: data?.bar_count,
    error,
    isLoading,
    refresh: mutate,
  };
}

/**
 * 获取市场分析 Hook
 *
 * @param ticker - 股票代码
 * @param tf - 时间周期
 * @param options - SWR 选项
 */
export function useAnalysis(
  ticker: string | undefined,
  tf: string = '1d',
  options: { refreshInterval?: number } = {}
) {
  const { data, error, isLoading, mutate } = useSWR<AnalysisReport>(
    ticker ? `analysis:${ticker}:${tf}` : null,
    () => fetchAnalysis(ticker!, tf),
    {
      refreshInterval: options.refreshInterval ?? REFRESH_INTERVAL,
      revalidateOnFocus: false,
    }
  );

  return {
    analysis: data,
    error,
    isLoading,
    refresh: mutate,
  };
}
