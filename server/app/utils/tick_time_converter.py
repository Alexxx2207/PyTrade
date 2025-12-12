from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Tuple


Tick = Tuple[datetime, float]


@dataclass(frozen=True)
class MinuteBar:
    minute: datetime
    open: float
    high: float
    low: float
    close: float
    tick_count: int


def minute_bars_from_ticks(
    ticks: Iterable[Tick],
    fill_missing_minutes: bool = True,
) -> List[MinuteBar]:
    """
    Convert ticks (timestamp, price) to minute bars. 
    The result is returned as a list.
    """
    cur_minute: Optional[datetime] = None
    o = h = l = c = 0.0
    tick_count = 0
    last_close: Optional[float] = None

    minute_bars: List[MinuteBar] = []

    for ts, price in ticks:
        m = ts.replace(second=0, microsecond=0)

        # Init on first tick
        if cur_minute is None:
            cur_minute = m
            o = h = l = c = price
            tick_count = 1
            last_close = c
            continue

        if m < cur_minute:
            raise ValueError(f"Ticks are not sorted: got {m} after {cur_minute}")

        # Same minute -> update
        if m == cur_minute:
            if price > h:
                h = price
            if price < l:
                l = price
            c = price
            tick_count += 1
            last_close = c
            continue

        # Minute advanced -> flush current bar
        minute_bars.append(MinuteBar(cur_minute, o, h, l, c, tick_count))

        # Fill gaps
        if fill_missing_minutes and last_close is not None:
            gap_minute = cur_minute + timedelta(minutes=1)
            while gap_minute < m:
                minute_bars.append(MinuteBar(gap_minute, last_close, last_close, last_close, last_close, 0))
                gap_minute += timedelta(minutes=1)

        # Start new bar
        cur_minute = m
        o = h = l = c = price
        tick_count = 1
        last_close = c

    # Flush last bar
    if cur_minute is not None:
        minute_bars.append(MinuteBar(cur_minute, o, h, l, c, tick_count))

    return minute_bars
