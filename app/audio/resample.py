from __future__ import annotations

import numpy as np
from scipy.signal import resample_poly


def to_mono_float32(audio: np.ndarray) -> np.ndarray:
    arr = np.asarray(audio)
    if arr.ndim == 2:
        arr = arr.mean(axis=1)
    return arr.astype(np.float32, copy=False)


def resample_audio(audio: np.ndarray, src_rate: int, dst_rate: int = 16000) -> np.ndarray:
    mono = to_mono_float32(audio)
    if src_rate == dst_rate:
        return mono
    if mono.size == 0:
        return mono

    gcd = np.gcd(src_rate, dst_rate)
    up = dst_rate // gcd
    down = src_rate // gcd
    return resample_poly(mono, up, down).astype(np.float32)
