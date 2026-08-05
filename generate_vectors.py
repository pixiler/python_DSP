"""Hafta 6 — Bonus 1: cok konfigurasyonlu test vektoru ureticisi.

Ayni testbench'i farkli tap sayilariyla kosturabilmek icin her konfigurasyona
ait katsayilari, beklenen cikisi ve olcum hedeflerini uretir.
`@pytest.mark.parametrize`'in VUnit karsiligi olan `add_config`, bu dosyanin
urettigi manifest'ten beslenir.

Tasarim notu — katsayilar neden VHDL paketinde:
    VUnit `add_config` yalnizca skaler ve string generic gecirebilir, dizi
    gecemez. `COEFFS` ise elaborasyon zamani sabiti oldugu icin dosyadan da
    okunamaz. Bu yuzden butun katsayi setleri tek bir pakete yazilir ve
    Python yalnizca `config_id` ile hangisinin secilecegini soyler.

Sabit noktali konvansiyonlar (fir_filter.vhd ile birebir ayni olmali):
    Format    : Q1.15 giris/cikis, Q2.30 akumulator
    Yuvarlama : round-half-up
    Tasma     : doygunluk
"""

import json
import warnings
from pathlib import Path

import numpy as np

from dsp import apply_filter, fir1, sine_wave, suppression_db

ROOT = Path(__file__).parent
VECTORS = ROOT / "vectors"
HDL_SRC = ROOT / "hdl" / "src"

# --- Sinyal ve olcum parametreleri ---------------------------------------
FS = 50_000
CUTOFF_HZ = 3_000.0

PASS_TONE_HZ = 1_000.0
STOP_TONE_HZ = 10_000.0
TONE_AMPLITUDE = 0.40
SIGNAL_DURATION_S = 0.1

# Olcum penceresi: en uzun filtrenin transient'ini (65 ornek) asar ve kalan
# 400 ornek her iki ton icin tam periyot sayisi verir (koherent ornekleme).
SKIP_SAMPLES = 100
ANALYSIS_LEN = 400
VECTOR_LEN = SKIP_SAMPLES + ANALYSIS_LEN

# --- Sartname -------------------------------------------------------------
MIN_STOPBAND_DB = -40.0       # 10 kHz en az bu kadar bastirilmali
MAX_PASSBAND_LOSS_DB = -1.0   # 1 kHz en fazla bu kadar kaybetmeli
REFERENCE_TOL_DB = 0.2        # donanim ile float referans arasindaki pay

# --- Sabit nokta ----------------------------------------------------------
FRACTION_BITS = 15
ACC_WIDTH = 32  # fir_filter.vhd icindeki MULT_WIDTH ile ayni olmali

Q15_MIN = np.iinfo(np.int16).min
Q15_MAX = np.iinfo(np.int16).max

# --- Konfigurasyonlar -----------------------------------------------------
CONFIG_ORDERS = [16, 32, 64]   # fir1 cift dereceyi tek yapar: 16 -> 17 katsayi
DEFAULT_CONFIG_ID = 1          # DC doygunluk testi bu konfigurasyonu kullanir

DC_VECTOR_LEN = 64


# ==========================================================================
# Sabit nokta yardimcilari
# ==========================================================================

def to_q15(x: np.ndarray, allow_clipping: bool = False) -> np.ndarray:
    """Float diziyi Q1.15 (int16) formatina cevirir, tasmada doyurur."""
    q = np.round(np.asarray(x, dtype=np.float64) * 2**FRACTION_BITS)

    if not allow_clipping and np.any((q < Q15_MIN) | (q > Q15_MAX)):
        warnings.warn("Q1.15 donusumunde tasma oldu, degerler doyuruldu", RuntimeWarning)

    return np.clip(q, Q15_MIN, Q15_MAX).astype(np.int16)


def from_q15(x: np.ndarray) -> np.ndarray:
    """Q1.15 tamsayiyi gercek deger domenine cevirir."""
    return x / (2**FRACTION_BITS)


def check_accumulator_width(h_fix: np.ndarray, label: str) -> int:
    """max|acc| <= max|x| * sum|h| sinirinin ACC_WIDTH'e sigdigini dogrula."""
    worst = 2**FRACTION_BITS * int(np.sum(np.abs(h_fix.astype(np.int64))))
    limit = 2 ** (ACC_WIDTH - 1)
    assert worst < limit, (
        f"[{label}] akumulator tasar: en kotu {worst}, {ACC_WIDTH} bit siniri "
        f"{limit}. MULT_WIDTH'i buyut veya katsayilari olcekle."
    )
    return worst


# ==========================================================================
# Dosya yazma (idempotent)
# ==========================================================================

