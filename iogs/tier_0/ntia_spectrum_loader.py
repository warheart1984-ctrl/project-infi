"""NTIA-style spectrum loader (frequency Hz, power spectral density)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, Union

import numpy as np

SpectrumLike = Union["NTIASpectrum", Mapping[str, Any], Sequence[Any], tuple]


@dataclass(frozen=True, slots=True)
class FreqPowerSpectrum:
    frequency_hz: np.ndarray
    power: np.ndarray


@dataclass
class NTIASpectrum:
    frequency_hz: np.ndarray
    power: np.ndarray
    units: str = "dBm/Hz"
    title: str = ""
    source_path: str = ""
    timestamp_utc: str | None = None


def to_ntia_spectrum(spec: SpectrumLike) -> NTIASpectrum:
    if isinstance(spec, NTIASpectrum):
        return spec
    if isinstance(spec, Mapping):
        freq = np.asarray(spec.get("frequency_hz") or spec.get("frequency"), dtype=np.float64)
        power = np.asarray(spec.get("power") or spec.get("flux"), dtype=np.float64)
        return NTIASpectrum(
            frequency_hz=freq,
            power=power,
            units=str(spec.get("units", "dBm/Hz")),
            title=str(spec.get("title", "")),
            source_path=str(spec.get("source_path", "")),
            timestamp_utc=spec.get("timestamp_utc"),
        )
    if isinstance(spec, (tuple, list)) and len(spec) >= 2:
        return NTIASpectrum(
            frequency_hz=np.asarray(spec[0], dtype=np.float64),
            power=np.asarray(spec[1], dtype=np.float64),
        )
    raise TypeError(f"Unsupported spectrum type: {type(spec)!r}")


def load_spectrum_file(path: Union[str, Path]) -> NTIASpectrum:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        data = np.genfromtxt(path, delimiter=",", names=True)
        names = data.dtype.names or ()
        freq_col = next((n for n in names if "freq" in n.lower()), names[0])
        pow_col = next((n for n in names if "power" in n.lower() or "dbm" in n.lower()), names[-1])
        return NTIASpectrum(
            frequency_hz=np.asarray(data[freq_col], dtype=np.float64),
            power=np.asarray(data[pow_col], dtype=np.float64),
            source_path=str(path),
        )
    raise ValueError(f"Unsupported spectrum file: {path}")
