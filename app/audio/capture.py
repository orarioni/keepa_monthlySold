from __future__ import annotations

import queue
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Tuple

import numpy as np
import sounddevice as sd


@dataclass
class CaptureChunk:
    data: np.ndarray
    sample_rate: int
    timestamp: float


class AudioCapture:
    def __init__(
        self,
        device: Optional[int],
        mode: str,
        sample_rate: int = 48000,
        channels: int = 2,
        blocksize: int = 0,
    ):
        self.device = device
        self.mode = mode
        self.sample_rate = sample_rate
        self.channels = channels
        self.blocksize = blocksize
        self._queue: "queue.Queue[CaptureChunk]" = queue.Queue(maxsize=128)
        self._stop = threading.Event()
        self._stream = None

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[capture warning] {status}")
        ts = time.time()
        chunk = np.copy(indata)
        try:
            self._queue.put_nowait(CaptureChunk(chunk, self.sample_rate, ts))
        except queue.Full:
            pass

    def start(self) -> None:
        kwargs = dict(
            samplerate=self.sample_rate,
            channels=self.channels,
            device=self.device,
            dtype="float32",
            callback=self._callback,
            blocksize=self.blocksize,
        )
        if self.mode == "loopback":
            kwargs["channels"] = max(self.channels, 2)
            kwargs["extra_settings"] = sd.WasapiSettings(loopback=True)

        self._stream = sd.InputStream(**kwargs)
        self._stream.start()

    def stop(self) -> None:
        self._stop.set()
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()

    def read(self, timeout: float = 0.5) -> Optional[CaptureChunk]:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None


class SlidingWindowBuffer:
    def __init__(self, sample_rate: int, max_sec: float = 30.0):
        self.sample_rate = sample_rate
        self.max_samples = int(max_sec * sample_rate)
        self._buf: Deque[np.ndarray] = deque()
        self._len = 0

    def append(self, chunk: np.ndarray) -> None:
        if chunk.size == 0:
            return
        self._buf.append(chunk)
        self._len += len(chunk)
        while self._len > self.max_samples and self._buf:
            old = self._buf.popleft()
            self._len -= len(old)

    def get_last(self, sec: float) -> np.ndarray:
        n = int(sec * self.sample_rate)
        if n <= 0 or self._len == 0:
            return np.zeros(0, dtype=np.float32)
        arr = np.concatenate(list(self._buf), axis=0)
        return arr[-n:]


def collect_for_step(
    capture: AudioCapture,
    buffer: SlidingWindowBuffer,
    target_step_sec: float,
    resample_fn,
    dst_rate: int = 16000,
    wav_sink: Optional[List[np.ndarray]] = None,
) -> Tuple[np.ndarray, float]:
    start = time.time()
    while time.time() - start < target_step_sec:
        chunk = capture.read(timeout=0.2)
        if chunk is None:
            continue
        if wav_sink is not None:
            wav_sink.append(chunk.data.copy())
        mono16 = resample_fn(chunk.data, chunk.sample_rate, dst_rate)
        buffer.append(mono16)

    return buffer.get_last(target_step_sec), time.time()
