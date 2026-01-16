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
  IPriceLine,
  CandlestickData,
  HistogramData,
  LineData,
  Time,
} from 'lightweight-charts';
import { Bar, Zone, EHLevels } from '../lib/api';

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
  currentPrice?: number;  // For calculating R1/R2/S1/S2
  timeframe?: string;  // For smart default visible range
  ehLevels?: EHLevels | null;  // Extended Hours levels (YC/PMH/PML/AHH/AHL)
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
  currentPrice,
  timeframe = '5m',
  ehLevels = null,
}: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const volumeMaSeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);
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
        supportZone: 'rgba(38, 166, 154, 0.2)',
        supportZoneLine: 'rgba(38, 166, 154, 0.4)',
        resistanceZone: 'rgba(239, 83, 80, 0.2)',
        resistanceZoneLine: 'rgba(239, 83, 80, 0.4)',
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
        // More subtle zone colors - less saturated
        supportZone: 'rgba(38, 166, 154, 0.15)',
        supportZoneLine: 'rgba(38, 166, 154, 0.35)',
        resistanceZone: 'rgba(239, 83, 80, 0.15)',
        resistanceZoneLine: 'rgba(239, 83, 80, 0.35)',
        volumeMa: '#ff9800',
      };

  // 初始化图表
  useEffect(() => {
    if (!containerRef.current) return;

    // 获取本地时区偏移（分钟）
    const timezoneOffset = new Date().getTimezoneOffset();

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
      localization: {
        locale: 'en-US',
        // 自定义时间格式化，显示本地时间
        timeFormatter: (time: number) => {
          const date = new Date(time * 1000);
          const hours = date.getHours().toString().padStart(2, '0');
          const minutes = date.getMinutes().toString().padStart(2, '0');
          return `${hours}:${minutes}`;
        },
        // 使用英文日期格式
        dateFormat: 'MMM dd',
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

    // 将 UTC 时间转换为本地时间戳（lightweight-charts 需要）
    // 通过添加时区偏移来显示本地时间
    const toLocalTimestamp = (isoString: string): Time => {
      const date = new Date(isoString);
      // 获取时区偏移（分钟），转换为秒
      const offsetSeconds = date.getTimezoneOffset() * 60;
      // 返回调整后的时间戳（让图表显示本地时间）
      return (date.getTime() / 1000 - offsetSeconds) as Time;
    };

    // K 线数据
    const candleData: CandlestickData[] = bars.map((bar) => ({
      time: toLocalTimestamp(bar.t),
      open: bar.o,
      high: bar.h,
      low: bar.l,
      close: bar.c,
    }));

    // 成交量数据
    const volumeData: HistogramData[] = bars.map((bar) => ({
      time: toLocalTimestamp(bar.t),
      value: bar.v,
      color: bar.c >= bar.o ? colors.upAlpha : colors.downAlpha,
    }));

    // Volume MA 数据
    const volumeMaData: LineData[] = bars.map((bar, i) => ({
      time: toLocalTimestamp(bar.t),
      value: volumeMA[i],
    })).filter(d => d.value > 0);

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);
    volumeMaSeriesRef.current.setData(volumeMaData);

    // Smart default visible range based on timeframe
    // 1m: ~120 bars (2 hours) - execution level
    // 5m: ~78 bars (1 trading day) - structure level
    // 1d: ~20 bars (1 month) - trend level
    const defaultVisibleBars: Record<string, number> = {
      '1m': 120,
      '5m': 78,
      '1d': 20,
    };
    const visibleBars = defaultVisibleBars[timeframe] || 78;
    const totalBars = bars.length;

    if (totalBars > 0 && chartRef.current) {
      // Show the most recent N bars with some padding on the right
      const from = Math.max(0, totalBars - visibleBars);
      const to = totalBars + 5; // Add padding for right margin
      chartRef.current.timeScale().setVisibleLogicalRange({ from, to });
    }
  }, [bars, chartReady, volumeMA, timeframe]);

  // 绘制区域 - 交易模式：只显示 R1/R2/S1/S2（最多4条线）
  useEffect(() => {
    if (!chartReady || !candleSeriesRef.current) return;

    const series = candleSeriesRef.current;

    // 清除旧的价格线
    priceLinesRef.current.forEach(line => {
      series.removePriceLine(line);
    });
    priceLinesRef.current = [];

    const price = currentPrice || (bars.length > 0 ? bars[bars.length - 1].c : 0);

    // 按距离当前价排序，找到 R1/R2（上方最近两个）和 S1/S2（下方最近两个）
    const resistanceByDistance = [...resistanceZones]
      .filter(z => (z.low + z.high) / 2 > price)
      .sort((a, b) => ((a.low + a.high) / 2) - ((b.low + b.high) / 2));

    const supportByDistance = [...supportZones]
      .filter(z => (z.low + z.high) / 2 < price)
      .sort((a, b) => ((b.low + b.high) / 2) - ((a.low + a.high) / 2));

    const r1 = resistanceByDistance[0];
    const r2 = resistanceByDistance[1];
    const s1 = supportByDistance[0];
    const s2 = supportByDistance[1];

    // R1: 最近阻力（实线，加粗）
    if (r1) {
      const line = series.createPriceLine({
        price: (r1.low + r1.high) / 2,
        color: colors.resistanceZoneLine,
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'R1',
      });
      priceLinesRef.current.push(line);
    }

    // R2: 次近阻力（虚线）
    if (r2) {
      const line = series.createPriceLine({
        price: (r2.low + r2.high) / 2,
        color: 'rgba(239, 83, 80, 0.4)',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'R2',
      });
      priceLinesRef.current.push(line);
    }

    // S1: 最近支撑（实线，加粗）
    if (s1) {
      const line = series.createPriceLine({
        price: (s1.low + s1.high) / 2,
        color: colors.supportZoneLine,
        lineWidth: 2,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'S1',
      });
      priceLinesRef.current.push(line);
    }

    // S2: 次近支撑（虚线）
    if (s2) {
      const line = series.createPriceLine({
        price: (s2.low + s2.high) / 2,
        color: 'rgba(38, 166, 154, 0.4)',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'S2',
      });
      priceLinesRef.current.push(line);
    }

    // ====== Extended Hours Levels ======
    // 使用独特的颜色和样式区分 EH levels
    const ehColors = {
      yc: '#f59e0b',      // 昨收 - 橙色（磁吸位）
      pmh: '#8b5cf6',     // 盘前高 - 紫色
      pml: '#8b5cf6',     // 盘前低 - 紫色
      ahh: '#6366f1',     // 盘后高 - 靛蓝
      ahl: '#6366f1',     // 盘后低 - 靛蓝
    };

    if (ehLevels) {
      // YC (昨收) - 最重要的磁吸位
      if (ehLevels.yc) {
        const line = series.createPriceLine({
          price: ehLevels.yc,
          color: ehColors.yc,
          lineWidth: 2,
          lineStyle: 0,  // 实线
          axisLabelVisible: true,
          title: 'YC',
        });
        priceLinesRef.current.push(line);
      }

      // PMH (盘前高)
      if (ehLevels.pmh) {
        const line = series.createPriceLine({
          price: ehLevels.pmh,
          color: ehColors.pmh,
          lineWidth: 1,
          lineStyle: 2,  // 虚线
          axisLabelVisible: true,
          title: 'PMH',
        });
        priceLinesRef.current.push(line);
      }

      // PML (盘前低)
      if (ehLevels.pml) {
        const line = series.createPriceLine({
          price: ehLevels.pml,
          color: ehColors.pml,
          lineWidth: 1,
          lineStyle: 2,  // 虚线
          axisLabelVisible: true,
          title: 'PML',
        });
        priceLinesRef.current.push(line);
      }

      // AHH (盘后高) - 点线
      if (ehLevels.ahh) {
        const line = series.createPriceLine({
          price: ehLevels.ahh,
          color: ehColors.ahh,
          lineWidth: 1,
          lineStyle: 3,  // 点线
          axisLabelVisible: false,  // 不显示标签避免拥挤
          title: '',
        });
        priceLinesRef.current.push(line);
      }

      // AHL (盘后低) - 点线
      if (ehLevels.ahl) {
        const line = series.createPriceLine({
          price: ehLevels.ahl,
          color: ehColors.ahl,
          lineWidth: 1,
          lineStyle: 3,  // 点线
          axisLabelVisible: false,
          title: '',
        });
        priceLinesRef.current.push(line);
      }
    }
  }, [supportZones, resistanceZones, chartReady, darkMode, currentPrice, bars, ehLevels]);

  // 高亮特定 bar (Evidence 定位)
  useEffect(() => {
    if (!chartReady || !candleSeriesRef.current || !chartRef.current) return;

    const series = candleSeriesRef.current;

    // 本地时间戳转换函数
    const toLocalTimestamp = (isoString: string): Time => {
      const date = new Date(isoString);
      const offsetSeconds = date.getTimezoneOffset() * 60;
      return (date.getTime() / 1000 - offsetSeconds) as Time;
    };

    if (highlightedBarTime) {
      const targetTime = new Date(highlightedBarTime).getTime() / 1000;
      const targetBar = bars.find(bar => {
        const barTime = new Date(bar.t).getTime() / 1000;
        return Math.abs(barTime - targetTime) < 60; // 1 minute tolerance
      });

      if (targetBar) {
        // 设置 marker（使用本地时间戳）
        series.setMarkers([
          {
            time: toLocalTimestamp(targetBar.t),
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
