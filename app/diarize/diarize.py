from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from app.diarize.align import assign_speakers, parse_transcript_lines


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Post diarization by pyannote")
    p.add_argument("--wav", type=Path, required=True)
    p.add_argument("--in-txt", type=Path, required=True)
    p.add_argument("--out-txt", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        print("HUGGINGFACE_TOKEN が未設定のため話者分離をスキップします。")
        print("手順:")
        print("  1) Hugging Faceで pyannote/speaker-diarization-3.1 の利用許諾を行う")
        print("  2) set HUGGINGFACE_TOKEN=hf_xxx を設定")
        print("  3) 再実行: python -m app.diarize.diarize --wav out.wav --in-txt out.txt --out-txt out_speaker.txt")
        return 0

    try:
        from pyannote.audio import Pipeline
    except Exception as e:
        print(f"pyannote.audio の読み込みに失敗: {e}")
        print("pip install pyannote.audio torch を実行してください。")
        return 1

    pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=token)
    diarization = pipe(str(args.wav))

    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append((float(turn.start), float(turn.end), str(speaker)))

    src_lines = args.in_txt.read_text(encoding="utf-8").splitlines()
    transcript = parse_transcript_lines(src_lines)
    labeled = assign_speakers(transcript, turns)

    args.out_txt.write_text("\n".join(labeled) + "\n", encoding="utf-8")
    print(f"written: {args.out_txt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
