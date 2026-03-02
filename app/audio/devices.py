from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sounddevice as sd


@dataclass
class DeviceInfo:
    index: int
    name: str
    hostapi: str
    max_input_channels: int
    max_output_channels: int
    default_samplerate: float


def _hostapi_name(hostapi_index: int) -> str:
    hostapis = sd.query_hostapis()
    if isinstance(hostapis, dict):
        hostapis = [hostapis]
    try:
        return str(hostapis[hostapi_index]["name"])
    except Exception:
        return f"hostapi:{hostapi_index}"


def list_devices(hostapi_filter: Optional[str] = None) -> List[DeviceInfo]:
    devices = sd.query_devices()
    if isinstance(devices, dict):
        devices = [devices]

    out: List[DeviceInfo] = []
    for idx, d in enumerate(devices):
        hostapi = _hostapi_name(int(d["hostapi"]))
        if hostapi_filter and hostapi_filter.lower() not in hostapi.lower():
            continue
        out.append(
            DeviceInfo(
                index=idx,
                name=str(d["name"]),
                hostapi=hostapi,
                max_input_channels=int(d["max_input_channels"]),
                max_output_channels=int(d["max_output_channels"]),
                default_samplerate=float(d["default_samplerate"]),
            )
        )
    return out


def format_devices(hostapi_filter: Optional[str] = None) -> str:
    rows = list_devices(hostapi_filter=hostapi_filter)
    if not rows:
        return "No devices found."

    lines = [
        "idx | hostapi | in/out | default_sr | name",
        "----+---------+--------+------------+-----",
    ]
    for d in rows:
        lines.append(
            f"{d.index:>3} | {d.hostapi:<20.20} | {d.max_input_channels}/{d.max_output_channels:<2}"
            f" | {d.default_samplerate:>10.1f} | {d.name}"
        )
    return "\n".join(lines)
