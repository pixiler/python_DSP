"""Hafta 6 — VHDL testbench'i icin test vektoru ureticisi.

`dsp/` paketiyle FIR katsayilarini, giris sinyalini ve beklenen cikisi uretir.
CSV'ler `vectors/`, uretilen VHDL katsayi paketi `hdl/src/` altina yazilir;
boylece katsayilar tek kaynaktan gelir ve CSV ile VHDL ayrisamaz.

Sabit noktali konvansiyonlar (fir_filter.vhd ile birebir ayni olmali):
    Format     : Q1.15 giris, Q1.15 cikis, Q2.30 akumulator
    Yuvarlama  : round-half-up
    Tasma      : doygunluk (sarma degil)

Uretilen dosyalar icerik degismediyse yeniden yazilmaz; aksi halde
simulatorun zaman damgasi kontrolu gereksiz "yeniden analiz et" uyarisi verir.

Gorev tanimi: docs/hafta6_gorev6_vunit.md — Bolum 3.1
"""

import json
import warnings
from pathlib import Path

import numpy as np

from dsp import apply_filter, fir1, sine_wave, suppression_db

ROOT = Path(__file__).parent
VECTORS = ROOT / "vectors"
HDL_SRC = ROOT / "hdl" / "src"

FS = 50_000
CUTOFF_HZ = 2_000.0
NUMTAPS = 16  # fir1 cift dereceyi tek yapar -> 17 katsayi

skip_samples = 50
analysis_len = 450

PASS_TONE_HZ = 1_000.0  # gecmesi beklenen ton
STOP_TONE_HZ = 10_000.0  # bastirilmasi beklenen ton
TONE_AMPLITUDE = 0.40  # iki ton toplaninca Q1.15 tam olcegini asmasin
SIGNAL_DURATION_S = 0.1
VECTOR_DURATION_S = 10e-3

DC_VECTOR_LEN = 64  # doygunluk testi icin tam olcek DC uzunlugu

FRACTION_BITS = 15
ACC_WIDTH = 32  # fir_filter.vhd icindeki MULT_WIDTH ile ayni olmali

Q15_MIN = np.iinfo(np.int16).min  # -32768
Q15_MAX = np.iinfo(np.int16).max  # +32767


def to_q15(x: np.ndarray, allow_clipping: bool = False) -> np.ndarray:
    """Float diziyi Q1.15 (int16) formatina cevirir.

    Args:
        x: Gercek deger domeninde giris ([-1, 1) araligi beklenir).
        allow_clipping: True ise doygunluk beklenen davranistir ve uyari
            verilmez (doygunluk testi vektorleri icin).

    Returns:
        Q1.15 tamsayi dizi. Aralik disi degerler doyurulur.
    """
    q = np.round(np.asarray(x, dtype=np.float64) * 2**FRACTION_BITS)

    if not allow_clipping and np.any((q < Q15_MIN) | (q > Q15_MAX)):
        warnings.warn(
            "Q1.15 donusumunde tasma oldu, degerler doyuruldu", RuntimeWarning
        )

    return np.clip(q, Q15_MIN, Q15_MAX).astype(np.int16)


def from_q15(x: np.ndarray) -> np.ndarray:
    """Q1.15 tamsayiyi gercek deger domenine geri cevirir."""
    return x / (2**FRACTION_BITS)


def worst_case_accumulator(h_fix: np.ndarray) -> int:
    """Akumulatorde olusabilecek en buyuk mutlak deger.

    Sinir tap sayisindan degil katsayilarin mutlak toplamindan gelir:
        max|acc| <= max|x| * sum|h|
    """
    return 2**FRACTION_BITS * int(np.sum(np.abs(h_fix.astype(np.int64))))


def check_accumulator_width(h_fix: np.ndarray, acc_width: int = ACC_WIDTH) -> int:
    """Akumulator genisliginin en kotu hali tuttugunu dogrula.

    Raises:
        AssertionError: Verilen genislik yetmiyorsa.
    """
    worst = worst_case_accumulator(h_fix)
    limit = 2 ** (acc_width - 1)
    assert worst < limit, (
        f"akumulator tasar: en kotu {worst} degeri {acc_width} bite sigmiyor "
        f"(sinir {limit}). MULT_WIDTH'i buyut veya katsayilari olcekle."
    )
    return worst


def write_if_changed(path: Path, content: str) -> bool:
    """Icerik degismisse yaz; degismemisse dosyaya hic dokunma.

    Dosyayi ayni icerikle yeniden yazmak zaman damgasini ilerletir ve
    simulator "derlenmis birim kaynaktan eski" uyarisi verir. Uretecin
    idempotent olmasi bu gurultuyu tamamen ortadan kaldirir.

    Returns:
        Dosya yazildiysa True, degismedigi icin atlandiysa False.
    """
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def render_coeffs_package(h_fix: np.ndarray) -> str:
    """Q1.15 katsayilardan VHDL katsayi paketi metni uret."""
    values = ",\n".join(f"        {int(c)}" for c in h_fix)
    return f"""-- OTOMATIK URETILDI — generate_vectors.py
-- Elle duzenlemeyin; degisiklikler bir sonraki calistirmada silinir.
--
-- Fs = {FS} Hz, kesim = {CUTOFF_HZ:.0f} Hz, tap = {len(h_fix)}
-- Format Q1.{FRACTION_BITS} (olcek 2**{FRACTION_BITS}), DC kazanci = {int(np.sum(h_fix))}

library ieee;
use ieee.std_logic_1164.all;

use work.fir_pkg.all;

package fir_coeffs_pkg is

    constant FIR_NUM_TAPS : natural := {len(h_fix)};

    constant FIR_COEFFS : coef_array_type(0 to FIR_NUM_TAPS - 1) := (
{values}
    );

end package fir_coeffs_pkg;
"""


