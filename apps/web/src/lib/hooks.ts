/**
 * 数据获取 Hooks
 *
 * 使用 SWR 进行数据获取和缓存。
 */

import useSWR, { useSWRConfig } from 'swr';
import { useState, useCallback } from 'react';
import { fetchBars, fetchAnalysis, fetchNarrative, BarsResponse, AnalysisReport, NarrativeResponse, ReportType } from './api';

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

/**
 * 生成叙事报告 Hook v2
 *
 * 支持多种报告类型：
 * - full: 完整 5m 结构分析（gpt-4o）
 * - quick: 简短更新（gpt-4o-mini）
 * - confirmation: 1m 执行确认
 * - context: 1D 背景框架
 *
 * @param ticker - 股票代码
 * @param tf - 时间周期
 * @param lang - 输出语言
 */
export function useNarrative(
  ticker: string | undefined,
  tf: string = '5m',
  lang: 'zh' | 'en' = 'zh'
) {
  const [narrative, setNarrative] = useState<NarrativeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // 通用生成函数
  const generate = useCallback(async (reportType: ReportType) => {
    if (!ticker) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchNarrative(ticker, tf, reportType, lang);
      setNarrative(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to generate narrative'));
    } finally {
      setIsLoading(false);
    }
  }, [ticker, tf, lang]);

  // 生成完整报告（手动触发，gpt-4o）
  const generateFullReport = useCallback(() => generate('full'), [generate]);

  // 生成简短更新（快速，gpt-4o-mini）
  const generateQuickUpdate = useCallback(() => generate('quick'), [generate]);

  // 生成 1m 确认报告
  const generateConfirmation = useCallback(() => generate('confirmation'), [generate]);

  // 生成 1D 背景报告
  const generateContext = useCallback(() => generate('context'), [generate]);

  // 清除叙事
  const clear = useCallback(() => {
    setNarrative(null);
    setError(null);
  }, []);

  return {
    narrative,
    isLoading,
    error,
    generate,
    generateFullReport,
    generateQuickUpdate,
    generateConfirmation,
    generateContext,
    clear,
  };
}
