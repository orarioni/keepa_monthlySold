from __future__ import annotations

from typing import Iterable, List, Tuple


def parse_transcript_lines(lines: Iterable[str]) -> List[Tuple[float, float, str]]:
    items = []
    for line in lines:
        line = line.strip()
        if not line or not line.startswith("["):
            continue
        try:
            ts, text = line.split("]", 1)
            ts = ts[1:]
            start_s, end_s = ts.split("-")
            items.append((float(start_s), float(end_s), text.strip()))
        except Exception:
            continue
    return items


def assign_speakers(
    transcript: List[Tuple[float, float, str]],
    speaker_turns: List[Tuple[float, float, str]],
) -> List[str]:
    out = []
    for s, e, txt in transcript:
        mid = (s + e) / 2
        speaker = "SPK?"
        for ts, te, spk in speaker_turns:
            if ts <= mid <= te:
                speaker = spk
                break
        out.append(f"[{s:8.2f}-{e:8.2f}] {speaker}: {txt}")
    return out