def write_if_changed(path: Path, content: str) -> bool:
    """Icerik degismisse yaz; degismemisse dosyaya hic dokunma.

    Ayni icerikle yeniden yazmak zaman damgasini ilerletir ve simulator
    gereksiz "derlenmis birim kaynaktan eski" uyarisi verir.
    """
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def save_vector(path: Path, data: np.ndarray) -> None:
    """Tamsayi diziyi satir basina bir deger olacak sekilde yaz."""
    write_if_changed(path, "\n".join(str(int(v)) for v in data) + "\n")


# ==========================================================================
# VHDL katsayi paketi
# ==========================================================================

def render_coeffs_package(coeff_sets: list[np.ndarray]) -> str:
    """Butun katsayi setlerini tek bir VHDL paketi olarak uret.

    Setler farkli uzunlukta oldugu icin en uzuna gore sifirla doldurulur;
    gercek uzunluk FIR_TAP_COUNTS'ta tutulur ve testbench dilimi ona gore
    alir, yani dolgu sifirlari DUT'a hic ulasmaz.
    """
    max_taps = max(len(c) for c in coeff_sets)
    tap_counts = ", ".join(str(len(c)) for c in coeff_sets)

    blocks = []
    for i, coeffs in enumerate(coeff_sets):
        padded = [int(v) for v in coeffs] + [0] * (max_taps - len(coeffs))
        values = ",\n".join(f"            {v}" for v in padded)
        comma = "," if i < len(coeff_sets) - 1 else ""
        blocks.append(
            f"        -- config {i}: {len(coeffs)} tap\n"
            f"        (\n{values}\n        ){comma}"
        )

    return f"""-- OTOMATIK URETILDI — generate_vectors.py
-- Elle duzenlemeyin; degisiklikler bir sonraki calistirmada silinir.
--
-- Fs = {FS} Hz, kesim = {CUTOFF_HZ:.0f} Hz, format Q1.{FRACTION_BITS}
-- Konfigurasyonlar (tap sayisi): {tap_counts}

library ieee;
use ieee.std_logic_1164.all;

use work.fir_pkg.all;

package fir_coeffs_pkg is

    constant FIR_MAX_TAPS       : natural := {max_taps};
    constant FIR_NUM_CONFIGS    : natural := {len(coeff_sets)};
    constant FIR_DEFAULT_CONFIG : natural := {DEFAULT_CONFIG_ID};

    type tap_count_array_t is array (natural range <>) of natural;
    type coef_set_array_t is
        array (natural range <>) of coef_array_type(0 to FIR_MAX_TAPS - 1);

    constant FIR_TAP_COUNTS : tap_count_array_t(0 to FIR_NUM_CONFIGS - 1) :=
        ({tap_counts});

    -- Kisa setler sifirla doldurulmustur; gecerli uzunluk FIR_TAP_COUNTS'ta.
    constant FIR_COEFF_SETS : coef_set_array_t(0 to FIR_NUM_CONFIGS - 1) := (
{chr(10).join(blocks)}
    );

end package fir_coeffs_pkg;
"""


# ==========================================================================
# Olcum ve sartname dogrulamasi
# ==========================================================================

def measure(y: np.ndarray, x: np.ndarray) -> tuple[float, float]:
    """Olcum penceresinde (passband_db, stopband_db) dondur."""
    sl = slice(SKIP_SAMPLES, SKIP_SAMPLES + ANALYSIS_LEN)
    return (
        suppression_db(y[sl], x[sl], FS, PASS_TONE_HZ),
        suppression_db(y[sl], x[sl], FS, STOP_TONE_HZ),
    )


def verify_spec(name: str, passband_db: float, stopband_db: float) -> None:
    """Konfigurasyonun sartnameyi sagladigini URETIM aninda dogrula.

    Sartnameyi saglamayan bir konfigurasyonu test setine koymak anlamsizdir:
    test hakli olarak kalir ve insan toleransi gevsetmeye egilimlenir.
    Hata burada, ne yapilmasi gerektigini soyleyen bir mesajla cikmali.
    """
    assert stopband_db <= MIN_STOPBAND_DB, (
        f"[{name}] stopband sartnameyi saglamiyor: {stopband_db:.2f} dB, en fazla "
        f"{MIN_STOPBAND_DB:.1f} dB olmali. Tap sayisini artir veya kesimi dusur."
    )
    assert passband_db >= MAX_PASSBAND_LOSS_DB, (
        f"[{name}] passband kaybi fazla: {passband_db:.2f} dB, en az "
        f"{MAX_PASSBAND_LOSS_DB:.1f} dB olmali. Kesim frekansini yukselt "
        f"(Hamming gecis bandi ~3,3/N kadar genistir)."
    )


# ==========================================================================
# Ana akis
# ==========================================================================

def build_input() -> np.ndarray:
    """Iki tonlu Q1.15 giris vektoru (butun konfigurasyonlar icin ortak)."""
    tones = sine_wave(PASS_TONE_HZ, SIGNAL_DURATION_S, FS) + sine_wave(
        STOP_TONE_HZ, SIGNAL_DURATION_S, FS
    )
    return to_q15(TONE_AMPLITUDE * tones)[:VECTOR_LEN]


