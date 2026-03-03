from __future__ import annotations


def merge_with_recent(recent_text: str, new_text: str, max_overlap: int = 40) -> str:
    a = recent_text.strip()
    b = new_text.strip()
    if not b:
        return ""
    if not a:
        return b

    max_k = min(len(a), len(b), max_overlap)
    overlap = 0
    for k in range(max_k, 0, -1):
        if a.endswith(b[:k]):
            overlap = k
            break
    return b[overlap:].strip()
