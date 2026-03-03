from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from faster_whisper import WhisperModel


@dataclass
class SegmentText:
    start: float
    end: float
    text: str


class Whisperer:
    def __init__(self, model_name: str, compute_type: str, device: str):
        self.model = WhisperModel(model_name, compute_type=compute_type, device=device)

    def transcribe(
        self,
        audio: np.ndarray,
        language: str = "ja",
        beam_size: int = 1,
    ) -> List[SegmentText]:
        lang = None if language == "auto" else language
        segments, _ = self.model.transcribe(
            audio,
            language=lang,
            beam_size=beam_size,
            vad_filter=False,
            word_timestamps=False,
        )
        out: List[SegmentText] = []
        for s in segments:
            txt = s.text.strip()
            if txt:
                out.append(SegmentText(start=float(s.start), end=float(s.end), text=txt))
        return out


def choose_compute_type(arg_compute: str) -> Tuple[str, str]:
    if arg_compute != "auto":
        return "cuda" if arg_compute == "float16" else "cpu", arg_compute

    try:
        import torch

        if torch.cuda.is_available():
            return "cuda", "float16"
    except Exception:
        pass

    return "cpu", "int8"
