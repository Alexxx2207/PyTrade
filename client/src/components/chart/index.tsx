import { useEffect, useRef } from "react";
import { useAsync } from "../../hooks/useAsync";
import { instrumentService } from "../../services/instruments-service";
import { CandlestickSeries, ColorType, createChart } from "lightweight-charts";
import { ticksToMinuteCandles } from "../../utils/converters";

interface ChartProps {
  instrument: string,
  height?: number
}

export function Chart({ instrument, height=500 } : ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);

  const { data: rawTicks } = useAsync(() => instrumentService.getData(instrument), [])

  useEffect(() => {
    const container = chartContainerRef.current;
    if (!container || !rawTicks) return;

    const chart = createChart(container, {
      layout: {
        textColor: 'black',
        background: { type: ColorType.Solid, color: 'white' },
      },
      width: container.clientWidth,
      height: height,
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#309e0eff',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#309e0eff',
      wickDownColor: '#ef5350',
    });

    const candles = ticksToMinuteCandles(rawTicks);

    candlestickSeries.setData(candles);
    
    chart.timeScale().fitContent();

    const handleResize = () => {
      if (!chartContainerRef.current) return;
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [rawTicks]);

  return (
    <div ref={chartContainerRef} />
  );
}