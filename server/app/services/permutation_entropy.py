from __future__ import annotations

import math
import itertools
from multiprocessing import Pool, cpu_count
from typing import Iterable, List, Tuple, Optional, Dict


def count_patterns_for_slice(args: Tuple[List[float], int, int, int, Dict[Tuple[int, ...], int]]) -> List[int]:
    segment, count_starts, m, tau, perm_to_id = args
    num_perms = math.factorial(m)
    counts = [0] * num_perms

    for i in range(count_starts):
        vals = [(segment[i + k * tau], k) for k in range(m)]
        vals.sort(key=lambda t: (t[0], t[1]))
        order = tuple(k for _, k in vals)
        counts[perm_to_id[order]] += 1

    return counts


def compute_entropy(counts: List[int], total: int) -> float:
    probabilities = [count / total for count in counts]
    
    H = 0.0
    for p in probabilities:
        if p > 0:
            H -= p * math.log(p)
    
    return H


def permutation_entropy_minutes_multiprocessed(
    minute_series: Iterable[float],
    *,
    m: int = 3,
    tau: int = 1,
    workers: Optional[int] = None,
    chunk_starts: Optional[int] = None,
) -> float:
    data = list(minute_series)
    n = len(data)

    if m < 2:
        raise ValueError("m must be >= 2")
    if tau < 1:
        raise ValueError("tau must be >= 1")

    tail = (m - 1) * tau
    last_start = n - tail
    if last_start <= 0:
        raise ValueError("Series too short for given m and tau")

    num_perms = math.factorial(m)
    perm_to_id = {p: i for i, p in enumerate(itertools.permutations(range(m)))}

    procs = workers or max(1, cpu_count() - 1)

    if chunk_starts is None:
        chunk_starts = last_start // (procs * 4)

    tasks: List[Tuple[List[float], int, int, int, Dict[Tuple[int, ...], int]]] = []
    s = 0
    while s < last_start:
        e = min(last_start, s + chunk_starts)
        segment = data[s : e + tail] 
        count_starts = e - s
        tasks.append((segment, count_starts, m, tau, perm_to_id))
        s = e

    with Pool(processes=procs) as pool:
        partials = pool.map(count_patterns_for_slice, tasks)

    counts = [0] * num_perms
    for part in partials:
        for i, c in enumerate(part):
            counts[i] += c

    H = compute_entropy(counts, last_start)
    Hmax = math.log(num_perms)
    Hnorm = (H / Hmax) if Hmax > 0 else 0.0
    
    return Hnorm
