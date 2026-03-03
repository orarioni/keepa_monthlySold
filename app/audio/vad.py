from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import webrtcvad


@dataclass
class VadConfig:
    aggressiveness: int = 2
    frame_ms: int = 30
    min_speech_ratio: float = 0.25


class VadGate:
    def __init__(self, config: VadConfig, sample_rate: int = 16000):
        self.config = config
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(config.aggressiveness)

    def has_speech(self, audio: np.ndarray) -> bool:
        if audio.size == 0:
            return False

        frame_samples = int(self.sample_rate * self.config.frame_ms / 1000)
        if frame_samples <= 0:
            return True

        data = np.clip(audio, -1.0, 1.0)
        pcm16 = (data * 32767.0).astype(np.int16)

        total = 0
        speech = 0
        for i in range(0, len(pcm16) - frame_samples + 1, frame_samples):
            frame = pcm16[i : i + frame_samples]
            total += 1
            if self.vad.is_speech(frame.tobytes(), self.sample_rate):
                speech += 1

        if total == 0:
            return False
        return (speech / total) >= self.config.min_speech_ratio
