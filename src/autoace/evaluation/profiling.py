"""Resource measurements for candidate pipelines."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

import psutil

T = TypeVar("T")


@dataclass(frozen=True)
class Measurement:
    elapsed_seconds: float
    peak_rss_mb: float
    value: object


def measure[T](callable_: Callable[[], T]) -> Measurement:
    process = psutil.Process(os.getpid())
    before = process.memory_info().rss
    started = time.perf_counter()
    value = callable_()
    elapsed = time.perf_counter() - started
    peak = max(before, process.memory_info().rss) / (1024 * 1024)
    return Measurement(elapsed_seconds=elapsed, peak_rss_mb=peak, value=value)