def save_vector(path: Path, data: np.ndarray) -> None:
    """Tamsayi diziyi satir basina bir deger olacak sekilde CSV'ye yaz."""
    write_if_changed(path, "\n".join(str(int(v)) for v in data) + "\n")


def main() -> None:
    VECTORS.mkdir(exist_ok=True)
    HDL_SRC.mkdir(parents=True, exist_ok=True)

    # --- Katsayilar -------------------------------------------------------
    h = fir1(NUMTAPS, CUTOFF_HZ / (FS / 2))
    h_fix = to_q15(h)
    worst_acc = check_accumulator_width(h_fix)

    # --- Iki tonlu ana vektor --------------------------------------------
    tones = sine_wave(PASS_TONE_HZ, SIGNAL_DURATION_S, FS) + sine_wave(
        STOP_TONE_HZ, SIGNAL_DURATION_S, FS
    )
    x_fix = to_q15(TONE_AMPLITUDE * tones)

    # Beklenen cikis donanimin gordugu (dekuantize) degerlerden hesaplanir;
    # boylece katsayi ve giris kuantizasyonu hata butcesinden dusuyor ve
    # karsilastirma toleranssiz (bit-birebir) yapilabiliyor.
    y_fix = to_q15(apply_filter(from_q15(x_fix), from_q15(h_fix)))

    n = int(round(VECTOR_DURATION_S * FS))

    # --- Doygunluk vektoru ------------------------------------------------
    # DC kazanci 1'in bir tik ustunde (katsayi yuvarlamasi), bu yuzden tam
    # olcek DC girisi cikista tasar ve doygunluk dalini calistirir.
    x_dc = np.full(DC_VECTOR_LEN, Q15_MAX, dtype=np.int16)
    y_dc = to_q15(
        apply_filter(from_q15(x_dc), from_q15(h_fix)), allow_clipping=True
    )

    # --- Yazma ------------------------------------------------------------
    save_vector(VECTORS / "coeffs.csv", h_fix)
    save_vector(VECTORS / "input.csv", x_fix[:n])
    save_vector(VECTORS / "expected.csv", y_fix[:n])
    save_vector(VECTORS / "input_dc.csv", x_dc)
    save_vector(VECTORS / "expected_dc.csv", y_dc)

    expected_passband_db  = suppression_db(y=from_q15(y_fix[skip_samples:analysis_len+skip_samples]), x=from_q15(x_fix[skip_samples:analysis_len+skip_samples]), fs= FS, tone_hz=PASS_TONE_HZ)
    expected_stopband_db  = suppression_db(y=from_q15(y_fix[skip_samples:analysis_len+skip_samples]), x=from_q15(x_fix[skip_samples:analysis_len+skip_samples]), fs= FS, tone_hz=STOP_TONE_HZ)

    pkg_written = write_if_changed(
        HDL_SRC / "fir_coeffs_pkg.vhd", render_coeffs_package(h_fix)
    )

    meta = {
    "fs": FS,
    "pass_tone_hz": PASS_TONE_HZ,
    "stop_tone_hz": STOP_TONE_HZ,
    "num_taps": len(h_fix),
    "group_delay": (len(h_fix) - 1) // 2,
    "skip_samples": skip_samples,          # transient + koherentlik icin
    "analysis_len": analysis_len,         # tam periyot sayisi
    "expected_passband_db": expected_passband_db,
    "expected_stopband_db": expected_stopband_db,
    }
    json_written = write_if_changed(VECTORS / "meta.json", json.dumps(meta, indent=2))

    # --- Ozet -------------------------------------------------------------
    print(f"tap sayisi         : {len(h_fix)}")
    print(f"grup gecikmesi     : {(len(h_fix) - 1) // 2} ornek")
    print(f"DC kazanci (Q1.15) : {int(np.sum(h_fix))}  (ideal {2**FRACTION_BITS})")
    print(f"en kotu akumulator : {worst_acc}  (sinir {2**(ACC_WIDTH - 1)})")
    print(f"ana vektor         : {n} ornek, cikis tepesi {int(np.max(np.abs(y_fix[:n])))}")
    print(f"dc vektoru         : {DC_VECTOR_LEN} ornek, cikis {int(y_dc[-1])} (doygunluk {Q15_MAX})")
    print(f"katsayi paketi     : {'yazildi' if pkg_written else 'degismedi, atlandi'}")
    print(f"meta paketi        : {'yazildi' if json_written else 'degismedi, atlandi'}")

if __name__ == "__main__":
    main()