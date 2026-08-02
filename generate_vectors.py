"""Hafta 6 — VHDL testbench'i icin test vektoru ureticisi (ISKELET).

`dsp/` paketiyle FIR katsayilarini, giris sinyalini ve beklenen cikisi
uretir; hepsini Q1.15 tamsayi olarak `vectors/` altina CSV yazar.

Gorev tanimi: docs/hafta6_gorev6_vunit.md — Bolum 3.1
"""

from pathlib import Path

import numpy as np

from dsp import fir1, sine_wave  # noqa: F401  (asagida kullanilacak)

ROOT = Path(__file__).parent
VECTORS = ROOT / "vectors"

FS, FC, NUMTAPS = 50_000, 1_000, 16  # 65 tap donanimda buyuk, 16 ile basla
Q15_ONE = 2**15 - 1  # Q1.15 tam olcek: 32767


def to_q15(x: np.ndarray) -> np.ndarray:
    """Float diziyi Q1.15 (int16) formatina cevirir.

    TODO: tasma kontrolu — 1.0'a cok yakin degerler kirpilir; kirpilan
    ornek varsa sessiz kalma, uyari ver.
    """
    raise NotImplementedError


def from_q15(x: np.ndarray) -> np.ndarray:
    """Q1.15 tamsayiyi float'a geri cevirir (dogrulama icin)."""
    raise NotImplementedError


def main() -> None:
    VECTORS.mkdir(exist_ok=True)

    # TODO 1: fir1 ile katsayilari uret (FS, FC, NUMTAPS)
    # TODO 2: to_q15 ile cevir — tasma kontrolunu unutma
    # TODO 3: giris sinyali: 1 kHz + 10 kHz toplami (Hafta 2 senaryosu), yine Q1.15
    # TODO 4: beklenen cikisi hesapla. Dikkat: apply_filter float, donanim
    #         tamsayi ile calisiyor; birebir tutmazlar. Ya sabit noktali bir
    #         referans modeli yaz ya da toleransli karsilastir
    #         (tolerans tablosu: kuantizasyon hatasi, ~1 LSB mertebesi).
    # TODO 5: ucunu ayri CSV'ye yaz: coeffs.csv, input.csv, expected.csv


if __name__ == "__main__":
    main()
