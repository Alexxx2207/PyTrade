import type { CandlestickData, UTCTimestamp } from "lightweight-charts";
import type { Tick } from "../services/instruments-service";

export function ticksToMinuteCandles(
  ticks: Tick[]
): CandlestickData[] {
  if (ticks.length === 0) return [];

  const sorted = [...ticks].sort((a, b) => a.timestamp - b.timestamp);

  const timeframeSeconds = 60;
  const buckets = new Map<number, CandlestickData>();

  for (const tick of sorted) {
    const bucketStartSec =
      Math.floor(tick.timestamp / timeframeSeconds) * timeframeSeconds;

    const existing = buckets.get(bucketStartSec);

    if (!existing) {
      buckets.set(bucketStartSec, {
        time: bucketStartSec as UTCTimestamp,
        open: tick.price,
        high: tick.price,
        low: tick.price,
        close: tick.price,
      });
    } else {
      existing.high = Math.max(existing.high, tick.price);
      existing.low = Math.min(existing.low, tick.price);
      existing.close = tick.price;
    }
  }

  return Array.from(buckets.entries())
    .sort(([a], [b]) => a - b)
    .map(([, candle]) => candle);
}