def main() -> None:
    VECTORS.mkdir(exist_ok=True)
    HDL_SRC.mkdir(parents=True, exist_ok=True)

    x_fix = build_input()
    save_vector(VECTORS / "input.csv", x_fix)

    coeff_sets: list[np.ndarray] = []
    configs: list[dict] = []

    for cfg_id, order in enumerate(CONFIG_ORDERS):
        h_fix = to_q15(fir1(order, CUTOFF_HZ / (FS / 2)))
        name = f"tap{len(h_fix)}"
        worst_acc = check_accumulator_width(h_fix, name)

        # Beklenen cikis, donanimin gordugu dekuantize degerlerden hesaplanir;
        # boylece karsilastirma toleranssiz (bit-birebir) yapilabilir.
        y_fix = to_q15(apply_filter(from_q15(x_fix), from_q15(h_fix)))
        passband_db, stopband_db = measure(from_q15(y_fix), from_q15(x_fix))
        verify_spec(name, passband_db, stopband_db)

        save_vector(VECTORS / f"expected_{name}.csv", y_fix)
        coeff_sets.append(h_fix)

        configs.append({
            "id": cfg_id,
            "name": name,
            "num_taps": int(len(h_fix)),
            "group_delay": int((len(h_fix) - 1) // 2),
            "dc_gain_q15": int(np.sum(h_fix)),
            "worst_accumulator": worst_acc,
            "expected_csv": f"expected_{name}.csv",
            "expected_passband_db": float(passband_db),
            "expected_stopband_db": float(stopband_db),
        })

    # --- DC doygunluk vektoru (yalnizca varsayilan konfigurasyon) ---------
    # Doygunlugun tetiklenmesi DC kazancinin 1'in ustunde olmasina bagli;
    # bu da katsayi yuvarlamasindan gelen 1 LSB'lik fazlalik. Kirilgan bir
    # bagimlilik, o yuzden burada acikca dogrulaniyor.
    h_default = coeff_sets[DEFAULT_CONFIG_ID]
    dc_gain = int(np.sum(h_default))
    assert dc_gain > 2**FRACTION_BITS, (
        f"varsayilan config {DEFAULT_CONFIG_ID}: DC kazanci {dc_gain} <= "
        f"{2**FRACTION_BITS}; tam olcek DC girisi cikista tasmaz ve doygunluk "
        f"dali test edilemez. Baska bir varsayilan konfigurasyon secin."
    )
    x_dc = np.full(DC_VECTOR_LEN, Q15_MAX, dtype=np.int16)
    y_dc = to_q15(apply_filter(from_q15(x_dc), from_q15(h_default)), allow_clipping=True)
    save_vector(VECTORS / "input_dc.csv", x_dc)
    save_vector(VECTORS / "expected_dc.csv", y_dc)

    # --- Manifest ---------------------------------------------------------
    manifest = {
        "fs": FS,
        "cutoff_hz": CUTOFF_HZ,
        "pass_tone_hz": PASS_TONE_HZ,
        "stop_tone_hz": STOP_TONE_HZ,
        "skip_samples": SKIP_SAMPLES,
        "analysis_len": ANALYSIS_LEN,
        "min_stopband_db": MIN_STOPBAND_DB,
        "max_passband_loss_db": MAX_PASSBAND_LOSS_DB,
        "reference_tol_db": REFERENCE_TOL_DB,
        "default_config_id": DEFAULT_CONFIG_ID,
        "input_csv": "input.csv",
        "input_dc_csv": "input_dc.csv",
        "expected_dc_csv": "expected_dc.csv",
        "configs": configs,
    }
    write_if_changed(VECTORS / "configs.json", json.dumps(manifest, indent=2) + "\n")

    pkg_written = write_if_changed(
        HDL_SRC / "fir_coeffs_pkg.vhd", render_coeffs_package(coeff_sets)
    )

    # --- Ozet -------------------------------------------------------------
    print(f"kesim {CUTOFF_HZ:.0f} Hz | pencere: {SKIP_SAMPLES} atla + {ANALYSIS_LEN} olc")
    print(f"{'config':>8} {'tap':>4} {'gecikme':>8} {'DC kaz.':>8} {'passband':>10} {'stopband':>10}")
    for c in configs:
        print(
            f"{c['name']:>8} {c['num_taps']:>4} {c['group_delay']:>8} "
            f"{c['dc_gain_q15']:>8} {c['expected_passband_db']:>9.2f}dB "
            f"{c['expected_stopband_db']:>9.2f}dB"
        )
    print(f"dc vektoru: config {DEFAULT_CONFIG_ID}, son cikis {int(y_dc[-1])} (doygunluk {Q15_MAX})")
    print(f"katsayi paketi: {'yazildi' if pkg_written else 'degismedi, atlandi'}")


if __name__ == "__main__":
    main()
