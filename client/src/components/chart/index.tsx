import { useEffect, useRef, useState } from "react";
import { instrumentService, type Tick } from "../../services/instruments-service";
import { CandlestickSeries, ColorType, createChart, type ISeriesApi } from "lightweight-charts";
import { ticksToMinuteCandles } from "../../utils/converters";
import { useAsync } from "../../hooks/useAsync";
import { io } from "socket.io-client";
import { config } from "../../config";
import styles from './styles.module.css'
import { Button } from "../button";

interface ChartProps {
  instrument: string,
  height?: number,
  minutesCount: number,
  setMinutesCount: (newValue: number) => void,
}

const socket = io(config.backendAddress, { transports: ["websocket"] });

export function Chart({ instrument, height=500, minutesCount, setMinutesCount } : ChartProps) {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  const [minutes, setMinutes] = useState<Tick[]>([])

  const { reload } = useAsync(async () => setMinutes(await instrumentService.getData(instrument, minutesCount)), [instrument])

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
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    })

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#309e0eff',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#309e0eff',
      wickDownColor: '#ef5350',
    })

    const candles = ticksToMinuteCandles(minutes)

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

  const candles = ticksToMinuteCandles(minutes)
  seriesRef.current.setData(candles)

}, [minutes])

  useEffect(() => {
    socket.on("connect", () => {
      console.log("connected:", socket.id)
      socket.emit("subscribe", { symbol: "ES" })
    })

    socket.on("disconnect", (reason) => {
      console.log("disconnected:", reason)
    })

    socket.on("price", (tick) => {
      setMinutes(old => [...old, tick])
    })

    return () => {
      socket.off("connect");
      socket.off("disconnect");
      socket.off("price");
    }
  }, [])

  return (
    <div className={styles.chart}>
      <div className={styles.options}>
        <h3>Minutes lookback</h3>
        <div className={styles.minutes}>
          <input value={minutesCount} onChange={(e) => {setMinutesCount(Number(e.target.value))}} />
          <Button onClick={() => reload()}>Reload</Button>
        </div>
      </div>
      <div ref={chartContainerRef} />
    </div>
  );
}