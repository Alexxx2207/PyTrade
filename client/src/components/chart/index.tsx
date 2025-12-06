import { useEffect, useRef, useState } from "react";
import { instrumentService } from "../../services/instruments-service";
import { CandlestickSeries, ColorType, createChart } from "lightweight-charts";
import { ticksToMinuteCandles } from "../../utils/converters";
import { useAsyncAction } from "../../hooks/useAsyncAction";

interface ChartProps {
  instrument: string,
  height?: number,
}

export function Chart({ instrument, height=500 } : ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const [ticks, setTicks] = useState(100)

  const { data: rawTicks, trigger } = useAsyncAction(() => instrumentService.getData(instrument, ticks))

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
    <div>
      <input value={ticks} onChange={(e) => {setTicks(Number(e.target.value))}} />
      <button onClick={() => trigger()}>Reload</button>
      <div ref={chartContainerRef} />
    </div>
  );
}