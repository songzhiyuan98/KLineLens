/**
 * K 线图表组件
 *
 * 使用 lightweight-charts 渲染 K 线图，并叠加支撑/阻力区域和成交量。
 */

import { useEffect, useRef, useState, useMemo } from 'react';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  LineData,
  Time,
} from 'lightweight-charts';
import { Bar, Zone } from '../lib/api';

interface CandlestickChartProps {
  bars: Bar[];
  supportZones?: Zone[];
  resistanceZones?: Zone[];
  height?: number;
  darkMode?: boolean;
  showVolume?: boolean;
  volumeMaPeriod?: number;
  highlightedBarTime?: string | null;
  onClearHighlight?: () => void;
}

// 计算 Volume MA
function calculateVolumeMA(bars: Bar[], period: number): number[] {
  const result: number[] = [];
  for (let i = 0; i < bars.length; i++) {
    if (i < period - 1) {
      result.push(0);
    } else {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += bars[i - j].v;
      }
      result.push(sum / period);
    }
  }
  return result;
}

// 计算当前 Volume Ratio
export function calculateVolumeRatio(bars: Bar[], period: number = 30): number {
  if (bars.length < period + 1) return 1;
  const currentVolume = bars[bars.length - 1].v;
  let sum = 0;
  for (let i = bars.length - period - 1; i < bars.length - 1; i++) {
    sum += bars[i].v;
  }
  const avgVolume = sum / period;
  return avgVolume > 0 ? currentVolume / avgVolume : 1;
}

