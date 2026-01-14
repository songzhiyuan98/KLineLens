/**
 * K 线图表组件
 *
 * 使用 lightweight-charts 渲染 K 线图，并叠加支撑/阻力区域。
 */

import { useEffect, useRef, useState } from 'react';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  Time,
} from 'lightweight-charts';
import { Bar, Zone } from '../lib/api';

interface CandlestickChartProps {
  bars: Bar[];
  supportZones?: Zone[];
  resistanceZones?: Zone[];
  height?: number;
}

export default function CandlestickChart({
  bars,
  supportZones = [],
  resistanceZones = [],
  height = 400,
}: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const [chartReady, setChartReady] = useState(false);

  // 初始化图表
  useEffect(() => {
    if (!containerRef.current) return;

    // 创建图表
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#eaeaea',
      },
      timeScale: {
        borderColor: '#eaeaea',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // 创建 K 线系列
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    // 创建成交量系列
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    setChartReady(true);

    // 响应式调整
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
  }, [height]);

  // 更新数据
  useEffect(() => {
    if (!chartReady || !candleSeriesRef.current || !volumeSeriesRef.current) return;

    // 转换 K 线数据
    const candleData: CandlestickData[] = bars.map((bar) => ({
      time: (new Date(bar.t).getTime() / 1000) as Time,
      open: bar.o,
      high: bar.h,
      low: bar.l,
      close: bar.c,
    }));

    // 转换成交量数据
    const volumeData: HistogramData[] = bars.map((bar) => ({
      time: (new Date(bar.t).getTime() / 1000) as Time,
      value: bar.v,
      color: bar.c >= bar.o ? '#26a69a80' : '#ef535080',
    }));

    candleSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);

    // 自适应显示
    chartRef.current?.timeScale().fitContent();
  }, [bars, chartReady]);

  // 绘制区域（使用 price lines）
  useEffect(() => {
    if (!chartReady || !candleSeriesRef.current) return;

    // 清除之前的价格线
    const series = candleSeriesRef.current;

    // 添加支撑区域
    supportZones.forEach((zone) => {
      series.createPriceLine({
        price: zone.low,
        color: '#26a69a40',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: false,
      });
      series.createPriceLine({
        price: zone.high,
        color: '#26a69a40',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: false,
      });
    });

    // 添加阻力区域
    resistanceZones.forEach((zone) => {
      series.createPriceLine({
        price: zone.low,
        color: '#ef535040',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: false,
      });
      series.createPriceLine({
        price: zone.high,
        color: '#ef535040',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: false,
      });
    });
  }, [supportZones, resistanceZones, chartReady]);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height,
        backgroundColor: '#fff',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    />
  );
}
