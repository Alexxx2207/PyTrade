from __future__ import annotations

import math
import statistics
from multiprocessing import Pool, cpu_count
from typing import List, Tuple


def logspace_intervals(min_w: int, max_w: int, count: int) -> List[int]:
    min_w = max(2, int(min_w))
    max_w = max(min_w + 1, int(max_w))

    if count <= 1:
        return [min_w]

    a = math.log10(min_w)
    b = math.log10(max_w)

    vals = set()
    for i in range(count):
        t = i / (count - 1)
        w = int(round(10 ** (a + (b - a) * t)))
        if w >= 2:
            vals.add(w)

    return sorted(vals)


def linreg_slope(xs: List[float], ys: List[float]) -> float:
    n = len(xs)
    if n < 2:
        raise ValueError("Need at least 2 points for regression")

    mx = sum(xs) / n
    my = sum(ys) / n

    num = 0.0
    den = 0.0
    for x, y in zip(xs, ys):
        dx = x - mx
        num += dx * (y - my)
        den += dx * dx

    if den == 0.0:
        raise ValueError("Degenerate regression (variance of x is zero)")

    return num / den


def rs_mean_for_window(args: Tuple[List[float], int]) -> Tuple[int, float]:
    series, window = args
    n = len(series)

    if window >= n:
        return window, math.nan

    rs_vals: List[float] = []

    for start in range(0, n - window + 1, window):
        chunk = series[start:start + window]
        if len(chunk) < 2:
            continue

        m = sum(chunk) / window

        cum = 0.0
        cum_min = 0.0
        cum_max = 0.0
        for v in chunk:
            cum += (v - m)
            if cum < cum_min:
                cum_min = cum
            if cum > cum_max:
                cum_max = cum
        R = cum_max - cum_min

        try:
            S = statistics.stdev(chunk)
        except statistics.StatisticsError:
            continue

        if S > 0.0 and math.isfinite(R) and math.isfinite(S):
            rs_vals.append(R / S)

    if not rs_vals:
        return window, math.nan

    return window, sum(rs_vals) / len(rs_vals)


def hurst_exponent_minutes_rs_multiprocessed(
    minute_series: List[float],
    *,
    min_points: int = 500,
    min_window: int = 10,
    max_window: int | None = None,
    num_windows: int = 20,
    num_workers: int | None = None,
) -> float:
    data = [minute_series[i] - minute_series[i-1] for i in range(1, len(minute_series))]
    n = len(data)

    if n < min_points:
        raise ValueError(f"Not enough minute points: {n} < {min_points}")

    if max_window is None:
        max_window = max(min_window + 1, n // 2)

    windows = logspace_intervals(min_window, max_window, num_windows)
    if len(windows) < 5:
        raise ValueError("Not enough distinct window sizes; adjust min/max/num_windows.")

    workers = num_workers or max(1, cpu_count() - 1)

    with Pool(processes=workers) as pool:
        results = pool.map(rs_mean_for_window, [(data, w) for w in windows])

    xs: List[float] = []
    ys: List[float] = []

    for w, rs in results:
        if rs > 0.0 and math.isfinite(rs):
            xs.append(math.log(w))
            ys.append(math.log(rs)) 

    if len(xs) < 5:
        raise ValueError("Insufficient valid (window, R/S) points; try more data or different windows.")

    return linreg_slope(xs, ys)
