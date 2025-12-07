import { useEffect, useRef, useState } from "react";
import { instrumentService, type Tick } from "../../services/instruments-service";
import { CandlestickSeries, ColorType, createChart, type ISeriesApi } from "lightweight-charts";
import { ticksToMinuteCandles } from "../../utils/converters";
import { useAsync } from "../../hooks/useAsync";
import { io } from "socket.io-client";

interface ChartProps {
  instrument: string,
  height?: number,
}

const socket = io("http://localhost:5000", { transports: ["websocket"] });

export function Chart({ instrument, height=500 } : ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);


  const [ticksCount, setTicksCount] = useState(100)
  const [ticks, setTicks] = useState<Tick[]>([])

  const { reload } = useAsync(async () => setTicks(await instrumentService.getData(instrument, ticksCount)), [])

  useEffect(() => {
    const container = chartContainerRef.current
    if (!container) return

    const chart = createChart(container, {
      layout: {
        textColor: 'black',
        background: { type: ColorType.Solid, color: 'white' },
      },
      width: container.clientWidth,
      height: height,
    })

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#309e0eff',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#309e0eff',
      wickDownColor: '#ef5350',
    })

    const candles = ticksToMinuteCandles(ticks)

    candlestickSeries.setData(candles)
    seriesRef.current = candlestickSeries

    chart.timeScale().fitContent()
    
    const handleResize = () => {
      if (!chartContainerRef.current) return;
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    };
  }, [])

  useEffect(() => {
  if (!seriesRef.current) return

  const candles = ticksToMinuteCandles(ticks)
  seriesRef.current.setData(candles)

}, [ticks]);

  useEffect(() => {
    socket.on("connect", () => {
      console.log("connected:", socket.id)
      socket.emit("subscribe", { symbol: "ES" })
    })

    socket.on("disconnect", (reason) => {
      console.log("disconnected:", reason)
    })

    socket.on("price", (tick) => {
      setTicks(old => [...old, tick])
    })

    return () => {
      socket.off("connect");
      socket.off("disconnect");
      socket.off("price");
    }
  }, [])

  return (
    <div>
      <input value={ticksCount} onChange={(e) => {setTicksCount(Number(e.target.value))}} />
      <button onClick={() => reload()}>Reload</button>
      <div ref={chartContainerRef} />
    </div>
  );
}