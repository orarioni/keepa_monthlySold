# WASAPI Loopback リアルタイム文字起こし (Windows 11 / Python)

Windows 11 上で **WASAPI loopback** を使って PC 再生音（Zoom/Teams/YouTube など）を取得し、`faster-whisper` で日本語文字起こしするローカル実行アプリです。必要ならマイク入力にも切り替えられます。

## 推奨デフォルト値（本実装）
- `window_sec=6.0`
- `step_sec=2.0`
- `commit_delay_sec=4.0`
- `vad_aggressiveness=2`
- `vad_min_ratio=0.25`

上記は「2〜6秒程度の体感遅延」と「取りこぼし抑制」のバランスを狙った初期値です。

## 要件
- OS: Windows 11
- Python: 3.10+
- 音声入力: WASAPI loopback 対応デバイス（またはマイク）

> 可能な限りローカル完結ですが、初回は Whisper モデル等のダウンロードが発生します。

## インストール
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

## 使い方

### 1) デバイス一覧
```bash
python -m app.main --list-devices
```

### 2) ループバック文字起こし
```bash
python -m app.main --mode loopback --device 3 --model small --language ja --save-txt out.txt
```

### 3) 録音も保存
```bash
python -m app.main --mode loopback --device 3 --save-wav out.wav --save-txt out.txt
```

### 4) マイク入力で文字起こし
```bash
python -m app.main --mode mic --device 1 --save-txt mic.txt
```

### 5) 軽い自己テスト（ダミー波形）
```bash
python -m app.main --self-test
```

## 任意: 話者分離（後処理）
```bash
python -m app.diarize.diarize --wav out.wav --in-txt out.txt --out-txt out_speaker.txt
```

- `HUGGINGFACE_TOKEN` が未設定なら、話者分離はスキップして手順を表示して終了します。
- `pyannote.audio` と `torch` は重いため、必要時のみ導入してください。
- 本機能は **後処理専用**（リアルタイム話者分離は対象外）。

## ループバック時の注意
- PC 側で音が出ていないと無音になります。
- 対象アプリが別デバイス出力だと取り込めない場合があります。
- Windows のミキサー/既定デバイス/アプリ別出力先を確認してください。
- 仮想オーディオケーブル（VB-CABLE など）を使うと経路制御が安定することがあります。
- `sounddevice` で loopback が難しい環境では `pyaudiowpatch` を代替案として検討してください。

## 調整ポイント（遅延・精度）
- `--model`: `small`（速い）→ `medium`（高精度）
- `--window-sec`: 大きいほど文脈が安定、遅延増
- `--step-sec`: 小さいほど更新頻度↑、CPU負荷↑
- `--commit-delay-sec`: 小さいほど早く確定、誤確定↑
- `--vad-aggressiveness`: 0〜3（大きいほど無音扱いが強い）
- `--vad-min-ratio`: Whisper投入の閾値
- `--compute-type`: `auto`, `float16`, `int8`, `float32`
- `--language`: `ja`（推奨）または `auto`

## エラー時の対処
- `--list-devices` で番号を再確認
- WASAPIデバイスを選択（`--hostapi wasapi`）
- `--sample-rate` を 48000/44100 で切替
- オーディオドライバ更新、Windows再起動
- それでも loopback 不可なら `pyaudiowpatch` 代替を検討