export default function CandlestickChart({
  bars,
  supportZones = [],
  resistanceZones = [],
  height = 400,
  darkMode = false,
  showVolume = true,
  volumeMaPeriod = 30,
  highlightedBarTime = null,
  onClearHighlight,
}: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const volumeMaSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const [chartReady, setChartReady] = useState(false);

  // 计算 volume MA
  const volumeMA = useMemo(() => calculateVolumeMA(bars, volumeMaPeriod), [bars, volumeMaPeriod]);

  // 颜色配置
  const colors = darkMode
    ? {
        background: '#0a0a0a',
        text: '#666666',
        gridLines: 'rgba(255,255,255,0.05)',
        border: 'transparent',
        up: '#26a69a',
        down: '#ef5350',
        upAlpha: '#26a69a80',
        downAlpha: '#ef535080',
        supportZone: '#26a69a40',
        resistanceZone: '#ef535040',
        volumeMa: '#ffa726',
      }
    : {
        background: '#ffffff',
        text: '#999999',
        gridLines: 'rgba(0,0,0,0.03)',
        border: 'transparent',
        up: '#26a69a',
        down: '#ef5350',
        upAlpha: '#26a69a60',
        downAlpha: '#ef535060',
        supportZone: '#26a69a30',
        resistanceZone: '#ef535030',
        volumeMa: '#ff9800',
      };

  // 初始化图表
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { color: colors.background },
        textColor: colors.text,
      },
      grid: {
        vertLines: { color: colors.gridLines },
        horzLines: { color: colors.gridLines },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: colors.border,
      },
      timeScale: {
        borderColor: colors.border,
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // K 线系列
    const candleSeries = chart.addCandlestickSeries({
      upColor: colors.up,
      downColor: colors.down,
      borderUpColor: colors.up,
      borderDownColor: colors.down,
      wickUpColor: colors.up,
      wickDownColor: colors.down,
      priceScaleId: 'right',
    });

    // 设置 K 线区域占比
    candleSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.05,
        bottom: showVolume ? 0.25 : 0.05,
      },
    });

    // 成交量系列
    const volumeSeries = chart.addHistogramSeries({
      color: colors.up,
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // Volume MA 线
    const volumeMaSeries = chart.addLineSeries({
      color: colors.volumeMa,
      lineWidth: 1,
      priceScaleId: 'volume',
      crosshairMarkerVisible: false,
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    volumeMaSeriesRef.current = volumeMaSeries;
    setChartReady(true);

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height, darkMode, showVolume]);

  // 更新数据
  useEffect(() => {
    if (!chartReady || !candleSeriesRef.current || !volumeSeriesRef.current || !volumeMaSeriesRef.current) return;

    // K 线数据
    const candleData: CandlestickData[] = bars.map((bar) => ({
      time: (new Date(bar.t).getTime() / 1000) as Time,
      open: bar.o,
      high: bar.h,
      low: bar.l,
      close: bar.c,
    }));

    // 成交量数据
    const volumeData: HistogramData[] = bars.map((bar) => ({
      time: (new Date(bar.t).getTime() / 1000) as Time,
      value: bar.v,
      color: bar.c >= bar.o ? colors.upAlpha : colors.downAlpha,
    }));

    // Volume MA 数据
    const volumeMaData: LineData[] = bars.map((bar, i) => ({
      time: (new Date(bar.t).getTime() / 1000) as Time,
      value: volumeMA[i],
    })).filter(d => d.value > 0);

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);
    volumeMaSeriesRef.current.setData(volumeMaData);

    chartRef.current?.timeScale().fitContent();
  }, [bars, chartReady, volumeMA]);

  // 绘制区域
  useEffect(() => {
    if (!chartReady || !candleSeriesRef.current) return;

    const series = candleSeriesRef.current;

    // 支撑区域
    supportZones.forEach((zone) => {
      series.createPriceLine({
        price: zone.low,
        color: colors.supportZone,
        lineWidth: 2,
        lineStyle: 2,
        axisLabelVisible: false,
      });
      series.createPriceLine({
        price: zone.high,
        color: colors.supportZone,
        lineWidth: 2,
        lineStyle: 2,
        axisLabelVisible: false,
      });
    });

    // 阻力区域
    resistanceZones.forEach((zone) => {
      series.createPriceLine({
        price: zone.low,
        color: colors.resistanceZone,
        lineWidth: 2,
        lineStyle: 2,
        axisLabelVisible: false,
      });
      series.createPriceLine({
        price: zone.high,
        color: colors.resistanceZone,
        lineWidth: 2,
        lineStyle: 2,
        axisLabelVisible: false,
      });
    });
  }, [supportZones, resistanceZones, chartReady, darkMode]);

  // 高亮特定 bar (Evidence 定位)
  useEffect(() => {
    if (!chartReady || !candleSeriesRef.current || !chartRef.current) return;

    const series = candleSeriesRef.current;

    if (highlightedBarTime) {
      const targetTime = new Date(highlightedBarTime).getTime() / 1000;
      const targetBar = bars.find(bar => {
        const barTime = new Date(bar.t).getTime() / 1000;
        return Math.abs(barTime - targetTime) < 60; // 1 minute tolerance
      });

      if (targetBar) {
        // 设置 marker
        series.setMarkers([
          {
            time: (new Date(targetBar.t).getTime() / 1000) as Time,
            position: 'aboveBar',
            color: '#ffa726',
            shape: 'arrowDown',
            text: '●',
          },
        ]);

        // 滚动到该位置
        chartRef.current.timeScale().scrollToPosition(-bars.indexOf(targetBar) + bars.length - 5, false);
      }
    } else {
      // 清除 marker
      series.setMarkers([]);
    }
  }, [highlightedBarTime, bars, chartReady]);

  // 点击图表空白处清除高亮
  useEffect(() => {
    if (!chartRef.current || !onClearHighlight) return;

    const chart = chartRef.current;
    const handleClick = () => {
      if (highlightedBarTime) {
        onClearHighlight();
      }
    };

    chart.subscribeClick(handleClick);
    return () => {
      chart.unsubscribeClick(handleClick);
    };
  }, [highlightedBarTime, onClearHighlight]);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height,
        backgroundColor: colors.background,
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    />
  );
}
